# Aide – Vaso

## Présentation

**Vaso** est un générateur de vases polygonaux paramétriques permettant de créer rapidement des formes originales destinées à l’impression 3D.

Le programme permet :

* de définir la géométrie d’un vase
* de visualiser un aperçu 2D et 3D
* de générer des formes aléatoires
* d’exporter le modèle en **STL**

Les modèles générés peuvent ensuite être ouverts dans un slicer (Cura, PrusaSlicer, etc.) pour l’impression.

---

# Onglet Général

L’onglet **Général** est la zone principale de travail.

La fenêtre est organisée en trois zones :

### Gauche

* **Paramètres généraux**
* **Forme du vase**

### Centre

* **Aperçu 3D**

### Droite

* **Silhouette (vue de profil)**
* **Vue du haut**

---

# Paramètres généraux

Permet de définir les caractéristiques globales du vase :

* **Hauteur (mm)**
* **Épaisseur des parois (mm)**
* **Épaisseur du fond (mm)**
* **Résolution radiale** (qualité circulaire)
* **Résolution verticale** (qualité en hauteur)
* **Nombre de profils**

Une résolution plus élevée produit un STL plus détaillé mais aussi plus lourd.

---

# Forme du vase

Le vase est défini par trois profils :

* **Bas**
* **Milieu**
* **Haut**

Pour chaque profil on peut définir :

* diamètre
* nombre de côtés du polygone
* rotation

Le profil central peut être légèrement déplacé verticalement pour créer des formes plus organiques.

---

# Aperçu 3D

La zone centrale affiche le modèle en **3D interactif**.

Fonctionnalités :

* rotation avec la souris
* zoom avec la molette
* rendu ombré

### Ombrage

Un curseur **Ombrage** permet d’ajuster l’intensité de l’éclairage du modèle.

* faible valeur → rendu plus plat
* valeur élevée → relief plus marqué

Ce réglage n’affecte **que l’aperçu**, pas le STL exporté.

---

# Aperçus 2D

Deux vues techniques sont affichées :

### Silhouette

Vue de profil du vase.

### Vue du haut

Vue du contour supérieur du vase.

Ces vues permettent de vérifier rapidement les proportions.

---

# Boutons principaux

En bas de la fenêtre :

### Aperçu

Met à jour les aperçus 2D et 3D.

### Aléatoire

Génère une nouvelle forme de vase.

La génération respecte les limites du volume d’impression définies dans **Options**.

### Générer STL

Crée un fichier STL dans le dossier d’export.

---

# Seed

La **seed** permet de reproduire exactement une génération aléatoire.

Exemple :

1. générer un vase aléatoire
2. noter la seed
3. réutiliser cette seed pour retrouver exactement la même forme.

---

# Onglet Options

L’onglet **Options** contient les paramètres globaux du programme.

---

## Thème

Permet de changer l’apparence graphique de l’application.

Le thème est mémorisé entre les sessions.

---

## Volume imprimante

Définit le volume maximal de l’imprimante :

* **Largeur max**
* **Profondeur max**
* **Hauteur max**

Ces valeurs servent à **contraindre la génération aléatoire** afin que les vases restent imprimables.

Les dimensions saisies n’empêchent pas de définir manuellement un vase plus grand, mais elles limitent la génération automatique.

---

## Export STL

Permet de choisir le dossier d’export des fichiers STL.

Par défaut, les fichiers sont exportés dans un dossier daté sur le Bureau.

---

# Export STL

Chaque export crée un fichier nommé automatiquement :

```
vaso_export_0.stl
vaso_export_1.stl
vaso_export_2.stl
```

Les fichiers sont incrémentés pour éviter d’écraser les précédents.

---

# Conseils d’impression

Avant impression :

1. ouvrir le STL dans un slicer
2. vérifier l’échelle
3. vérifier l’épaisseur des parois
4. vérifier l’absence d’erreurs de maillage

Pour un vase en **mode vase (spiralize)** dans Cura :

* épaisseur de paroi ≥ largeur de buse
* fond suffisant (≥ 2 mm recommandé)

---

# Remarques

Les formes générées peuvent produire des géométries très variées.
Il est conseillé de vérifier chaque modèle dans un slicer avant impression.

Vaso est conçu pour **explorer rapidement des formes paramétriques et génératives**.
