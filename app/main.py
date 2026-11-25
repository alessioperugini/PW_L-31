"""MuseoDigitale: API REST del museo (FastAPI) e pubblicazione delle pagine web."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import database
from app.database import get_db
from app.modelli import Credenziali, NuovaOpera, NuovaPrenotazione, NuovoEvento, NuovoFeedback, Registrazione
from app.repository import EventoRepository, OperaRepository, PrenotazioneRepository, UtenteRepository
from app.servizi import ErroreRegola, ServizioPrenotazioni
from app.sicurezza import crea_sessione, hash_password, solo_amministratore, utente_corrente, verifica_password


@asynccontextmanager
async def avvio(app):
    database.inizializza()  # crea le tabelle e i dati di esempio al primo avvio
    yield


app = FastAPI(title="MuseoDigitale API", version="1.0",
              description="API del prototipo per il Museo Civico di Borgo San Valerio (ente simulato).",
              lifespan=avvio)


@app.exception_handler(ErroreRegola)
def gestisci_errore(request: Request, errore: ErroreRegola):
    return JSONResponse(status_code=errore.codice_http, content={"detail": errore.messaggio})


# ---------------------------------------------------------------- Accesso
@app.post("/api/registrazione", status_code=201, tags=["Accesso"])
def registrazione(dati: Registrazione, con=Depends(get_db)):
    utenti = UtenteRepository(con)
    if utenti.cerca_per_email(dati.email):
        raise HTTPException(409, "Email già registrata")
    nuovo_id = utenti.crea(dati.email, dati.nome, dati.cognome, hash_password(dati.password))
    return {"id": nuovo_id}


@app.post("/api/login", tags=["Accesso"])
def login(cred: Credenziali, con=Depends(get_db)):
    utente = UtenteRepository(con).cerca_per_email(cred.email)
    if utente is None or not verifica_password(cred.password, utente["password_hash"]):
        raise HTTPException(401, "Email o password non corretti")
    token = crea_sessione(con, utente["id"])
    return {"token": token, "utente": {k: utente[k] for k in ("id", "nome", "cognome", "ruolo")}}


@app.post("/api/logout", status_code=204, tags=["Accesso"])
def logout(utente=Depends(utente_corrente), con=Depends(get_db)):
    con.execute("DELETE FROM sessione WHERE utente_id = ?", (utente["id"],))
    con.commit()


# ---------------------------------------------------------------- Catalogo
@app.get("/api/opere", tags=["Catalogo"])
def elenco_opere(q: str = "", sezione: str = "", con=Depends(get_db)):
    return OperaRepository(con).cerca(q, sezione)


@app.post("/api/opere", status_code=201, tags=["Catalogo"])
def nuova_opera(dati: NuovaOpera, con=Depends(get_db), admin=Depends(solo_amministratore)):
    try:
        return {"id": OperaRepository(con).crea(dati.model_dump())}
    except Exception:
        raise HTTPException(409, "Numero di inventario già presente")


# ---------------------------------------------------------------- Eventi
@app.get("/api/eventi", tags=["Eventi"])
def elenco_eventi(con=Depends(get_db)):
    return EventoRepository(con).elenca_futuri()


@app.post("/api/eventi", status_code=201, tags=["Eventi"])
def nuovo_evento(dati: NuovoEvento, con=Depends(get_db), admin=Depends(solo_amministratore)):
    repo = EventoRepository(con)
    return repo.leggi(repo.crea(dati.model_dump()))


@app.get("/api/eventi/{evento_id}/prenotazioni", tags=["Eventi"])
def prenotati_evento(evento_id: int, con=Depends(get_db), admin=Depends(solo_amministratore)):
    return PrenotazioneRepository(con).dell_evento(evento_id)


# ---------------------------------------------------------------- Prenotazioni e feedback
@app.post("/api/prenotazioni", status_code=201, tags=["Prenotazioni"])
def prenota(dati: NuovaPrenotazione, utente=Depends(utente_corrente), con=Depends(get_db)):
    nuovo_id = ServizioPrenotazioni(con).prenota(utente["id"], dati.evento_id, dati.posti)
    return PrenotazioneRepository(con).leggi(nuovo_id)


@app.get("/api/prenotazioni/mie", tags=["Prenotazioni"])
def mie_prenotazioni(utente=Depends(utente_corrente), con=Depends(get_db)):
    return PrenotazioneRepository(con).dell_utente(utente["id"])


@app.delete("/api/prenotazioni/{prenotazione_id}", status_code=204, tags=["Prenotazioni"])
def annulla(prenotazione_id: int, utente=Depends(utente_corrente), con=Depends(get_db)):
    ServizioPrenotazioni(con).annulla(utente["id"], prenotazione_id)


@app.post("/api/prenotazioni/{prenotazione_id}/presenza", tags=["Prenotazioni"])
def registra_presenza(prenotazione_id: int, con=Depends(get_db), admin=Depends(solo_amministratore)):
    ServizioPrenotazioni(con).registra_presenza(prenotazione_id)
    return PrenotazioneRepository(con).leggi(prenotazione_id)


@app.post("/api/feedback", status_code=201, tags=["Prenotazioni"])
def feedback(dati: NuovoFeedback, utente=Depends(utente_corrente), con=Depends(get_db)):
    nuovo_id = ServizioPrenotazioni(con).lascia_feedback(utente["id"], dati.prenotazione_id, dati.voto, dati.commento)
    return {"id": nuovo_id}


# ---------------------------------------------------------------- Dashboard
@app.get("/api/dashboard", tags=["Dashboard"])
def dashboard(con=Depends(get_db), admin=Depends(solo_amministratore)):
    return PrenotazioneRepository(con).statistiche()


# Le pagine web (HTML, CSS, JavaScript) sono servite dallo stesso server
app.mount("/", StaticFiles(directory=Path(__file__).parent.parent / "static", html=True), name="sito")
