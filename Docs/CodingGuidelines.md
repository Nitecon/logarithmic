# General Python Project - Coding Guidelines

## 1. Introduction

This document provides a set of general coding standards and best practices for Python projects. The goal is to maintain code quality, consistency, and maintainability across all services and applications.

> **Project-Specific Documentation**
>
> This document is for **general** Python standards. All project-specific information, such as:
>
> * Detailed architecture (e.g., specific microservices, data flow)
> * Domain logic and business rules
> * Environment setup (e.g., specific `.env` keys)
> * Deployment procedures
>
> ...must be documented in a separate file, such as `docs/README.md` or `docs/architecture.md`.

---

## 2. Table of Contents

1.  [Introduction](#1-introduction)
2.  [Table of Contents](#2-table-of-contents)
3.  [General Quick Guidelines](#3-general-quick-guidelines)
4.  [Project Structure](#4-project-structure)
5.  [Code Organization](#5-code-organization)
6.  [Configuration Management](#6-configuration-management)
7.  [Error Handling & Exceptions](#7-error-handling-exceptions)
8.  [Logging Standards](#8-logging-standards)
9.  [Testing Guidelines](#9-testing-guidelines)
10. [Documentation](#10-documentation)
11. [CI/CD](#11-cicd)
12. [Security & Performance](#12-security-performance)
13. [Appendix: Web & Data Patterns](#13-appendix-web-data-patterns)

---

## 3. General Quick Guidelines

* **Project Structure**: Follow the standard `src/` layout. (See [Project Structure](#4-project-structure)).
* **Dependencies**: Manage dependencies and project settings via `pyproject.toml`.
* **Configuration**: Use `pydantic-settings` to load configuration from environment variables. Do not read `os.environ` directly in application code.
* **Logging**: Use Python's built-in `logging` module. Get loggers with `logging.getLogger(__name__)`.
* **Data Models**: Use `pydantic` models for all data structures, API payloads, and message formats. This provides runtime validation.
* **Testing**: Use `pytest` for all tests. Use `pytest-mock` for mocking and `pytest.mark.parametrize` for table-driven tests.
* **Formatting**: Use `black` for code formatting and `ruff` (or `isort`) for import sorting. This is non-negotiable and should be enforced by CI.
* **Type Hinting**: All new code **must** include type hints for function arguments and return values.

---

## 4. Project Structure

A standard `src`-based layout is preferred as it prevents common import issues.

. ├── src/ │ └── my_project/ # Main application package │ ├── init.py │ ├── main.py # Application entry point (runs the service) │ ├── app.py # FastAPI/Flask app definition (if web service) │ ├── config.py # Configuration (Pydantic models) │ ├── core/ # Core business logic │ │ ├── init.py │ │ └── services.py │ │ │ └── data/ # Data access, models, db clients │ ├── init.py │ ├── models.py # Pydantic data models │ └── database.py # Database connection/repository logic │ ├── tests/ # All tests │ ├── conftest.py # Pytest fixtures │ ├── test_core.py │ └── test_data.py │ ├── docs/ # Documentation │ └── README.md # PROJECT-SPECIFIC architecture/setup │ ├── .github/ # GitHub workflows │ └── workflows/ │ └── ci.yml │ ├── pyproject.toml # Project definition, dependencies, tool config ├── requirements.txt # (Optional) Pinned dependencies for prod builds └── README.md # General project overview (what it is)


---

## 5. Code Organization

* **`src/my_project/main.py`**: The main entry point. Responsible for loading config, setting up logging, and starting the application (e.g., running the web server or starting a processing loop).
* **`src/my_project/config.py`**: Defines `pydantic-settings` models for loading all environment variables.
* **`src/my_project/app.py`**: (If web service) Defines the FastAPI/Flask application object, registers routes, and includes health/metrics endpoints.
* **`src/my_project/core/`**: Contains the main business logic of the application, decoupled from the web framework or data layer.
* **`src/my_project/data/`**: Contains all logic for interacting with databases, external APIs, or message queues. Pydantic models should be defined in `data/models.py`.

---

## 6. Configuration Management

All configuration must be done through environment variables.

### Configuration Loading

Use `pydantic-settings` to load config into a typed object. This provides validation and IDE auto-completion.

```python
# src/my_project/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class DatabaseSettings(BaseSettings):
    # Prefix: MY_PROJECT_DATABASE_URL="..."
    model_config = SettingsConfigDict(env_prefix='MY_PROJECT_DATABASE_')
    
    url: str
    pool_size: int = 5

class AppSettings(BaseSettings):
    # Prefix: MY_PROJECT_LOG_LEVEL="INFO"
    model_config = SettingsConfigDict(env_prefix='MY_PROJECT_')
    
    log_level: str = "INFO"
    debug: bool = False
    db: DatabaseSettings = DatabaseSettings()

@lru_cache
def load_settings() -> AppSettings:
    """Loads and caches the application settings."""
    return AppSettings()

# --- Usage in other modules ---
# from my_project.config import load_settings
#
# settings = load_settings()
# log.setLevel(settings.log_level)
# db_conn = create_pool(settings.db.url)

7. Error Handling & Exceptions

Define custom exceptions for your application's domain. This makes error handling more explicit.
Python

# src/my_project/core/exceptions.py

class MyProjectError(Exception):
    """Base exception for this application."""
    pass

class InvalidInputError(MyProjectError):
    """Raised for invalid user input or request data."""
    def __init__(self, message: str = "Invalid input provided"):
        super().__init__(message)

class ProcessingError(MyProjectError):
    """Raised when a core business logic step fails."""
    def __init__(self, message: str = "Failed to process request"):
        super().__init__(message)

Error Handling Pattern

Catch specific custom exceptions first, then catch general exceptions.
Python

# src/my_project/core/services.py
from .exceptions import InvalidInputError, ProcessingError, MyProjectError
from .models import RequestModel, ResponseModel
import logging

log = logging.getLogger(__name__)

class MainService:
    def handle_request(self, req: RequestModel) -> ResponseModel:
        try:
            if not req.name:
                raise InvalidInputError("Missing name in request")
            
            # ... core logic ...
            result = self._do_work(req)
            if not result:
                raise ProcessingError("Work resulted in no output")
            
            return ResponseModel(status="Success", data=result)
        
        except MyProjectError as e:
            # Handle known application errors
            log.warning(
                "Request failed validation or processing", 
                extra={"request_id": req.id, "error": str(e)}
            )
            return ResponseModel(status="Failure", error_message=str(e))
        
        except Exception as e:
            # Handle unexpected errors
            log.error(
                "Unhandled exception during request processing",
                exc_info=True,
                extra={"request_id": req.id}
            )
            return ResponseModel(status="Failure", error_message="Internal server error")

8. Logging Standards

Log Levels

    DEBUG: Detailed information for debugging.

    INFO: General operational information (e.g., "Service started," "Request received").

    WARNING: Non-critical issues (e.g., "Retrying connection," "Invalid data received").

    ERROR: Errors that prevent an operation from completing (includes exception info).

    CRITICAL: Errors that require the application to stop.

Logging Best Practices

    Structured Logging: Use the extra kwarg to add key-value pairs. This is essential for observability platforms (Datadog, Splunk, etc.).

    Context: Include relevant context (e.g., request_id, user_id).

    Exception Logging: Use exc_info=True in log.error or log.critical calls within an except block to capture the stack trace.

    Sensitive Data: Never log sensitive information (passwords, credentials, full tokens, PII).

    Get Logger: Always use logging.getLogger(__name__) at the top of the file.

Python

import logging
log = logging.getLogger(__name__)

# Good: Includes context
log.info(
    "Processing new request",
    extra={"request_id": req_id, "user_id": user_id}
)

# Good: Includes stack trace in an except block
try:
    x = 1 / 0
except ZeroDivisionError:
    log.error(
        "Failed to process data",
        exc_info=True,
        extra={"request_id": req_id}
    )

# Bad: Missing context and structure
log.info("Processing request " + req_id)

9. Testing Guidelines

Unit Tests

    Place tests in the tests/ directory, mirroring the package structure.

    Use pytest as the test runner.

    Use pytest.mark.parametrize for table-driven tests.

    Use pytest-mock (via the mocker fixture) for mocking.

    Unit tests should not make network calls or touch a real database.

Python

# tests/test_core_service.py
import pytest
from src.my_project.core.services import MainService
from src.my_project.core.models import RequestModel, ResponseModel
from src.my_project.core.exceptions import ProcessingError

@pytest.mark.parametrize(
    "name, request_data, mock_result, expected_response, expect_exception",
    [
        (
            "valid request",
            RequestModel(id="123", name="test"),
            {"foo": "bar"},
            ResponseModel(status="Success", data={"foo": "bar"}),
            None
        ),
        (
            "processing failure",
            RequestModel(id="456", name="fail"),
            None,
            None,
            ProcessingError
        ),
        # ... more test cases
    ]
)
def test_handle_request(
    mocker, name, request_data, mock_result, expected_response, expect_exception
):
    # 1. Setup
    mock_db = mocker.MagicMock()
    if expect_exception:
        mock_db.do_work.side_effect = expect_exception
    else:
        mock_db.do_work.return_value = mock_result
    
    service = MainService(db_client=mock_db)
    
    # 2. Execute & Assert
    if expect_exception:
        # Test for known failure case
        response = service.handle_request(request_data)
        assert response.status == "Failure"
    else:
        # Test for success case
        response = service.handle_request(request_data)
        assert response == expected_response

10. Documentation

Code Documentation

    Document all public functions, classes, and modules using docstrings.

    Follow Google or reST docstring format.

    Include argument descriptions, return values, and any exceptions raised.

    Use type hints to supplement, not replace, docstrings.

Project Documentation

    README.md (root): High-level overview. What is this project? How do I do a basic install?

    docs/README.md or docs/architecture.md: Project-specific details. This is where domain logic, architecture diagrams, setup guides, and environment variables are documented.

11. CI/CD

GitHub Actions (or similar)

    CI pipelines must run on all pull requests.

    CI pipeline must include:

        Linting: ruff check .

        Formatting: black --check . and ruff format --check .

        Testing: pytest

Container Images

    Use multi-stage builds in your Dockerfile to create small, secure production images.

    Run containers as a non-root user.

    Scan images for vulnerabilities as part of the CI/CD process.

12. Security & Performance

Security

    Dependencies: Regularly update dependencies and use tools like pip-audit or safety to scan for vulnerabilities.

    Least Privilege: Ensure the application (and its container/VM) has only the minimum permissions necessary to function.

    Inputs: Validate all inputs, especially those from users or external systems (Pydantic helps with this).

Performance

    Async: Use asyncio and httpx/aiohttp for I/O-bound applications (like web servers or API clients).

    Caching: Use functools.lru_cache for simple in-memory caching or Redis for distributed caching.

    Timeouts: Always set timeouts for all external calls (databases, APIs, etc.).

13. Appendix: Web & Data Patterns

    The following sections provide common patterns for web applications and data access.

A. Web Framework & Routing (FastAPI)

Shutterstock

FastAPI is recommended for new web services due to its performance and automatic data validation with Pydantic.
Python

# src/my_project/app.py
from fastapi import FastAPI, Depends, HTTPException
from .config import load_settings, AppSettings
from .core.services import MainService
from .data.models import RequestModel, ResponseModel

app = FastAPI()
service = MainService() # Use dependency injection for this in a real app

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}

@app.post("/process", response_model=ResponseModel)
async def process_request(
    request: RequestModel, # 1. Validates request body
    settings: AppSettings = Depends(load_settings) # 2. Injects config
):
    """
    Processes a new request.
    """
    try:
        # 3. Call core logic
        response = service.handle_request(request)
        if response.status == "Failure":
            raise HTTPException(status_code=400, detail=response.error_message)
        
        # 4. FastAPI serializes the Pydantic response model
        return response
    
    except HTTPException:
        raise # Re-raise FastAPI errors
    except Exception as e:
        log.error("Unhandled API error", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

B. Data Access Pattern (Repository)

Decouple your business logic from your database implementation using the Repository pattern.
Python

# src/my_project/data/database.py
from abc import ABC, abstractmethod
from .models import MyDataModel
import logging

log = logging.getLogger(__name__)

class AbstractRepository(ABC):
    """Defines the interface for data access."""
    
    @abstractmethod
    def get_by_id(self, item_id: str) -> MyDataModel | None:
        raise NotImplementedError
    
    @abstractmethod
    def save(self, model: MyDataModel) -> None:
        raise NotImplementedError

class PostgresRepository(AbstractRepository):
    """PostgreSQL implementation of the repository."""
    
    def __init__(self, db_pool):
        self.db = db_pool # Assumes a connection pool
    
    def get_by_id(self, item_id: str) -> MyDataModel | None:
        log.debug("Fetching from Postgres", extra={"id": item_id})
        # ... conn = self.db.get_conn() ...
        # ... row = conn.execute("SELECT ...") ...
        # return MyDataModel.model_validate(row) if row else None
        pass
        
    def save(self, model: MyDataModel) -> None:
        log.debug("Saving to Postgres", extra={"id": model.id})
        # ... conn = self.db.get_conn() ...
        # ... conn.execute("INSERT ...") ...
        pass

class MemoryRepository(AbstractRepository):
    """In-memory implementation for testing."""
    
    def __init__(self):
        self._data = {}
        
    def get_by_id(self, item_id: str) -> MyDataModel | None:
        return self._data.get(item_id)
        
    def save(self, model: MyDataModel) -> None:
        self._data[model.id] = model