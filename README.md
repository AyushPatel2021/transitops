# Znova - Enterprise Web Application Framework

A comprehensive, production-ready web application framework inspired by enterprise standards, built with FastAPI (Python) and Vue.js (TypeScript). This framework provides an enterprise-grade foundation for building scalable web applications with minimal boilerplate code.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+

### Local Development Setup

#### 1. Clone and Configure

```bash
# Clone the repository
git clone <repository-url>
cd znova

# Copy environment file
cp .env.example .env
# Edit .env with your database credentials
```

#### 2. Database Setup

```bash
# Create PostgreSQL database
createdb enterprise_db

# Or using psql
psql -U postgres
CREATE DATABASE enterprise_db;
\q
```

#### 3. Backend Setup

```bash
# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r ../requirements.txt
```

#### 4. Frontend Setup

```bash
# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Starting the Application

#### Option 1: Quick Start (Recommended for Development)

```bash
# From project root - starts backend with auto-migration
python run.py
```

This will:
- Check and create migrations if needed
- Apply database migrations
- Seed initial data (admin user, roles)
- Start the backend server on http://localhost:8000

In a separate terminal:
```bash
# Start frontend
cd frontend
npm run dev
```

Frontend will be available at http://localhost:5173

#### Option 2: Fresh Database Setup

```bash
# Drops existing database, recreates it, and starts server
python setup_fresh.py

# With demo data
python setup_fresh.py --demo
```

This will:
- Drop and recreate the database
- Clean old migration files
- Create fresh initial migration
- Apply migrations
- Seed initial data
- Start the backend server

#### Option 3: Manual Start

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Default Access

- **Admin**: admin@example.com / admin123
- **User**: user@example.com / user123
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173

## 🏭 Production Deployment

### Environment Configuration

```bash
# Update .env for production
ENVIRONMENT=production
DEBUG=False
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=<generate-strong-secret-key>
```

### Option 1: Docker Deployment

```bash
# Build and start services
docker-compose -f deploy/docker-compose.production.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 2: Manual Production Deployment

#### Backend

```bash
# Install production dependencies
pip install -r requirements.txt gunicorn

# Run migrations
cd backend
alembic upgrade head

# Start with Gunicorn
gunicorn backend.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

#### Frontend

```bash
# Build for production
cd frontend
npm run build

# Serve with nginx (example config in deploy/nginx.prod.conf)
# Copy dist/ to nginx web root
sudo cp -r dist/* /var/www/html/
```

### Production Checklist

- [ ] Set strong SECRET_KEY in .env
- [ ] Configure proper DATABASE_URL
- [ ] Set ENVIRONMENT=production
- [ ] Disable DEBUG mode
- [ ] Configure CORS for your domain
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Configure logging and monitoring
- [ ] Review security settings

## 🎨 Framework Features

### Model System
- Automatic CRUD with Odoo-style field definitions
- UI auto-generated from metadata with built-in dark mode support
- Advanced search with tag-based filtering

### Real-Time Engine
- WebSocket-driven notifications
- Live data synchronization

### Enterprise Features
- Sequence System: Auto-numbering for business records
- Cron Manager: Scheduled tasks and background processes
- Secure Auth: JWT-based with Role-Based Access Control (RBAC)
- Image handling: Upload and processing with automatic UI integration

## 📁 Project Structure

```
znova/
├── backend/                    # FastAPI Backend
│   ├── api/                   # API endpoints
│   ├── core/                  # Framework core
│   ├── models/                # Application models
│   ├── services/              # Business logic
│   ├── data/                  # Initial data and menus
│   ├── migrations/            # Database migrations
│   └── scripts/               # Utility scripts
├── frontend/                  # Vue.js Frontend
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   ├── views/             # Page components
│   │   ├── stores/            # Pinia state management
│   │   └── core/              # Core utilities
│   └── package.json
├── deploy/                    # Deployment configs
├── run.py                     # Development startup script
├── setup_fresh.py             # Fresh database setup script
└── requirements.txt           # Python dependencies
```

## 🔧 Core Concepts

### Model Definition

```python
from backend.core.base_model import BaseModel
from backend.core import fields

class Equipment(BaseModel):
    __tablename__ = "equipment"

    name = fields.Char(label="Equipment Name", required=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance')
    ], label="Status", default="active")
    category_id = fields.Many2one("category", label="Category")
    requests = fields.One2many("request", "equipment_id", label="Requests")
```

### Automatic API Generation

The framework automatically generates REST endpoints:

- `GET /api/v1/models/equipment` - List records
- `POST /api/v1/models/equipment` - Create record
- `GET /api/v1/models/equipment/{id}` - Get record
- `PUT /api/v1/models/equipment/{id}` - Update record
- `DELETE /api/v1/models/equipment/{id}` - Delete record

## 🛠️ Tech Stack

**Backend:**
- FastAPI - Modern Python web framework
- SQLAlchemy - Database ORM
- PostgreSQL - Primary database
- Alembic - Database migrations
- JWT - Authentication tokens

**Frontend:**
- Vue.js 3 - Progressive JavaScript framework
- TypeScript - Type-safe JavaScript
- Pinia - State management
- PrimeVue - UI component library
- Vite - Fast build tool

## 📚 Documentation

- **[Development Guide](DEVELOPMENT.md)** - Complete framework documentation

## 🔑 Key Features

### Security
- JWT-based authentication
- Role-based access control
- Server-side validation
- CORS protection
- SQL injection prevention

### Performance
- Database connection pooling
- Automatic query optimization
- Lazy loading relationships
- Efficient WebSocket handling
- Static file optimization

### Developer Experience
- Automatic API generation
- Hot reload development
- Type safety with TypeScript
- Comprehensive error handling
- Built-in testing framework

## 📖 Getting Started

1. Follow the Quick Start guide above
2. Read the [Development Guide](DEVELOPMENT.md)
3. Explore existing models in `backend/models/`
4. Build your first model following the patterns
5. Deploy using the production guide

---

**Znova** - Building enterprise applications, simplified.
