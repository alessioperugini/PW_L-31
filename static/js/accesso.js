"use strict";

async function accedi(email, password) {
  const esito = await api("/api/login", "POST", { email: email, password: password });
  sessionStorage.setItem("token", esito.token);
  sessionStorage.setItem("utente", JSON.stringify(esito.utente));
  location.href = esito.utente.ruolo === "amministratore" ? "gestione.html" : "eventi.html";
}

document.getElementById("form-login").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await accedi(document.getElementById("login-email").value, document.getElementById("login-password").value);
  } catch (errore) {
    mostraMessaggio(errore.message, true);
  }
});

document.getElementById("form-registrazione").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!document.getElementById("reg-consenso").checked) {
    mostraMessaggio("Per registrarti devi accettare l'informativa privacy.", true);
    return;
  }
  const email = document.getElementById("reg-email").value;
  const password = document.getElementById("reg-password").value;
  try {
    await api("/api/registrazione", "POST", {
      nome: document.getElementById("reg-nome").value,
      cognome: document.getElementById("reg-cognome").value,
      email: email, password: password, consenso_privacy: true,
    });
    await accedi(email, password);
  } catch (errore) {
    mostraMessaggio(errore.message, true);
  }
});
