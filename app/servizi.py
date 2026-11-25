"""Regole di funzionamento delle prenotazioni e dei feedback."""

from app.database import adesso
from app.repository import EventoRepository, FeedbackRepository, PrenotazioneRepository


class ErroreRegola(Exception):
    """Errore sollevato quando un'operazione non rispetta le regole del museo."""

    def __init__(self, codice_http, messaggio):
        super().__init__(messaggio)
        self.codice_http = codice_http
        self.messaggio = messaggio


class ServizioPrenotazioni:
    def __init__(self, con):
        self.con = con
        self.eventi = EventoRepository(con)
        self.prenotazioni = PrenotazioneRepository(con)
        self.feedback = FeedbackRepository(con)

    def prenota(self, utente_id, evento_id, posti):
        evento = self.eventi.leggi(evento_id)
        if evento is None:
            raise ErroreRegola(404, "Evento non trovato")
        if evento["data_ora"] < adesso():
            raise ErroreRegola(409, "L'evento si è già svolto")
        if self.prenotazioni.attiva(utente_id, evento_id):
            raise ErroreRegola(409, "Hai già una prenotazione per questo evento")
        if posti > evento["posti_disponibili"]:
            raise ErroreRegola(409, f"Posti insufficienti: ne restano {evento['posti_disponibili']}")
        nuovo_id = self.prenotazioni.crea(utente_id, evento_id, posti)
        self.con.commit()
        return nuovo_id

    def annulla(self, utente_id, prenotazione_id):
        p = self.prenotazioni.leggi(prenotazione_id)
        if p is None or p["utente_id"] != utente_id:
            raise ErroreRegola(404, "Prenotazione non trovata")
        if p["stato"] != "confermata" or p["data_ora"] < adesso():
            raise ErroreRegola(409, "Questa prenotazione non si può annullare")
        self.prenotazioni.cambia_stato(prenotazione_id, "annullata")

    def registra_presenza(self, prenotazione_id):
        p = self.prenotazioni.leggi(prenotazione_id)
        if p is None:
            raise ErroreRegola(404, "Prenotazione non trovata")
        if p["stato"] == "annullata":
            raise ErroreRegola(409, "La prenotazione è stata annullata")
        self.prenotazioni.cambia_stato(prenotazione_id, "presente")

    def lascia_feedback(self, utente_id, prenotazione_id, voto, commento):
        p = self.prenotazioni.leggi(prenotazione_id)
        if p is None or p["utente_id"] != utente_id:
            raise ErroreRegola(404, "Prenotazione non trovata")
        if p["data_ora"] > adesso():
            raise ErroreRegola(409, "Potrai lasciare un voto dopo l'evento")
        if p["stato"] == "annullata" or p["feedback_inviato"]:
            raise ErroreRegola(409, "Non è possibile lasciare un voto per questa prenotazione")
        return self.feedback.crea(prenotazione_id, voto, commento)
