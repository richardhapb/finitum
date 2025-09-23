- [ ] Migrate models
- [ ] Use OAuth one time and store credentials in database
- [ ] Modularize OAuth server
- [ ] Test OAuth flow


# Code Structure Recommendations and Alembic Migration Guide

After analyzing your codebase, here are my recommendations for improving code structure and implementing Alembic migrations for your new models.

## Code Structure Improvements

### 1. Package Organization

Organize your code into proper packages:

```
finitum/
├── alembic/            # Migration scripts
├── src/
│   ├── api/            # FastAPI routes and endpoints
│   ├── core/           # Core functionality and config
│   │   ├── config.py   # Configuration settings
│   │   └── logging.py  # Logging setup (extracted from utils.py)
│   ├── db/             # Database related code
│   │   ├── models.py   # SQLModel models
│   │   └── session.py  # Session management
│   ├── parsers/        # Parsing logic
│   │   ├── email.py    # Email parsing
│   │   └── finance.py  # Finance data extraction
│   ├── services/       # Business logic
│   │   ├── email.py    # Email service
│   │   └── finance.py  # Finance service
│   ├── tasks/          # Celery tasks
│   ├── ui/             # Dashboard and UI components
│   └── main.py         # Application entry point
└── tests/              # Test files
```

### 2. Use Dependency Injection

Extract service classes to reduce direct dependencies and improve testability:

```python
# Example service class approach
class EmailService:
    def __init__(self, credentials: Credentials, user: User):
        self.credentials = credentials
        self.user = user

    def get_messages(self, query: str, date_from: datetime = None):
        # Implementation
```

### 3. Use Data Transfer Objects (DTOs)

Create proper input/output models for your API endpoints:

```python
class ExpenseResponse(SQLModel):
    id: int
    commerce: str
    amount: float
    currency: Currency
    category: ExpenseCategory
    date: datetime

    model_config = {"from_attributes": True}
```

## Alembic Migration Setup

To set up Alembic for your new models:

1. First, update your alembic/env.py to include your SQLModel metadata:

```python
# In alembic/env.py
from models import SQLModel

# Replace target_metadata = None with:
target_metadata = SQLModel.metadata
```

2. Create a new migration for your models:

```bash
alembic revision --autogenerate -m "Add new models"
```

3. Apply the migration:

```bash
alembic upgrade head
```

Here's a more detailed guide for implementing Alembic migrations:

File: /Users/richard/proj/finitum/alembic/env.py:11-22
```python
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from models import SQLModel  # Import your SQLModel models
target_metadata = SQLModel.metadata  # Use SQLModel's metadata
```

For new model migrations, follow these steps:

1. Add your new models to models.py
2. Run: `alembic revision --autogenerate -m "Description of your changes"`
3. Review the generated migration in alembic/versions/
4. Apply the migration: `alembic upgrade head`

## Specific Code Improvements

### 1. Configuration Management

Create a centralized configuration system:

```python
# src/core/config.py
import os
from dotenv import load_dotenv
from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://user:pass@localhost/finitum"
    REDIS_URL: str = "redis://localhost:6379/0"
    GOOGLE_CLIENT: str = ""
    GOOGLE_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:9090/google_oauth2callback"
    ALLOWED_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"

# Load environment variables first
load_dotenv()
settings = Settings()
```

### 2. Email and Message Handling

Refactor the email_manager.py to use proper dependency injection and service patterns.

### 3. Parser Improvements

The parser.py file is quite large - consider splitting it into smaller, focused modules:

```
src/parsers/
├── __init__.py
├── base.py        # Base parsing functionality
├── expense.py     # Expense parsing logic
├── transfer.py    # Transfer parsing logic
└── category.py    # Category classification
```

## Summary

1. Organize your code into logical packages with clear responsibilities
2. Use dependency injection to reduce tight coupling
3. Create proper DTOs for API communication
4. Set up Alembic with SQLModel metadata for automatic migrations
5. Extract configuration into a centralized system
6. Split large files into focused modules

This will make your codebase more maintainable, testable, and easier to evolve as your application grows.

