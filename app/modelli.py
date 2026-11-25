"""Modelli Pydantic: descrivono e controllano i dati che arrivano alle API."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Registrazione(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    nome: str = Field(min_length=1, max_length=60)
    cognome: str = Field(min_length=1, max_length=60)
    password: str = Field(min_length=8)
    consenso_privacy: Literal[True]   # la registrazione è possibile solo accettando l'informativa


class Credenziali(BaseModel):
    email: str
    password: str


class NuovaOpera(BaseModel):
    inventario: str = Field(min_length=1)
    titolo: str = Field(min_length=1)
    autore: str = Field(min_length=1)
    anno: Optional[str] = None
    sezione: str = Field(min_length=1)
    descrizione: Optional[str] = None


class NuovoEvento(BaseModel):
    titolo: str = Field(min_length=1)
    tipo: Literal["visita_guidata", "laboratorio", "conferenza"]
    descrizione: Optional[str] = None
    data_ora: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$")
    capienza: int = Field(gt=0)


class NuovaPrenotazione(BaseModel):
    evento_id: int
    posti: int = Field(ge=1, le=4)


class NuovoFeedback(BaseModel):
    prenotazione_id: int
    voto: int = Field(ge=1, le=5)
    commento: Optional[str] = Field(default=None, max_length=500)
