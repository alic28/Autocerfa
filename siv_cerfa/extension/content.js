/**
 * SIV → CERFA  — content.js v2.0
 * Lecture uniquement sur l'écran de récapitulatif : ivo_cht_toVal
 */

(function () {
  "use strict";

  const SIV_RECAP_URL = "ivo_cht_toVal";
  const SERVER_URL    = "http://localhost:5000/generer";

  // ── Utilitaires ────────────────────────────────────────────────────────

  function isRecapPage() {
    return window.location.href.includes(SIV_RECAP_URL);
  }

  function $q(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $qa(sel, ctx) { return [...(ctx || document).querySelectorAll(sel)]; }

  function textOf(el) {
    return el ? el.textContent.replace(/\s+/g, " ").trim() : "";
  }

  // Trouver la valeur d'une cellule dont le LABEL voisin contient le texte cherché
  function findCellValue(labelText) {
    const rows = $qa("tr, .siv-row, .row, .info-row");
    for (const row of rows) {
      const cells = $qa("td, th, .cell, .label, .value", row);
      for (let i = 0; i < cells.length - 1; i++) {
        if (textOf(cells[i]).toLowerCase().includes(labelText.toLowerCase())) {
          return textOf(cells[i + 1]);
        }
      }
    }
    // Fallback : chercher dans tout le DOM
    const allEls = $qa("[class*='label'],[class*='value'],[class*='field']");
    for (let i = 0; i < allEls.length - 1; i++) {
      if (textOf(allEls[i]).toLowerCase().includes(labelText.toLowerCase())) {
        return textOf(allEls[i + 1]);
      }
    }
    return "";
  }

  // Lire les inputs/selects/spans avec un label contenant le texte
  function findInputValue(labelText) {
    const inputs = $qa("input, select, textarea");
    for (const inp of inputs) {
      const lbl = inp.labels && inp.labels[0]
        ? textOf(inp.labels[0])
        : textOf(inp.previousElementSibling) || inp.id || inp.name || "";
      if (lbl.toLowerCase().includes(labelText.toLowerCase())) {
        return inp.value || inp.textContent || "";
      }
    }
    return "";
  }

  // ── Extraction des données SIV ─────────────────────────────────────────

  function extractData() {
    const data = {
      type_demarche: "changement_proprietaire",
      immatriculation: "",
      dossier: "",
      vehicule: {},
      titulaire: {},
      date_signature: today(),
    };

    // ── Numéro de dossier / immatriculation ──────────────────────────────
    // Ex: "Dossier N° : GP-910-RT"
    const dossierEl = $q("[class*='dossier'], [id*='dossier'], .dossier-num");
    if (dossierEl) {
      data.dossier = textOf(dossierEl).replace(/^[^:]*:\s*/, "").trim();
    }
    if (!data.dossier) {
      // Chercher le texte "Dossier N°"
      const allText = $qa("*");
      for (const el of allText) {
        if (el.children.length === 0) {
          const t = textOf(el);
          const m = t.match(/Dossier\s+N[°o]?\s*[:.]?\s*([A-Z]{2}-\d{3}-[A-Z]{2}|[A-Z0-9-]+)/i);
          if (m) { data.dossier = m[1].trim(); break; }
        }
      }
    }
    data.immatriculation = data.dossier;

    // ── Véhicule ──────────────────────────────────────────────────────────
    // VIN : chercher le champ "E" ou "Identification du Véhicule"
    const vinEl = $q("input[name*='vin'], input[id*='vin'], input[name*='E ']");
    if (vinEl) {
      data.vehicule.vin = vinEl.value.trim();
    }
    if (!data.vehicule.vin) {
      // Chercher une valeur qui ressemble à un VIN (17 car. alphanumériques)
      const vinMatch = document.body.innerText.match(/\b([A-HJ-NPR-Z0-9]{17})\b/);
      if (vinMatch) data.vehicule.vin = vinMatch[1];
    }

    // Marque D.1
    const marqueEl = $q("input[value][class*='marque'], input[name*='marque']")
      || findInputEl("D.1") || findInputEl("Marque");
    if (marqueEl) data.vehicule.marque = marqueEl.value.trim();
    if (!data.vehicule.marque) data.vehicule.marque = findCellValue("D.1") || findCellValue("Marque");

    // Genre J.1
    data.vehicule.genre = findCellValue("J.1") || findCellValue("Genre");

    // Date de première immatriculation
    const dateEl = $q("[class*='premiere-immat'], [id*='premiereImmat']");
    if (dateEl) {
      data.vehicule.date_premiere_immat = textOf(dateEl);
    }
    if (!data.vehicule.date_premiere_immat) {
      // Chercher dans le DOM : "Date de première immatriculation"
      const m = document.body.innerText.match(/premi.re\s+immatriculation[^:]*:\s*(\d{2}\/\d{2}\/\d{4})/i);
      if (m) data.vehicule.date_premiere_immat = m[1];
    }

    // ── Titulaire ─────────────────────────────────────────────────────────
    // Sur l'écran récap, le titulaire est dans un tableau "Titulaire et co-titulaires"
    // avec lignes : Identité | Adresse | Nature

    parseTitulaire(data);

    return data;
  }

  function findInputEl(label) {
    const inputs = $qa("input");
    for (const inp of inputs) {
      const name = (inp.name || inp.id || "").toLowerCase();
      if (name.includes(label.toLowerCase())) return inp;
      const prev = inp.previousElementSibling;
      if (prev && textOf(prev).toLowerCase().includes(label.toLowerCase())) return inp;
    }
    return null;
  }

  function parseTitulaire(data) {
    // Le tableau titulaire a en général :
    // - une ligne d'en-tête: Identité | Adresse | Nature
    // - une ligne de données

    // Chercher le bloc "Titulaire et co-titulaires"
    let titBlock = null;
    const headers = $qa("h2, h3, h4, th, .section-title, [class*='titre']");
    for (const h of headers) {
      if (/titulaire/i.test(textOf(h))) {
        titBlock = h.closest("table, .section, fieldset, div") || h.parentElement;
        break;
      }
    }

    if (titBlock) {
      const rows = $qa("tr", titBlock);
      for (const row of rows) {
        const cells = $qa("td", row);
        if (cells.length >= 2) {
          const identite = textOf(cells[0]);
          const adresse  = textOf(cells[1]);
          const nature   = cells[2] ? textOf(cells[2]) : "";

          if (/titulaire/i.test(nature) || rows.indexOf(row) === 1) {
            parseIdentite(identite, data.titulaire);
            parseAdresse(adresse, data.titulaire);
            break;
          }
        }
      }
    }

    // Fallback : chercher directement dans le texte de la page
    if (!data.titulaire.nom) {
      fallbackTitulaire(data);
    }
  }

  function parseIdentite(identite, tit) {
    // Format SIV typique : "NOM PRENOM" sur première ligne
    // Puis "né(e) le JJ/MM/AAAA à COMMUNE (DEPT)"
    const lines = identite.split(/\n|\r|\|/).map(s => s.trim()).filter(Boolean);
    if (lines.length >= 1) {
      const nomPrenom = lines[0];
      // Heuristique : le nom est en MAJUSCULES, le prénom peut être mixte
      // Format SIV : "PRENOM NOM" ou "NOM PRENOM"
      const parts = nomPrenom.split(" ");
      if (parts.length >= 2) {
        // SIV affiche généralement "PRENOM NOM" ou "NOM PRENOM"
        // On met tout dans prenom + nom séparément
        tit.prenom = parts.slice(0, -1).join(" ");
        tit.nom    = parts[parts.length - 1];
        // Si le nom est plus court et en majuscules → c'est probablement le nom de famille
        // Simplification : on envoie tel quel, le server concatène
        tit._full_name = nomPrenom;
      }
    }

    // Chercher la date et lieu de naissance
    const naissMatch = identite.match(/né\(?e?\)?\s+le\s+(\d{2}\/\d{2}\/\d{4})\s+[àa]\s+([^(]+)\((\d{2,3})\)/i);
    if (naissMatch) {
      tit.date_naissance         = naissMatch[1];
      tit.commune_naissance      = naissMatch[2].trim();
      tit.departement_naissance  = naissMatch[3].trim();
    }
  }

  function parseAdresse(adresse, tit) {
    // Format : "5 RUE PASTEUR\n59300 VALENCIENNES"
    // ou "5 RUE PASTEUR 59300 VALENCIENNES"
    const lines = adresse.split(/\n|\r/).map(s => s.trim()).filter(Boolean);

    // Ligne 1 : N° voie type libellé
    const voieLine = lines[0] || adresse;
    const voieMatch = voieLine.match(/^(\d+)\s+(\w+)\s+(.+)$/);
    if (voieMatch) {
      tit.num_voie     = voieMatch[1];
      tit.type_voie    = voieMatch[2];
      tit.libelle_voie = voieMatch[3].trim();
    }

    // Ligne 2 : CP COMMUNE
    const cpLine = lines[1] || "";
    const cpMatch = cpLine.match(/^(\d{5})\s+(.+)$/);
    if (cpMatch) {
      tit.code_postal = cpMatch[1];
      tit.commune     = cpMatch[2].trim();
    }
  }

  function fallbackTitulaire(data) {
    // Dernier recours : chercher dans "Adresse d'expédition"
    const allText = document.body.innerText;

    // Adresse expédition : "MME NOM PRENOM\nN RUE VILLE\nCP COMMUNE"
    const expMatch = allText.match(/Adresse\s+d.exp.dition\s*[:\n]+([^\n]+)\n([^\n]+)\n(\d{5}\s+[^\n]+)/i);
    if (expMatch) {
      const nomLine = expMatch[1].replace(/^(M\.|MME|MR|MONSIEUR|MADAME)\s+/i, "").trim();
      const parts   = nomLine.split(" ");
      data.titulaire._full_name = nomLine;
      data.titulaire.nom        = parts[parts.length - 1];
      data.titulaire.prenom     = parts.slice(0, -1).join(" ");

      parseAdresse(expMatch[2] + "\n" + expMatch[3], data.titulaire);
    }

    // Date de naissance
    const naissMatch = allText.match(/né\(?e?\)?\s+le\s+(\d{2}\/\d{2}\/\d{4})\s+[àa]\s+([^(]+)\((\d{2,3})\)/i);
    if (naissMatch) {
      data.titulaire.date_naissance        = naissMatch[1];
      data.titulaire.commune_naissance     = naissMatch[2].trim();
      data.titulaire.departement_naissance = naissMatch[3].trim();
    }
  }

  function today() {
    const d = new Date();
    return `${String(d.getDate()).padStart(2,"0")}/${String(d.getMonth()+1).padStart(2,"0")}/${d.getFullYear()}`;
  }

  // ── Normalisation du payload avant envoi ──────────────────────────────

  function normalizePayload(d) {
    const t = d.titulaire;
    // Si _full_name est disponible, l'utiliser pour nom/prenom
    if (t._full_name) {
      const parts = t._full_name.trim().split(" ");
      // SIV : format "PRENOM NOM" (nom en dernier) ou "NOM PRENOM"
      // On essaie de déduire : si le dernier mot est court et tout-caps c'est sûrement le nom
      t.nom    = t.nom    || parts[parts.length - 1];
      t.prenom = t.prenom || parts.slice(0, -1).join(" ");
    }
    return d;
  }

  // ── Affichage barre ───────────────────────────────────────────────────

  function injectBar() {
    if (document.getElementById("siv-cerfa-bar")) return;

    const bar = document.createElement("div");
    bar.id = "siv-cerfa-bar";
    bar.style.cssText = [
      "position:fixed","top:0","left:0","right:0","z-index:99999",
      "background:#E55A00","color:#fff","display:flex","align-items:center",
      "padding:6px 14px","font:bold 14px Arial,sans-serif","gap:12px",
      "box-shadow:0 2px 6px rgba(0,0,0,.4)"
    ].join(";");

    const title = document.createElement("span");
    title.textContent = "🖨 SIV→CERFA";

    const btn = document.createElement("button");
    btn.textContent = "Générer les CERFA";
    btn.style.cssText = [
      "background:#fff","color:#E55A00","border:none","padding:5px 14px",
      "border-radius:4px","font-weight:bold","font-size:13px","cursor:pointer"
    ].join(";");

    const status = document.createElement("span");
    status.id = "siv-cerfa-status";
    status.style.cssText = "font-size:12px;font-weight:normal;margin-left:8px";

    btn.onclick = async () => {
      status.textContent = "⏳ Extraction des données…";
      try {
        const raw     = extractData();
        const payload = normalizePayload(raw);
        console.log("[SIV→CERFA] Payload:", JSON.stringify(payload, null, 2));

        status.textContent = "⏳ Génération des CERFA…";
        const resp = await fetch(SERVER_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const result = await resp.json();

        // Ouvrir les PDFs
        const urls = Object.values(result).filter(u => u && u.startsWith("http"));
        if (urls.length === 0) throw new Error("Aucun CERFA généré");

        urls.forEach(url => window.open(url, "_blank"));
        status.textContent = `✅ ${urls.length} CERFA ouvert(s)`;
        status.style.color = "#AAFFAA";
      } catch (err) {
        status.textContent = `❌ ${err.message}`;
        status.style.color = "#FFAAAA";
        console.error("[SIV→CERFA]", err);
      }
    };

    bar.appendChild(title);
    bar.appendChild(btn);
    bar.appendChild(status);
    document.body.prepend(bar);
    document.body.style.marginTop = "38px";
  }

  // ── Initialisation ────────────────────────────────────────────────────

  function init() {
    if (!isRecapPage()) return;
    // Attendre que la page soit rendue
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", injectBar);
    } else {
      setTimeout(injectBar, 500);
    }
  }

  init();
})();
