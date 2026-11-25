"""Test funzionali delle API (il codice TF-xx corrisponde alla tabella della relazione)."""

from datetime import datetime, timedelta

from tests.conftest import accedi

ADMIN = ("admin@museo.example", "Admin2026")
VISITATORE = ("visitatore@museo.example", "Visitatore2026")


def crea_evento(client, admin, capienza, giorni=10):
    data = (datetime.now() + timedelta(days=giorni)).strftime("%Y-%m-%dT%H:%M")
    risposta = client.post("/api/eventi", headers=admin, json={
        "titolo": "Evento di prova", "tipo": "visita_guidata", "data_ora": data, "capienza": capienza})
    return risposta.json()["id"]


def registra(client, email):
    client.post("/api/registrazione", json={"email": email, "nome": "Mario", "cognome": "Verdi",
                                            "password": "Password1", "consenso_privacy": True})
    return accedi(client, email, "Password1")


def test_tf01_ricerca_catalogo(client):
    assert len(client.get("/api/opere").json()) == 10
    risultati = client.get("/api/opere", params={"q": "Valsecchi"}).json()
    assert len(risultati) == 2
    assert all(o["sezione"] == "Archeologia" for o in client.get("/api/opere", params={"sezione": "Archeologia"}).json())


def test_tf02_registrazione_e_accesso(client):
    dati = {"email": "mario@prova.it", "nome": "Mario", "cognome": "Verdi",
            "password": "Password1", "consenso_privacy": True}
    assert client.post("/api/registrazione", json=dati).status_code == 201
    assert client.post("/api/registrazione", json=dati).status_code == 409                 # email già usata
    assert client.post("/api/registrazione", json={**dati, "email": "a@b.it", "consenso_privacy": False}).status_code == 422
    assert client.post("/api/login", json={"email": "mario@prova.it", "password": "Password1"}).status_code == 200
    assert client.post("/api/login", json={"email": "mario@prova.it", "password": "sbagliata"}).status_code == 401


def test_tf03_prenotazione_aggiorna_i_posti(client):
    admin = accedi(client, *ADMIN)
    evento_id = crea_evento(client, admin, capienza=5)
    visitatore = accedi(client, *VISITATORE)
    assert client.post("/api/prenotazioni", headers=visitatore, json={"evento_id": evento_id, "posti": 2}).status_code == 201
    evento = [e for e in client.get("/api/eventi").json() if e["id"] == evento_id][0]
    assert evento["posti_disponibili"] == 3


def test_tf04_capienza_non_superabile(client):
    admin = accedi(client, *ADMIN)
    evento_id = crea_evento(client, admin, capienza=3)
    client.post("/api/prenotazioni", headers=accedi(client, *VISITATORE), json={"evento_id": evento_id, "posti": 2})
    risposta = client.post("/api/prenotazioni", headers=registra(client, "altro@prova.it"),
                           json={"evento_id": evento_id, "posti": 2})
    assert risposta.status_code == 409
    assert "ne restano 1" in risposta.json()["detail"]


def test_tf05_prenotazione_doppia(client):
    evento_id = crea_evento(client, accedi(client, *ADMIN), capienza=10)
    visitatore = accedi(client, *VISITATORE)
    client.post("/api/prenotazioni", headers=visitatore, json={"evento_id": evento_id, "posti": 1})
    assert client.post("/api/prenotazioni", headers=visitatore, json={"evento_id": evento_id, "posti": 1}).status_code == 409


def test_tf06_annullamento(client):
    evento_id = crea_evento(client, accedi(client, *ADMIN), capienza=2)
    visitatore = accedi(client, *VISITATORE)
    p = client.post("/api/prenotazioni", headers=visitatore, json={"evento_id": evento_id, "posti": 2}).json()
    assert client.delete(f"/api/prenotazioni/{p['id']}", headers=registra(client, "x@prova.it")).status_code == 404
    assert client.delete(f"/api/prenotazioni/{p['id']}", headers=visitatore).status_code == 204
    evento = [e for e in client.get("/api/eventi").json() if e["id"] == evento_id][0]
    assert evento["posti_disponibili"] == 2


def test_tf07_regole_feedback(client):
    visitatore = accedi(client, *VISITATORE)
    mie = client.get("/api/prenotazioni/mie", headers=visitatore).json()
    futura = [p for p in mie if p["data_ora"] > datetime.now().strftime("%Y-%m-%dT%H:%M")][0]
    assert client.post("/api/feedback", headers=visitatore, json={"prenotazione_id": futura["id"], "voto": 5}).status_code == 409
    passata = [p for p in mie if p["stato"] == "presente" and not p["feedback_inviato"]][0]
    assert client.post("/api/feedback", headers=visitatore, json={"prenotazione_id": passata["id"], "voto": 4}).status_code == 201
    assert client.post("/api/feedback", headers=visitatore, json={"prenotazione_id": passata["id"], "voto": 4}).status_code == 409


def test_tf08_funzioni_riservate(client):
    assert client.get("/api/dashboard").status_code == 401
    assert client.get("/api/dashboard", headers=accedi(client, *VISITATORE)).status_code == 403
    admin = accedi(client, *ADMIN)
    assert client.get("/api/dashboard", headers=admin).status_code == 200
    prenotati = client.get("/api/eventi/4/prenotazioni", headers=admin).json()
    risposta = client.post(f"/api/prenotazioni/{prenotati[0]['id']}/presenza", headers=admin)
    assert risposta.json()["stato"] == "presente"
