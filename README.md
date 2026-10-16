# 🤖 DevDocs AI — AI-Powered Developer Knowledge API

An AI-powered developer documentation assistant built with **FastAPI, PostgreSQL, pgvector, and Retrieval-Augmented Generation (RAG)**.

DevDocs AI allows developers to upload PDF, TXT, and Markdown documentation, ask questions about their content, and receive AI-generated answers with relevant source citations.

The application uses **Ollama with Qwen3:4B for local development** and **Google Gemini API with `gemini-3.8-flash` as the configured production model**.

---

## 📌 Table of Contents

* [Overview](#-overview)
* [Features](#-features)
* [Technology Stack](#-technology-stack)
* [System Architecture](#-system-architecture)
* [How RAG Works](#-how-rag-works)
* [AI Provider Architecture](#[.gitignore](.gitignore)-ai-provider-architecture)
* [Database Design](#-database-design)
* [API Endpoints](#-api-endpoints)
* [Project Structure](#-project-structure)
* [Environment Variables](#-environment-variables)
* [Installation](#-installation)
* [Running the Application](#-running-the-application)
* [API Documentation](#-api-documentation)
* [Production Deployment](#-production-deployment)
* [Security](#-security)
* [Testing](#-testing)
* [Future Improvements](#-future-improvements)
* [License](#-license)

---

## 🎯 Overview

Developers often need to search through large technical documentation files to find specific information.

DevDocs AI simplifies this process by allowing developers to organize documents into workspaces and ask questions using natural language.

Instead of sending entire documents to a language model, DevDocs AI retrieves relevant text chunks from PostgreSQL using vector similarity search. These chunks provide context for generating relevant answers.

The API returns both the generated answer and source metadata so users can identify which documents contributed to the response.

### Example Use Case

A developer uploads:

* FastAPI documentation
* SQLAlchemy documentation
* PostgreSQL notes
* Docker documentation

The developer asks:

> What is dependency injection in FastAPI?

DevDocs AI retrieves relevant chunks, sends them to the configured AI model, and returns an answer with source references.

---

## ✨ Features

### 🔐 Authentication

* User registration and login
* Secure password hashing
* JWT-based authentication
* Access token management
* Refresh token support, if enabled
* Current authenticated user
* Role-based authorization
* Active and inactive account management

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
* Restrict access to workspace owners
* Support administrative access

### 📄 Document Management

* Upload PDF, TXT, and Markdown files
* Validate supported file types
* Validate file sizes
* Store uploaded files in Supabase Storage
* Track document processing status
* Retrieve document metadata
* List and delete documents

### 🧠 RAG Pipeline

* Extract text from uploaded documents
* Clean extracted text
* Split text into smaller chunks
* Generate embeddings
* Store embeddings using pgvector
* Retrieve relevant chunks through vector similarity search
* Generate context-aware answers

### 🤖 AI Integration

* Ollama for local development
* Qwen3:4B local language model
* Google Gemini API for production
* Configurable AI provider
* Separate LLM and embedding services
* Context-aware question answering

### 📚 Source Citations

* Return source document information
* Include document IDs and filenames
* Identify source chunk indexes
* Associate retrieved context with generated answers

### ☁️ Deployment

* Supabase PostgreSQL
* pgvector vector search
* Supabase Storage
* Render deployment
* Environment-based configuration
* Docker support for local development

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
| Password Hashing            | bcrypt or another supported secure hashing implementation |
| Local AI Runtime            | Ollama                                                    |
| Local AI Model              | Qwen3:4B                                                  |
| Production AI Provider      | Google Gemini API                                         |
| Configured Production Model | `gemini-3.8-flash`                                        |
| Embeddings                  | Configurable embedding model                              |
| File Storage                | Supabase Storage                                          |
| Testing                     | Pytest, HTTPX                                             |
| Containerization            | Docker, Docker Compose                                    |
| Version Control             | Git, GitHub                                               |
| Deployment                  | Render                                                    |

**Model configuration note:** `gemini-3.8-flash` is the requested model identifier. Verify its exact ID and availability in the official Gemini API model documentation before deploying.

---

## 🏗️ System Architecture

### Local Development Architecture

```text
                       User
                         |
                         v
                 FastAPI Application
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
       Authentication  RAG Service  Document Service
             |           |           |
             |           v           |
             |    Embedding Service  |
             |           |           |
             |           v           |
             |    PostgreSQL         |
             |    + pgvector         |
             |                       |
             v                       v
         JWT System           Supabase Storage
                         |
                         v
                  Ollama Provider
                         |
                         v
                      Qwen3:4B
```

### Production Architecture

```text
                         User
                           |
                           v
                    Render Deployment
                           |
                           v
                    FastAPI Application
                           |
               +-----------+-----------+
               |           |           |
               v           v           v
          Supabase      Supabase     Gemini API
         PostgreSQL      Storage       |
               |                       |
               v                       v
            pgvector             AI Generation
```

### Architectural Principles

* Keep business logic outside API routers.
* Separate document processing from AI generation.
* Use a dedicated embedding service.
* Keep AI provider integrations modular.
* Enforce authentication and workspace ownership.
* Store uploaded files outside the application filesystem.
* Keep secrets in environment variables.

---

## 🧠 How RAG Works

RAG stands for **Retrieval-Augmented Generation**.

It combines information retrieval with language generation. Instead of relying only on information learned during model training, the application retrieves relevant content from a user's documents.

DevDocs AI has two main processing pipelines.

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

If processing fails, the document status should be updated to `FAILED` whenever possible.

### 2. Question-Answering Pipeline

```text
User Question
      |
      v
Validate User Authentication
      |
      v
Validate Workspace Ownership
      |
      v
Generate Question Embedding
      |
      v
Vector Similarity Search
      |
      v
Retrieve Relevant Chunks
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

This architecture makes it possible to configure different providers for local development and production.

### Architecture

```text
                  Application
                       |
                       v
                   LLMService
                       |
              +--------+--------+
              |                 |
              v                 v
        OllamaProvider     GeminiProvider
              |                 |
              v                 v
           Qwen3:4B       Gemini API
                         gemini-3.8-flash
```

### 🏠 Local Development

The application uses Ollama to run Qwen3:4B locally.

```env
LLM_PROVIDER=ollama

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:4b
```

### ☁️ Production

The application is configured to use the Gemini API.

```env
LLM_PROVIDER=gemini

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.8-flash
```

### Provider Benefits

* Switch providers through configuration.
* Keep provider-specific code out of routers.
* Simplify local development.
* Use hosted inference in production.
* Make testing and maintenance easier.

**Important:** The LLM and embedding models serve different purposes.

The LLM generates answers, while the embedding model converts text into vectors for semantic search.

Changing the LLM does not automatically change the embedding model. Document chunks and user questions must use compatible embedding models with matching vector dimensions.

Official model documentation: https://ai.google.dev/gemini-api/docs/models

---

## 🗄️ Database Design

DevDocs AI uses Supabase PostgreSQL for relational data and pgvector for vector search.

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
| filename     | Original filename            |
| file_type    | File format                  |
| file_size    | File size                    |
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

In the actual application, vector searches should also restrict results to the authorized workspace.

The vector column dimensions must match the selected embedding model.

---

## 🔌 API Endpoints

The API follows a versioned route structure using `/api/v1`.

### Authentication

| Method | Endpoint                | Description                                            |
| ------ | ----------------------- | ------------------------------------------------------ |
| POST   | `/api/v1/auth/register` | Register a new user                                    |
| POST   | `/api/v1/auth/login`    | Authenticate a user                                    |
| POST   | `/api/v1/auth/refresh`  | Refresh an access token, if implemented                |
| GET    | `/api/v1/auth/me`       | Retrieve the current user                              |
| POST   | `/api/v1/auth/logout`   | Log out or revoke a token, depending on implementation |

### Users

| Method | Endpoint           | Description                         |
| ------ | ------------------ | ----------------------------------- |
| GET    | `/api/v1/users/me` | Retrieve the current user's profile |
| PATCH  | `/api/v1/users/me` | Update the current user's profile   |
| DELETE | `/api/v1/users/me` | Delete the current user's account   |

### Workspaces

| Method | Endpoint                            | Description                |
| ------ | ----------------------------------- | -------------------------- |
| POST   | `/api/v1/workspaces`                | Create a workspace         |
| GET    | `/api/v1/workspaces`                | List accessible workspaces |
| GET    | `/api/v1/workspaces/{workspace_id}` | Retrieve workspace details |
| PATCH  | `/api/v1/workspaces/{workspace_id}` | Update a workspace         |
| DELETE | `/api/v1/workspaces/{workspace_id}` | Delete a workspace         |

### Documents

| Method | Endpoint                          | Description                               |
| ------ | --------------------------------- | ----------------------------------------- |
| POST   | `/api/v1/documents`               | Upload a document                         |
| GET    | `/api/v1/documents`               | List accessible documents                 |
| GET    | `/api/v1/documents/{document_id}` | Retrieve document details                 |
| DELETE | `/api/v1/documents/{document_id}` | Delete a document and its associated data |

### AI Chat

| Method | Endpoint       | Description                                 |
| ------ | -------------- | ------------------------------------------- |
| POST   | `/api/v1/chat` | Ask questions about workspace documentation |

These endpoints describe the intended API design. Verify each route against the actual implementation before treating it as available.

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
  "question": "What is dependency injection in FastAPI?"
}
```

### Response

```json
{
  "answer": "Dependency injection in FastAPI allows a path operation to declare the dependencies it requires. FastAPI resolves these dependencies and provides their results when handling the request.",
  "sources": [
    {
      "document_id": 1,
      "filename": "fastapi.pdf",
      "chunk_index": 12
    }
  ]
}
```

The source metadata identifies the retrieved document chunk associated with the answer.

---

## 📂 Project Structure

The following is a suggested structure. Adjust it to match the actual repository.

```text
DevDocs-AI/
│
├── app/
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   │
│   ├── database/
│   │   └── session.py
│   │
│   ├── models/
│   │   ├── user_model.py
│   │   ├── workspace_model.py
│   │   ├── document_model.py
│   │   └── document_chunk_model.py
│   │
│   ├── schemas/
│   │   ├── user_schema.py
│   │   ├── workspace_schema.py
│   │   ├── document_schema.py
│   │   └── chat_schema.py
│   │
│   ├── routers/
│   │   ├── auth_router.py
│   │   ├── user_router.py
│   │   ├── workspace_router.py
│   │   ├── document_router.py
│   │   └── chat_router.py
│   │
│   ├── services/
│   │   ├── user_service.py
│   │   ├── workspace_service.py
│   │   ├── document_service.py
│   │   ├── embedding_service.py
│   │   ├── rag_service.py
│   │   └── llm_service.py
│   │
│   ├── providers/
│   │   ├── ollama_provider.py
│   │   └── gemini_provider.py
│   │
│   └── dependencies/
│       └── auth_dependency.py
│
├── alembic/
├── tests/
├── .env.example
├── .gitignore
├── alembic.ini
├── main.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Environment Variables

Create a `.env` file in the project root.

### Example

```env
APP_NAME=DevDocs AI
APP_VERSION=1.0.0
DEBUG=true

DATABASE_URL=your_database_connection_string

JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=8

LLM_PROVIDER=ollama

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:4b

GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.8-flash

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key
SUPABASE_STORAGE_BUCKET=documents
```

Use only the variables required by your implementation.

For production, configure environment variables through the hosting platform.

Never commit real API keys, database credentials, or JWT secrets to GitHub.

---

## 🚀 Installation

### Prerequisites

Install:

* Python
* Git
* Access to a Supabase PostgreSQL database
* Ollama for local model inference
* A Gemini API key for production integration

### 1. Clone the Repository

```bash
git clone https://github.com/Rezwan-Islam-Raju/devdocs-ai.git
```

Navigate into the project:

```bash
cd DevDocs-AI
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

Create `.env` and configure your database, JWT, Supabase Storage, and AI settings.

### 5. Enable pgvector

Open the Supabase SQL Editor and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Confirm that your database schema, vector dimensions, and SQLAlchemy models are configured correctly.

### 6. Run Database Migrations

```bash
alembic upgrade head
```

### 7. Start Ollama

Download the local model:

```bash
ollama pull qwen3:4b
```

Make sure Ollama is running and accessible at:

```text
http://localhost:11434
```

### 8. Start the API

If `main.py` is located in the project root:

```bash
uvicorn main:app --reload
```

The application should now be available locally.

---

## 📖 API Documentation

FastAPI automatically generates interactive API documentation.

### Swagger UI

http://127.0.0.1:8000/docs

### ReDoc

http://127.0.0.1:8000/redoc

Use Swagger UI to explore endpoints, inspect request and response schemas, and test authenticated API operations.

---

## ☁️ Production Deployment

The production architecture uses managed services to reduce infrastructure requirements.

### Deployment Services

| Service             | Responsibility                                      |
| ------------------- | --------------------------------------------------- |
| Render              | FastAPI hosting                                     |
| Supabase PostgreSQL | Relational database                                 |
| pgvector            | Vector similarity search                            |
| Supabase Storage    | Uploaded document storage                           |
| Gemini API          | AI answer generation and, if configured, embeddings |

### Production Environment

Configure the required environment variables in Render.

Example:

```env
DEBUG=false
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_production_api_key
GEMINI_MODEL=gemini-3.8-flash
DATABASE_URL=your_production_database_url
```

Configure JWT secrets, Supabase credentials, storage settings, and the embedding model as required by the application.

### Deployment Considerations

* Do not run Ollama inside a small Render free-tier instance.
* Store documents in object storage instead of the ephemeral application filesystem.
* Run database migrations as part of the deployment process.
* Handle database connection limits.
* Handle Gemini API errors and rate limits.
* Enforce document upload limits.
* Avoid exposing secrets in logs or error responses.
* Verify free-tier quotas and availability before deployment.

Free-tier limitations may change over time.

---

## 🔒 Security

### Authentication

* Hash passwords before storing them.
* Validate JWT signatures and expiration.
* Reject invalid or expired tokens.
* Check account status.
* Protect private endpoints with authentication dependencies.

### Authorization

* Verify workspace ownership before retrieving documents.
* Restrict vector searches to the authorized workspace.
* Prevent cross-user access to documents and chunks.
* Protect administrative operations with role checks.

### File Upload Security

* Validate file extensions and file sizes.
* Do not trust user-supplied filenames.
* Use safe storage object paths.
* Handle malformed files safely.
* Clean up stored files and associated database records during deletion.

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

---

## 🧪 Testing

DevDocs AI uses Pytest and HTTPX for automated API testing.

Recommended test cases include:

* User registration
* Login and authentication
* Invalid and expired JWTs
* Workspace CRUD operations
* Workspace ownership checks
* Document upload validation
* Document processing success and failure
* Embedding generation
* Vector similarity search
* AI chat responses
* Source citation metadata
* Cross-workspace access prevention
* Document deletion
* Account deletion

Run tests with:

```bash
pytest
```

Mock external AI services where appropriate to avoid unnecessary API usage and make tests more predictable.

---

## 🔮 Future Improvements

Potential future enhancements include:

* Celery and Redis for background processing
* Streaming AI responses
* Conversation history
* Hybrid keyword and vector search
* Retrieval reranking
* Improved chunking strategies
* Document reprocessing
* Usage tracking and rate limiting
* More comprehensive integration tests
* Docker-based production deployment
* Advanced observability and monitoring

These are optional extensions for future versions.

---

## 📌 Project Status

**Development in progress.**

The README describes the intended architecture and feature set. Actual API availability depends on the implementation and testing status of each feature.

---

## 📄 License

Add an appropriate open-source license before distributing the project.

---

**DevDocs AI — Turn your documentation into an AI-powered knowledge base.**
