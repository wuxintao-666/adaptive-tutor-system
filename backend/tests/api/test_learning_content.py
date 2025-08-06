# tests/api/test_learning_content.py
import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add the backend directory to the path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.insert(0, backend_path)

# Now import the app
from app.main import app

client = TestClient(app)

def test_get_learning_content():
    """Test getting learning content for a topic"""
    response = client.get("/api/v1/learning-content/div_span")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["message"] == "success"
    assert "data" in data
    assert data["data"]["topic_id"] == "div_span"
    assert "title" in data["data"]
    assert "code" in data["data"]
    assert "documentation_md" in data["data"]

def test_get_learning_content_not_found():
    """Test getting learning content for a non-existent topic"""
    response = client.get("/api/v1/learning-content/non_existent_topic")
    assert response.status_code == 404

def test_get_test_task():
    """Test getting test task for a topic"""
    response = client.get("/api/v1/test-tasks/div_span")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["message"] == "success"
    assert "data" in data
    assert data["data"]["topic_id"] == "div_span"
    assert "description_md" in data["data"]
    assert "start_code" in data["data"]
    assert "checkpoints" in data["data"]

def test_get_test_task_not_found():
    """Test getting test task for a non-existent topic"""
    response = client.get("/api/v1/test-tasks/non_existent_topic")
    assert response.status_code == 404