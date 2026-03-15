# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format s'inspire de **Keep a Changelog**  
https://keepachangelog.com/fr/1.0.0/



## [0.3.0] - 2026-03-15

### Ajouté

 - Parametres d'aléatoire 


## [0.2.15] — 2026-03-15

### Modifié

 - Indications "style de vase" reduites


## [0.2.14] — 2026-03-15

### Modifié

 - Indications "style de vase" reduites


## [0.2.13] — 2026-03-15

### Modifié

 - Indications "style de vase" reduites


## [0.2.12] — 2026-03-15

### Modifié

 - L'aleatoire genere bien entre 3 et 10 polygones et indique X pour les polygones non générés 


## [0.2.11] — 2026-03-15

### Modifié

 - fentres de droite remises l'une au dessus de l'autre
 - Boutons centrés


## [0.2.10] — 2026-03-15

### Modifié

 - Parametres généraux et forme du vase mainteant dans une fenetre divisée en deux onglets


## [0.2.9] — 2026-03-15

### Modifié

 - Onglet options remanié


## [0.2.8] — 2026-03-15

### Ajouté

 - Profils d'imprimantes modifiables en combobox


## [0.2.7] — 2026-03-14

### Modifié

 - Mise en valeur du texte dans la section Aide


## [0.2.6] — 2026-03-14

### Ajouté

 - Ajout de la taille max possible pour l'imprimante 3D dans l'ongelt options


## [0.2.5] — 2026-03-14

### Modifié

 - Doublons de titres des fen^tres 2D et 3D supprimés

### Ajouté

 - Centrage des boutons -Aperçu- / -aléatoire- / -Générer .STL-


## [0.2.4] — 2026-03-14

### Ajouté

 - Fader pour regler le shading dans le rendu 3D
 - Traduction du réglage Shading par Ombrage


## [0.2.3] — 2026-03-14

### Ajouté

 - Effet "Shading" de lumiere pour donner une profondeur au rendu 3D

## [0.2.2] — 2026-03-14

### Modifié

 - Simplification des rendu 2D et 3D
 - Changement du placement des fenêtres

## [0.2.1] — 2026-03-14

### Modifié

 - Rendu 3D sur la fenetre principale, au milieu, 2D en dessous

## [0.2.0] — 2026-03-14

### Ajouté

 - Introduction du rendu 3D

## [0.1.10] — 2026-03-14

### Modifié

 - Modification de la présentation de l'affichage du N° de version dans la barre de titre


## [0.1.9] — 2026-03-14

### Modifié

 - Affichage du N° de version dans la barre de titre


## [0.1.8] — 2026-03-14

### Modifié

 - Plus de popup de confirmation de génération de .STL
 - Vue 2D améliorée: matplotlib ferme bien le polygone "vue de dessus"

## [0.1.7] — 2026-03-14

### Modifié

 - Le Décalage du polygone centrale introduit dans la v0.1.5 etait par erreur
   horizontale, il est maintenant verticale.


## [0.1.6] — 2026-03-14

### Ajouté

 - Nombre de polygones possible: non plus 3 mais entre 3 et 10


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

