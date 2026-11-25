"""Classi per l'accesso ai dati: ogni classe contiene le query SQL di una tabella.

Tutte le query usano i parametri '?' e non uniscono mai il testo inserito dall'utente
alla stringa SQL: in questo modo si evita la SQL injection.
"""

from app.database import adesso


class Repository:
    """Classe base con i metodi comuni a tutte le altre."""

    def __init__(self, con):
        self.con = con

    def leggi_uno(self, sql, parametri=()):
        riga = self.con.execute(sql, parametri).fetchone()
        return dict(riga) if riga else None

    def leggi_molti(self, sql, parametri=()):
        return [dict(r) for r in self.con.execute(sql, parametri).fetchall()]


class UtenteRepository(Repository):
    def cerca_per_email(self, email):
        return self.leggi_uno("SELECT * FROM utente WHERE email = ?", (email.lower(),))

    def crea(self, email, nome, cognome, password_hash):
        cur = self.con.execute(
            "INSERT INTO utente (email, nome, cognome, password_hash, consenso_privacy) VALUES (?, ?, ?, ?, 1)",
            (email.lower(), nome, cognome, password_hash))
        self.con.commit()
        return cur.lastrowid


class OperaRepository(Repository):
    def cerca(self, testo=None, sezione=None):
        sql, parametri = "SELECT * FROM opera WHERE 1 = 1", []
        if testo:
            sql += " AND (titolo LIKE ? OR autore LIKE ? OR descrizione LIKE ?)"
            parametri += [f"%{testo}%"] * 3
        if sezione:
            sql += " AND sezione = ?"
            parametri.append(sezione)
        return self.leggi_molti(sql + " ORDER BY sezione, titolo", tuple(parametri))

    def crea(self, dati):
        cur = self.con.execute(
            "INSERT INTO opera (inventario, titolo, autore, anno, sezione, descrizione) "
            "VALUES (:inventario, :titolo, :autore, :anno, :sezione, :descrizione)", dati)
        self.con.commit()
        return cur.lastrowid


class EventoRepository(Repository):
    # i posti prenotati non sono salvati ma calcolati sommando le prenotazioni non annullate
    SELECT = ("SELECT e.*, "
              "COALESCE((SELECT SUM(p.posti) FROM prenotazione p "
              "          WHERE p.evento_id = e.id AND p.stato <> 'annullata'), 0) AS posti_prenotati, "
              "(SELECT GROUP_CONCAT(o.titolo, ', ') FROM evento_opera eo JOIN opera o ON o.id = eo.opera_id "
              " WHERE eo.evento_id = e.id) AS opere "
              "FROM evento e")

    def elenca_futuri(self):
        eventi = self.leggi_molti(self.SELECT + " WHERE e.data_ora >= ? ORDER BY e.data_ora", (adesso(),))
        for e in eventi:
            e["posti_disponibili"] = e["capienza"] - e["posti_prenotati"]
        return eventi

    def leggi(self, evento_id):
        evento = self.leggi_uno(self.SELECT + " WHERE e.id = ?", (evento_id,))
        if evento:
            evento["posti_disponibili"] = evento["capienza"] - evento["posti_prenotati"]
        return evento

    def crea(self, dati):
        cur = self.con.execute("INSERT INTO evento (titolo, tipo, descrizione, data_ora, capienza) "
                               "VALUES (:titolo, :tipo, :descrizione, :data_ora, :capienza)", dati)
        self.con.commit()
        return cur.lastrowid


class PrenotazioneRepository(Repository):
    SELECT = ("SELECT p.*, e.titolo AS evento, e.data_ora, u.nome || ' ' || u.cognome AS nominativo, "
              "EXISTS (SELECT 1 FROM feedback f WHERE f.prenotazione_id = p.id) AS feedback_inviato "
              "FROM prenotazione p JOIN evento e ON e.id = p.evento_id JOIN utente u ON u.id = p.utente_id")

    def leggi(self, prenotazione_id):
        return self.leggi_uno(self.SELECT + " WHERE p.id = ?", (prenotazione_id,))

    def dell_utente(self, utente_id):
        return self.leggi_molti(self.SELECT + " WHERE p.utente_id = ? ORDER BY e.data_ora DESC", (utente_id,))

    def dell_evento(self, evento_id):
        return self.leggi_molti(self.SELECT + " WHERE p.evento_id = ? ORDER BY u.cognome", (evento_id,))

    def attiva(self, utente_id, evento_id):
        return self.leggi_uno("SELECT id FROM prenotazione WHERE utente_id = ? AND evento_id = ? "
                              "AND stato <> 'annullata'", (utente_id, evento_id))

    def crea(self, utente_id, evento_id, posti):
        return self.con.execute("INSERT INTO prenotazione (utente_id, evento_id, posti) VALUES (?, ?, ?)",
                                (utente_id, evento_id, posti)).lastrowid

    def cambia_stato(self, prenotazione_id, stato):
        self.con.execute("UPDATE prenotazione SET stato = ? WHERE id = ?", (stato, prenotazione_id))
        self.con.commit()

    def statistiche(self):
        """Indicatori per la dashboard dell'amministratore."""
        ora = adesso()
        generali = self.leggi_uno(
            "SELECT (SELECT COUNT(*) FROM evento WHERE data_ora < ?) AS eventi_svolti, "
            "(SELECT COALESCE(SUM(posti), 0) FROM prenotazione WHERE stato = 'presente') AS partecipanti, "
            "(SELECT COUNT(*) FROM prenotazione p JOIN evento e ON e.id = p.evento_id "
            "  WHERE e.data_ora >= ? AND p.stato = 'confermata') AS prenotazioni_attive, "
            "(SELECT ROUND(AVG(voto), 1) FROM feedback) AS voto_medio", (ora, ora))
        per_evento = self.leggi_molti(
            "SELECT e.titolo, e.capienza, "
            "COALESCE(SUM(CASE WHEN p.stato <> 'annullata' THEN p.posti END), 0) AS prenotati "
            "FROM evento e LEFT JOIN prenotazione p ON p.evento_id = e.id GROUP BY e.id ORDER BY e.data_ora")
        for e in per_evento:
            e["riempimento"] = round(100 * e["prenotati"] / e["capienza"])
        voti = {str(v): 0 for v in range(1, 6)}
        for r in self.leggi_molti("SELECT voto, COUNT(*) AS n FROM feedback GROUP BY voto"):
            voti[str(r["voto"])] = r["n"]
        return {"generali": generali, "per_evento": per_evento, "voti": voti}


class FeedbackRepository(Repository):
    def crea(self, prenotazione_id, voto, commento):
        cur = self.con.execute("INSERT INTO feedback (prenotazione_id, voto, commento) VALUES (?, ?, ?)",
                               (prenotazione_id, voto, commento))
        self.con.commit()
        return cur.lastrowid
