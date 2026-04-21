"""
data_engine.py için unit testler.
Çalıştırmak için: pytest tests/ -v
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# --- TEST VERİSİ ---
def make_sample_df():
    return pd.DataFrame({
        'Employee_Name': ['Alice', 'Bob', 'Carol', 'Dave', 'Eve'],
        'Department':    ['IT', 'IT', 'HR', 'HR', 'Finance'],
        'Salary':        [60000, 45000, 70000, 50000, 80000],
        'Sex':           ['F', 'M', 'F', 'M', 'F'],
        'PerformanceScore': ['Exceeds', 'Fully Meets', 'Exceeds', 'Needs Improvement', 'Fully Meets'],
        'EngagementSurvey': [2.5, 4.0, 2.8, 4.5, 1.9],
        'EmpSatisfaction':  [3.0, 4.0, 2.5, 4.0, 2.0],
        'SpecialProjectsCount': [0, 2, 0, 1, 0],
        'DateofHire': ['2018-01-01', '2019-06-15', '2017-03-20', '2020-11-01', '2016-08-05'],
        'Termd': [0, 0, 0, 0, 0],
        'ManagerName': ['Mgr A', 'Mgr A', 'Mgr B', 'Mgr B', 'Mgr C'],
    })


@pytest.fixture
def engine_with_data(tmp_path):
    """Geçici CSV dosyasıyla HRDataEngine örneği oluşturur."""
    from Backend.data_engine import HRDataEngine

    csv_path = tmp_path / "test_data.csv"
    make_sample_df().to_csv(csv_path, index=False)

    # Path güvenlik kontrolünü bypass etmek için patch kullanıyoruz
    with patch.object(HRDataEngine, '__init__', lambda self, fp: None):
        eng = HRDataEngine.__new__(HRDataEngine)
        eng.file_path = csv_path
        eng.df = make_sample_df()
        eng.df['DateofHire'] = pd.to_datetime(eng.df['DateofHire'])
        eng.df['Log_Salary'] = np.log1p(eng.df['Salary'])
    return eng


# --- calculate_dynamic_kpi TESTLERİ ---

class TestCalculateDynamicKPI:

    def test_mean_salary_all_departments(self, engine_with_data):
        result = engine_with_data.calculate_dynamic_kpi("All", "Salary", "mean")
        assert result["value"] == pytest.approx(61000.0, rel=1e-2)
        assert result["status"] == "Reliable"

    def test_mean_salary_single_department(self, engine_with_data):
        result = engine_with_data.calculate_dynamic_kpi("IT", "Salary", "mean")
        assert result["value"] == pytest.approx(52500.0, rel=1e-2)
        assert result["department"] == "IT"

    def test_invalid_metric_returns_error(self, engine_with_data):
        result = engine_with_data.calculate_dynamic_kpi("All", "DROP TABLE", "mean")
        assert "error" in result

    def test_invalid_calc_type_returns_error(self, engine_with_data):
        result = engine_with_data.calculate_dynamic_kpi("All", "Salary", "delete")
        assert "error" in result

    def test_nonexistent_department_returns_error(self, engine_with_data):
        result = engine_with_data.calculate_dynamic_kpi("Mars", "Salary", "mean")
        assert "error" in result

    def test_empty_dataframe_returns_error(self, engine_with_data):
        engine_with_data.df = pd.DataFrame()
        result = engine_with_data.calculate_dynamic_kpi("All", "Salary", "mean")
        assert "error" in result


# --- predict_flight_risk_advanced TESTLERİ ---

class TestFlightRiskAdvanced:

    def test_returns_list(self, engine_with_data):
        result = engine_with_data.predict_flight_risk_advanced()
        assert isinstance(result, list)

    def test_does_not_mutate_original_df(self, engine_with_data):
        """KRITIK: self.df'in orijinal sütunları korunmalı."""
        original_cols = set(engine_with_data.df.columns)
        engine_with_data.predict_flight_risk_advanced()
        assert set(engine_with_data.df.columns) == original_cols, \
            "predict_flight_risk_advanced self.df'i mutate etti!"

    def test_result_contains_required_fields(self, engine_with_data):
        result = engine_with_data.predict_flight_risk_advanced()
        if result:
            required_fields = {'Employee_Name', 'Department', 'Salary', 'ManagerName'}
            assert required_fields.issubset(result[0].keys())

    def test_empty_df_returns_empty_list(self, engine_with_data):
        engine_with_data.df = pd.DataFrame()
        assert engine_with_data.predict_flight_risk_advanced() == []


# --- get_risk_summary TESTLERİ ---

class TestGetRiskSummary:

    def test_returns_required_keys(self, engine_with_data):
        result = engine_with_data.get_risk_summary()
        assert 'total_employees' in result
        assert 'average_salary' in result
        assert 'flight_risk_count' in result
        assert 'average_engagement' in result

    def test_total_employees_correct(self, engine_with_data):
        result = engine_with_data.get_risk_summary()
        assert result['total_employees'] == 5


# --- analyze_gender_pay_gap TESTLERİ ---

class TestGenderPayGap:

    def test_returns_dict(self, engine_with_data):
        result = engine_with_data.analyze_gender_pay_gap()
        assert isinstance(result, dict)

    def test_pay_gap_column_exists(self, engine_with_data):
        result = engine_with_data.analyze_gender_pay_gap()
        for dept, vals in result.items():
            assert 'Pay_Gap_Percentage' in vals
