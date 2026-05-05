/**
 * SIV → CERFA — Content Script v1.3
 * Corrections majeures :
 *  - Blacklist des valeurs parasites (navigation, JSF placeholders "SL")
 *  - Restriction de la lecture au contenu principal (hors menu nav)
 *  - Lecture ciblée par attributs name/id JSF du SIV Pro
 */
(function () {
  "use strict";

  const ACTION = window.location.pathname.split("/do/").pop() || "";

  const SCREENS = {
    VEHICULE:  "ivo_cht_recherche_init",
    TITULAIRE: "sp_saisiepers",
    COTIT:     "sp_action",
    RECAP:     "ivo_cht_toVal",
  };

  function getScreen() {
    if (ACTION === SCREENS.VEHICULE)  return "vehicule";
    if (ACTION === SCREENS.TITULAIRE) return "titulaire";
    if (ACTION === SCREENS.COTIT)     return "cotitulaire";
    if (ACTION === SCREENS.RECAP)     return "recap";
    return "autre";
  }
  const SCREEN = getScreen();

  // ─── Zone de contenu principal (hors menu navigation) ────────────────────
  // Le SIV Pro a un menu à gauche/haut — on restreint la lecture au contenu

  function getContentZone() {
    // Essayer de trouver le conteneur principal du formulaire
    const candidates = [
      "#contenu", "#content", "#main", "#formulaire",
      ".contenu", ".content", ".main-content", ".corps",
      "form", "[id*='form']", "[id*='content']",
    ];
    for (const sel of candidates) {
      const el = document.querySelector(sel);
      if (el && el.querySelectorAll("input").length > 1) return el;
    }
    return document.body;
  }

  // ─── Blacklist de valeurs parasites ──────────────────────────────────────

  const BLACKLIST_PATTERNS = [
    /^SL$/i,                           // JSF select placeholder vide
    /^FNI/i,                           // Navigation "FNIChanger le titulaire..."
    /Changer le titulaire/i,           // Navigation
    /Inscrire l.achat/i,               // Navigation
    /Inscrire la cession/i,            // Navigation
    /Série normale/i,                  // Navigation
    /Première Immat/i,                 // Navigation
    /Convertir un dossier/i,           // Navigation
    /Numéro de l.établissement/i,      // Placeholder texte
    /par le système lors/i,            // "Généré par le système..."
    /Sélectionner/i,                   // Option select par défaut
    /^\s*$/ ,                          // Vide
    /^-+$/,                            // Tirets seuls
  ];

  function isValid(val) {
    if (!val) return false;
    const v = val.trim();
    if (v.length === 0) return false;
    return !BLACKLIST_PATTERNS.some(re => re.test(v));
  }

  function clean(val) {
    return isValid(val) ? val.trim() : "";
  }

  // ─── Helpers de lecture DOM ───────────────────────────────────────────────

  /**
   * Cherche un input dans la zone de contenu principal uniquement.
   * Priorité : attributs name/id JSF > libellé texte
   */
  function readInput(...nameFragments) {
    const zone = getContentZone();
    for (const frag of nameFragments) {
      // Par name ou id contenant le fragment
      const el = zone.querySelector(
        `input[name*="${frag}"]:not([type=hidden]),
         select[name*="${frag}"],
         input[id*="${frag}"]:not([type=hidden]),
         select[id*="${frag}"]`
      );
      if (el && isValid(el.value)) return el.value.trim();
    }
    return "";
  }

  /**
   * Lit un champ par son libellé texte, en se limitant à la zone principale.
   * Évite de lire le menu de navigation.
   */
  function readByLabel(labelText) {
    const zone = getContentZone();
    const els = zone.querySelectorAll("td, th, label");
    for (const el of els) {
      const t = el.textContent.trim().replace(/\s+/g, " ");
      if (!t.toLowerCase().includes(labelText.toLowerCase())) continue;
      if (t.length > labelText.length + 30) continue; // éviter les cellules trop longues

      // Input dans la même cellule
      const selfInp = el.querySelector("input:not([type=hidden]), select");
      if (selfInp && isValid(selfInp.value)) return selfInp.value.trim();

      // Input dans la cellule suivante
      const next = el.nextElementSibling;
      if (next) {
        const ni = next.querySelector("input:not([type=hidden]), select");
        if (ni && isValid(ni.value)) return ni.value.trim();
        const txt = next.textContent.trim();
        if (isValid(txt) && txt.length < 100) return txt;
      }

      // Input dans la ligne parente
      const row = el.closest("tr, fieldset");
      if (row) {
        const ri = row.querySelector("input:not([type=hidden]), select");
        if (ri && isValid(ri.value)) return ri.value.trim();
      }
    }
    return "";
  }

  /**
   * Lit la cellule de valeur dans le tableau récapitulatif.
   * Format : cellule label "E" | input ou texte valeur
   */
  function readRecap(code) {
    const zone = getContentZone();
    const cells = zone.querySelectorAll("td, th");
    for (let i = 0; i < cells.length; i++) {
      if (cells[i].textContent.trim() !== code) continue;
      const inp = cells[i].querySelector("input");
      if (inp && isValid(inp.value)) return inp.value.trim();
      const next = cells[i + 1];
      if (!next) continue;
      const ni = next.querySelector("input");
      if (ni && isValid(ni.value)) return ni.value.trim();
      const val = next.textContent.trim();
      if (isValid(val) && val !== code && val.length < 100) return val;
    }
    return "";
  }

  /** Sexe depuis les radio buttons */
  function readSexe() {
    const zone = getContentZone();
    for (const r of zone.querySelectorAll('input[type="radio"]:checked')) {
      const lbl = document.querySelector(`label[for="${r.id}"]`);
      const t = (lbl?.textContent || r.value || "").toLowerCase();
      if (t.includes("masculin")) return "M";
      if (t.includes("féminin") || t.includes("feminin")) return "F";
    }
    return "";
  }

  /** Mandataire = société connectée dans "Bienvenue, DREUX CARTE GRISE." */
  function readMandataire() {
    const m = document.body.innerText.match(/Bienvenue[,\s]+(.+?)\s*\./i);
    return m ? m[1].trim() : "";
  }

  /** Numéro de dossier */
  function getDossier() {
    const m = document.body.innerText.match(
      /Dossier\s+N[°o\.]\s*[:\-]?\s*([A-Z]{2}-\d{3}-[A-Z]{2})/i
    );
    return m ? m[1].trim() : "";
  }

  function todayStr() {
    const d = new Date();
    return `${String(d.getDate()).padStart(2,"0")}/${String(d.getMonth()+1).padStart(2,"0")}/${d.getFullYear()}`;
  }

  // ─── Écran 1 : Véhicule (ivo_cht_recherche_init) ─────────────────────────

  function readEcranVehicule() {
    // Les inputs du SIV Pro ont des noms JSF — on lit par libellé puisqu'on
    // ne connaît pas les attributs name exacts
    const immat = clean(
      readByLabel("Numéro d'immatriculation") ||
      readInput("immat", "numImmat", "immatriculation")
    );
    const vin = clean(
      readByLabel("Numéro d'identification véhicule") ||
      readInput("vin", "numVin", "identification")
    );
    const formule = clean(
      readByLabel("Numéro de formule du CI") ||
      readByLabel("Numéro de formule") ||
      readInput("formule", "numFormule")
    );

    const data = {
      screen:           "vehicule",
      dossier:          getDossier(),
      mandataire_nom:   readMandataire(),
      mandataire_siret: clean(readByLabel("SIREN/SIRET") || readInput("siret")),
      immatriculation:  immat.replace(/\s+/g, "-").toUpperCase(),
      vin:              vin.toUpperCase(),
      numero_formule:   formule,
    };

    console.log("[SIV→CERFA] Écran véhicule :", data);
    chrome.storage.local.set({ siv_vehicule: data });
    showToast("✅ Véhicule mémorisé : " + (immat || "—"));
    return data;
  }

  // ─── Écran titulaire (sp_saisiepers) ─────────────────────────────────────

  function readEcranTitulaire() {
    const zone = getContentZone();

    // Type de voie = premier <select> dans la zone adresse
    const selects = [...zone.querySelectorAll("select")];
    const typeVoieEl = selects.find(s =>
      s.name?.toLowerCase().includes("voie") ||
      s.id?.toLowerCase().includes("voie") ||
      s.closest("tr, div")?.textContent?.toLowerCase().includes("type")
    );
    const typeVoie = clean(typeVoieEl?.value || "");

    // Numéro de voie = input court (max 4 chars en général)
    const numVoieEl = [...zone.querySelectorAll("input[maxlength='4'], input[size='4']")]
      .find(el => isValid(el.value));
    const numVoie = clean(numVoieEl?.value || readByLabel("Numéro") || readInput("numVoie"));

    const data = {
      screen: "titulaire",
      type: "personne_physique",
      nom:               clean(readByLabel("(*) Nom")    || readByLabel("Nom :") || readInput("nom")),
      nom_usage:         clean(readByLabel("Nom d'usage")                         || readInput("nomUsage")),
      prenom:            clean(readByLabel("(*) Prénom") || readByLabel("Prénom :") || readInput("prenom")),
      sexe:              readSexe(),
      date_naissance:    clean(readByLabel("(*) Date de naissance") || readByLabel("Date de naissance")),
      commune_naissance: clean(readByLabel("(*) Commune")  || readByLabel("Commune :")),
      departement_naissance: clean(readByLabel("(*) Département") || readByLabel("Département :")),
      etage:        clean(readByLabel("Etage / Escalier")),
      immeuble:     clean(readByLabel("Immeuble / Résidence")),
      num_voie:     numVoie,
      type_voie:    typeVoie,
      libelle_voie: clean(readByLabel("Libellé") || readInput("libelleVoie", "libelle")),
      lieu_dit:     clean(readByLabel("Lieu-dit") || readInput("lieuDit")),
      code_postal:  clean(readByLabel("Code postal")       || readInput("codePostal", "cp")),
      commune:      clean(readByLabel("Bureau distributeur") || readInput("bureauDistributeur")),
    };

    console.log("[SIV→CERFA] Écran titulaire :", data);
    chrome.storage.local.set({ siv_titulaire: data });
    showToast("✅ Titulaire mémorisé : " + ([data.prenom, data.nom].filter(Boolean).join(" ") || "—"));
    return data;
  }

  // ─── Écran récapitulatif (ivo_cht_toVal) ─────────────────────────────────

  /**
   * Parse le titulaire depuis le tableau récap.
   * Structure attendue en colonne 0 :
   *   "INES LEA OMONT\nné(e) le 21/01/2006 à LA TESTE DE BUCH (33)"
   * Structure attendue en colonne 1 :
   *   "5 RUE PASTEUR\n59300 VALENCIENNES"
   */
  function parseTitulaireRecap() {
    const r = {
      nom: "", prenom: "", sexe: "",
      date_naissance: "", commune_naissance: "", departement_naissance: "",
      num_voie: "", type_voie: "", libelle_voie: "",
      code_postal: "", commune: "",
    };

    const zone = getContentZone();
    for (const row of zone.querySelectorAll("table tr")) {
      const cells = [...row.querySelectorAll("td")];
      if (cells.length < 2) continue;
      const identity = cells[0]?.textContent?.trim() || "";
      const adresse  = cells[1]?.textContent?.trim() || "";
      if (!identity.match(/né\(e\)/i)) continue;

      // Nom/Prénom (1re ligne)
      const nameLine = identity.split("\n")[0].trim();
      const parts = nameLine.split(/\s+/);
      if (parts.length >= 2) {
        r.nom    = parts[parts.length - 1];
        r.prenom = parts.slice(0, -1).join(" ");
      } else {
        r.nom = nameLine;
      }

      // Naissance
      const nm = identity.match(
        /né\(e\)\s+le\s+(\d{2}\/\d{2}\/\d{4})\s+[àa]\s+(.+?)\s+\((\d{2,3})\)/i
      );
      if (nm) {
        r.date_naissance        = nm[1];
        r.commune_naissance     = nm[2].trim();
        r.departement_naissance = nm[3];
      }

      // Sexe depuis adresse expédition
      const expTxt = document.body.innerText;
      if (/Adresse d.exp[eé]dition[\s\S]{0,50}MME/i.test(expTxt))   r.sexe = "F";
      else if (/Adresse d.exp[eé]dition[\s\S]{0,50}M\.\s/i.test(expTxt)) r.sexe = "M";

      // Adresse
      const aLines = adresse.split("\n").map(l => l.trim()).filter(Boolean);
      if (aLines[0]) {
        const vm = aLines[0].match(/^(\d+[a-zA-Z]?)\s*(bis|ter|quater)?\s*([A-ZÀÂÄÉÈÊËÎÏÔÙÛÜ]+)\.?\s+(.+)$/i);
        if (vm) {
          r.num_voie    = vm[1];
          r.type_voie   = vm[3];
          r.libelle_voie = vm[4].trim();
        } else {
          r.libelle_voie = aLines[0];
        }
      }
      if (aLines[1]) {
        const cm = aLines[1].match(/^(\d{5})\s+(.+)$/);
        if (cm) { r.code_postal = cm[1]; r.commune = cm[2].trim(); }
      }
      break;
    }
    return r;
  }

  async function buildPayload() {
    const bodyText = document.body.innerText;

    // Véhicule depuis le récap
    const vehicule = {
      vin:              readRecap("E"),
      marque:           readRecap("D.1"),
      genre:            readRecap("J.1"),
      carrosserie:      readRecap("J.3"),
      puissance_fiscale: readRecap("P.6"),
      energie:          readRecap("P.3"),
    };
    const dm = bodyText.match(/Date de premi[eè]re immatriculation\s+(\d{2}\/\d{2}\/\d{4})/i);
    vehicule.date_premiere_immat = dm?.[1] || "";

    const titulaireRecap = parseTitulaireRecap();

    return new Promise((resolve) => {
      chrome.storage.local.get(["siv_vehicule", "siv_titulaire"], (stored) => {
        const sv = stored.siv_vehicule  || {};
        const st = stored.siv_titulaire || {};

        // Fusion : données écrans dédiés > parsing récap > vide
        const titulaire = {
          type: "personne_physique",
          nom:               st.nom                   || titulaireRecap.nom,
          prenom:            st.prenom                || titulaireRecap.prenom,
          nom_usage:         st.nom_usage             || "",
          sexe:              st.sexe                  || titulaireRecap.sexe,
          date_naissance:    st.date_naissance        || titulaireRecap.date_naissance,
          commune_naissance: st.commune_naissance     || titulaireRecap.commune_naissance,
          departement_naissance: st.departement_naissance || titulaireRecap.departement_naissance,
          etage:             st.etage                 || "",
          immeuble:          st.immeuble              || "",
          num_voie:          st.num_voie              || titulaireRecap.num_voie,
          type_voie:         st.type_voie             || titulaireRecap.type_voie,
          libelle_voie:      st.libelle_voie          || titulaireRecap.libelle_voie,
          lieu_dit:          st.lieu_dit              || "",
          code_postal:       st.code_postal           || titulaireRecap.code_postal,
          commune:           st.commune               || titulaireRecap.commune,
        };

        const payload = {
          type_demarche:    "changement_proprietaire",
          dossier:          sv.dossier          || getDossier(),
          immatriculation:  sv.immatriculation  || "",
          numero_formule:   sv.numero_formule   || "",
          mandataire_nom:   sv.mandataire_nom   || readMandataire(),
          mandataire_siret: sv.mandataire_siret || "",
          vehicule,
          titulaire,
          fait_a:         "Dreux",
          date_signature: todayStr(),
        };

        console.log("[SIV→CERFA] Payload final :", JSON.stringify(payload, null, 2));
        resolve(payload);
      });
    });
  }

  // ─── Toast ───────────────────────────────────────────────────────────────

  function showToast(msg, type = "success") {
    const ex = document.getElementById("siv-cerfa-toast");
    if (ex) ex.remove();
    const t = document.createElement("div");
    t.id = "siv-cerfa-toast";
    t.textContent = msg;
    const bg = { error:"#c0392b", info:"#2980b9", success:"#27ae60" }[type] || "#27ae60";
    t.style.cssText = `position:fixed;top:54px;right:16px;z-index:999999;
      background:${bg};color:#fff;padding:10px 18px;border-radius:6px;
      font:bold 13px/1.4 Arial,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.3);
      cursor:pointer;max-width:420px;`;
    t.onclick = () => t.remove();
    document.body.appendChild(t);
    setTimeout(() => { t.style.opacity="0"; setTimeout(() => t.remove(), 400); }, 5000);
  }

  // ─── Barre d'outils ──────────────────────────────────────────────────────

  const SCREEN_LABELS = {
    vehicule:    "📋 Infos véhicule",
    titulaire:   "👤 Saisie titulaire",
    cotitulaire: "👥 Titulaire / Co-titulaire",
    recap:       "⭐ Récapitulatif",
    autre: "—",
  };

  function injectToolbar() {
    if (document.getElementById("siv-cerfa-toolbar")) return;
    const dossier = getDossier();
    const isRecap = SCREEN === "recap";

    const bar = document.createElement("div");
    bar.id = "siv-cerfa-toolbar";
    bar.innerHTML = `
      <div class="siv-cerfa-logo">📄 SIV→CERFA</div>
      ${dossier ? `<div class="siv-cerfa-dossier">Dossier&nbsp;<strong>${dossier}</strong></div>` : ""}
      <div class="siv-cerfa-screen">${SCREEN_LABELS[SCREEN] || "—"}</div>
      <div class="siv-cerfa-spacer"></div>
      ${isRecap
        ? `<button id="siv-btn-generer" class="siv-btn siv-btn-primary">🖨️&nbsp;Générer les CERFA</button>`
        : `<button id="siv-btn-memo" class="siv-btn siv-btn-secondary">💾&nbsp;Mémoriser cet écran</button>`
      }
      <div id="siv-cerfa-status"></div>
    `;
    document.body.prepend(bar);

    document.getElementById("siv-btn-memo")?.addEventListener("click", () => {
      const btn = document.getElementById("siv-btn-memo");
      if (btn) { btn.disabled = true; btn.textContent = "⏳..."; }
      setTimeout(() => {
        if      (SCREEN === "vehicule")    readEcranVehicule();
        else if (SCREEN === "titulaire")   readEcranTitulaire();
        else if (SCREEN === "cotitulaire") showToast("ℹ️ Cliquez sur Suivant puis Générer CERFA sur le récap", "info");
        else showToast("ℹ️ Pas de données à mémoriser ici", "info");
        if (btn) { btn.disabled = false; btn.textContent = "💾 Mémoriser cet écran"; }
      }, 200);
    });

    document.getElementById("siv-btn-generer")?.addEventListener("click", handleGenerer);
  }

  async function handleGenerer() {
    const btn    = document.getElementById("siv-btn-generer");
    const status = document.getElementById("siv-cerfa-status");
    if (btn) { btn.disabled = true; btn.textContent = "⏳ Lecture..."; }
    try {
      const payload = await buildPayload();
      if (btn) btn.textContent = "⏳ Génération...";
      const resp = await fetch("http://localhost:5000/generer", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) { const e = await resp.json().catch(()=>({})); throw new Error(e.error || `Erreur ${resp.status}`); }
      const result = await resp.json();
      let count = 0;
      if (result.cerfa_13757_url) { window.open(result.cerfa_13757_url, "_blank"); count++; }
      if (result.cerfa_13750_url) { setTimeout(() => window.open(result.cerfa_13750_url, "_blank"), 400); count++; }
      showToast(`✅ ${count} CERFA générés — vérifiez les nouveaux onglets`);
      if (status) status.textContent = `✅ ${count} CERFA ouverts`;
    } catch (err) {
      const net = err.message?.includes("fetch") || err.message?.includes("Failed");
      showToast(net ? "❌ Service non démarré — lancez start_server.bat" : `❌ ${err.message}`, "error");
      if (status) status.textContent = net ? "❌ Service non démarré" : `❌ ${err.message}`;
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = "🖨️ Générer les CERFA"; }
    }
  }

  // ─── Init ─────────────────────────────────────────────────────────────────

  function init() {
    console.log(`[SIV→CERFA] v1.3 | action=${ACTION} | écran=${SCREEN}`);
    injectToolbar();
    if (SCREEN === "vehicule")   setTimeout(readEcranVehicule,  800);
    if (SCREEN === "titulaire")  setTimeout(readEcranTitulaire, 800);
  }

  document.readyState === "loading"
    ? document.addEventListener("DOMContentLoaded", init)
    : init();
})();
