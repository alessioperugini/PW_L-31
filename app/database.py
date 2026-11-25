"""Connessione alla base dati SQLite, creazione delle tabelle e dati di esempio."""

import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

CARTELLA = Path(__file__).resolve().parent
PERCORSO_DB = str(CARTELLA.parent / "data" / "museo.db")


def adesso():
    """Data e ora attuali nel formato usato nel database, ad esempio 2026-11-11T18:30."""
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


def apri_connessione():
    con = sqlite3.connect(PERCORSO_DB, check_same_thread=False)
    con.row_factory = sqlite3.Row          # le righe si leggono come dizionari
    con.execute("PRAGMA foreign_keys = ON")  # attiva il controllo delle chiavi esterne
    return con


def get_db():
    """Usata da FastAPI: apre una connessione per ogni richiesta e la chiude alla fine."""
    con = apri_connessione()
    try:
        yield con
    finally:
        con.close()


def inizializza():
    Path(PERCORSO_DB).parent.mkdir(exist_ok=True)
    con = apri_connessione()
    con.executescript((CARTELLA / "schema.sql").read_text(encoding="utf-8"))
    if con.execute("SELECT COUNT(*) FROM utente").fetchone()[0] == 0:
        carica_dati_di_esempio(con)
    con.close()


# --- Dati di esempio: il Museo Civico di Borgo San Valerio è inventato ---------------------

OPERE = [
    ("BSV-01", "Madonna con il Bambino", "Maestro di San Valerio", "1460 ca.", "Pittura antica",
     "Tavola d'altare proveniente dalla pieve del borgo."),
    ("BSV-02", "Ritratto di gentiluomo", "Anonimo veneto", "1540 ca.", "Pittura antica",
     "Il personaggio regge un guanto, simbolo del suo rango."),
    ("BSV-03", "Veduta del borgo", "Ettore Valsecchi", "1872", "Ottocento",
     "Il borgo come appariva prima dell'arrivo della ferrovia."),
    ("BSV-04", "La filandaia", "Ettore Valsecchi", "1879", "Ottocento",
     "Scena di lavoro femminile nella filanda del paese."),
    ("BSV-05", "Anfora vinaria", "Produzione locale", "I sec. d.C.", "Archeologia",
     "Trovata nel 1931 durante i lavori per l'acquedotto."),
    ("BSV-06", "Fibula a balestra", "Produzione longobarda", "VII sec.", "Archeologia",
     "Spilla in bronzo dorato da una sepoltura di Valle Ronco."),
    ("BSV-07", "Lucerna con rosetta", "Produzione romana", "II sec. d.C.", "Archeologia",
     "Lampada a olio in terracotta con tracce di uso."),
    ("BSV-08", "Telaio domestico", "Manifattura locale", "fine XIX sec.", "Arti e mestieri",
     "Telaio a pedali usato per tessere la canapa."),
    ("BSV-09", "Insegna del fabbro", "Anonimo", "1905", "Arti e mestieri",
     "Insegna in ferro battuto dell'ultima forgia del centro."),
    ("BSV-10", "Composizione n. 7", "Nora Albani", "1961", "Novecento",
     "Opera astratta donata dall'artista al museo."),
]

# titolo, tipo, descrizione, giorni da oggi, ora, capienza, opere collegate
EVENTI = [
    ("Visita guidata: il Rinascimento nel borgo", "visita_guidata", "Percorso tra le opere più antiche.",
     -40, "10:30", 25, ["BSV-01", "BSV-02"]),
    ("Laboratorio: tessere la canapa", "laboratorio", "Attività per bambini dai 6 anni.",
     -25, "16:00", 15, ["BSV-08"]),
    ("Conferenza: gli scavi del 1931", "conferenza", "La storia dei ritrovamenti archeologici.",
     -10, "18:00", 50, ["BSV-05", "BSV-07"]),
    ("Visita guidata: i Longobardi a Valle Ronco", "visita_guidata", "Corredi e vita quotidiana.",
     6, "10:30", 25, ["BSV-06"]),
    ("Laboratorio: piccoli archeologi", "laboratorio", "Simulazione di uno scavo per famiglie.",
     14, "16:00", 15, ["BSV-05"]),
    ("Conferenza: Nora Albani e l'astrattismo", "conferenza", "Incontro con la curatrice.",
     28, "18:00", 50, ["BSV-10"]),
]

