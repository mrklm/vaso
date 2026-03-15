
# Aide – Vaso

## Présentation

Vaso est un générateur de vases paramétriques pour l’impression 3D.

L’application permet :
- de créer des vases polygonaux
- de générer des formes aléatoires
- de visualiser un aperçu 2D et 3D
- d’exporter un modèle STL

Les fichiers générés peuvent être ouverts dans Cura, PrusaSlicer ou tout autre slicer.

---

## Organisation de l’interface

La fenêtre principale est composée de :

- Paramètres généraux
- Profils du vase
- Aperçu 3D
- Silhouette
- Vue du haut

---

## Paramètres généraux

### Hauteur
Hauteur totale du vase.

### Épaisseur coque
Épaisseur de la paroi latérale.

### Épaisseur fond
Épaisseur du fond.

### Résolution circulaire
Nombre d’échantillons autour du vase.

### Résolution verticale
Nombre d’échantillons sur la hauteur.

### Nombre de profils (2‑10)
Nombre de sections qui définissent la silhouette.

- 2 profils : forme très simple
- plus de profils : formes plus complexes

### Seed
Permet de reproduire exactement une génération aléatoire.

### Style aléatoire
Famille de formes utilisée pour la génération.

### Forcer la complexité
Si activé, le niveau de complexité est imposé.

### Complexité
- Sobre
- Moyen
- Complexe

### Forcer la texture
Si activé, la texture choisie dans l’interface est imposée.

### Texture
Motif appliqué sur la surface du vase.

### Zoom texture
Échelle du motif.

---

## Profils du vase

Chaque profil définit :

- hauteur (%)
- diamètre
- nombre de côtés
- rotation

Règles importantes :

- le premier profil doit être à **0 %**
- le dernier profil doit être à **100 %**
- les hauteurs doivent être croissantes

---

## Aperçu 3D

L’aperçu permet de visualiser le vase avant export.

Le calcul peut être lent selon :

- résolution circulaire
- résolution verticale
- complexité de la texture
- nombre de profils

---

## Boutons

### Aperçu
Met à jour les aperçus.

### Aléatoire
Génère un nouveau vase.

### Générer STL
Exporte le modèle.

---

# Section technique code

## Architecture

Le projet repose sur quatre fichiers principaux :

app.py  
Interface utilisateur et logique principale

generator.py  
Génération géométrique et maillage

model.py  
Structures de données (profils et paramètres)

exporter.py  
Export STL

## Pipeline de génération

1. Lecture des paramètres UI
2. Construction de VaseParameters
3. Génération des profils
4. Construction du maillage
5. Aperçu 2D / 3D
6. Export STL

## Aperçu 3D

L’aperçu utilise :

- matplotlib
- Poly3DCollection
- un maillage simplifié pour accélérer l’affichage

## Génération aléatoire

La génération dépend :

- du style choisi
- de la complexité
- de la seed
- du volume imprimante

Le nombre de profils peut varier de **2 à 10**.

## Notes techniques

- L’aperçu est volontairement moins détaillé que le STL.
- Les callbacks Tkinter doivent être définis avant utilisation.
- La validation impose toujours :
  - premier profil = 0%
  - dernier profil = 100%
