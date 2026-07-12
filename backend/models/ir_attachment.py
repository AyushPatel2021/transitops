from backend.core.znova_model import ZnovaModel
from backend.core import fields, api
import hashlib
import base64

class IrAttachment(ZnovaModel):
    __tablename__ = "ir_attachment"
    _model_name_ = "ir.attachment"
    _name_field_ = "name"
    _description_ = "Attachment"

    name = fields.Char(label="Filename", required=True)
    datas = fields.Text(label="File Content")  # base64 encoded
    file_size = fields.Integer(label="File Size (bytes)")
    mimetype = fields.Char(label="MIME Type")
    checksum = fields.Char(label="Checksum (SHA256)", compute="_compute_checksum", store=True)
    
    # Link to parent record
    res_model = fields.Char(label="Resource Model", required=True)
    res_id = fields.Integer(label="Resource ID", required=True)
    res_field = fields.Char(label="Resource Field")
    
    description = fields.Char(label="Description")
    
    _role_permissions = {
        "admin": {"create": True, "read": True, "write": True, "delete": True},
        "manager": {"create": True, "read": True, "write": True, "delete": True},
        "player": {"create": True, "read": True, "write": False, "delete": False},
        "scorer": {"create": True, "read": True, "write": True, "delete": True}
    }

    @api.depends('datas')
    def _compute_checksum(self):
        """Compute SHA256 checksum of file data"""
        if self.datas:
            # Decode base64 and compute hash
            try:
                file_bytes = base64.b64decode(self.datas)
                self.checksum = hashlib.sha256(file_bytes).hexdigest()
            except Exception:
                self.checksum = None
        else:
            self.checksum = None
