-- Schema della base dati di MuseoDigitale (SQLite)

CREATE TABLE IF NOT EXISTS utente (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    email            TEXT    NOT NULL UNIQUE,
    nome             TEXT    NOT NULL,
    cognome          TEXT    NOT NULL,
    password_hash    TEXT    NOT NULL,
    ruolo            TEXT    NOT NULL DEFAULT 'visitatore'
                     CHECK (ruolo IN ('visitatore', 'amministratore')),
    consenso_privacy INTEGER NOT NULL CHECK (consenso_privacy = 1)
);

CREATE TABLE IF NOT EXISTS sessione (
    token      TEXT    PRIMARY KEY,
    utente_id  INTEGER NOT NULL REFERENCES utente(id),
    scade_il   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS opera (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    inventario   TEXT    NOT NULL UNIQUE,
    titolo       TEXT    NOT NULL,
    autore       TEXT    NOT NULL,
    anno         TEXT,
    sezione      TEXT    NOT NULL,
    descrizione  TEXT
);

CREATE TABLE IF NOT EXISTS evento (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    titolo       TEXT    NOT NULL,
    tipo         TEXT    NOT NULL CHECK (tipo IN ('visita_guidata', 'laboratorio', 'conferenza')),
    descrizione  TEXT,
    data_ora     TEXT    NOT NULL,
    capienza     INTEGER NOT NULL CHECK (capienza > 0)
);

-- Un evento può riguardare più opere e un'opera può comparire in più eventi
CREATE TABLE IF NOT EXISTS evento_opera (
    evento_id  INTEGER NOT NULL REFERENCES evento(id),
    opera_id   INTEGER NOT NULL REFERENCES opera(id),
    PRIMARY KEY (evento_id, opera_id)
);

CREATE TABLE IF NOT EXISTS prenotazione (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    utente_id   INTEGER NOT NULL REFERENCES utente(id),
    evento_id   INTEGER NOT NULL REFERENCES evento(id),
    posti       INTEGER NOT NULL CHECK (posti BETWEEN 1 AND 4),
    stato       TEXT    NOT NULL DEFAULT 'confermata'
                CHECK (stato IN ('confermata', 'annullata', 'presente'))
);

CREATE TABLE IF NOT EXISTS feedback (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    prenotazione_id  INTEGER NOT NULL UNIQUE REFERENCES prenotazione(id),
    voto             INTEGER NOT NULL CHECK (voto BETWEEN 1 AND 5),
    commento         TEXT
);
