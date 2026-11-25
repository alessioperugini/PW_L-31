"use strict";

async function cerca(evento) {
  if (evento) evento.preventDefault();
  const testo = document.getElementById("testo").value.trim();
  const sezione = document.getElementById("sezione").value;
  const opere = await api(`/api/opere?q=${encodeURIComponent(testo)}&sezione=${encodeURIComponent(sezione)}`);

  const griglia = document.getElementById("risultati");
  griglia.innerHTML = "";
  for (const o of opere) {
    griglia.append(crea("article", "scheda",
      crea("span", "etichetta", o.sezione),
      crea("h3", "", o.titolo),
      crea("p", "meta", o.autore + (o.anno ? ", " + o.anno : "")),
      crea("p", "", o.descrizione),
      crea("p", "meta", "Inventario " + o.inventario)));
  }
  if (opere.length === 0) griglia.append(crea("p", "vuoto", "Nessuna opera trovata."));
}

document.getElementById("ricerca").addEventListener("submit", cerca);
document.getElementById("sezione").addEventListener("change", cerca);
cerca();
