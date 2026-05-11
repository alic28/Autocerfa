/**
 * SIV → CERFA — content.js v15.0
 *
 * Extension 100% locale : aucun serveur, aucun .bat.
 * Génère les CERFA directement dans le navigateur via pdf-lib.
 *
 * Workflows supportés :
 *
 *  ┌──────────────────────────────────┬─────────────────┬────────────────┐
 *  │ Page SIV                         │ URL contient    │ CERFA générés  │
 *  ├──────────────────────────────────┼─────────────────┼────────────────┤
 *  │ Récap changement de titulaire    │ ivo_cht_toVal   │ 13750 + 13757  │
 *  │ Saisie cession (ECR_IVO_CES_02)  │ ivo_ces_        │ 13757 seul     │
 *  └──────────────────────────────────┴─────────────────┴────────────────┘
 *
 * Nouveautés v15.0 :
 *  - Extraction du n° de téléphone (#telephonePortable) sur le récap titulaire
 *    → injecté dans le 13750 via la clé "telephone"
 *  - Workflow cession : génération du mandat 13757 dès la page de saisie
 *    avec mention "Enregistrement de cession" comme objet du mandat
 */

(function () {
  "use strict";

  const VERSION = "15.1.0";

  // ─── Détection page SIV ───────────────────────────────────────────────

  function getPageType() {
    const url = window.location.href;
    if (url.includes("ivo_cht_toVal")) return "recap_changement";
    // Pattern "ivo_ces_" couvre toutes les pages cession (saisie ET récap).
    if (/\/do\/ivo_ces_/i.test(url)) return "cession";
    // Fallback : détection par breadcrumb si l'URL ne matche pas
    const txt = document.body && document.body.innerText || "";
    if (/Inscrire\s+la\s+cession/i.test(txt) && !/ivo_cht/i.test(url)) {
      return "cession";
    }
    return "autre";
  }

  // ─── Helpers DOM ──────────────────────────────────────────────────────

  function getAllCells() {
    const cells = [];
    document.querySelectorAll("table td, table th").forEach(td => {
      const t = td.innerText.replace(/\s+/g, " ").trim();
      if (t.length > 0) cells.push(t);
    });
    return cells;
  }

  function cellAfter(cells, label) {
    const idx = cells.indexOf(label);
    return idx >= 0 && idx < cells.length - 1 ? cells[idx + 1].trim() : "";
  }

  function cellAfterContains(cells, text) {
    const idx = cells.findIndex(c => c.includes(text));
    return idx >= 0 && idx < cells.length - 1 ? cells[idx + 1].trim() : "";
  }

  /** Renvoie la valeur d'un input par son id, ou "" si absent/vide */
  function inputValue(id) {
    const el = document.getElementById(id);
    return el ? (el.value || "").trim() : "";
  }

  // ─── Extraction écran récap changement titulaire ──────────────────────

  function extractFromRecap() {
    const cells   = getAllCells();
    const lines   = document.body.innerText
      .split(/\r?\n/)
      .map(l => l.replace(/\s+/g, " ").trim())
      .filter(l => l.length > 0);
    const bodyTxt = lines.join("\n");

    const demarche = "changement_proprietaire";

    // Dossier / immat
    const immatRegex = /\b([A-Z]{2}-\d{3}-[A-Z]{2})\b/;
    const immatMatch = bodyTxt.match(immatRegex);
    const immat      = immatMatch ? immatMatch[1] : "";

    // VIN
    const vinRegex = /\b([A-HJ-NPR-Z0-9]{17})\b/;
    const vinMatch = bodyTxt.match(vinRegex);
    const vin      = vinMatch ? vinMatch[1] : "";

    // Codes carte grise
    const marque        = cellAfter(cells, "D.1") || cellAfterContains(cells, "Marque");
    const j1Idx         = cells.indexOf("J.1");
    const genre         = j1Idx >= 0 ? (cells[j1Idx + 1] || "") : "";
    const carrosserie   = cellAfter(cells, "J.3");
    const puissance     = cellAfter(cells, "P.6");
    const energie       = cellAfter(cells, "P.3");

    // Date première immat
    const dateMatch = bodyTxt.match(/premi[èe]re\s+immatriculation[^0-9]{0,30}(\d{2}\/\d{2}\/\d{4})/i);
    const datePremImmat = dateMatch ? dateMatch[1] : "";

    // Numéro de formule
    const formuleMatch = bodyTxt.match(/(?:N°\s*formule|num[ée]ro\s+de\s+formule)[^A-Z0-9]{0,10}([A-Z0-9]{8,})/i);
    const numFormule = formuleMatch ? formuleMatch[1] : "";

    // Identité titulaire
    let nom = "", prenom = "", dateNaiss = "", communeNaiss = "", deptNaiss = "";

    const idLineRegex = /\b([A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ][A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ\s\-']{1,60}?)\s+n[ée]\(e\)\s+le\s+(\d{2}\/\d{2}\/\d{4})\s+[àa]\s+([A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ\s\-']{1,40}?)\s+\(([0-9A-Z]{2,5})\)/i;

    function tryMatchId(text) {
      const m = text.match(idLineRegex);
      if (!m) return false;
      let fullName = m[1].trim().replace(/\s+/g, " ");
      fullName = fullName.split(/\s+(?:TITULAIRE|MENTIONS?|SANS|USAGE|VEHICULE|VÉHICULE|DOSSIER|CO\-?TITULAIRE|LOCATAIRE|LOUEUR|GENRE|NUMERO|NUMÉRO|IDENTIT[ÉE])\b/i)[0].trim();
      dateNaiss      = m[2];
      communeNaiss   = m[3].trim().replace(/\s+/g, " ");
      deptNaiss      = m[4];
      const parts = fullName.split(/\s+/);
      if (parts.length >= 2) {
        nom    = parts[parts.length - 1];
        prenom = parts.slice(0, -1).join(" ");
      } else {
        nom = fullName;
      }
      return true;
    }

    outerId:
    for (let i = 0; i < lines.length; i++) {
      if (tryMatchId(lines[i])) break;
      if (i > 0 && tryMatchId(lines[i-1] + " " + lines[i])) break outerId;
    }

    // Adresse titulaire
    let numVoie = "", typeVoie = "", libelleVoie = "", codePostal = "", commune = "";

    const adrLineRegex = /\b(\d+)\s+(RUE|AV|AVENUE|BD|BOULEVARD|ALL[ÉE]E|PLACE|CHEMIN|ROUTE|IMPASSE|SQUARE|QUAI|CHE|CHS|VOIE|RTE|PL|PASSAGE|COUR|COURS|RES|RESIDENCE|DOMAINE|LOTISSEMENT|LIEU.DIT|LIEU.|HAMEAU|FAUBOURG|VILLAGE|TRAVERSE|MONTEE|RAMPE|SENTIER|VENELLE|CARREFOUR|ESPLANADE|PARVIS|PROMENADE|ROND.POINT|RUELLE|PARC|PORT)\s+([A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ0-9\s\-']{1,50}?)\s+(\d{5})\s+([A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ\-']+(?:\s+[A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ\-']+){0,5})/i;

    function tryMatchAdr(text) {
      const m = text.match(adrLineRegex);
      if (!m) return false;
      numVoie     = m[1];
      typeVoie    = m[2];
      libelleVoie = m[3].trim().replace(/\s+/g, " ");
      codePostal  = m[4];
      commune     = m[5].trim().replace(/\s+/g, " ")
                      .split(/\s+(?:TITULAIRE|MENTIONS?|SANS|USAGE|VEHICULE|VÉHICULE|DOSSIER|CO\-?TITULAIRE|LOCATAIRE|LOUEUR|NATURE|ADRESSE|IDENTIT[ÉE])\b/i)[0]
                      .trim();
      return true;
    }

    outerAdr:
    for (let i = 0; i < lines.length; i++) {
      if (tryMatchAdr(lines[i])) break;
      if (i + 1 < lines.length && tryMatchAdr(lines[i] + " " + lines[i+1])) break outerAdr;
    }

    // ── NOUVEAU v15 : Téléphone portable du titulaire ────────────────
    // Saisie sur l'écran récap dans <input id="telephonePortable">
    const telephone = inputValue("telephonePortable");

    const today = new Date();
    const jj    = String(today.getDate()).padStart(2, "0");
    const mm    = String(today.getMonth() + 1).padStart(2, "0");
    const aaaa  = String(today.getFullYear());

    return {
      type_demarche: demarche,
      immat,
      vin,
      marque,
      genre_national: genre,
      carrosserie,
      puissance_fiscale: puissance,
      energie,
      date_premiere_immat: datePremImmat,
      numero_formule: numFormule,
      titulaire: {
        nom, prenom,
        date_naissance: dateNaiss,
        commune_naissance: communeNaiss,
        departement_naissance: deptNaiss,
        num_voie: numVoie,
        type_voie: typeVoie,
        libelle_voie: libelleVoie,
        code_postal: codePostal,
        commune,
        telephone
      },
      date_signature: { jj, mm, aaaa }
    };
  }

  // ─── Extraction page cession (ECR_IVO_CES_02 ou similaire) ────────────

  function extractFromCession() {
    const bodyTxt = document.body.innerText;

    // ── Immatriculation ──────────────────────────────────────────────
    let immat = "";
    document.querySelectorAll("input[type=text], input:not([type])").forEach(inp => {
      if (immat) return;
      const v = (inp.value || "").trim().toUpperCase();
      if (/^[A-Z]{2}-?\d{3}-?[A-Z]{2}$/.test(v)) {
        immat = v.includes("-") ? v : v.replace(/^([A-Z]{2})(\d{3})([A-Z]{2})$/, "$1-$2-$3");
      }
    });
    if (!immat) {
      const m = bodyTxt.match(/\b([A-Z]{2}-\d{3}-[A-Z]{2})\b/);
      if (m) immat = m[1];
    }

    // ── VIN ──────────────────────────────────────────────────────────
    let vin = "";
    document.querySelectorAll("input[type=text], input:not([type])").forEach(inp => {
      if (vin) return;
      const v = (inp.value || "").trim().toUpperCase();
      if (/^[A-HJ-NPR-Z0-9]{17}$/.test(v)) vin = v;
    });
    if (!vin) {
      const m = bodyTxt.match(/\b([A-HJ-NPR-Z0-9]{17})\b/);
      if (m) vin = m[1];
    }

    // ── Identité du titulaire ou de l'acquéreur (professionnel) ─────
    // Sur la page ECR_IVO_CES_02, le label contient "Identité du titulaire
    // ou de l'acquéreur (professionnel)".
    let identite = "";

    // 1) Cherche un label dont le texte matche, puis remonte à l'input lié
    const labels = document.querySelectorAll("label");
    for (const lab of labels) {
      const txt = lab.textContent.replace(/\s+/g, " ").trim();
      if (/identit[ée].*(titulaire|acqu[ée]reur)|acqu[ée]reur.*professionnel/i.test(txt)) {
        const forId = lab.getAttribute("for");
        if (forId) {
          const inp = document.getElementById(forId);
          if (inp && inp.value && inp.value.trim().length > identite.length) {
            identite = inp.value.trim();
          }
        }
      }
    }

    // 2) Fallback : scanner les inputs par nom contenant les mots-clés métier
    if (!identite) {
      document.querySelectorAll("input[type=text], input:not([type])").forEach(inp => {
        const ctx = ((inp.name || "") + " " + (inp.id || "")).toLowerCase();
        const v = (inp.value || "").trim();
        if (!v || v.length < 3) return;
        if (/acqu|raison.?sociale|d[ée]nomination|professionnel|titulaire/i.test(ctx)) {
          if (v.length > identite.length) identite = v;
        }
      });
    }

    // 3) Dernier recours : la cellule située APRÈS un libellé "Identité..."
    if (!identite) {
      const cells = getAllCells();
      const idx = cells.findIndex(c => /identit[ée].*(titulaire|acqu[ée]reur)/i.test(c));
      if (idx >= 0 && idx < cells.length - 1) identite = cells[idx + 1].trim();
    }

    const today = new Date();
    const jj    = String(today.getDate()).padStart(2, "0");
    const mm    = String(today.getMonth() + 1).padStart(2, "0");
    const aaaa  = String(today.getFullYear());

    return {
      type_demarche: "declaration_cession",
      immat,
      vin,
      // Pour la cession on n'a pas l'adresse vendeur — c'est volontaire.
      // L'identité acquéreur professionnel devient le mandant du 13757.
      titulaire: {
        nom: identite,
        prenom: "",
        date_naissance: "",
        commune_naissance: "",
        departement_naissance: "",
        num_voie: "",
        type_voie: "",
        libelle_voie: "",
        code_postal: "",
        commune: "",
        telephone: ""
      },
      objet_mandat: "Enregistrement de cession",
      date_signature: { jj, mm, aaaa }
    };
  }

  // ─── Construction des champs CERFA depuis le payload ──────────────────

  function buildFields13757(payload) {
    const t = payload.titulaire || {};
    return {
      nom_prenom:    `${t.nom || ""} ${t.prenom || ""}`.trim().toUpperCase(),
      num_voie:      t.num_voie || "",
      type_voie:     (t.type_voie || "").toUpperCase(),
      libelle_voie:  (t.libelle_voie || "").toUpperCase(),
      code_postal:   t.code_postal || "",
      commune:       (t.commune || "").toUpperCase(),
      marque:        (payload.marque || "").toUpperCase(),
      vin:           (payload.vin || "").toUpperCase(),
      immat:         (payload.immat || "").toUpperCase(),
      jour:          payload.date_signature.jj,
      mois:          payload.date_signature.mm,
      annee:         payload.date_signature.aaaa,
      // v15 — objet du mandat (rempli uniquement en cession)
      objet_mandat:  payload.objet_mandat || ""
    };
  }

  function buildFields13750(payload) {
    const t = payload.titulaire || {};
    const [nj, nm, na] = (t.date_naissance || "").split("/");
    return {
      immat:        (payload.immat || "").toUpperCase(),
      date_immat: (payload.date_premiere_immat || "").replace(/\//g, " "),
      marque:       (payload.marque || "").toUpperCase(),
      vin:          (payload.vin || "").toUpperCase(),
      genre:        (payload.genre_national || "").toUpperCase(),
      nom_prenom:   `${t.nom || ""} ${t.prenom || ""}`.trim().toUpperCase(),
      naiss_jour:   nj || "",
      naiss_mois:   nm || "",
      naiss_annee:  na || "",
      naiss_com:    (t.commune_naissance || "").toUpperCase(),
      naiss_dep:    t.departement_naissance || "",
      num_voie:     t.num_voie || "",
      type_voie:    (t.type_voie || "").toUpperCase(),
      libelle_voie: (t.libelle_voie || "").toUpperCase(),
      code_postal:  t.code_postal || "",
      commune:      (t.commune || "").toUpperCase(),
      // v15 — téléphone portable
      telephone:    t.telephone || "",
      // v15.1 — date du jour pour signature titulaire (zone "Le :")
      date_signature: `${payload.date_signature.jj}/${payload.date_signature.mm}/${payload.date_signature.aaaa}`
    };
  }

  // ─── Recherche automatique du template ────────────────────────────────

  async function findTemplateUrl(formId) {
    const candidates = [
      `templates/cerfa_${formId}.pdf`,
      `templates/cerfa_${formId}.jpg`,
      `templates/cerfa_${formId}.jpeg`,
      `templates/cerfa_${formId}.png`
    ];
    for (const path of candidates) {
      const url = chrome.runtime.getURL(path);
      try {
        const r = await fetch(url, { method: "HEAD" });
        if (r.ok) return url;
      } catch (_) { /* essayer suivant */ }
    }
    throw new Error(
      `Aucun template trouvé pour le CERFA ${formId}. ` +
      `Placez cerfa_${formId}.pdf (ou .jpg / .png) dans le dossier templates/.`
    );
  }

  // ─── Génération PDFs et ouverture ─────────────────────────────────────

  async function generateAllCerfas(pageType) {
    const [coords, config] = await Promise.all([
      fetch(chrome.runtime.getURL("coords.json")).then(r => r.json()),
      fetch(chrome.runtime.getURL("config.json")).then(r => r.json()).catch(() => ({}))
    ]);

    const payload = pageType === "cession"
      ? extractFromCession()
      : extractFromRecap();

    console.log(`[SIV→CERFA v${VERSION}] Page=${pageType} — Payload extrait :`, JSON.parse(JSON.stringify(payload)));

    if (config?.debug?.enabled) {
      console.log("[SIV→CERFA DEBUG] coords.json chargé :", coords);
      console.log("[SIV→CERFA DEBUG] Champs 13757 :", buildFields13757(payload));
      if (payload.type_demarche === "changement_proprietaire") {
        console.log("[SIV→CERFA DEBUG] Champs 13750 :", buildFields13750(payload));
      }
    }

    const ts        = new Date().toISOString().slice(0, 19).replace(/[-:T]/g, "");
    const immatStr  = (payload.immat || "AAAAAAA").replace(/-/g, "");
    const baseName  = `${ts}_${immatStr}`;
    const generated = [];

    // CERFA 13757 (mandat) — toujours
    {
      const fields = buildFields13757(payload);
      const tplUrl = await findTemplateUrl("13757");
      const blob = await window.SivCerfaPdf.fillCerfa(
        "13757", fields, coords, tplUrl,
        {
          debug: !!(config?.debug?.enabled),
          render: config?.render || {}
        }
      );
      generated.push({ name: `${baseName}_cerfa_13757.pdf`, blob });
    }

    // CERFA 13750 — UNIQUEMENT pour le changement de propriétaire
    if (payload.type_demarche === "changement_proprietaire") {
      const fields = buildFields13750(payload);
      const tplUrl = await findTemplateUrl("13750");
      const blob = await window.SivCerfaPdf.fillCerfa(
        "13750", fields, coords, tplUrl,
        {
          debug: !!(config?.debug?.enabled),
          render: config?.render || {}
        }
      );
      generated.push({ name: `${baseName}_cerfa_13750.pdf`, blob });
    }

    return { generated, payload };
  }

  // ─── Injection barre orange + bouton ──────────────────────────────────

  function injectBar(pageType) {
    if (document.getElementById("siv-cerfa-bar")) return;

    const bar = document.createElement("div");
    bar.id = "siv-cerfa-bar";

    const title = document.createElement("span");
    title.className = "siv-cerfa-title";
    title.textContent = "🖨 SIV → CERFA";

    const btn = document.createElement("button");
    btn.id = "siv-cerfa-btn";
    btn.type = "button";
    btn.textContent = pageType === "cession"
      ? "Générer le mandat (cession)"
      : "Générer les CERFA";

    const status = document.createElement("span");
    status.id = "siv-cerfa-status";

    btn.addEventListener("click", async () => {
      btn.disabled = true;
      status.textContent = "⏳ Génération en cours…";
      status.className = "";

      try {
        const { generated } = await generateAllCerfas(pageType);

        if (generated.length === 0) throw new Error("Aucun CERFA généré.");

        for (const { name, blob } of generated) {
          const url = URL.createObjectURL(blob);
          const win = window.open(url, "_blank");
          if (!win) {
            const a = document.createElement("a");
            a.href = url;
            a.download = name;
            document.body.appendChild(a);
            a.click();
            a.remove();
          }
          setTimeout(() => URL.revokeObjectURL(url), 30_000);
        }

        const msg = `✅ ${generated.length} CERFA généré(s)`;
        status.textContent = msg;
        status.className = "siv-cerfa-ok";
        console.log("[SIV→CERFA]", msg, generated.map(g => g.name));
      } catch (err) {
        console.error("[SIV→CERFA] Erreur :", err);
        status.textContent = `❌ ${err.message}`;
        status.className = "siv-cerfa-ko";
      } finally {
        btn.disabled = false;
      }
    });

    bar.appendChild(title);
    bar.appendChild(btn);
    bar.appendChild(status);

    document.body.prepend(bar);
    document.body.classList.add("siv-cerfa-bar-active");
  }

  // ─── Init ─────────────────────────────────────────────────────────────

  function init() {
    const pageType = getPageType();
    console.log(`[SIV→CERFA] content.js v${VERSION} chargé sur ${location.href} — page=${pageType}`);
    if (pageType === "autre") return;
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", () => injectBar(pageType));
    } else {
      setTimeout(() => injectBar(pageType), 300);
    }
  }

  init();
})();
