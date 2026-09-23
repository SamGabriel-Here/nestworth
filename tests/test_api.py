from fastapi.testclient import TestClient

from src.api.app import app
from src.pipeline.generate import CITIES

client = TestClient(app)
HOME = {"area": 1100, "bedrooms": 3, "bathrooms": 2, "stories": 2, "city": "Mumbai",
        "location": "Suburb", "property_type": "Apartment", "house_age": 8, "parking": 1,
        "main_road": "yes", "furnishing_status": "semi-furnished"}


def test_predict_returns_estimate_inside_interval():
    r = client.post("/api/predict", json=HOME)
    assert r.status_code == 200
    body = r.json()
    assert body["interval"]["lo"] <= body["estimate"] <= body["interval"]["hi"]
    assert len(body["factors"]) == 5
    assert len(body["comparables"]) == 5
    assert body["mae"] > 0


def test_curve_and_cities():
    body = client.post("/api/predict", json=HOME).json()
    assert any(p["area"] == HOME["area"] for p in body["curve"])
    assert all(p["lo"] <= p["estimate"] <= p["hi"] for p in body["curve"])
    assert sorted(c["city"] for c in body["cities"]) == sorted(CITIES)
    prices = [c["estimate"] for c in body["cities"]]
    assert prices == sorted(prices, reverse=True)


def test_predict_rejects_unknown_values():
    assert client.post("/api/predict", json={**HOME, "city": "Atlantis"}).status_code == 422
    assert client.post("/api/predict", json={**HOME, "property_type": "Castle"}).status_code == 422


def test_frontend_is_served():
    assert client.get("/").status_code == 200
