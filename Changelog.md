# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format s'inspire de **Keep a Changelog**  
https://keepachangelog.com/fr/1.0.0/



## [0.1.5] — 2026-03-14

### Modifié

 - Polygone du milieu décalable


## [0.1.4] — 2026-03-14

### Modifié

 - Combobox Thème déplacée dans option
 - plus de thème aleatoire, mainteant garde en memoire deriner thème 


## [0.1.3] — 2026-03-14

### Modifié

 - Découpage du programme en onglet: général/options/aide
 - Suppression du titre et N° de version dans le fenetre programme

## [0.1.2] — 2026-03-14

### Ajouté

 - Programme versionné, version affiché dans le titre
 - Exports des fichiers STL dans un répértoire et numerotés

## [0.1.0] — 2026-03-13

### Ajouté
- Création du projet **Vaso**, générateur procédural de vases polygonaux.
- Génération de maillages 3D exportables en **STL** pour impression 3D.
- Interface graphique **Python / Tkinter**.
- Aperçu 2D intégré avec **Matplotlib** :
  - silhouette du vase
  - vue du haut du contour.
- Paramètres de génération :
  - hauteur du vase
  - épaisseur de coque
  - épaisseur du fond
  - résolution radiale et verticale
  - diamètre bas / milieu / haut
  - nombre de côtés des profils
  - rotation des profils.
- Système **Seed** permettant de reproduire exactement un vase généré.
- Bouton **Aléatoire** pour générer automatiquement un nouveau vase.
- Export STL avec sélection du chemin de sortie.
- Chemin par défaut de l’export sur le **Bureau**, compatible :
  - Windows
  - macOS
  - Linux.
- Icône de l'application **Vaso**.
- Aperçu du maillage compatible **Cura**.

### Amélioré
- Correction du maillage de la base du vase pour obtenir un objet **étanche (watertight)**.
- Fermeture correcte :
  - du dessous du vase
  - de la lèvre supérieure
  - du dessus du fond intérieur.
- Amélioration de la stabilité du générateur de maillage.

### Interface
- Ajout d’un **système de thèmes graphiques**.
- Sélection du thème via une **combobox** dans l’interface.
- Thème **aléatoire à chaque ouverture du programme**.
- Intégration de plusieurs styles :
  - sombres
  - clairs
  - thèmes “Pouêt-Pouêt”.

### Technique
- Architecture du projet séparée en modules :
  - `app.py` — interface graphique
  - `generator.py` — génération du maillage
  - `model.py` — structures de données
  - `exporter.py` — export STL
- Gestion des dépendances via `requirements.txt`.
- Gestion de l’environnement Python avec **venv**.

### Dépôt Git
- Initialisation du dépôt Git.
- Publication du projet sur GitHub :
  
  https://github.com/mrklm/vaso

- Ajout d’un `.gitignore` adapté aux projets Python.
- Exclusion des fichiers générés :
  - `.stl`
  - `.gcode`.