NOMI = ["Luca", "Elena", "Paolo", "Chiara", "Davide", "Marta", "Andrea", "Laura", "Matteo", "Irene"]
COGNOMI = ["Rossi", "Greco", "Marino", "Costa", "Fontana", "Moretti", "Barbieri", "Villa", "Serra", "Sala"]


def carica_dati_di_esempio(con):
    from app.sicurezza import hash_password

    rnd = random.Random(7)
    con.execute("INSERT INTO utente (email, nome, cognome, password_hash, ruolo, consenso_privacy) "
                "VALUES ('admin@museo.example', 'Giulia', 'Ferri', ?, 'amministratore', 1)",
                (hash_password("Admin2026"),))
    con.execute("INSERT INTO utente (email, nome, cognome, password_hash, consenso_privacy) "
                "VALUES ('visitatore@museo.example', 'Sara', 'Conti', ?, 1)",
                (hash_password("Visitatore2026"),))
    password_finta = hash_password("utente-di-prova")
    for i in range(20):
        nome, cognome = rnd.choice(NOMI), rnd.choice(COGNOMI)
        con.execute("INSERT INTO utente (email, nome, cognome, password_hash, consenso_privacy) "
                    "VALUES (?, ?, ?, ?, 1)", (f"utente{i}@esempio.example", nome, cognome, password_finta))

    for opera in OPERE:
        con.execute("INSERT INTO opera (inventario, titolo, autore, anno, sezione, descrizione) "
                    "VALUES (?, ?, ?, ?, ?, ?)", opera)

    visitatori = [r[0] for r in con.execute("SELECT id FROM utente WHERE ruolo = 'visitatore'")]
    for titolo, tipo, descrizione, giorni, ora, capienza, opere in EVENTI:
        data_ora = (datetime.now() + timedelta(days=giorni)).strftime("%Y-%m-%d") + "T" + ora
        evento_id = con.execute("INSERT INTO evento (titolo, tipo, descrizione, data_ora, capienza) "
                                "VALUES (?, ?, ?, ?, ?)", (titolo, tipo, descrizione, data_ora, capienza)).lastrowid
        for inventario in opere:
            opera_id = con.execute("SELECT id FROM opera WHERE inventario = ?", (inventario,)).fetchone()[0]
            con.execute("INSERT INTO evento_opera VALUES (?, ?)", (evento_id, opera_id))

        # prenotazioni casuali: gli eventi passati sono quasi pieni, quelli futuri a metà
        occupati = 0
        limite = capienza * (0.9 if giorni < 0 else 0.5)
        for utente_id in rnd.sample(visitatori, len(visitatori)):
            posti = rnd.choice([1, 2, 2, 3])
            if occupati + posti > limite:
                continue
            occupati += posti
            if giorni < 0:
                stato = "presente" if rnd.random() < 0.85 else "confermata"
            else:
                stato = "confermata"
            pren_id = con.execute("INSERT INTO prenotazione (utente_id, evento_id, posti, stato) "
                                  "VALUES (?, ?, ?, ?)", (utente_id, evento_id, posti, stato)).lastrowid
            if stato == "presente" and rnd.random() < 0.7:
                con.execute("INSERT INTO feedback (prenotazione_id, voto) VALUES (?, ?)",
                            (pren_id, rnd.choices([5, 4, 3, 2], weights=[45, 35, 15, 5])[0]))
    con.commit()
