from fastapi.testclient import TestClient

from fhir_gateway.interfaces.http.app import create_app


def test_health_returns_http_200():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200


def test_health_returns_status_ok():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.json() == {"status": "ok"}
