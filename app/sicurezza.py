"""Password, token di accesso e controllo dei ruoli."""

import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import Depends, Header, HTTPException

from app import database


def hash_password(password):
    """Calcola l'hash della password con un 'sale' casuale (PBKDF2 con SHA-256)."""
    sale = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(sale), 200_000)
    return sale + "$" + digest.hex()


def verifica_password(password, memorizzato):
    sale, digest = memorizzato.split("$")
    calcolato = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(sale), 200_000)
    return secrets.compare_digest(calcolato.hex(), digest)


def crea_sessione(con, utente_id):
    token = secrets.token_urlsafe(32)
    scadenza = (datetime.now() + timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M")
    con.execute("INSERT INTO sessione (token, utente_id, scade_il) VALUES (?, ?, ?)", (token, utente_id, scadenza))
    con.commit()
    return token


def utente_corrente(authorization: str = Header(default=""), con=Depends(database.get_db)):
    """Legge il token dall'intestazione 'Authorization: Bearer <token>' e restituisce l'utente."""
    token = authorization.removeprefix("Bearer ").strip()
    riga = con.execute(
        "SELECT u.id, u.email, u.nome, u.cognome, u.ruolo FROM sessione s JOIN utente u ON u.id = s.utente_id "
        "WHERE s.token = ? AND s.scade_il >= ?", (token, database.adesso())).fetchone()
    if riga is None:
        raise HTTPException(401, "Devi effettuare l'accesso")
    return dict(riga)


def solo_amministratore(utente=Depends(utente_corrente)):
    if utente["ruolo"] != "amministratore":
        raise HTTPException(403, "Funzione riservata all'amministratore")
    return utente
