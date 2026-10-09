from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import (
    AppException,
    NotFoundError,
    ValidationError,
    app_exception_handler,
    generic_exception_handler,
)
from app.core.middleware import RequestTracingMiddleware

# Create isolated test app for error handling
sample_app = FastAPI()
sample_app.add_middleware(RequestTracingMiddleware)
sample_app.add_exception_handler(AppException, app_exception_handler)
sample_app.add_exception_handler(Exception, generic_exception_handler)


@sample_app.get("/trigger-not-found")
def trigger_not_found():
    raise NotFoundError("Clinical document not found", details={"doc_id": "123"})


@sample_app.get("/trigger-validation")
def trigger_validation():
    raise ValidationError("Invalid observation unit", details={"unit": "invalid"})


@sample_app.get("/trigger-unhandled")
def trigger_unhandled():
    raise RuntimeError("Unexpected failure")


client = TestClient(sample_app, raise_server_exceptions=False)


def test_not_found_error_response():
    res = client.get("/trigger-not-found")
    assert res.status_code == 404
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"
    assert "request_id" in data["error"]


def test_validation_error_response():
    res = client.get("/trigger-validation")
    assert res.status_code == 400
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["details"]["unit"] == "invalid"


def test_unhandled_error_response():
    res = client.get("/trigger-unhandled")
    assert res.status_code == 500
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "request_id" in data["error"]
