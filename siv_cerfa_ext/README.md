# SIV → CERFA — Extension Edge | Dreux Carte Grise

**Version 15.1** — production

Génère automatiquement les CERFA 13750 et 13757 directement depuis le SIV Pro. **100% local**, aucun serveur, aucun .bat, aucune installation Python.

Tous les templates DCG personnalisés et les coordonnées calibrées sont déjà intégrés dans cette version.

---

## Nouveautés v15

- **Téléphone portable** ajouté automatiquement sur le CERFA 13750 (lu depuis l'écran récap, champ « Numéro de portable du titulaire pour le suivi du titre »).
- **Date du jour** ajoutée automatiquement sur le 13750 dans la zone « Le titulaire » (champ « Le : »).
- **Workflow déclaration de cession** : génère le mandat 13757 seul dès la page de saisie cession, avec mention « Enregistrement de cession » comme objet du mandat.

---

## Pour les salariés (utilisation au quotidien)

### Changement de titulaire
1. Se connecter au [SIV Pro](https://pro-siv.interieur.gouv.fr) avec le certificat numérique habituel.
2. Saisir la démarche jusqu'à l'écran **Récapitulatif** (URL contient `ivo_cht_toVal`).
3. Une **barre orange** apparaît en haut de la page avec un bouton **« Générer les CERFA »**.
4. Cliquer dessus → **2 onglets** s'ouvrent avec le **13750** et le **13757** pré-remplis.

### Déclaration de cession
1. Ouvrir une démarche de cession sur le SIV Pro.
2. Sur la page de saisie (immat + VIN + identité acquéreur), la **barre orange** apparaît avec un bouton **« Générer le mandat (cession) »**.
3. Cliquer dessus → **1 onglet** s'ouvre avec le **13757** pré-rempli (mention « Enregistrement de cession » dans l'objet du mandat).

---

## Installation par poste (5 minutes, à faire une seule fois)

1. Décompresser `siv_cerfa_ext` à un emplacement stable :
   - **Recommandé** : `C:\Outils\siv_cerfa_ext` ou un partage réseau lisible
   - **À éviter** : un dossier temporaire ou avec espaces/accents
2. Ouvrir Edge → barre d'adresse : `edge://extensions/`
3. Activer **« Mode développeur »** (interrupteur bas-gauche)
4. Cliquer **« Charger l'extension non empaquetée »** → sélectionner le dossier `siv_cerfa_ext`
5. (Optionnel) Cliquer le puzzle 🧩 en haut à droite → épingler 📌 l'extension

---

## Démarches supportées

| Démarche SIV                    | CERFA 13750 | CERFA 13757 | Page de déclenchement       |
|---------------------------------|:-----------:|:-----------:|-----------------------------|
| Changement de titulaire         |     ✅      |     ✅      | Récap (`ivo_cht_toVal`)     |
| Déclaration de cession          |     —       |     ✅      | Saisie cession (`ivo_ces_*`)|

---

## Mise à jour de l'extension

1. Remplacer le dossier complet par la nouvelle version
2. `edge://extensions/` → bouton **↻ Actualiser** sur la card de l'extension
3. Recharger l'onglet SIV en cours

---

## Ajustement des nouvelles coordonnées (téléphone et objet)

Les positions des deux nouveaux champs (`telephone` sur le 13750 et `objet_mandat` sur le 13757) ont été estimées et peuvent demander un ajustement fin sur ton template DCG personnalisé.

**Pour ajuster** :
1. Ouvrir `coords.json` dans n'importe quel éditeur texte
2. Trouver le bloc `"key": "telephone"` (section `"13750"`) ou `"key": "objet_mandat"` (section `"13757"`)
3. Modifier `x` (gauche/droite) et `y` (haut/bas), valeurs en pixels image — voir `image_width` et `image_height` au bas de chaque section pour la référence
4. Recharger l'extension (`edge://extensions/` → ↻) puis F5 sur l'onglet SIV
5. Re-générer un CERFA pour vérifier

Conventions :
- **Augmenter `x`** = déplace vers la droite
- **Augmenter `y`** = déplace vers le bas
- **`fs`** = taille de police en points

Valeurs initiales par défaut :
- `telephone` (13750) : x=880, y=805, fs=12
- `objet_mandat` (13757) : x=130, y=745, fs=13

---

## Confidentialité

- Aucune donnée ne quitte le navigateur
- Aucun appel réseau externe pendant la génération
- L'extension n'a accès qu'aux pages `https://pro-siv.interieur.gouv.fr/*`

---

## Dépannage

| Problème | Solution |
|----------|----------|
| Barre orange absente | F5 sur la page. Vérifier que l'URL contient `ivo_cht_toVal` (changement) ou `ivo_ces_` (cession). |
| Pop-up bloqué | Cliquer l'icône bloqueur dans la barre d'adresse → Toujours autoriser |
| Données manquantes en cession | F12 → Console → regarder `[SIV→CERFA] Payload extrait`. M'envoyer le contenu. |
| Téléphone absent sur 13750 | Vérifier qu'il est bien saisi dans le champ « Numéro de portable » sur le récap SIV avant de cliquer le bouton. |
| Position du téléphone / objet à ajuster | Voir section « Ajustement des nouvelles coordonnées » ci-dessus. |
| Extension désactivée au redémarrage | Edge désactive parfois le mode dev. Voir `INSTALLATION.md`. |

---

## Contenu de l'extension

```
siv_cerfa_ext/
├── manifest.json          Déclaration de l'extension
├── content.js             Lit les écrans SIV + injecte la barre orange
├── content.css            Styles de la barre orange
├── pdf-generator.js       Générateur PDF (utilise pdf-lib)
├── coords.json            Coordonnées calibrées DCG (déjà intégrées)
├── config.json            Config mandataire DCG
├── popup.html             Popup d'info de l'extension
├── lib/
│   └── pdf-lib.min.js     Bibliothèque pdf-lib
├── templates/
│   ├── cerfa_13757.pdf    Mandat DCG personnalisé
│   └── cerfa_13750.pdf    Demande certificat
└── icons/                 Icônes 16/48/128
```

---

*Dreux Carte Grise — http://rapidcartegrise.fr — 09.83.31.79.65*
