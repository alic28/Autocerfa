# Installation SIV → CERFA v14 — Guide complet

## Prérequis

Microsoft Edge ou Google Chrome (n'importe quelle version récente). Aucun autre logiciel à installer.

---

## Installation poste par poste

### Étape 1 — Copier le dossier de l'extension

Placer le dossier complet `siv_cerfa_extension` à un emplacement stable :

- **Recommandé** : `C:\Outils\siv_cerfa_extension`
- **À éviter** : un emplacement temporaire ou avec espaces/accents

⚠ **Important** : Edge garde une référence vers ce dossier. Si vous le supprimez ou le déplacez, l'extension cesse de fonctionner. Pour un déploiement multi-postes, utilisez plutôt la méthode GPO ci-dessous.

### Étape 2 — Charger dans Edge

1. Ouvrir Microsoft Edge
2. Dans la barre d'adresse, taper : `edge://extensions/` puis Entrée
3. En bas à gauche, activer **« Mode développeur »**
4. En haut, cliquer sur **« Charger l'extension non empaquetée »**
5. Naviguer jusqu'à `C:\Outils\siv_cerfa_extension` et cliquer **« Sélectionner un dossier »**

L'extension apparaît dans la liste avec le nom **« SIV → CERFA | Dreux Carte Grise »**.

### Étape 3 — Épingler l'icône (recommandé)

1. Cliquer sur l'icône puzzle 🧩 en haut à droite d'Edge
2. Cliquer sur l'épingle 📌 à côté de **« SIV → CERFA »**
3. L'icône orange « CG » apparaît dans la barre d'outils

### Étape 4 — Tester

1. Aller sur https://pro-siv.interieur.gouv.fr et se connecter
2. Démarrer une démarche jusqu'à l'écran récapitulatif
3. La barre orange doit apparaître en haut de la page avec le bouton **« Générer les CERFA »**

---

## Déploiement multi-postes par GPO (Active Directory)

Pour distribuer l'extension automatiquement à tous les salariés sans manipulation, sans dépendre du dossier local de chaque poste :

### Option A — Distribution sideload via partage réseau

1. Placer le dossier `siv_cerfa_extension` sur un partage réseau lisible par tous les utilisateurs (ex: `\\serveur\Outils\siv_cerfa_extension\`).
2. Dans la **Stratégie de groupe** (gpedit.msc ou GPO AD) :
   - Configuration ordinateur → Modèles d'administration → Microsoft Edge → Extensions
   - Activer **« Configurer les paramètres d'installation forcée des extensions »**
   - Ajouter l'entrée pointant vers le partage
3. Au prochain login, l'extension est chargée automatiquement.

### Option B — Publication sur Microsoft Edge Add-ons (officiel)

Pour une vraie distribution sans mode développeur :

1. Créer un compte développeur Microsoft Partner Center (~ 16 €/an).
2. Empaqueter l'extension en `.zip` via le bouton « Empaqueter l'extension » sur `edge://extensions/`.
3. Soumettre via https://partner.microsoft.com/dashboard/microsoftedge.
4. Une fois acceptée (24-48 h), l'extension est installable en 1 clic depuis le Edge Add-ons Store.

---

## Mise à jour de l'extension

Quand le code de l'extension est mis à jour :

1. Remplacer le dossier complet par la nouvelle version
2. Aller sur `edge://extensions/` → cliquer le bouton **↻ Actualiser** sur la carte de l'extension
3. Recharger l'onglet SIV en cours

---

## Personnalisation

### Remplacer le coords.json calibré

Si vous avez recalibré les positions des champs avec votre éditeur visuel :

1. Copier votre `coords.json` à la racine du dossier de l'extension (écraser l'existant).
2. Sur `edge://extensions/`, cliquer le bouton **↻ Actualiser** sur l'extension.
3. Recharger l'onglet SIV.

### Remplacer les templates par des versions personnalisées (DCG)

Le mandat 13757 personnalisé contient probablement déjà votre raison sociale comme mandataire. Pour utiliser cette version :

1. Convertir votre PDF personnalisé en JPG haute définition (1240×1755 px recommandé) :
   - En ligne : https://pdf2jpg.net
   - Avec Acrobat : Fichier → Exporter → Image → JPEG (qualité élevée)
2. Renommer le fichier en `cerfa_13757.jpg`
3. Le placer dans le dossier `templates/` (écraser l'existant).
4. Recharger l'extension.

### Modifier la société mandataire affichée

Éditer `config.json` :

```json
{
  "mandataire": {
    "raison_sociale": "DREUX CARTE GRISE",
    "siret": "12345678901234",
    "fait_a_default": "Dreux"
  }
}
```

---

## Désinstallation

`edge://extensions/` → cliquer **« Supprimer »** sur la carte de l'extension.

Aucun fichier résiduel hors du dossier de l'extension lui-même.

---

## Dépannage

| Problème | Solution |
|----------|----------|
| Barre orange absente sur l'écran récap | Vérifier que l'URL contient bien `ivo_cht_toVal`. Recharger la page. |
| « Pop-up bloqué » sur Edge | Cliquer sur l'icône bloqueur dans la barre d'adresse → Toujours autoriser pour ce site |
| Texte mal aligné sur le PDF | Le `coords.json` ne correspond pas au template utilisé. Voir « Personnalisation ». |
| Extension désactivée au redémarrage | Edge désactive parfois les extensions « non empaquetées ». Solution : passer par GPO ou Edge Add-ons Store. |
| Données absentes sur le PDF | Ouvrir F12 → Console, regarder `[SIV→CERFA] Payload extrait` pour voir ce qui a été lu de l'écran. |

---

## Confidentialité

Aucune donnée ne quitte le navigateur. La génération des CERFA se fait intégralement en local via la bibliothèque pdf-lib. Aucun appel réseau externe n'est effectué pendant la génération.

L'extension n'a accès qu'aux pages `https://pro-siv.interieur.gouv.fr/*` (déclaré dans le manifeste).

---

*Dreux Carte Grise — Mai 2026*
