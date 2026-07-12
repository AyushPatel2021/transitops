from datetime import date
from datetime import datetime
from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi import HTTPException

import backend.main
import backend.models
import backend.models.audit_log
from backend.core import fields
from backend.core.api import onchange
from backend.core.background_scheduler import get_scheduler
from backend.core.background_scheduler import setup_database_cron_task
from backend.core.base_model import Environment
from backend.core.data_loader import DataLoader
from backend.core.database import Base
from backend.core.database import SessionLocal
from backend.core.database import engine
from backend.core.error_handler import EnhancedErrorHandler
from backend.core.error_handler import setup_error_handlers
from backend.core.exceptions import UserError
from backend.core.sequence_mixin import SequenceMixin
from backend.core.znova_model import ZnovaModel
from backend.models.audit_log import AuditLog
from backend.models.cron import Cron
from backend.models.sequence import Sequence


ONE_BY_ONE_PNG = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/6X6"
    "n9sAAAAASUVORK5CYII="
)


class TestTag(ZnovaModel):
    __test__ = False
    __tablename__ = "test_tag"
    _model_name_ = "test.tag"
    _name_field_ = "name"
    _description_ = "Test Tag"

    name = fields.Char(required=True)


class TestBook(ZnovaModel):
    __test__ = False
    __tablename__ = "test_book"
    _model_name_ = "test.book"
    _name_field_ = "title"
    _description_ = "Test Book"

    title = fields.Char(required=True)
    summary = fields.Text()
    page_count = fields.Integer(default=1)
    active = fields.Boolean(default=True)
    published_on = fields.Date()
    reviewed_at = fields.DateTime()
    metadata_json = fields.JSON(default=dict)
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active")],
        default="draft",
    )
    author_id = fields.Many2one("test.author", required=True)
    tag_ids = fields.Many2many("test.tag")
    cover_image = fields.Image()
    manual_file = fields.Attachment()
    supporting_files = fields.Attachments()
    conditional_note = fields.Char(required="[('state', '=', 'active')]")
    title_upper = fields.Char(compute="_compute_title_upper", store=False)

    def _compute_title_upper(self):
        self.title_upper = self.title.upper() if self.title else None

    @onchange("title")
    def _onchange_title(self):
        if self.title:
            self.summary = f"Summary for {self.title}"


class TestAuthor(ZnovaModel):
    __test__ = False
    __tablename__ = "test_author"
    _model_name_ = "test.author"
    _name_field_ = "name"
    _description_ = "Test Author"

    name = fields.Char(required=True)
    book_ids = fields.One2many("test.book", "author_id")


class TestSequencedDoc(SequenceMixin, ZnovaModel):
    __test__ = False
    __tablename__ = "test_sequenced_doc"
    _model_name_ = "test.sequenced.doc"
    _name_field_ = "name"
    _sequence_field = "number"
    _sequence_code = "test.sequenced.doc"

    number = fields.Char(default="New")
    name = fields.Char(required=True)


class TestCronTarget(ZnovaModel):
    __test__ = False
    __tablename__ = "test_cron_target"
    _model_name_ = "test.cron.target"
    _name_field_ = "name"

    name = fields.Char(required=True)

    @classmethod
    def run_marker(cls, db):
        record = cls.create(db, {"name": "cron-ran"})
        return {"record_id": record.id}


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_all_field_types_metadata_and_column_nullability():
    metadata = TestBook.get_ui_metadata()
    field_meta = metadata["fields"]

    assert field_meta["title"]["type"] == "string"
    assert field_meta["summary"]["type"] == "text"
    assert field_meta["page_count"]["type"] == "integer"
    assert field_meta["active"]["type"] == "boolean"
    assert field_meta["published_on"]["type"] == "date"
    assert field_meta["reviewed_at"]["type"] == "datetime"
    assert field_meta["metadata_json"]["type"] == "json"
    assert field_meta["state"]["type"] == "selection"
    assert field_meta["author_id"]["type"] == "many2one"
    assert field_meta["tag_ids"]["type"] == "many2many"
    assert field_meta["cover_image"]["type"] == "image"
    assert field_meta["manual_file"]["type"] == "attachment"
    assert field_meta["supporting_files"]["type"] == "attachments"
    assert field_meta["conditional_note"]["required"] == "[('state', '=', 'active')]"
    assert TestAuthor.get_ui_metadata()["fields"]["book_ids"]["type"] == "one2many"

    assert TestBook.__table__.columns["title"].nullable is False
    assert TestBook.__table__.columns["conditional_note"].nullable is True
    assert "manual_file" not in TestBook.__table__.columns
    assert "supporting_files" not in TestBook.__table__.columns


