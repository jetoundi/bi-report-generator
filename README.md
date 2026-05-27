# 📊 BI Report Generator

> Script Python qui transforme automatiquement n'importe quel fichier CSV en rapport BI HTML complet et autonome.

**Projet académique** — Master Humanités Numériques · UPHF 2025–2026 · Jeanne Etoundi Ntsama

---

## ✨ Fonctionnalités

- **Détection automatique** des colonnes numériques, dates et catégories
- **4 visualisations** générées automatiquement : bar chart, donut, courbe temporelle, Top/Bottom
- **KPIs calculés** : totaux, moyennes, min, max
- **Qualité des données** : valeurs manquantes, doublons
- **Export HTML autonome** : tout embarqué en base64, aucune dépendance externe
- **CLI flexible** : un seul fichier CSV suffit

## 🚀 Utilisation

```bash
# Installation
pip install -r requirements.txt

# Usage minimal
python generate_report.py data/ventes_demo.csv

# Usage avancé
python generate_report.py data/ventes_demo.csv --output output/rapport_ventes.html --title "Rapport Ventes 2024"
```

## 📁 Structure

```
bi-report-generator/
├── generate_report.py          # Script principal
├── requirements.txt            # Dépendances
├── README_bi_report_generator.md
├── data/
│   └── ventes_demo.csv         # Dataset de démonstration (30 lignes)
└── output/
    └── rapport_ventes.html     # Rapport HTML généré (démo)
```

## 🛠️ Technologies

| Outil | Usage |
|-------|-------|
| `pandas` | Chargement, nettoyage, agrégations |
| `matplotlib` | 4 graphiques embarqués en base64 |
| `argparse` | Interface ligne de commande (CLI) |
| `jinja2` | Templating HTML |

## 💡 Contexte

Projet inspiré de l'expérience **Data Analyst bénévole aux Petits Riens** (Bruxelles, 2022–2023), où la génération manuelle de rapports représentait un coût temps considérable. Ce script automatise entièrement ce processus.

---
*Master Humanités Numériques · UPHF Valenciennes · 2025–2026*
