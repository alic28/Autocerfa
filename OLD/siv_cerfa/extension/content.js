/**
 * SIV → CERFA — content.js v5.0
 * Approche 100% texte brut : aucune lecture de cellule.
 * Toutes les valeurs sont extraites par regex sur document.body.innerText
 */
(function () {
  "use strict";

  const VERSION    = "v5.0";
  const SERVER_URL = "http://localhost:5000/generer";

  function isRecapPage() {
    return window.location.href.includes("ivo_cht_toVal");
  }

  // ── Extraction par REGEX sur le texte brut ────────────────────────────

  function extractData() {
    // body.innerText conserve les retours à la ligne entre éléments visuels
    const body = document.body.innerText;

    // 1. Numéro de dossier   "Dossier N° : GP-910-RT"
    const dossier = pick(body, /Dossier\s+N[°o]\s*:\s*([A-Z]{2}-\d{3}-[A-Z]{2})/);

    // 2. VIN — 17 caractères alphanumériques (norme VIN)
    const vin = pick(body, /\b([A-HJ-NPR-Z0-9]{17})\b/);

    // 3. Marque  ligne "Marque D.1 FIAT"
    const marque = pick(body, /Marque\s+D\.?1\s+(\S+)/);

    // 4. Genre   ligne "Genre J.1 VP"
    const genre = pick(body, /Genre\s+J\.?1\s+([A-Z]{1,3})\b/);

    // 5. Date 1re immat
    const datePremImmat = pick(body, /Date\s+de\s+premi.re\s+immatriculation\s+(\d{2}\/\d{2}\/\d{4})/i);

    // 6. Identité titulaire
    //    Pattern : "PRÉNOM NOM né(e) le DD/MM/YYYY à COMMUNE (DEPT)"
    //    Le nom + prénom ne contient QUE des majuscules + espaces + tirets + apostrophes
    //    Cela exclut la nav menu (qui contient des minuscules)
    let nom = "", prenom = "", dateNaiss = "", communeNaiss = "", deptNaiss = "";
    const naissM = body.match(
      /([A-ZÀ-Ÿ][A-ZÀ-Ÿ \-']+?)\s+né\(?e?\)?\s+le\s+(\d{2}\/\d{2}\/\d{4})\s+à\s+([^(\n]+?)\s+\((\d{2,3})\)/
    );
    if (naissM) {
      const fullName = naissM[1].trim();
      const parts    = fullName.split(/\s+/);
      nom            = parts[parts.length - 1];
      prenom         = parts.slice(0, -1).join(" ");
      dateNaiss      = naissM[2];
      communeNaiss   = naissM[3].trim();
      deptNaiss      = naissM[4];
    }

    // 7. Adresse — bloc "Adresse d'expédition"
    //    Format :
    //      Adresse d'expédition
    //      MME OMONT INES LEA           ← civilité + nom prénom (ignoré ici)
    //      5 RUE PASTEUR                ← num + type + libellé
    //      59300 VALENCIENNES           ← cp + commune
    let numVoie = "", typeVoie = "", libelleVoie = "", cp = "", commune = "";
    const adrM = body.match(
      /Adresse\s+d['']?expédition[\s\S]*?\n\s*[A-ZÀ-Ÿ\.\s]+\n\s*(\d+)\s+(\S+)\s+([^\n]+?)\n\s*(\d{5})\s+([^\n]+)/i
    );
    if (adrM) {
      numVoie     = adrM[1].trim();
      typeVoie    = adrM[2].trim();
      libelleVoie = adrM[3].trim();
      cp          = adrM[4].trim();
      commune     = adrM[5].trim();
    }
    // Fallback : chercher directement "DIGIT WORD ... CP COMMUNE" dans le titulaire
    if (!cp) {
      const fb = body.match(/(\d+)\s+(RUE|AVENUE|AV|BD|BOULEVARD|PLACE|PL|CHEMIN|CHE|IMPASSE|IMP|ROUTE|RTE|ALL[ÉE]E|ALLEE|QUAI|COURS|VOIE|RESIDENCE|HAMEAU|LOTISSEMENT|SQUARE|VILLA|FAUBOURG|PASSAGE|RAMPE)\s+([A-ZÀ-Ÿ \-']+?)\s+(\d{5})\s+([A-ZÀ-Ÿ\- ]+)/i);
      if (fb) {
        numVoie     = fb[1];
        typeVoie    = fb[2];
        libelleVoie = fb[3].trim();
        cp          = fb[4];
        commune     = fb[5].trim();
      }
    }

    return {
      _version:        VERSION,
      type_demarche:   "changement_proprietaire",
      dossier,
      immatriculation: dossier,
      mandataire_nom:  "DREUX CARTE GRISE",
      vehicule: { vin, marque, genre, date_premiere_immat: datePremImmat },
      titulaire: {
        nom, prenom,
        date_naissance:        dateNaiss,
        commune_naissance:     communeNaiss,
        departement_naissance: deptNaiss,
        num_voie:              numVoie,
        type_voie:             typeVoie,
        libelle_voie:          libelleVoie,
        code_postal:           cp,
        commune:               commune,
      },
      date_signature: today(),
    };
  }

  function pick(text, regex) {
    const m = text.match(regex);
    return m ? m[1].trim() : "";
  }

  function today() {
    const d = new Date();
    return `${String(d.getDate()).padStart(2,"0")}/${String(d.getMonth()+1).padStart(2,"0")}/${d.getFullYear()}`;
  }

  // ── Barre orange ──────────────────────────────────────────────────────

  function injectBar() {
    if (document.getElementById("siv-cerfa-bar")) return;

    const bar = document.createElement("div");
    bar.id = "siv-cerfa-bar";
    Object.assign(bar.style, {
      position: "fixed", top: "0", left: "0", right: "0", zIndex: "99999",
      background: "#E55A00", color: "#fff",
      display: "flex", alignItems: "center",
      padding: "6px 14px", gap: "12px",
      font: "bold 14px Arial,sans-serif",
      boxShadow: "0 2px 6px rgba(0,0,0,.4)"
    });

    const title = document.createElement("span");
    title.textContent = `🖨 SIV→CERFA ${VERSION}`;

    const btn = document.createElement("button");
    btn.id = "siv-cerfa-btn";
    btn.textContent = "Générer les CERFA";
    Object.assign(btn.style, {
      background: "#fff", color: "#E55A00", border: "none",
      padding: "5px 16px", borderRadius: "4px",
      fontWeight: "bold", fontSize: "13px", cursor: "pointer"
    });

    const status = document.createElement("span");
    status.id = "siv-cerfa-status";
    status.style.fontSize = "12px";
    status.style.fontWeight = "normal";

    btn.onclick = handleGenerate;

    bar.appendChild(title);
    bar.appendChild(btn);
    bar.appendChild(status);
    document.body.prepend(bar);
    document.body.style.paddingTop = "38px";
  }

  async function handleGenerate() {
    const status = document.getElementById("siv-cerfa-status");
    const btn    = document.getElementById("siv-cerfa-btn");
    btn.disabled = true;
    status.style.color = "#fff";
    status.textContent = "⏳ Extraction…";

    try {
      const data = extractData();

      // Log pour debug : visible dans la console F12
      console.log(`[SIV→CERFA ${VERSION}] Extraction :`, data);

      if (!data.dossier)       throw new Error("Dossier introuvable");
      if (!data.titulaire.nom) throw new Error("Nom titulaire introuvable");
      if (!data.vehicule.vin)  throw new Error("VIN introuvable");

      status.textContent = "⏳ Génération…";

      const resp = await fetch(SERVER_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });

      if (!resp.ok) throw new Error(`Serveur HTTP ${resp.status}`);
      const result = await resp.json();
      if (result.error) throw new Error(result.error);

      const urls = Object.values(result).filter(u => typeof u === "string" && u.startsWith("http"));
      if (!urls.length) throw new Error("Aucun PDF généré");

      urls.forEach(u => window.open(u, "_blank"));
      status.style.color = "#AAFFAA";
      status.textContent = `✅ ${urls.length} CERFA — ${data.titulaire.nom} ${data.titulaire.prenom}`;
    } catch (err) {
      status.style.color = "#FFAAAA";
      status.textContent = `❌ ${err.message}`;
      console.error(`[SIV→CERFA ${VERSION}]`, err);
    } finally {
      btn.disabled = false;
    }
  }

  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.action === "generer") handleGenerate();
  });

  function init() {
    if (!isRecapPage()) return;
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", () => setTimeout(injectBar, 600));
    } else {
      setTimeout(injectBar, 600);
    }
  }

  init();
})();
