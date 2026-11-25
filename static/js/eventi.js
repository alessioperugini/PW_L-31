"use strict";

function schedaEvento(ev) {
  // barra che mostra quanto è pieno l'evento
  const barra = crea("div", "barra", crea("span", ""));
  barra.firstChild.style.width = Math.round(100 * ev.posti_prenotati / ev.capienza) + "%";

  const azioni = crea("div", "riga-azioni");
  if (ev.posti_disponibili === 0) {
    azioni.append(crea("span", "etichetta grigia", "Esaurito"));
  } else if (!utenteCollegato()) {
    const link = crea("a", "bottone secondario", "Accedi per prenotare");
    link.href = "accesso.html";
    azioni.append(link);
  } else {
    const scelta = crea("select", "");
    for (let n = 1; n <= Math.min(4, ev.posti_disponibili); n++) {
      const opzione = crea("option", "", n === 1 ? "1 posto" : n + " posti");
      opzione.value = n;
      scelta.append(opzione);
    }
    const bottone = crea("button", "", "Prenota");
    bottone.onclick = () => prenota(ev.id, Number(scelta.value));
    azioni.append(scelta, bottone);
  }

  return crea("article", "scheda",
    crea("span", "etichetta", TIPI[ev.tipo]),
    crea("h3", "", ev.titolo),
    crea("p", "meta", dataLeggibile(ev.data_ora)),
    crea("p", "", ev.descrizione),
    ev.opere ? crea("p", "meta", "Opere: " + ev.opere) : null,
    barra,
    crea("p", "meta", ev.posti_disponibili + " posti disponibili su " + ev.capienza),
    azioni);
}

async function caricaEventi() {
  const eventi = await api("/api/eventi");
  const griglia = document.getElementById("eventi");
  griglia.innerHTML = "";
  eventi.forEach(ev => griglia.append(schedaEvento(ev)));
}

async function prenota(eventoId, posti) {
  try {
    const p = await api("/api/prenotazioni", "POST", { evento_id: eventoId, posti: posti });
    mostraMessaggio(`Prenotazione confermata: ${p.posti} ${p.posti === 1 ? "posto" : "posti"} per «${p.evento}».`);
  } catch (errore) {
    mostraMessaggio(errore.message, true);
  }
  window.scrollTo(0, 0);
  caricaEventi();
}

caricaEventi();
