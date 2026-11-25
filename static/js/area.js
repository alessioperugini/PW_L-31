"use strict";

const STATI = { confermata: ["Confermata", "verde"], annullata: ["Annullata", "grigia"], presente: ["Partecipato", "gialla"] };

function moduloVoto(p) {
  const voto = crea("select", "");
  const vuota = crea("option", "", "Voto...");
  vuota.value = "";
  voto.append(vuota);
  for (let v = 5; v >= 1; v--) {
    const opzione = crea("option", "", "★".repeat(v));
    opzione.value = v;
    voto.append(opzione);
  }
  const commento = crea("input", "");
  commento.placeholder = "Commento (facoltativo)";
  const invia = crea("button", "", "Invia");
  invia.onclick = async () => {
    if (!voto.value) { mostraMessaggio("Scegli un voto da 1 a 5 stelle.", true); return; }
    try {
      await api("/api/feedback", "POST", { prenotazione_id: p.id, voto: Number(voto.value), commento: commento.value });
      mostraMessaggio("Grazie, il tuo voto è stato registrato.");
      carica();
    } catch (errore) { mostraMessaggio(errore.message, true); }
  };
  return crea("div", "riga-azioni", voto, commento, invia);
}

function schedaPrenotazione(p) {
  const [testo, colore] = STATI[p.stato];
  const futura = new Date(p.data_ora + ":00") > new Date();
  const scheda = crea("article", "scheda",
    crea("span", "etichetta " + colore, testo),
    crea("h3", "", p.evento),
    crea("p", "meta", dataLeggibile(p.data_ora)),
    crea("p", "meta", p.posti === 1 ? "1 posto" : p.posti + " posti"));

  if (futura && p.stato === "confermata") {
    const annulla = crea("button", "secondario", "Annulla prenotazione");
    annulla.onclick = async () => {
      await api("/api/prenotazioni/" + p.id, "DELETE");
      mostraMessaggio("Prenotazione annullata.");
      carica();
    };
    scheda.append(crea("div", "riga-azioni", annulla));
  } else if (!futura && p.stato !== "annullata") {
    scheda.append(p.feedback_inviato ? crea("p", "meta", "✓ Voto inviato") : moduloVoto(p));
  }
  return scheda;
}

async function carica() {
  const elenco = await api("/api/prenotazioni/mie");
  const griglia = document.getElementById("prenotazioni");
  griglia.innerHTML = "";
  elenco.forEach(p => griglia.append(schedaPrenotazione(p)));
  if (elenco.length === 0) griglia.append(crea("p", "vuoto", "Non hai ancora prenotazioni."));
}

if (!utenteCollegato()) location.href = "accesso.html";
else carica();