def test_create_search_write_to_dict_and_unlink(db):
    env = Environment(db)
    author = env["test.author"].create({"name": "Ada"})._records[0]
    tag = env["test.tag"].create({"name": "Important"})._records[0]
    reviewed_at = datetime(2026, 1, 2, 3, 4, 5)

    book = env["test.book"].create({
        "title": "Engine",
        "summary": "Initial",
        "page_count": 42,
        "active": True,
        "published_on": "2026-01-01",
        "reviewed_at": reviewed_at.isoformat(),
        "metadata_json": {"level": "core"},
        "state": "active",
        "author_id": {"id": author.id},
        "tag_ids": [tag.id],
        "cover_image": ONE_BY_ONE_PNG,
        "unknown_payload_key": "ignored",
    })._records[0]

    assert book.id
    assert book.published_on == date(2026, 1, 1)
    assert book.metadata_json == {"level": "core"}
    assert book.author.id == author.id
    assert TestBook.search([("author_id.name", "=", "Ada")], db=db).ids() == [book.id]
    assert TestBook.search([("tag_ids", "in", [tag.id])], db=db).ids() == [book.id]

    as_dict = book.to_dict(max_depth=1)
    assert as_dict["author_id"]["id"] == author.id
    assert as_dict["tag_ids"] == [tag.id]
    assert as_dict["title_upper"] == "ENGINE"

    book.write(db, {
        "title": "Engine 2",
        "tag_ids": [],
    })
    assert book.title == "Engine 2"
    assert book.to_dict()["tag_ids"] == []

    assert book.unlink(db) is True
    assert TestBook.search([("id", "=", book.id)], db=db).ids() == []


def test_one2many_create_update_delete_operations(db):
    env = Environment(db)
    author = env["test.author"].create({
        "name": "Grace",
        "book_ids": {
            "create": [
                {"title": "Compiler", "author_id": None},
                {"title": "Runtime", "author_id": None},
            ]
        },
    })._records[0]

    books = TestBook.search([("author_id", "=", author.id)], order="title asc", db=db)
    assert len(books) == 2
    first_book = books[0]._records[0]

    author.write(db, {
        "book_ids": {
            "update": [{"id": first_book.id, "title": "Compiler Updated"}],
            "delete": [books[1].id],
        }
    })

    remaining = TestBook.search([("author_id", "=", author.id)], db=db)
    assert remaining.ids() == [first_book.id]
    assert remaining.title == "Compiler Updated"


def test_onchange_preserves_relational_values(db):
    author = TestAuthor.create(db, {"name": "Linus"})
    tag = TestTag.create(db, {"name": "Kernel"})
    result = TestBook.trigger_onchange(
        {
            "title": "Kernel Internals",
            "author_id": {"id": author.id},
            "tag_ids": [{"id": tag.id, "name": "Kernel"}],
        },
        "title",
        db=db,
    )

    assert result["summary"] == "Summary for Kernel Internals"
    assert result["tag_ids"] == [{"id": tag.id, "name": "Kernel"}]


def test_sequence_model_and_sequence_mixin(db):
    sequence = Sequence.create_sequence(
        db,
        name="Test Document Sequence",
        code="test.sequenced.doc",
        prefix="DOC",
        padding=4,
        number_next=7,
    )

    assert sequence.preview_format() == "DOC0007"
    assert Sequence.next_by_code(db, "test.sequenced.doc") == "DOC0007"
    assert Sequence.get_sequence_info(db, "test.sequenced.doc")["next_number"] == 8

    doc = TestSequencedDoc.create(db, {"name": "Spec", "number": "New"})
    assert doc.number == "DOC0008"

    TestSequencedDoc.reset_sequence(db, number_next=3)
    assert Sequence.get_sequence_info(db, "test.sequenced.doc")["next_number"] == 3


def test_cron_execution_and_due_job_runner(db):
    cron = Cron.create(db, {
        "name": "Test Cron",
        "code": "test.cron",
        "model_name": "test.cron.target",
        "function_name": "run_marker",
        "interval_number": 1,
        "interval_type": "minutes",
        "next_call": datetime.now() - timedelta(minutes=1),
        "active": True,
    })

    result = Cron.run_due_jobs(db)
    assert result["executed"] == 1
    assert TestCronTarget.search([("name", "=", "cron-ran")], db=db).ids()

    db.refresh(cron)
    assert cron.last_call is not None
    assert cron.next_call > cron.last_call


@pytest.mark.asyncio
async def test_database_cron_background_task_registration(db):
    scheduler = get_scheduler()
    scheduler.tasks.clear()

    await setup_database_cron_task(interval_seconds=30, run_immediately=False)

    assert "database_cron_runner" in scheduler.tasks
    assert scheduler.tasks["database_cron_runner"].interval_seconds == 30


@pytest.mark.asyncio
async def test_http_400_error_maps_to_user_error_shape():
    response = await EnhancedErrorHandler.handle_http_exception(
        None,
        HTTPException(status_code=400, detail="Bad user input"),
    )

    assert response.status_code == 400
    assert b"USER_ERROR" in response.body


def test_error_handlers_and_backend_startup_import():
    app = FastAPI()
    setup_error_handlers(app)

    assert UserError in app.exception_handlers
    assert backend.main.app.title == "Znova API"


def test_data_loader_keeps_real_user_id_field(db):
    loader = DataLoader(db)
    user = loader._create_or_update_record

    assert callable(user)
    assert "user_id" in AuditLog._field_definitions
