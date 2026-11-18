from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.evals.golden_dataset import GOLDEN_BENCHMARK_CASES


def test_golden_dataset_structure():
    """Verify that all golden benchmark cases are well-formed and categorised."""
    assert len(GOLDEN_BENCHMARK_CASES) >= 10
    for case in GOLDEN_BENCHMARK_CASES:
        assert case.id.startswith("golden_")
        assert len(case.question.strip()) > 10
        assert case.difficulty in ("easy", "medium", "hard")
        assert case.category
        assert "SELECT" in case.golden_sql.upper()
        assert "ecommerce." in case.golden_sql


def test_evals_api_endpoints():
    """Test REST API endpoints for EvalOps benchmark suite."""
    app = create_app()
    with TestClient(app) as client:
        # 1. GET /api/v1/evals/cases
        cases_resp = client.get("/api/v1/evals/cases")
        assert cases_resp.status_code == 200
        cases = cases_resp.json()
        assert len(cases) == len(GOLDEN_BENCHMARK_CASES)
        assert cases[0]["id"] == "golden_01"

        # 2. Filter cases by difficulty
        easy_resp = client.get("/api/v1/evals/cases?difficulty=easy")
        assert easy_resp.status_code == 200
        easy_cases = easy_resp.json()
        assert all(c["difficulty"] == "easy" for c in easy_cases)

        # 3. POST /api/v1/evals/run (mock run)
        run_resp = client.post("/api/v1/evals/run", json={"mock_run": True})
        assert run_resp.status_code == 200
        run_data = run_resp.json()
        assert run_data["summary"]["passed_cases"] == len(GOLDEN_BENCHMARK_CASES)
        assert run_data["summary"]["accuracy_percentage"] == 100.0

        # 4. GET /api/v1/evals/latest
        latest_resp = client.get("/api/v1/evals/latest")
        assert latest_resp.status_code == 200
        latest_data = latest_resp.json()
        assert "summary" in latest_data
        assert "results" in latest_data
        assert latest_data["summary"]["total_cases"] == len(GOLDEN_BENCHMARK_CASES)
        assert latest_data["summary"]["accuracy_percentage"] >= 0.0

        # 5. GET /api/v1/evals/history
        hist_resp = client.get("/api/v1/evals/history")
        assert hist_resp.status_code == 200
        history = hist_resp.json()
        assert len(history) >= 1
