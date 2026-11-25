import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Ogni test usa una base dati nuova con i dati di esempio."""
    monkeypatch.setattr(database, "PERCORSO_DB", str(tmp_path / "prova.db"))
    with TestClient(app) as c:
        yield c


def accedi(client, email, password):
    risposta = client.post("/api/login", json={"email": email, "password": password})
    return {"Authorization": "Bearer " + risposta.json()["token"]}
