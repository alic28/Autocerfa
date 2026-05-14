/**
 * SIV → CERFA — pdf-generator.js v14.1
 *
 * Remplit un PDF CERFA dans le navigateur via pdf-lib (déjà chargé).
 * Détecte automatiquement le format du template (JPEG, PNG ou PDF)
 * et utilise la méthode adéquate.
 *
 * Convention coords.json :
 *   x, y       = coin haut-gauche du texte, en pixels image (réf 1240×1755)
 *   w          = largeur disponible
 *   fs         = font size en pt PDF
 *   image_w/h  = dimensions de référence du template
 *
 * Conversion image → PDF :
 *   sx = pdf_width / image_width
 *   sy = pdf_height / image_height
 *   pdf_x      = x * sx
 *   baseline_y = pdf_height - y * sy - fs * 0.85
 */

(function (global) {
  "use strict";

  const A4_WIDTH_PT  = 595.28;
  const A4_HEIGHT_PT = 841.89;

  /**
   * Détecte le format d'un fichier par ses magic bytes.
   * @param {ArrayBuffer} bytes
   * @returns {"jpeg" | "png" | "pdf" | "unknown"}
   */
  function detectFormat(bytes) {
    const view = new Uint8Array(bytes);
    if (view.length < 4) return "unknown";

    // JPEG : FF D8 FF
    if (view[0] === 0xFF && view[1] === 0xD8 && view[2] === 0xFF) {
      return "jpeg";
    }
    // PNG : 89 50 4E 47
    if (view[0] === 0x89 && view[1] === 0x50 && view[2] === 0x4E && view[3] === 0x47) {
      return "png";
    }
    // PDF : 25 50 44 46 ("%PDF")
    if (view[0] === 0x25 && view[1] === 0x50 && view[2] === 0x44 && view[3] === 0x46) {
      return "pdf";
    }
    return "unknown";
  }

  /**
   * Nettoie une chaîne pour la rendre compatible avec la police Helvetica/WinAnsi :
   *   - Supprime tabs, retours chariots, caractères de contrôle
   *   - Remplace les caractères Unicode non WinAnsi par leur équivalent ASCII
   *   - Collapse les espaces multiples
   * @param {string} s
   * @returns {string}
   */
  function sanitizeForPdf(s) {
    if (!s) return "";
    return String(s)
      // Caractères de contrôle (\t \n \r \v \f + autres < 0x20) → espace
      .replace(/[\x00-\x1F\x7F]/g, " ")
      // Caractères typographiques Unicode → ASCII
      .replace(/[\u2018\u2019\u201A\u201B]/g, "'")    // guillemets simples
      .replace(/[\u201C\u201D\u201E\u201F]/g, '"')    // guillemets doubles
      .replace(/[\u2013\u2014\u2015]/g, "-")          // tirets longs
      .replace(/\u2026/g, "...")                       // points de suspension
      .replace(/[\u00A0\u202F\u2007]/g, " ")          // espaces insécables
      // Caractères au-delà de WinAnsi (extended Latin, emojis, etc.)
      // → on remplace les caractères > 0xFF par "?", sauf on garde les latins étendus
      .replace(/[\u0100-\uFFFF]/g, (ch) => {
        const code = ch.charCodeAt(0);
        // Conserver les caractères latins étendus communs (déjà dans WinAnsi)
        if (code === 0x0152 || code === 0x0153) return ch; // Œ œ
        if (code === 0x0160 || code === 0x0161) return ch; // Š š
        if (code === 0x0178 || code === 0x017D || code === 0x017E) return ch; // Ÿ Ž ž
        return "";
      })
      // Collapse les espaces multiples
      .replace(/\s+/g, " ")
      .trim();
  }

  /**
   * Génère un PDF CERFA rempli.
   * @param {string} formId        - "13750" ou "13757"
   * @param {object} payload       - { key: value }
   * @param {object} coords        - coords.json complet
   * @param {string} templateUrl   - chrome.runtime.getURL(...) du template
   * @param {object} [options]     - { debug, render: { baseline_offset_ratio, y_offset_pt, x_offset_pt } }
   * @returns {Promise<Blob>}
   */
  async function fillCerfa(formId, payload, coords, templateUrl, options) {
    const opts = options || {};
    const debug = !!opts.debug;
    const render = opts.render || {};
    const baselineRatio = (typeof render.baseline_offset_ratio === "number") ? render.baseline_offset_ratio : 0.85;
    const yOffset       = (typeof render.y_offset_pt === "number") ? render.y_offset_pt : 0;
    const xOffset       = (typeof render.x_offset_pt === "number") ? render.x_offset_pt : 0;
    const { PDFDocument, StandardFonts, rgb } = global.PDFLib;

    const formCoords = coords[formId];
    if (!formCoords) throw new Error(`Form ${formId} introuvable dans coords.json`);

    // ── Charger le template ──────────────────────────────────────────────
    const tplBytes = await fetch(templateUrl).then(r => {
      if (!r.ok) throw new Error(`Template ${templateUrl} introuvable (${r.status})`);
      return r.arrayBuffer();
    });

    const fmt = detectFormat(tplBytes);

    let pdfDoc;
    let page;
    let pageWidth;
    let pageHeight;

    if (fmt === "pdf") {
      // ── Cas PDF : charger directement et écrire par-dessus ─────────────
      pdfDoc = await PDFDocument.load(tplBytes);
      const pages = pdfDoc.getPages();
      if (pages.length === 0) throw new Error("Le template PDF n'a aucune page");
      page = pages[0];
      const sz = page.getSize();
      pageWidth  = sz.width;
      pageHeight = sz.height;
    } else if (fmt === "jpeg" || fmt === "png") {
      // ── Cas image : créer un PDF A4 et dessiner l'image en fond ────────
      pdfDoc = await PDFDocument.create();
      page = pdfDoc.addPage([A4_WIDTH_PT, A4_HEIGHT_PT]);
      pageWidth  = A4_WIDTH_PT;
      pageHeight = A4_HEIGHT_PT;

      const img = (fmt === "jpeg")
        ? await pdfDoc.embedJpg(tplBytes)
        : await pdfDoc.embedPng(tplBytes);

      page.drawImage(img, {
        x: 0, y: 0,
        width:  pageWidth,
        height: pageHeight
      });
    } else {
      // ── Format non reconnu : erreur explicite ──────────────────────────
      const head = new Uint8Array(tplBytes).slice(0, 4);
      const hex  = Array.from(head).map(b => b.toString(16).padStart(2, "0")).join(" ");
      throw new Error(
        `Template "${templateUrl}" : format non reconnu (magic bytes: ${hex}). ` +
        `Formats acceptés : JPEG, PNG, PDF.`
      );
    }

    // ── Embedder la police ───────────────────────────────────────────────
    const font = await pdfDoc.embedFont(StandardFonts.Helvetica);

    // ── Calculer les facteurs de mise à l'échelle ────────────────────────
    const sx = pageWidth  / formCoords.image_width;
    const sy = pageHeight / formCoords.image_height;

    if (debug) {
      console.log(`[SIV→CERFA DEBUG] ${formId} :`);
      console.log(`  - Format template     : ${fmt}`);
      console.log(`  - Page PDF            : ${pageWidth.toFixed(2)} × ${pageHeight.toFixed(2)} pt`);
      console.log(`  - Image référence     : ${formCoords.image_width} × ${formCoords.image_height} px`);
      console.log(`  - Scale x / y         : ${sx.toFixed(4)} / ${sy.toFixed(4)}`);
      console.log(`  - Baseline ratio      : ${baselineRatio}`);
      console.log(`  - Y offset (pt)       : ${yOffset}`);
      console.log(`  - X offset (pt)       : ${xOffset}`);
      console.log(`  - Nombre de champs    : ${formCoords.fields.length}`);
    }

    // ── Dessiner chaque champ ────────────────────────────────────────────
    for (const f of formCoords.fields) {
      let value = payload[f.key];
      if (value === undefined || value === null) continue;
      value = sanitizeForPdf(String(value));
      if (!value) continue;

      const fs   = f.fs || 9;
      const xPt  = f.x * sx + xOffset;
      const yTop = pageHeight - f.y * sy + yOffset;
      const yBl  = yTop - fs * baselineRatio;

      const maxWidth = (f.w || 999) * sx;
let displayText = value;
let textWidth   = font.widthOfTextAtSize(displayText, fs);
let fsAuto      = fs;

if (textWidth > maxWidth && displayText.length > 3) {
  while (textWidth > maxWidth && fsAuto > fs - 3 && fsAuto > 6) {
    fsAuto -= 0.5;
    textWidth = font.widthOfTextAtSize(displayText, fsAuto);
  }
  if (textWidth > maxWidth) {
    while (displayText.length > 1 && font.widthOfTextAtSize(displayText + "…", fsAuto) > maxWidth) {
      displayText = displayText.slice(0, -1);
    }
    displayText += "…";
  }
}

const cs = f.cs || 0;
if (cs > 0) {
  let curX = xPt;
  for (const ch of displayText) {
    page.drawText(ch, { x: curX, y: yBl, size: fsAuto, font, color: rgb(0, 0, 0) });
    curX += font.widthOfTextAtSize(ch, fsAuto) + cs;
  }
} else {
  page.drawText(displayText, {
    x: xPt, y: yBl, size: fsAuto, font, color: rgb(0, 0, 0)
  });
}

      // ── Mode debug : encadrer la zone EXACTE du texte rendu ───────────
      if (debug) {
        const wPt = (f.w || 50) * sx;
        // Le rect bleu = zone exacte du texte (yTop = haut du texte, yBl = baseline)
        page.drawRectangle({
          x: xPt,
          y: yBl,
          width: wPt,
          height: yTop - yBl,
          borderColor: rgb(0, 0, 1),
          borderWidth: 0.6,
          opacity: 0
        });
        // Petite ligne rouge horizontale à yTop (= position calibrée du top du texte)
        page.drawLine({
          start: { x: xPt - 4, y: yTop },
          end:   { x: xPt + wPt, y: yTop },
          thickness: 0.4,
          color: rgb(1, 0, 0)
        });
        // Label du champ en rouge au-dessus
        page.drawText(f.key, {
          x: xPt,
          y: yTop + 1.5,
          size: 5,
          font,
          color: rgb(1, 0, 0)
        });
      }
    }

    // ── Métadonnées du PDF (titre d'onglet, auteur, etc.) ────────────────
    const titreCerfa = (formId === "13757") ? "Mandat d'immatriculation" : "Demande de certificat d'immatriculation";
    pdfDoc.setTitle(`CERFA ${formId} — ${titreCerfa}`);
    pdfDoc.setAuthor("Dreux Carte Grise");
    pdfDoc.setCreator("SIV → CERFA Extension");
    pdfDoc.setSubject(`CERFA n° ${formId}`);
    pdfDoc.setProducer("pdf-lib");

    // ── Export ──────────────────────────────────────────────────────────
    const pdfBytes = await pdfDoc.save();
    return new Blob([pdfBytes], { type: "application/pdf" });
  }
/**
   * Fusionne plusieurs PDFs en un seul, dans l'ordre fourni.
   * @param {Blob[]} blobs - Liste de blobs PDF à fusionner
   * @returns {Promise<Blob>}
   */
  async function mergePdfs(blobs) {
    const { PDFDocument } = global.PDFLib;
    const merged = await PDFDocument.create();
    for (const blob of blobs) {
      const buf = await blob.arrayBuffer();
      const doc = await PDFDocument.load(buf);
      const pages = await merged.copyPages(doc, doc.getPageIndices());
      pages.forEach(p => merged.addPage(p));
    }
    const bytes = await merged.save();
    return new Blob([bytes], { type: "application/pdf" });
  }
  // -- global.SivCerfaPdf = { fillCerfa, detectFormat };
  global.SivCerfaPdf = { fillCerfa, detectFormat, mergePdfs };

})(window);
