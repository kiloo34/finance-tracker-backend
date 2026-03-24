# 🔧 FinancePro – Backend User Manual

**Application**: FinancePro API (Finance Tracker Backend)
**Version**: 1.0.0
**Stack**: FastAPI, SQLAlchemy (async), PostgreSQL, Python 3.11+
**Base URL**: `http://localhost:8000`
**Interactive Docs**: `http://localhost:8000/docs` (Swagger UI)

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Authentication](#2-authentication)
3. [API Endpoints Overview](#3-api-endpoints-overview)
4. [Transactions API](#4-transactions-api)
5. [Accounts & Pockets API](#5-accounts--pockets-api)
6. [Budgets API](#6-budgets-api)
7. [Financial Goals API](#7-financial-goals-api)
8. [Obligations API (Receivables & Debts)](#8-obligations-api-receivables--debts)
9. [Categories API](#9-categories-api)
10. [Reports API](#10-reports-api)
11. [Notifications API](#11-notifications-api)
12. [Sessions API](#12-sessions-api)
13. [Audit Log API](#13-audit-log-api)
14. [Financial Evaluation API](#14-financial-evaluation-api)
15. [Health Check](#15-health-check)
16. [Running the Backend](#16-running-the-backend)
17. [Database Setup & Migrations](#17-database-setup--migrations)
18. [Seeding Data](#18-seeding-data)
19. [Running Tests](#19-running-tests)
20. [Docker Deployment](#20-docker-deployment)

---

## 1. Getting Started

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python      | ≥ 3.11  |
| PostgreSQL  | ≥ 14    |
| pip         | latest  |

### Installation

```bash
cd fintrack-be

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file at `fintrack-be/.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/fintrack
SECRET_KEY=your-very-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

> See `.env.example` for all available variables.

---

## 2. Authentication

The API uses **JWT Bearer Token** authentication.

### Register a New User

```
POST /auth/register
```

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "StrongPassword123"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com"
}
```

---

### Login

```
POST /auth/login
```

**Request Body (form-data):**
```
username = johndoe
password = StrongPassword123
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in all subsequent requests as an `Authorization` header:

```
Authorization: Bearer <access_token>
```

### Rate Limiting

All API endpoints are protected by a **rate limiter** to prevent abuse. Exceeding the limit returns HTTP `429 Too Many Requests`.

---

## 3. API Endpoints Overview

| Resource | Prefix | Methods |
|----------|--------|---------|
| Auth | `/auth` | POST register, POST login |
| Transactions | `/transactions` | GET, POST, PUT, DELETE, GET /export/csv |
| Accounts | `/accounts` | GET, POST |
| Pockets | `/accounts/{id}/pockets` | GET, POST |
| Transfer | `/accounts/transfer` | POST |
| Budgets | `/budgets` | GET, POST, PUT, DELETE |
| Goals | `/goals` | GET, POST, PUT, DELETE |
| Obligations | `/obligations` | GET, POST, PUT, DELETE |
| Categories | `/categories` | GET, POST, PUT, DELETE |
| Reports | `/reports` | GET |
| Notifications | `/notifications` | GET, PUT |
| Sessions | `/sessions` | GET, DELETE |
| Audit | `/audit` | GET |
| Evaluate | `/evaluate` | POST |

---

## 4. Transactions API

### Get All Transactions

```
GET /transactions/
```

| Query Param | Default | Description |
|-------------|---------|-------------|
| `skip` | 0 | Pagination offset |
| `limit` | 100 | Max results to return |

Returns all transactions belonging to the authenticated user.

---

### Create a Transaction

```
POST /transactions/
```

**Request Body:**
```json
{
  "type": "expense",
  "amount": 150000,
  "description": "Lunch at warung",
  "category_id": 3,
  "transaction_date": "2026-03-04"
}
```

- `type`: `"income"` or `"expense"`
- `amount`: positive number
- `category_id`: ID of an existing category
- `transaction_date`: ISO 8601 date string

---

### Update a Transaction

```
PUT /transactions/{transaction_id}
```

Send the full updated transaction object (same body as create).

---

### Delete a Transaction

```
DELETE /transactions/{transaction_id}
```

Returns confirmation of deletion.

---

### Export Transactions as CSV

```
GET /transactions/export/csv
```

Downloads all transactions as a `.csv` file with columns:
`ID`, `Date`, `Type`, `Amount`, `Description`, `Category ID`, `Created At`

---

## 5. Accounts & Pockets API

### List All Accounts

```
GET /accounts/
```

Returns all bank accounts for the authenticated user, including associated pockets.

---

### Create an Account

```
POST /accounts/
```

**Request Body:**
```json
{
  "account_number": "1234567890",
  "owner_name": "John Doe"
}
```

---

### List Pockets for an Account

```
GET /accounts/{account_id}/pockets
```

---

### Create a Pocket

```
POST /accounts/{account_id}/pockets
```

**Request Body:**
```json
{
  "pocket_number": "P-001",
  "name": "Emergency Fund",
  "sort": "saving",
  "currency": "IDR"
}
```

- `sort`: `"saving"` or `"spending"`

---

### Transfer Between Pockets

```
POST /accounts/transfer
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `source_pocket_id` | int | Source pocket ID |
| `destination_pocket_id` | int | Destination pocket ID |
| `amount` | decimal | Amount to transfer |

> ⚠️ **Rule**: Transfers are only allowed between pockets **within the same account**. Cross-account transfers are rejected with HTTP `400`.

**Response:**
```json
{
  "message": "Transfer successful",
  "source_balance": 500000,
  "dest_balance": 1500000
}
```

---

## 6. Budgets API

### Get All Budgets

```
GET /budgets/
```

Returns all budgets for the authenticated user.

---

### Create a Budget

```
POST /budgets/
```

**Request Body:**
```json
{
  "category_id": 2,
  "amount_limit": 2000000,
  "month": 3,
  "year": 2026
}
```

---

### Update a Budget

```
PUT /budgets/{budget_id}
```

Same body as create.

---

### Delete a Budget

```
DELETE /budgets/{budget_id}
```

---

## 7. Financial Goals API

### Get All Goals

```
GET /goals/
```

---

### Create a Goal

```
POST /goals/
```

**Request Body:**
```json
{
  "name": "Emergency Fund",
  "description": "6 months of expenses",
  "target_amount": 30000000,
  "current_amount": 5000000,
  "target_date": "2026-12-31",
  "status": "in_progress"
}
```

- `status`: `"in_progress"` or `"completed"` or `"cancelled"`

---

### Update a Goal

```
PUT /goals/{goal_id}
```

Used to update progress (e.g., increase `current_amount`).

---

### Delete a Goal

```
DELETE /goals/{goal_id}
```

---

## 8. Obligations API (Receivables & Debts)

Obligations manage both **receivables** (money others owe you) and **debts** (money you owe others).

### Get All Obligations

```
GET /obligations/
```

| Query Param | Options | Description |
|-------------|---------|-------------|
| `type` | `receivable`, `debt` | Filter by obligation type |
| `skip` | int | Pagination |
| `limit` | int | Max results |

---

### Create an Obligation

```
POST /obligations/
```

**Request Body:**
```json
{
  "type": "receivable",
  "contact_name": "Budi Santoso",
  "amount": 500000,
  "remaining_amount": 500000,
  "due_date": "2026-04-01",
  "description": "Lunch loan",
  "status": "unpaid"
}
```

- `type`: `"receivable"` or `"debt"`
- `status`: `"unpaid"`, `"partially_paid"`, `"paid"`

---

### Update an Obligation

```
PUT /obligations/{obligation_id}
```

Used to record partial/full payments by updating `remaining_amount` and `status`.

---

### Delete an Obligation

```
DELETE /obligations/{obligation_id}
```

---

## 9. Categories API

### Get All Categories

```
GET /categories/
```

---

### Create a Category

```
POST /categories/
```

**Request Body:**
```json
{
  "name": "Food & Drinks",
  "type": "expense"
}
```

- `type`: `"income"` or `"expense"`

---

### Update a Category

```
PUT /categories/{category_id}
```

---

### Delete a Category

```
DELETE /categories/{category_id}
```

---

## 10. Reports API

```
GET /reports/
```

Returns aggregated financial data for the authenticated user, including:
- Monthly income vs. expense totals
- Category-level spending breakdowns
- Budget utilization data

Used to power the frontend charts and analytics page.

---

## 11. Notifications API

### Get Notifications

```
GET /notifications/
```

Returns all notifications for the user (e.g., debt due date reminders).

### Mark Notification as Read

```
PUT /notifications/{notification_id}
```

---

## 12. Sessions API

### Get Active Sessions

```
GET /sessions/
```

Returns all active login sessions for the authenticated user, including device, IP, and last activity.

### Revoke a Session

```
DELETE /sessions/{session_id}
```

Immediately invalidates the specified session token.

### Revoke All Other Sessions

```
DELETE /sessions/
```

Revokes all sessions **except** the current one.

---

## 13. Audit Log API

```
GET /audit/
```

Returns a full log of all actions performed by the authenticated user, including:
- `login` / `logout`
- `transaction.create` / `transaction.update` / `transaction.delete`
- `obligation.create.*`
- `session.revoke`
- `evaluate.run`

Each entry includes: timestamp, action type, IP address, resource type/ID.

---

## 14. Financial Evaluation API

```
POST /evaluate/
```

Runs a financial health evaluation for the authenticated user. Returns an analysis of income vs. expenses, savings rate, and debt-to-income ratio.

---

## 15. Health Check

```
GET /health
```

Returns API and database connectivity status:

```json
{
  "status": "healthy",
  "database": "connected"
}
```

If the database is unreachable:
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "detail": "..."
}
```

---

## 16. Running the Backend

### Development Server

```bash
cd fintrack-be
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be accessible at `http://localhost:8000`.

### Interactive API Docs

| Tool | URL |
|------|-----|
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |

---

## 17. Database Setup & Migrations

The project uses **Alembic** for schema migrations.

### Initialize Database

```bash
cd fintrack-be
alembic upgrade head
```

This runs all migrations and creates the full schema.

### Create a New Migration

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

### Manual Init (init.sql)

The `init.sql` file can also be used to initialize a fresh database directly:

```bash
psql -U postgres -d fintrack -f init.sql
```

---

## 18. Seeding Data

### Seed Categories

Populates default income and expense categories (Food, Transport, Salary, etc.):

```bash
python seed_categories.py
```

### Seed Users

Creates default test users (admin and regular user roles):

```bash
python seed_users.py
```

Default seeded credentials:
| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | admin |
| user1 | user123 | user |

> ⚠️ Change these passwords immediately in production environments.

---

## 19. Running Tests

```bash
cd fintrack-be
source venv/bin/activate
pytest
```

Test files are located in the `tests/` directory and `test_api.py`.

### Run a Specific Test File

```bash
pytest tests/test_transactions.py -v
```

### Run with Coverage

```bash
pytest --cov=app tests/
```

---

## 20. Docker Deployment

### Build & Run with Docker Compose

```bash
cd fintrack-be
docker-compose up --build
```

This starts:
- The FastAPI backend on port `8000`
- A PostgreSQL database container

### Environment for Docker

Update `docker-compose.yml` with your database credentials or use a `.env` file.

### Single Container Build

```bash
docker build -t fintrack-be .
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://postgres:password@host.docker.internal:5432/fintrack \
  -e SECRET_KEY=your-secret \
  fintrack-be
```

---

## Error Reference

| HTTP Code | Meaning |
|-----------|---------|
| `200` | Success |
| `201` | Resource created |
| `400` | Bad request (e.g. insufficient funds, validation error) |
| `401` | Unauthorized – missing or invalid token |
| `403` | Forbidden – access denied |
| `404` | Resource not found |
| `422` | Unprocessable entity – request body validation failed |
| `429` | Too Many Requests – rate limit exceeded |
| `500` | Internal server error |
| `503` | Service unavailable – database connection issue |

---

## Project Structure

```
fintrack-be/
├── app/
│   ├── auth/           # JWT authentication logic & routes
│   ├── core/           # Rate limiter, exception handlers, audit logger
│   ├── jobs/           # Background jobs (debt reminder scheduler)
│   ├── models.py       # SQLAlchemy ORM models
│   ├── schemas.py      # Pydantic request/response schemas
│   ├── database.py     # Async DB session factory
│   ├── routers/        # API route handlers (one file per resource)
│   ├── services/       # Business logic layer
│   └── repositories/   # Data access layer
├── migrations/         # Alembic migration files
├── tests/              # pytest test suite
├── seed_categories.py  # Category seeder
├── seed_users.py       # User seeder
├── requirements.txt    # Python dependencies
├── alembic.ini         # Alembic configuration
├── Dockerfile
└── docker-compose.yml
```

---

*FinancePro Backend API – Enterprise Financial Intelligence. © 2026*
