/**
 * SIV → CERFA — Popup JavaScript
 * Affiche les données mémorisées et l'état du service local.
 */

const SERVICE_URL = "http://localhost:5000";

// ─── Vérification du service local ────────────────────────────────────────

async function checkService() {
  const statusEl = document.getElementById("service-status");
  const footerEl = document.getElementById("footer-service");

  try {
    const resp = await fetch(`${SERVICE_URL}/health`, { signal: AbortSignal.timeout(2000) });
    if (resp.ok) {
      statusEl.className = "service-status service-ok";
      statusEl.innerHTML = '<div class="dot dot-ok"></div><span>Service local actif ✓</span>';
      footerEl.textContent = "✅ actif";
      return true;
    }
  } catch (_) {}

  statusEl.className = "service-status service-error";
  statusEl.innerHTML = '<div class="dot dot-error"></div><span>Service non démarré — lancez <strong>start_server.bat</strong></span>';
  footerEl.textContent = "❌ inactif";
  return false;
}

// ─── Affichage des données mémorisées ─────────────────────────────────────

function updateDisplay(data) {
  const set = (id, val, fallback = "—") => {
    const el = document.getElementById(id);
    if (!el) return;
    const v = (val || "").trim();
    el.textContent = v || fallback;
    el.classList.toggle("data-empty", !v);
  };

  const e1 = data.siv_ecran1 || {};
  const e3 = data.siv_ecran3 || {};

  set("d-immat",    e1.immatriculation);
  set("d-vin",      e1.vin);
  set("d-dossier",  e1.dossier);
  set("d-marque",   "");  // Disponible seulement depuis le récap

  const nom    = [e3.prenom, e3.nom].filter(Boolean).join(" ");
  const adresse = [e3.num_voie, e3.libelle_voie, e3.code_postal, e3.commune].filter(Boolean).join(" ");
  set("d-titulaire", nom);
  set("d-adresse",   adresse.length > 35 ? adresse.substring(0, 32) + "..." : adresse);

  // Activer le bouton si au moins un immat est mémorisé
  const btn = document.getElementById("btn-generer");
  if (btn) btn.disabled = !e1.immatriculation;
}

// ─── Génération depuis la popup (sur l'onglet actif) ──────────────────────

document.getElementById("btn-generer")?.addEventListener("click", async () => {
  const btn = document.getElementById("btn-generer");
  btn.disabled = true;
  btn.textContent = "⏳ En cours...";

  try {
    // Injecter et déclencher la génération dans l'onglet actif
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        const btn = document.getElementById("siv-btn-generer");
        if (btn) {
          btn.click();
        } else {
          alert("Naviguez d'abord jusqu'à l'écran Récapitulatif du SIV.");
        }
      },
    });
  } catch (err) {
    console.error(err);
  } finally {
    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = "🖨️ Générer les CERFA";
    }, 2000);
  }
});

// ─── Effacer les données ───────────────────────────────────────────────────

document.getElementById("btn-clear")?.addEventListener("click", () => {
  chrome.storage.local.remove(["siv_ecran1", "siv_ecran3"], () => {
    updateDisplay({});
    document.getElementById("btn-generer").disabled = true;
  });
});

// ─── Init ──────────────────────────────────────────────────────────────────

(async () => {
  await checkService();
  chrome.storage.local.get(["siv_ecran1", "siv_ecran3"], updateDisplay);
})();
