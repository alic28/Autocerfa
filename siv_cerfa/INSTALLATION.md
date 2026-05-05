# 📄 SIV → CERFA — Guide d'installation

Extension Microsoft Edge + Service local pour générer automatiquement
les formulaires CERFA 13750 et 13757 depuis les écrans du SIV.

---

## ⚡ Installation en 3 étapes

### Étape 1 — Installer Python (si pas déjà fait)

1. Aller sur https://www.python.org/downloads/
2. Télécharger Python 3.10 ou plus récent (Windows)
3. **Cocher "Add Python to PATH"** lors de l'installation
4. Installer

---

### Étape 2 — Installer l'extension dans Edge

1. Ouvrir **Microsoft Edge**
2. Aller dans le menu `···` → **Extensions** → **Gérer les extensions**
3. Activer le **Mode développeur** (interrupteur en bas à gauche)
4. Cliquer sur **"Charger l'extension non empaquetée"**
5. Sélectionner le dossier **`extension`** (dans ce dossier siv_cerfa)
6. L'extension apparaît avec l'icône 📄 orange dans la barre Edge

---

### Étape 3 — Démarrer le service local

Double-cliquer sur **`start_server.bat`**

Une fenêtre noire s'ouvre et affiche :
```
============================================================
  SIV → CERFA  |  Dreux Carte Grise
  Service local de generation des formulaires CERFA
============================================================
  URL    : http://localhost:5000
  Laissez cette fenetre ouverte pendant votre utilisation du SIV.
```

> ⚠️ **Laisser cette fenêtre ouverte** pendant toute la durée d'utilisation du SIV.

---

## 🔄 Utilisation au quotidien

### Pour un changement de titulaire :

```
1. Ouvrez le SIV et naviguez vers "Changer le titulaire > Série normale"

2. Écran 1 (Infos véhicule) :
   → La barre orange apparaît en haut de page
   → Les données sont lues automatiquement ✓

3. Écrans 2, 3 (Usages, Titulaire) :
   → Remplissez normalement
   → Cliquez "💾 Mémoriser cet écran" sur l'écran du titulaire

4. Écran Récapitulatif :
   → Le bouton "🖨️ Générer les CERFA" apparaît en haut
   → Cliquez dessus

5. → 2 nouveaux onglets s'ouvrent avec :
      • Le CERFA 13750 (Demande de certificat d'immatriculation)
      • Le CERFA 13757 (Mandat d'immatriculation)

6. Imprimez ou téléchargez depuis les onglets
```

---

## 🗂️ Où sont sauvegardés les CERFA ?

Dans le dossier **`output\`** du projet, avec un nom incluant la date et l'immatriculation :
```
output\
  20241115_143022_GP910RT_cerfa_13750.pdf
  20241115_143022_GP910RT_cerfa_13757.pdf
```

---

## 🔧 En cas de problème

### L'icône orange n'apparaît pas dans Edge
→ Vérifier que l'extension est bien activée dans `edge://extensions/`
→ Vérifier que le Mode développeur est activé

### "Service non démarré" dans la barre orange
→ Lancer `start_server.bat` et laisser la fenêtre ouverte
→ Vérifier qu'aucun antivirus ne bloque localhost:5000

### Les données ne sont pas toutes remplies
→ Utiliser le bouton "💾 Mémoriser cet écran" sur chaque écran important
→ Le récapitulatif (écran 4) est le plus complet — toujours s'y rendre avant de générer

### Les CERFA s'ouvrent mais les données manquent
→ Les noms de champs du SIV ont peut-être changé
→ Contacter le développeur avec une capture d'écran

---

## 🚀 Démarrage rapide quotidien

1. Double-clic sur `start_server.bat` → laisser ouvert
2. Ouvrir Edge → naviguer sur le SIV
3. Travailler normalement → cliquer "🖨️ Générer les CERFA" sur le récap

---

## 📁 Structure du projet

```
siv_cerfa\
├── start_server.bat          ← Démarrage en 1 clic (Windows)
├── server\
│   └── server.py             ← Service Flask local (port 5000)
├── extension\
│   ├── manifest.json         ← Déclaration de l'extension Edge
│   ├── content.js            ← Script de lecture des pages SIV
│   ├── content.css           ← Styles de la barre orange
│   ├── popup.html/js         ← Interface popup de l'extension
│   └── icons\                ← Icônes de l'extension
├── src\                      ← Générateur CERFA (Python)
├── templates\                ← Images JPEG des formulaires CERFA
└── output\                   ← PDFs générés (créé automatiquement)
```
