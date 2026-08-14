from app import app, load_model
import pandas as pd


def test_public_pages_render():
    client = app.test_client()
    for path in ("/", "/register", "/login", "/admin"):
        response = client.get(path)
        assert response.status_code == 200
    html = client.get("/").get_data(as_text=True)
    assert "SpefacTech" in html
    assert "2019" in html


def test_protected_pages_redirect_without_session():
    client = app.test_client()
    assert client.get("/cropRecommender").status_code == 302
    assert client.get("/dashboard").status_code == 302


def test_post_requires_csrf_token():
    client = app.test_client()
    assert client.post("/getinfo", data={"username": "demo", "password": "demo"}).status_code == 400


def test_model_pipeline_predicts():
    model = load_model()
    sample = pd.DataFrame(
        [{
            "pH": 7.03,
            "N": 118.72,
            "P": 25.0,
            "K": 185.82,
            "OC": 0.78,
            "Particles": 0.0016862,
            "Water_holding_content": 1.4,
            "Soil_type": "clay",
        }]
    )
    prediction = model.predict(sample)[0]
    assert isinstance(prediction, str)
    assert prediction
