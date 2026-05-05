const SERVER = "http://localhost:5000";

document.addEventListener("DOMContentLoaded", async () => {
  const status  = document.getElementById("status");
  const btnGen  = document.getElementById("btnGenerer");
  const btnSrv  = document.getElementById("btnServer");
  const btnList = document.getElementById("btnList");

  // Vérifier si on est sur la page recap SIV
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab && tab.url && tab.url.includes("ivo_cht_toVal")) {
    status.textContent = "✅ Page récapitulatif détectée — prêt à générer.";
    btnGen.disabled = false;
  }

  // Bouton Générer → déclencher le clic dans content.js via message
  btnGen.onclick = () => {
    chrome.tabs.sendMessage(tab.id, { action: "generer" });
    window.close();
  };

  // Vérifier le serveur
  btnSrv.onclick = async () => {
    status.textContent = "⏳ Vérification du serveur…";
    try {
      const r = await fetch(`${SERVER}/health`, { signal: AbortSignal.timeout(3000) });
      const d = await r.json();
      status.textContent = `✅ Serveur OK — version ${d.version || "?"}`;
    } catch {
      status.textContent = "❌ Serveur introuvable. Lancer start_server.bat";
    }
  };

  // Lister les derniers CERFA
  btnList.onclick = async () => {
    status.textContent = "⏳ Récupération…";
    try {
      const r = await fetch(`${SERVER}/list`);
      const list = await r.json();
      if (list.length === 0) { status.textContent = "Aucun CERFA généré."; return; }
      list.slice(0, 5).forEach(f => window.open(f.url, "_blank"));
      status.textContent = `📂 ${Math.min(list.length, 5)} fichier(s) ouvert(s).`;
    } catch {
      status.textContent = "❌ Serveur introuvable.";
    }
  };
});
