# Project Kaagapay Backend

A secure web-based notification bridge between victims of gender-related issues and the Kaagapay volunteer network. This platform utilizes a "Bridge Concept" to ensure immediate response without compromising sensitive narrative data.

---

## 🏗️ Project Architecture (Clean Architecture)

The project is strictly separated into layers to ensure the Domain logic remains independent of the Infrastructure (Database/API).

```text
project-kaagapay/
├── app/
│   ├── api/                # Presentation: FastAPI routes & controllers
│   ├── core/               # Core Config: Security & Env settings
│   ├── models/             # Domain:
│   │   ├── entities/       # SQLAlchemy Models (DB Schema)
│   │   └── dtos/           # Pydantic Schemas (Request/Response)
│   ├── services/           # Application: Business Logic (Handshake/TTL)
│   └── db.py               # Infrastructure: Session & Engine setup
├── migrations/             # Alembic migration versions
├── .env                    # Secrets (DB credentials)
├── alembic.ini             # Alembic configuration
├── pyproject.toml          # uv project file
└── README.md
```

---

## 🚀 Setup with `uv`

### 1. Install `uv`
**Linux/macOS:**
```bash
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
```
**Windows (PowerShell):**
```powershell
powershell -c "irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex"
```

### 2. Initialize Environment
```bash
# Create virtual environment
uv venv

# Activate (Linux/macOS)
source .venv/bin/activate
# Activate (Windows)
.venv\Scripts\activate

# Install from requirements
uv pip install -r requirements.txt
```

---

## 🗄️ Database Management (Alembic)

We use Alembic to manage our Supabase PostgreSQL schema migrations.

### Create a Migration
Run this whenever you change anything in `app/models/entities/`:
```bash
alembic revision --autogenerate -m "description_of_changes"
```

### Apply to Supabase
```bash
alembic upgrade head
```

---

## ⚡ Running the Server

To start the local development server:

```bash
uvicorn main:app --reload --port 8000
```

---

## 🔐 Environment Variables (.env)
Create a `.env` in the root folder. **Do not commit this file.**

```env
# Full URL for SQLAlchemy/Alembic
DATABASE_URL=postgresql+psycopg2://postgres.[ref]:[pass]@[host]:5432/postgres?sslmode=require

# Individual Fallbacks
user=...
password=...
host=...
port=5432
dbname=postgres
```

---

## 🛡️ Security Logic
```
- **Anonymity:** No narratives are stored in the database.
- **Handshake:** Token-based system (`case_id`) for secure victim-volunteer pairing.
- **TTL:** Specific volunteer requests expire in 15 minutes via background workers.
```

---

## 🔐 Authentication (Getting a Token)

To access protected admin or volunteer routes, you must first obtain an `access_token` from Supabase.

### 1. Login via Terminal
Run this command (replace placeholders with your real info):

```bash
curl -X POST 'https://sjsgbvfpgxniweyvxemp.supabase.co/auth/v1/token?grant_type=password' \
-H "apikey: YOUR_SUPABASE_ANON_KEY" \
-H "Content-Type: application/json" \
-d '{
  "email": "sample@gmail.com",
  "password": "YOUR_PASSWORD"
}'
```

### 2. Using the Token
Copy the `access_token` from the response and use it in the **Authorize** button in Swagger (`/docs`) or as a Bearer token in your API requests.
- **Header format**: `Authorization: Bearer <your_token>`
