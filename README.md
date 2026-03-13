# Vaso

Vaso est un générateur de vases polygonaux en Python.

Le projet permet de créer des vases à partir de plusieurs profils squelettes polygonaux, interpolés verticalement, puis exportés en STL pour impression 3D.

## Fonctionnalités prévues

- définition de 3 à 10 profils squelettes
- réglage du diamètre, du nombre de côtés et de la rotation de chaque profil
- interpolation entre profils
- génération d'un maillage triangulé
- export STL
- interface graphique Tkinter
- aperçu de la forme générée

## Structure actuelle

- `app.py` : point d'entrée du programme
- `model.py` : structures de données
- `generator.py` : génération géométrique
- `exporter.py` : export STL

## Installation sous Windows

Ouvrir un terminal dans le dossier du projet, puis créer un environnement virtuel :

```powershell
python -m venv .venv