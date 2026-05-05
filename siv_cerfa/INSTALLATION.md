# SIV → CERFA — Guide d'installation v2.0
## Dreux Carte Grise

---

## Prérequis

- **Windows 10/11**
- **Python 3.9+** — [python.org](https://python.org) (cocher "Add to PATH" à l'installation)
- **Microsoft Edge** (ou Chrome)
- **Connexion SIV Pro** avec certificat numérique

---

## Installation (5 minutes)

### 1. Extraire le ZIP

Extraire le dossier `siv_cerfa/` dans un emplacement **sans espace ni accent**  
✅ `C:\outils\siv_cerfa\`  
❌ `C:\Mes Documents\SIV CERFA\`

### 2. Démarrer le serveur local

Double-cliquer sur **`start_server.bat`**

- L'invite de commande installe les dépendances automatiquement
- Le message `Serving Flask on http://127.0.0.1:5000` confirme que c'est prêt
- **Laisser cette fenêtre ouverte** pendant toute la session

### 3. Installer l'extension Edge

1. Ouvrir Edge → taper `edge://extensions/` dans la barre d'adresse
2. Activer **"Mode développeur"** (bouton en bas à gauche)
3. Cliquer **"Charger l'extension non empaquetée"**
4. Sélectionner le dossier **`siv_cerfa\extension\`**
5. L'icône 🖨 apparaît dans la barre d'outils Edge

> Pour Chrome : même procédure sur `chrome://extensions/`

---

## Utilisation

1. Se connecter sur **[SIV Pro](https://pro-siv.interieur.gouv.fr)**
2. Saisir la démarche (ex: Changer le titulaire)
3. Naviguer jusqu'à l'**écran Récapitulatif** (`ivo_cht_toVal`)
4. La **barre orange** apparaît en haut de la page
5. Cliquer **"Générer les CERFA"**
6. Les PDF s'ouvrent automatiquement dans de nouveaux onglets

---

## Fichiers générés

Les CERFA sont enregistrés dans le dossier `output/` avec le format :  
`AAAAMMJJ_HHMMSS_IMMAT_cerfa_13757.pdf`  
`AAAAMMJJ_HHMMSS_IMMAT_cerfa_13750.pdf`

---

## Dépannage

| Problème | Solution |
|----------|----------|
| Barre orange absente | Vérifier que l'URL contient bien `ivo_cht_toVal` |
| "Serveur introuvable" | Relancer `start_server.bat` |
| PDF vide ou données manquantes | Vérifier la console (F12 → Console) |
| Python non reconnu | Réinstaller Python en cochant "Add to PATH" |

---

## Types de démarches supportés

| Démarche | CERFA 13757 | CERFA 13750 |
|----------|:-----------:|:-----------:|
| Changement de propriétaire | ✅ | ✅ |
| Déclaration de cession | ✅ | — |

---

## Templates PDF

Les templates personnalisés se trouvent dans `templates/` :
- `cerfa_13757_template.pdf` — Mandat pré-rempli "DREUX CARTE GRISE"
- `cerfa_13750_template.pdf` — Demande de certificat d'immatriculation

Pour mettre à jour un template, remplacer le fichier PDF correspondant.

---

*Dreux Carte Grise — http://rapidcartegrise.fr — 09.83.31.79.65*
