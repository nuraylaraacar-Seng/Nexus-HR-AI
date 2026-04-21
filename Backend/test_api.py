"""
FastAPI endpoint'leri için integration testler.
Çalıştırmak için: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def client():
    """Test client'ı mock data engine ile oluşturur."""
    mock_engine = MagicMock()
    mock_engine.df = pd.DataFrame({'Salary': [50000, 60000]})
    mock_engine.calculate_dynamic_kpi.return_value = {
        "department": "All", "metric": "Salary",
        "calculation": "mean", "value": 55000.0,
        "total_employees": 2, "status": "Reliable"
    }
    mock_engine.predict_flight_risk_advanced.return_value = [
        {"Employee_Name": "Test User", "Department": "IT", "Salary": 45000, "ManagerName": "Mgr A"}
    ]
    mock_engine.analyze_gender_pay_gap.return_value = {
        "IT": {"M": 60000, "F": 50000, "Pay_Gap_Percentage": 16.7}
    }
    mock_engine.get_risk_summary.return_value = {
        "total_employees": 100, "average_salary": 55000,
        "flight_risk_count": 10, "average_engagement": 3.2
    }
    mock_engine.get_correlation_matrix.return_value = {
        "EngagementSurvey": 0.45, "EmpSatisfaction": 0.38, "SpecialProjectsCount": 0.21
    }

    mock_ai = MagicMock()
    mock_ai.model = MagicMock()
    mock_ai.generate_executive_summary.return_value = {
        "report_title": "AI Stratejik Yönetici Özeti",
        "ai_insight": "Test insight.",
        "status": "Success"
    }

    with patch('Backend.main.engine', mock_engine), patch('Backend.main.ai_engine', mock_ai):
        from Backend.main import app
        with TestClient(app) as c:
            yield c


# --- HEALTH CHECK ---

def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# --- KPI ENDPOİNT ---

class TestKPIEndpoint:

    def test_valid_kpi_request(self, client):
        response = client.post("/api/v1/analytics/kpi", json={
            "department": "All", "metric": "Salary", "calc_type": "mean"
        })
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_invalid_metric_rejected(self, client):
        response = client.post("/api/v1/analytics/kpi", json={
            "department": "All", "metric": "DROP TABLE", "calc_type": "mean"
        })
        assert response.status_code == 422  # Pydantic validation error

    def test_invalid_calc_type_rejected(self, client):
        response = client.post("/api/v1/analytics/kpi", json={
            "department": "All", "metric": "Salary", "calc_type": "delete"
        })
        assert response.status_code == 422


# --- FLIGHT RISK ENDPOİNT ---

def test_flight_risk_returns_list(client):
    response = client.get("/api/v1/analytics/flight-risk")
    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)


# --- GENDER PAY GAP ENDPOİNT ---

def test_gender_pay_gap_returns_dict(client):
    response = client.get("/api/v1/analytics/gender-pay-gap")
    assert response.status_code == 200
    assert isinstance(response.json()["data"], dict)


# --- AI SUMMARY ENDPOİNT ---

def test_ai_summary_success(client):
    response = client.get("/api/v1/ai/executive-summary")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "report_title" in data
    assert "ai_insight" in data
