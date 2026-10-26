# 🤖 Rezifa AI — AI-Powered Developer Knowledge API

An AI-powered developer documentation assistant built with **FastAPI, PostgreSQL, pgvector, and Retrieval-Augmented Generation (RAG)**.

Rezifa AI allows developers to upload PDF, TXT, and Markdown documentation, ask questions about their content, and receive AI-generated answers with relevant source citations.

The default chat model is **Google Gemini `gemini-3.5-flash-lite`**. Ollama with Qwen3:4B remains available for local inference.

---

## 📌 Table of Contents

* [Overview](#-overview)
* [Features](#-features)
* [Technology Stack](#-technology-stack)
* [System Architecture](#-system-architecture)
* [How RAG Works](#-how-rag-works)
* [AI Provider Architecture](#-ai-provider-architecture)
* [Database Design](#-database-design)
* [API Endpoints](#-api-endpoints)
* [Project Structure](#-project-structure)
* [Environment Variables](#-environment-variables)
* [Installation](#-installation)
* [API Documentation](#-api-documentation)
* [Deployment Notes](#-deployment-notes)
* [Security](#-security)
* [Testing](#-testing)
* [Current Limitations](#-current-limitations)

---

## 🎯 Overview

Developers often need to search through large technical documentation files to find specific information.

Rezifa AI simplifies this process by allowing developers to organize documents into workspaces and ask questions using natural language.

Instead of sending entire documents to a language model, Rezifa AI retrieves relevant text chunks from PostgreSQL using vector similarity search. These chunks provide context for generating relevant answers.

Workspace chat returns the generated answer and source metadata so users can
identify which document chunks were retrieved. General chat returns no sources.

### Example Use Case

A developer uploads:

* FastAPI documentation
* SQLAlchemy documentation
* PostgreSQL notes
* Docker documentation

The developer asks:

> What is dependency injection in FastAPI?

Rezifa AI retrieves relevant chunks, sends them to the configured AI model, and returns an answer with source references.

---

## ✨ Features

### 🔐 Authentication

* User registration and login
* Password hashing with bcrypt
* Bearer access tokens signed as JWTs
* Current-user profile, profile update, password change, and account deletion
* Active-account check during login

### 👤 User Management

* Retrieve the current user's profile
* Update account information
* Delete the user's account
* Protect private account information

### 📁 Workspace Management

* Create multiple workspaces
* Organize documentation by workspace
* Retrieve workspace details
* Update workspace information
* Delete workspaces
* Restrict workspace operations to the owner

### 📄 Document Management

* Upload PDF, TXT, and Markdown files to Supabase Storage
* List documents in a workspace owned by the current user
* Track processing status (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`)
* Store file metadata and extracted chunks in PostgreSQL
* No document-listing-by-ID or document-delete API is currently exposed

### 🧠 RAG Pipeline

* Extract text from uploaded documents
* Clean extracted text
* Split text into smaller chunks
* Generate embeddings
* Store embeddings using pgvector
* Retrieve up to five nearby chunks from the selected workspace
* Generate context-aware answers when a workspace is provided
* Answer general chat requests without document retrieval

### 🤖 AI Integration

* Ollama for local development
* Qwen3:4B local language model
* Google Gemini and OpenRouter for hosted inference
* Selectable Gemini, OpenRouter, or Ollama chat provider
* Gemini embeddings (`gemini-embedding-001`, 1536 dimensions) are used regardless of chat provider
* Context-aware question answering

### 📚 Source Citations

* Return source document information
* Include document IDs and filenames
* Identify source chunk indexes
* Associate retrieved context with generated answers

### ☁️ Storage and Configuration

* Supabase PostgreSQL
* pgvector vector search
* Supabase Storage
* Environment-based configuration

---

## 🛠️ Technology Stack

| Category                    | Technology                                                |
| --------------------------- | --------------------------------------------------------- |
| Language                    | Python                                                    |
| Backend Framework           | FastAPI                                                   |
| Data Validation             | Pydantic                                                  |
| ORM                         | SQLAlchemy                                                |
| Database Migrations         | Alembic                                                   |
| Database                    | Supabase PostgreSQL                                       |
| Vector Search               | pgvector                                                  |
| Authentication              | JWT                                                       |
| Password Hashing             | bcrypt                                                    |
| Local AI Runtime            | Ollama                                                    |
| Example Local AI Model      | `qwen3:4b`                                                |
| Hosted AI Providers         | Google Gemini API, OpenRouter                             |
| Default Chat Model          | `gemini-3.5-flash-lite`                                   |
| Embedding Model             | `gemini-embedding-001` (1536 dimensions)                 |
| File Storage                | Supabase Storage                                          |
| Tests                       | Python `unittest`                                         |
| Version Control             | Git, GitHub                                               |

The backend chat default is set by `DEFAULT_MODEL_PROVIDER` and `DEFAULT_MODEL`.
`GEMINI_MODEL` supplies the Gemini model when Gemini is selected without a
different model override.

---

## 🏗️ System Architecture

### Application Components

```text
User
 |
 v
FastAPI
 ├── Authentication and workspaces ─────────────> PostgreSQL
 ├── Upload ──> Supabase Storage
 │              └── Background processing ──> Gemini embeddings ──> PostgreSQL/pgvector
 └── Chat ──> Gemini / OpenRouter / Ollama
```

Document processing is queued with FastAPI `BackgroundTasks` in the running
application process; it is not a separate durable worker queue.

---

## 🧠 How RAG Works

RAG stands for **Retrieval-Augmented Generation**.

It combines information retrieval with language generation. Instead of relying only on information learned during model training, the application retrieves relevant content from a user's documents.

Rezifa AI has two main processing pipelines.

### 1. Document Ingestion Pipeline

```text
Document Upload
      |
      v
File Validation
      |
      v
Upload to Supabase Storage
      |
      v
Text Extraction
      |
      v
Text Cleaning
      |
      v
Text Chunking
      |
      v
Embedding Generation
      |
      v
Store Chunks + Embeddings
      |
      v
PostgreSQL + pgvector
      |
      v
Update Document Status
      |
      v
COMPLETED
```

Text files are decoded as UTF-8 (invalid bytes are ignored), PDFs are read
with `pypdf`, and text is split into 500-word chunks with 50-word overlap.
Each chunk is embedded with Gemini before the document status becomes
`COMPLETED`. Processing uses in-process FastAPI background tasks. If processing
fails, the status is set to `FAILED` when possible.

### 2. Question-Answering Pipeline

```text
User Question
      |
      v
Validate User Authentication
      |
      v
If workspace_id is provided:
      |
      v
Validate Workspace Ownership
      |
      v
Create Gemini Question Embedding
      |
      v
Search up to 5 chunks (distance <= 0.45)
      |
      v
Construct Contextual Prompt
      |
      v
Call LLM Provider
      |
      v
Generate Answer
      |
      v
Attach Source Metadata
      |
      v
Return Answer + Sources
```

### Example

**Question:**

```text
What is dependency injection in FastAPI?
```

**Retrieved context:**

```text
FastAPI provides dependency injection through its
dependency system. Dependencies can be declared
using Depends() and resolved for each request.
```

**Example answer:**

```text
Dependency injection in FastAPI allows a path
operation to declare the dependencies it needs.

FastAPI resolves these dependencies and provides
their results when handling the request.
```

**Sources:**

```text
- fastapi.pdf
- backend-notes.md
```

The actual answer depends on the retrieved documentation.

---

## 🤖 AI Provider Architecture

AI provider integrations are separated from API routers and business logic.

Chat requests can select a provider and model. Gemini is the default in the
example configuration; OpenRouter and Ollama are also supported.

### Architecture

```text
                  Application
                       |
                       v
                   LLMService
                       |
              +----------+----------+
              |          |          |
              v          v          v
           Ollama     Gemini    OpenRouter
              |          |          |
              v          +-----+----+
           Qwen3:4B       Hosted models
```

### 🏠 Local Development

The application uses Ollama to run Qwen3:4B locally.

```env
DEFAULT_MODEL_PROVIDER=ollama
DEFAULT_MODEL=qwen3:4b

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:4b
```

### ☁️ Hosted providers

Use Gemini or OpenRouter for hosted chat. Gemini is also required for document
embeddings and workspace retrieval.

```env
LLM_PROVIDER=gemini

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash-lite
```

**Important:** The LLM and embedding models serve different purposes.

The selected chat LLM generates answers. Gemini creates 1536-dimensional
embeddings for document chunks and questions, regardless of the chat provider.

Changing the chat provider does not change the embedding model. Existing
database vector dimensions must match the embedding vectors.

Official model documentation: https://ai.google.dev/gemini-api/docs/models

---

## 🗄️ Database Design

Rezifa AI uses Supabase PostgreSQL for relational data and pgvector for vector search.

### 1. Users

Stores user account information.

| Field         | Description           |
| ------------- | --------------------- |
| id            | Primary key           |
| name          | User's name           |
| email         | Unique email address  |
| password_hash | Hashed password       |
| role          | User role             |
| is_active     | Account status        |
| created_at    | Creation timestamp    |
| updated_at    | Last update timestamp |

### 2. Workspaces

Stores user-created workspaces.

| Field       | Description               |
| ----------- | ------------------------- |
| id          | Primary key               |
| name        | Workspace name            |
| description | Workspace description     |
| owner_id    | Workspace owner's user ID |
| created_at  | Creation timestamp        |
| updated_at  | Last update timestamp     |

### 3. Documents

Stores metadata about uploaded files.

| Field        | Description                  |
| ------------ | ---------------------------- |
| id           | Primary key                  |
| workspace_id | Associated workspace         |
| file_name    | Uploaded filename            |
| file_type    | `pdf`, `txt`, or `md`         |
| file_size    | Uploaded size in bytes       |
| storage_path | Supabase Storage object path |
| status       | Processing status            |
| created_at   | Creation timestamp           |
| updated_at   | Last update timestamp        |

### Document Status

```text
PENDING
PROCESSING
COMPLETED
FAILED
```

### 4. Document Chunks

Stores extracted text and its embedding.

| Field       | Description              |
| ----------- | ------------------------ |
| id          | Primary key              |
| document_id | Associated document      |
| content     | Extracted text chunk     |
| chunk_index | Position in the document |
| embedding   | Vector embedding         |
| created_at  | Creation timestamp       |

### Database Relationships

```text
Users
  |
  | One-to-Many
  v
Workspaces
  |
  | One-to-Many
  v
Documents
  |
  | One-to-Many
  v
Document Chunks
```

### Vector Search

A simplified PostgreSQL query using pgvector:

```sql
SELECT
    id,
    document_id,
    content,
    chunk_index,
    embedding <=> :question_embedding AS distance
FROM document_chunks
ORDER BY embedding <=> :question_embedding
LIMIT 5;
```

The `<=>` operator calculates cosine distance.

Lower distances generally indicate more similar vectors.

The application restricts the search to the requested workspace and returns
only chunks at or below a cosine distance of `0.45`.

The current model and embedding service use 1536-dimensional vectors from
Gemini. Review the Alembic migration history against the target database
before applying schema changes.

---

## 🔌 API Endpoints

The API follows a versioned route structure using `/api/v1`.

### Authentication

| Method | Endpoint                | Description                                            |
| ------ | ----------------------- | ------------------------------------------------------ |
| POST   | `/api/v1/auth/register` | Register a new user                                    |
| POST   | `/api/v1/auth/login`    | Authenticate a user                                    |
| GET    | `/api/v1/auth/`         | Retrieve the current user                              |
| PUT    | `/api/v1/auth/`         | Update the current user's name, email, and password     |
| PATCH  | `/api/v1/auth/`         | Change the current user's password                     |
| POST   | `/api/v1/auth/logout`   | Return a logout message; the JWT is not revoked         |
| DELETE | `/api/v1/auth/`         | Delete the current user's account                      |

### Workspaces

| Method | Endpoint                            | Description                |
| ------ | ----------------------------------- | -------------------------- |
| POST   | `/api/v1/workspaces/`               | Create a workspace         |
| GET    | `/api/v1/workspaces/`               | List the current user's workspaces |
| GET    | `/api/v1/workspaces/{workspace_id}` | Retrieve workspace details |
| PATCH  | `/api/v1/workspaces/{workspace_id}` | Update a workspace         |
| DELETE | `/api/v1/workspaces/{workspace_id}` | Delete a workspace         |

### Documents

| Method | Endpoint                    | Description |
| ------ | --------------------------- | ----------- |
| POST   | `/api/v1/documents/upload`  | Upload PDF, TXT, or Markdown as multipart form data |
| GET    | `/api/v1/documents/`        | List documents in an owned workspace (`workspace_id` query parameter) |

### AI Chat

| Method | Endpoint       | Description                                 |
| ------ | -------------- | ------------------------------------------- |
| POST   | `/api/v1/chat` | Ask questions about workspace documentation |
| GET    | `/api/v1/models` | List available Gemini, OpenRouter, and Ollama models |

### Health

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET    | `/health` | Check that the API process responds |
| GET    | `/health/db` | Run a database `SELECT 1` check |

Workspace collection routes include a trailing slash; workspace item routes
use `/api/v1/workspaces/{workspace_id}`.

---

## 💬 AI Chat Example

### Request

```http
POST /api/v1/chat
Content-Type: application/json
Authorization: Bearer <access_token>
```

```json
{
  "workspace_id": 1,
  "question": "What is dependency injection in FastAPI?",
  "provider": "openrouter",
  "model": "openrouter/free"
}
```

Both `provider` and `model` are optional. Omitting them uses the configured
backend defaults. Without `workspace_id`, chat uses general knowledge and
returns an empty `sources` list. With a workspace, the API verifies ownership,
creates a Gemini question embedding, and searches up to five chunks with a
cosine distance of at most `0.45`.

The model catalog filters OpenRouter models to those reporting zero input and
output prices; pricing, account access, and quotas can change. Gemini models
are listed as free only when configured in `GEMINI_FREE_MODELS`. Ollama
models run locally. Provider rate-limit responses may include a retry hint.

### Response

```json
{
  "answer": "Dependency injection in FastAPI allows a path operation to declare the dependencies it requires. FastAPI resolves these dependencies and provides their results when handling the request.",
  "sources": [
    {
      "document_id": 1,
      "file_name": "fastapi.pdf",
      "chunk_index": 12
    }
  ]
}
```

The source metadata identifies the retrieved document chunk associated with the answer.

---

## 📂 Project Structure

Main application files:

```text
devdocs-ai/
├── app/
│   ├── api/v1/
│   │   ├── ai/ai_chat_router.py
│   │   ├── documents/documents_router.py
│   │   ├── model/model_router.py
│   │   ├── users/users_router.py
│   │   └── workspaces/workspace_router.py
│   ├── core/                 # Settings and JWT/password helpers
│   ├── database/             # Async SQLAlchemy session and engine
│   ├── dependencies/         # Bearer-token dependency
│   ├── models/               # User, workspace, document, and chunk models
│   ├── schemas/              # Pydantic request/response schemas
│   └── services/             # User, workspace, document, embedding, and LLM logic
├── alembic/                  # Database migration configuration and revisions
├── frontend/                 # Static HTML, CSS, JavaScript, and logo
├── test/                     # Focused provider-selection tests
├── .env.example
├── alembic.ini
├── main.py                   # FastAPI application and static frontend mount
└── requirements.txt
```

---

## ⚙️ Environment Variables

Create a `.env` file in the project root.

### Example

```env
APP_NAME=Rezifa AI
APP_VERSION=1.0.0
DEBUG=True

DATABASE_URL=postgresql+asyncpg://postgres:<password>@<host>:5432/postgres
SECRET_KEY=<generate-a-long-random-secret>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=8

SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_KEY=<supabase-service-role-key>
SUPABASE_BUCKET_NAME=devdocs-documents

GEMINI_API_KEY=<gemini-api-key>
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_FREE_MODELS=

LLM_PROVIDER=gemini
DEFAULT_MODEL_PROVIDER=gemini
DEFAULT_MODEL=gemini-3.5-flash-lite
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:4b

OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

`DATABASE_URL`, `SECRET_KEY`, `SUPABASE_URL`, and `SUPABASE_KEY` are required
settings. A Gemini API key is needed for document embeddings and Gemini chat.
Ollama and OpenRouter credentials are only needed when those chat providers
are used. Keep the Supabase service-role key on the server; never expose it in
frontend code.

For production, configure environment variables through the hosting platform.

Never commit real API keys, database credentials, or JWT secrets to GitHub.

---

## 🚀 Installation

### Prerequisites

Install:

* Python and Git
* Supabase PostgreSQL with pgvector and a configured Storage bucket
* A Gemini API key (embeddings use Gemini even when chat uses another provider)
* Ollama only if using local chat; OpenRouter API key only if using OpenRouter

### 1. Clone the Repository

```bash
git clone https://github.com/Rezwan-Islam-Raju/devdocs-ai.git
```

Navigate into the cloned project:

```bash
cd devdocs-ai
```


### 2. Create a Virtual Environment

Windows PowerShell:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

In Windows PowerShell, copy the example file only if you do not already have `.env`, then edit its placeholders:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Set `DATABASE_URL`, `SECRET_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, and
`GEMINI_API_KEY` in `.env`. Use a PostgreSQL connection string; the application
converts its driver to `postgresql+asyncpg`. URL-encode special characters in
the database password. Create the Storage bucket named by
`SUPABASE_BUCKET_NAME` (defaults to `devdocs-documents`).

Gemini embeddings are used for document ingestion and workspace chat,
regardless of the selected chat provider. Configure `DEFAULT_MODEL_PROVIDER`
and `DEFAULT_MODEL` to choose the backend default. `GET /api/v1/models` returns
the provider catalog. OpenRouter zero-price listings and Gemini's optional
`GEMINI_FREE_MODELS` allowlist are indicators only; check current account
pricing and quota with each provider. Never commit `.env` or put real
credentials in source files.

### 5. Enable pgvector

Alembic includes a migration that enables pgvector. If the database role
cannot create the extension, enable it in Supabase before running migrations:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

The SQLAlchemy model and Gemini embedding service expect 1536 dimensions.
There is a migration mismatch to resolve before using Alembic on a fresh
database: `ed264cf862b7` adds a 768-dimensional vector column, while the
current model and later migration expect 1536 dimensions; the later migration
does not convert the vector type. Update/verify the migration chain and
database schema before running `alembic upgrade head`.

On startup, `main.py` also calls SQLAlchemy `create_all` for missing tables.
That does not upgrade existing tables; use Alembic for schema changes.

### 6. Run Database Migrations

```bash
alembic upgrade head
```

### 7. Start Ollama (only when using Ollama chat)

Download the local model:

```bash
ollama pull qwen3:4b
```

Make sure Ollama is running and accessible at:

```text
http://localhost:11434
```

### 8. Start the API and frontend

From the project root, run:

```powershell
python -m uvicorn main:app --reload
```

Keep the terminal open. FastAPI serves the backend and frontend together at **http://127.0.0.1:8000/**; no separate frontend build or server is needed.

### Rezifa AI web interface

Open **http://127.0.0.1:8000/** to use the built-in HTML, CSS, and JavaScript interface. Do not open `frontend/index.html` directly as a `file://` URL: the `/static/` assets and backend API are served by FastAPI. Sign in or create an account, create a workspace, then upload PDF, TXT, or Markdown files to ask questions about your documentation.

The frontend files are `frontend/index.html`, `frontend/styles.css`, and `frontend/app.js`. FastAPI serves the page at `/` and its CSS/JavaScript from `/static/`. Tailwind utility styles load from the CDN, so a browser internet connection is needed for those utilities; the app's custom responsive styles and animations remain in `frontend/styles.css`. Document listing is available at `GET /api/v1/documents/?workspace_id={workspace_id}` and requires a bearer token for a workspace you own.

---

## 📖 API Documentation

FastAPI automatically generates interactive API documentation.

### Swagger UI

http://127.0.0.1:8000/docs

### ReDoc

http://127.0.0.1:8000/redoc

Use Swagger UI to explore endpoints, inspect request and response schemas, and test authenticated API operations.

---

## ☁️ Deployment Notes

The repository contains a FastAPI application, Alembic migrations, and a
frontend served by FastAPI. It does not include a hosting-provider deployment
configuration. To deploy, provide the required environment variables, install
the requirements, apply and verify database migrations, and run an ASGI server
such as Uvicorn.

Before exposing an instance publicly:

* Restrict CORS origins in `main.py`; the current configuration allows all
  origins.
* Use HTTPS and protect all server-side secrets.
* Set upload size limits at the application and/or reverse-proxy layer; the
  current upload route only checks the filename extension.
* Use a durable worker for document processing if tasks must survive process
  restarts; processing currently uses in-process FastAPI background tasks.
* Review database migrations and pgvector dimensions against the target
  database.
* Verify Gemini/OpenRouter pricing, availability, and quotas.

---

## 🔒 Security

### Authentication

* Hash passwords before storing them.
* Validate JWT signatures and expiration.
* Reject invalid or expired tokens.
* Login rejects inactive accounts; the bearer-token dependency validates the
  token but does not recheck account status on each request.
* Protect private endpoints with authentication dependencies.

### Authorization

* Verify workspace ownership before retrieving documents.
* Restrict vector searches to the authorized workspace.
* Prevent cross-user access to documents and chunks.
* The current API does not expose separate administrative operations.

### File Upload Security

* The upload route allows only `.pdf`, `.txt`, and `.md` filename extensions.
* It currently has no application-level upload-size limit and uses the
  uploaded filename in the Supabase Storage path; review these behaviors
  before public deployment.
* Document processing errors are logged and the document status is set to
  `FAILED` when possible.
* There is currently no document-delete API endpoint.

### AI Security

* Treat uploaded documents as untrusted content.
* Do not allow document text to override system instructions.
* Prevent retrieval from unauthorized workspaces.
* Avoid exposing internal prompts or secrets.
* Do not assume generated answers are always correct.

### Secret Management

* Keep `.env` out of version control.
* Use separate development and production credentials.
* Protect database connection strings.
* Use a strong JWT secret.
* Never expose a Supabase service-role key to public clients.
* The frontend stores its bearer token in browser `localStorage`; account for
  the associated XSS risk when deploying.
* Logout returns a message but does not revoke an issued JWT. Tokens remain
  usable until expiration.

---

## 🧪 Testing

The current focused test suite uses Python's standard-library `unittest` and
covers provider selection, model catalog filtering, and LLM response/error
handling. It does not currently provide full database or API integration
coverage.

Run tests with:

```powershell
python -m unittest discover -s test -p "test_*.py"
```

The tests mock provider calls and do not require live Gemini, OpenRouter, or
Ollama requests.

---

## ⚠️ Current Limitations

* The project is in development; tests currently focus on LLM provider
  selection and response handling, not end-to-end database workflows.
* The document upload endpoint has no application-level size limit.
* Document processing runs as an in-process background task and is not
  persisted across process restarts.
* There is no document-delete API; file-size policy and Supabase Storage
  cleanup need attention before production use.
* Account/workspace deletion does not explicitly remove matching files from
  Supabase Storage, so orphaned objects may remain.
* CORS currently allows all origins and should be restricted for deployment.
* Logout does not revoke the token; it remains valid until its expiry.
* No `LICENSE` file is currently included in the repository.

---

**Rezifa AI — Turn your documentation into an AI-powered knowledge base.**
