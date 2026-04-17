import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "TechNoir RAG API" in response.json().get("message", "")

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_version():
    response = client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()

def test_unauthenticated_me():
    response = client.get("/auth/me")
    assert response.status_code == 401  # Token missing or invalid usually throws 401 here

def test_unauthenticated_collections():
    response = client.get("/collections")
    assert response.status_code == 401

def test_login_invalid_credentials():
    response = client.post("/auth/login", json={"email": "wrong@example.com", "password": "wrong"})
    assert response.status_code == 401
    assert "detail" in response.json()
