// Funzioni usate da tutte le pagine
"use strict";

function utenteCollegato() {
  try { return JSON.parse(sessionStorage.getItem("utente")); } catch { return null; }
}

// Chiama le API del server e restituisce la risposta già convertita da JSON
async function api(indirizzo, metodo = "GET", dati) {
  const opzioni = { method: metodo, headers: {} };
  const token = sessionStorage.getItem("token");
  if (token) opzioni.headers["Authorization"] = "Bearer " + token;
  if (dati !== undefined) {
    opzioni.headers["Content-Type"] = "application/json";
    opzioni.body = JSON.stringify(dati);
  }
  const risposta = await fetch(indirizzo, opzioni);
  if (risposta.status === 204) return null;
  const corpo = await risposta.json();
  if (!risposta.ok) {
    // FastAPI restituisce il motivo dell'errore nel campo "detail"
    const motivo = typeof corpo.detail === "string" ? corpo.detail : "Dati non validi, controlla i campi";
    throw new Error(motivo);
  }
  return corpo;
}

// Crea un elemento HTML; il testo viene inserito come testo semplice, mai come codice HTML
function crea(tag, classe, ...contenuto) {
  const elemento = document.createElement(tag);
  if (classe) elemento.className = classe;
  for (const parte of contenuto) {
    if (parte !== null && parte !== undefined) elemento.append(parte);
  }
  return elemento;
}

function dataLeggibile(testo) {
  const d = new Date(testo + ":00");
  return d.toLocaleDateString("it-IT", { weekday: "short", day: "numeric", month: "long", year: "numeric" }) +
    ", ore " + d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
}

const TIPI = { visita_guidata: "Visita guidata", laboratorio: "Laboratorio", conferenza: "Conferenza" };

function mostraMessaggio(testo, errore = false) {
  const box = document.getElementById("messaggio");
  box.textContent = testo;
  box.className = "avviso visibile " + (errore ? "errore" : "ok");
}

// Menu in alto: le voci cambiano in base all'utente collegato
function disegnaMenu() {
  const utente = utenteCollegato();
  const pagina = location.pathname.split("/").pop() || "index.html";
  const voci = [["index.html", "Catalogo"], ["eventi.html", "Eventi"]];
  if (utente) voci.push(["area.html", "Le mie prenotazioni"]);
  if (utente && utente.ruolo === "amministratore") voci.push(["gestione.html", "Gestione"]);

  const nav = crea("nav", "");
  for (const [link, testo] of voci) {
    const a = crea("a", link === pagina ? "attivo" : "", testo);
    a.href = link;
    nav.append(a);
  }
  const box = crea("div", "utente-box");
  if (utente) {
    const esci = crea("button", "", "Esci");
    esci.onclick = async () => {
      try { await api("/api/logout", "POST"); } catch { /* sessione già scaduta */ }
      sessionStorage.clear();
      location.href = "index.html";
    };
    box.append(utente.nome, esci);
  } else {
    const accedi = crea("a", "bottone secondario", "Accedi");
    accedi.href = "accesso.html";
    box.append(accedi);
  }
  const marchio = crea("a", "marchio", "Museo Civico di Borgo San Valerio", crea("small", "", "MuseoDigitale"));
  marchio.href = "index.html";
  const testata = document.getElementById("testata");
  testata.className = "testata";
  testata.append(crea("div", "contenitore", marchio, nav, box));
}

document.addEventListener("DOMContentLoaded", disegnaMenu);
