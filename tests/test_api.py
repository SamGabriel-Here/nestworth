from fastapi.testclient import TestClient

from src.api.app import app

client = TestClient(app)
HOME = {"area": 1100, "bedrooms": 3, "bathrooms": 2, "stories": 2, "city": "Mumbai",
        "location": "Suburb", "house_age": 8, "parking": 1, "main_road": "yes",
        "furnishing_status": "semi-furnished"}


def test_predict_returns_estimate_inside_interval():
    r = client.post("/api/predict", json=HOME)
    assert r.status_code == 200
    body = r.json()
    assert body["interval"]["lo"] <= body["estimate"] <= body["interval"]["hi"]
    assert len(body["factors"]) == 5
    assert len(body["comparables"]) == 5
    assert body["mae"] > 0


def test_predict_rejects_unknown_city():
    assert client.post("/api/predict", json={**HOME, "city": "Pune"}).status_code == 422


def test_frontend_is_served():
    assert client.get("/").status_code == 200
