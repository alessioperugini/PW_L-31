# MuseoDigitale

Prototipo di piattaforma web per un museo civico: catalogo delle opere, prenotazione di eventi e visite guidate, raccolta dei voti dei visitatori e una dashboard con alcuni indicatori.
Il *Museo Civico di Borgo San Valerio* è un ente inventato e tutti i dati sono di fantasia.

Project Work, corso di laurea L-31 Informatica per le Aziende Digitali, Università Telematica Pegaso. Tema 1, traccia 22.

## Tecnologie

- **Front-end:** HTML, CSS e JavaScript (cartella `static`)
- **Back-end:** Python con FastAPI (cartella `app`)
- **Base dati:** SQLite (file `data/museo.db`, creato al primo avvio)
- **Test:** pytest (cartella `tests`)

## Struttura del codice

```
app/main.py         endpoint delle API e avvio dell'applicazione
app/database.py     connessione al database, creazione tabelle, dati di esempio
app/schema.sql      definizione delle tabelle
app/modelli.py      controllo dei dati ricevuti (Pydantic)
app/repository.py   classi con le query SQL
app/servizi.py      regole su prenotazioni e voti
app/sicurezza.py    password, token di accesso, controllo dei ruoli
static/             pagine web
tests/              test automatici
docs/diagrammi/     diagrammi usati nella relazione
```

## Come avviarlo

1. Installa Python 3.11 o successivo da [python.org](https://www.python.org/downloads/). Su Windows spunta *Add Python to PATH*.
2. Su Windows fai doppio clic su `avvia.bat`. Su macOS o Linux esegui `sh avvia.sh`.
3. Apri il browser su http://localhost:8000.

La documentazione delle API si apre all'indirizzo http://localhost:8000/docs.
Per ripartire con i dati di esempio iniziali chiudi il server e cancella la cartella `data`.

## Account di prova

| Ruolo | Email | Password |
|---|---|---|
| Amministratore | admin@museo.example | Admin2026 |
| Visitatore | visitatore@museo.example | Visitatore2026 |

## Test

```
python -m pytest -v
```

## API

| Metodo | Percorso | Chi può usarlo |
|---|---|---|
| POST | /api/registrazione | tutti |
| POST | /api/login | tutti |
| POST | /api/logout | utente collegato |
| GET | /api/opere | tutti |
| POST | /api/opere | amministratore |
| GET | /api/eventi | tutti |
| POST | /api/eventi | amministratore |
| GET | /api/eventi/{id}/prenotazioni | amministratore |
| POST | /api/prenotazioni | utente collegato |
| GET | /api/prenotazioni/mie | utente collegato |
| DELETE | /api/prenotazioni/{id} | titolare della prenotazione |
| POST | /api/prenotazioni/{id}/presenza | amministratore |
| POST | /api/feedback | titolare della prenotazione |
| GET | /api/dashboard | amministratore |
