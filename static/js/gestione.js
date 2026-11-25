"use strict";

// Disegna un grafico a barre orizzontali con semplici elementi HTML
function grafico(id, voci, massimo) {
  const contenitore = document.getElementById(id);
  contenitore.innerHTML = "";
  for (const [etichetta, valore, suffisso] of voci) {
    const barra = crea("span", "");
    barra.style.width = (100 * valore / massimo) + "%";
    contenitore.append(crea("div", "voce",
      crea("span", "", etichetta), crea("div", "traccia", barra), crea("span", "valore", valore + suffisso)));
  }
}

async function caricaDashboard() {
  const d = await api("/api/dashboard");
  const g = d.generali;
  const tessere = [
    [g.eventi_svolti, "eventi svolti"],
    [g.partecipanti, "partecipanti"],
    [g.prenotazioni_attive, "prenotazioni per eventi futuri"],
    [g.voto_medio ? g.voto_medio + " / 5" : "–", "voto medio"],
  ];
  const kpi = document.getElementById("kpi");
  kpi.innerHTML = "";
  for (const [valore, testo] of tessere) kpi.append(crea("div", "scheda", crea("strong", "", valore), crea("span", "", testo)));

  grafico("grafico-eventi", d.per_evento.map(e => [e.titolo.split(": ").pop(), e.riempimento, "%"]), 100);
  const voti = Object.entries(d.voti).reverse().map(([v, n]) => ["★".repeat(v), n, ""]);
  grafico("grafico-voti", voti, Math.max(1, ...voti.map(v => v[1])));
}

async function caricaEventi() {
  // per la registrazione delle presenze si usano gli eventi futuri (più vicino in alto)
  const eventi = await api("/api/eventi");
  const scelta = document.getElementById("scelta-evento");
  scelta.innerHTML = "";
  for (const ev of eventi) {
    const opzione = crea("option", "", dataLeggibile(ev.data_ora).split(",")[0] + " – " + ev.titolo);
    opzione.value = ev.id;
    scelta.append(opzione);
  }
  caricaPrenotati();
}

async function caricaPrenotati() {
  const eventoId = document.getElementById("scelta-evento").value;
  const corpo = document.getElementById("elenco-prenotati");
  corpo.innerHTML = "";
  if (!eventoId) return;
  for (const p of await api(`/api/eventi/${eventoId}/prenotazioni`)) {
    const cella = crea("td", "");
    if (p.stato === "confermata") {
      const bottone = crea("button", "secondario", "Registra ingresso");
      bottone.onclick = async () => { await api(`/api/prenotazioni/${p.id}/presenza`, "POST"); caricaPrenotati(); caricaDashboard(); };
      cella.append(bottone);
    }
    corpo.append(crea("tr", "", crea("td", "", p.nominativo), crea("td", "numero", p.posti),
      crea("td", "", crea("span", "etichetta " + (p.stato === "presente" ? "gialla" : "verde"), p.stato)), cella));
  }
}

document.getElementById("form-evento").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/api/eventi", "POST", {
      titolo: document.getElementById("ev-titolo").value,
      tipo: document.getElementById("ev-tipo").value,
      descrizione: document.getElementById("ev-descrizione").value,
      data_ora: document.getElementById("ev-data").value,
      capienza: Number(document.getElementById("ev-capienza").value),
    });
    mostraMessaggio("Evento pubblicato.");
    e.target.reset();
    caricaEventi();
    caricaDashboard();
  } catch (errore) { mostraMessaggio(errore.message, true); }
  window.scrollTo(0, 0);
});

document.getElementById("scelta-evento").addEventListener("change", caricaPrenotati);

const utente = utenteCollegato();
if (!utente || utente.ruolo !== "amministratore") location.href = "accesso.html";
else { caricaDashboard(); caricaEventi(); }
