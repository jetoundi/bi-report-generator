#!/usr/bin/env python3
"""
========================================================
BI Report Generator — Jeanne Etoundi Ntsama
========================================================
Génère automatiquement un rapport BI HTML complet
depuis n'importe quel fichier CSV.

Usage:
    python generate_report.py data.csv
    python generate_report.py data.csv --output mon_rapport.html
    python generate_report.py data.csv --title "Rapport Ventes 2024"

Dépendances:
    pip install -r requirements.txt
========================================================
"""

import argparse
import base64
import io
import os
import sys
from datetime import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd

# ──────────────────────────────────────────────
# PALETTE COULEURS
# ──────────────────────────────────────────────
COLORS = ['#4A7C6F', '#C9A84C', '#6B52C8', '#D85A30', '#378ADD',
          '#1D9E75', '#DC6080', '#3DC4B0', '#9B8EE0', '#8B7355']

# ──────────────────────────────────────────────
# 1. CHARGEMENT & DÉTECTION AUTOMATIQUE
# ──────────────────────────────────────────────
def load_and_detect(filepath):
    """Charge le CSV et détecte automatiquement les colonnes."""
    df = pd.read_csv(filepath, sep=None, engine='python', encoding='utf-8-sig')
    df.columns = df.columns.str.strip()

    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    date_cols = [c for c in df.columns if any(k in c.lower() for k in ['date','mois','année','year','month','periode'])]
    cat_cols = df.select_dtypes(include='object').columns.tolist()

    # Tentative de conversion date
    for col in date_cols:
        try:
            df[col] = pd.to_datetime(df[col])
        except Exception:
            pass

    return df, numeric_cols, date_cols, cat_cols

# ──────────────────────────────────────────────
# 2. KPIs
# ──────────────────────────────────────────────
def compute_kpis(df, numeric_cols):
    kpis = {}
    for col in numeric_cols[:4]:
        kpis[col] = {
            'total': df[col].sum(),
            'moyenne': df[col].mean(),
            'min': df[col].min(),
            'max': df[col].max(),
        }
    kpis['_nb_lignes'] = len(df)
    kpis['_nb_colonnes'] = len(df.columns)
    kpis['_valeurs_manquantes'] = int(df.isnull().sum().sum())
    return kpis

# ──────────────────────────────────────────────
# 3. GRAPHIQUES → base64
# ──────────────────────────────────────────────
def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=130, bbox_inches='tight',
                facecolor='#FDFAF3', edgecolor='none')
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return b64

def chart_bar(df, cat_col, num_col):
    agg = df.groupby(cat_col)[num_col].sum().nlargest(10).sort_values()
    fig, ax = plt.subplots(figsize=(7, 4), facecolor='#FDFAF3')
    bars = ax.barh(agg.index, agg.values, color=COLORS[:len(agg)], height=0.6)
    ax.set_facecolor('#FDFAF3')
    ax.set_xlabel(num_col, fontsize=9, color='#5C4A2A')
    ax.set_title(f'Top 10 — {cat_col} par {num_col}', fontsize=11, fontweight='bold', color='#1E1810', pad=10)
    ax.tick_params(colors='#8B7355', labelsize=8)
    ax.spines[['top','right','left']].set_visible(False)
    ax.xaxis.grid(True, alpha=0.25, linestyle='--')
    for bar in bars:
        ax.text(bar.get_width() * 1.01, bar.get_y() + bar.get_height()/2,
                f'{bar.get_width():,.0f}', va='center', fontsize=7.5, color='#5C4A2A')
    fig.tight_layout()
    return fig_to_b64(fig)

def chart_donut(df, cat_col, num_col):
    agg = df.groupby(cat_col)[num_col].sum().nlargest(6)
    fig, ax = plt.subplots(figsize=(6, 4), facecolor='#FDFAF3')
    wedges, texts, autotexts = ax.pie(
        agg.values, labels=None, colors=COLORS[:len(agg)],
        autopct='%1.1f%%', startangle=90,
        wedgeprops=dict(width=0.55, edgecolor='#FDFAF3', linewidth=1.5),
        pctdistance=0.75
    )
    for at in autotexts:
        at.set_fontsize(8)
        at.set_color('#1E1810')
    ax.set_facecolor('#FDFAF3')
    ax.legend(agg.index, loc='center left', bbox_to_anchor=(1, 0.5),
              fontsize=8, frameon=False, labelcolor='#5C4A2A')
    ax.set_title(f'Répartition — {num_col} par {cat_col}', fontsize=11,
                 fontweight='bold', color='#1E1810', pad=10)
    fig.tight_layout()
    return fig_to_b64(fig)

def chart_line(df, date_col, num_col):
    df_sorted = df.dropna(subset=[date_col, num_col]).sort_values(date_col)
    monthly = df_sorted.set_index(date_col)[num_col].resample('ME').sum()
    fig, ax = plt.subplots(figsize=(7, 3.5), facecolor='#FDFAF3')
    ax.plot(monthly.index, monthly.values, color=COLORS[0], linewidth=2,
            marker='o', markersize=4, markerfacecolor='#C9A84C', markeredgewidth=0)
    ax.fill_between(monthly.index, monthly.values, alpha=0.1, color=COLORS[0])
    ax.set_facecolor('#FDFAF3')
    ax.set_title(f'Évolution mensuelle — {num_col}', fontsize=11,
                 fontweight='bold', color='#1E1810', pad=10)
    ax.tick_params(colors='#8B7355', labelsize=8)
    ax.spines[['top','right']].set_visible(False)
    ax.yaxis.grid(True, alpha=0.25, linestyle='--')
    fig.tight_layout()
    return fig_to_b64(fig)

def chart_top_bottom(df, cat_col, num_col):
    agg = df.groupby(cat_col)[num_col].sum()
    top5 = agg.nlargest(5)
    bot5 = agg.nsmallest(5)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.5), facecolor='#FDFAF3')
    ax1.barh(top5.index, top5.values, color='#4A7C6F', height=0.55)
    ax1.set_title('Top 5', fontsize=10, fontweight='bold', color='#1E1810')
    ax1.set_facecolor('#FDFAF3')
    ax1.tick_params(colors='#8B7355', labelsize=7.5)
    ax1.spines[['top','right','left']].set_visible(False)
    ax2.barh(bot5.index, bot5.values, color='#D85A30', height=0.55)
    ax2.set_title('Bottom 5', fontsize=10, fontweight='bold', color='#1E1810')
    ax2.set_facecolor('#FDFAF3')
    ax2.tick_params(colors='#8B7355', labelsize=7.5)
    ax2.spines[['top','right','left']].set_visible(False)
    fig.suptitle(f'Classement — {cat_col} par {num_col}', fontsize=11,
                 fontweight='bold', color='#1E1810', y=1.02)
    fig.tight_layout()
    return fig_to_b64(fig)

# ──────────────────────────────────────────────
# 4. TEMPLATE HTML
# ──────────────────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#FDFAF3;color:#1E1810;font-family:'Segoe UI',DM Sans,sans-serif;padding:2rem}}
header{{background:#1E1810;color:#FAF7F0;padding:2rem 2.5rem;border-radius:8px;margin-bottom:2rem;display:flex;justify-content:space-between;align-items:flex-start}}
header h1{{font-size:1.6rem;font-weight:700;margin-bottom:.3rem}}
header p{{font-size:.8rem;opacity:.5}}
.badge{{background:#C9A84C;color:#1E1810;font-size:.68rem;font-weight:600;padding:.2rem .75rem;border-radius:20px;letter-spacing:.08em;text-transform:uppercase}}
.kpi-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;margin-bottom:2rem}}
.kpi{{background:white;border:1px solid #E4DDD0;border-radius:8px;padding:1.25rem;text-align:center}}
.kpi-num{{font-size:2rem;font-weight:700;color:#4A7C6F;margin-bottom:.25rem}}
.kpi-lbl{{font-size:.68rem;text-transform:uppercase;letter-spacing:.1em;color:#8B7355}}
.section-title{{font-size:.7rem;text-transform:uppercase;letter-spacing:.15em;color:#8B7355;margin-bottom:1rem;display:flex;align-items:center;gap:.75rem}}
.section-title::after{{content:'';flex:1;height:1px;background:#E4DDD0}}
.charts-grid{{display:grid;grid-template-columns:1fr 1fr;gap:1.25rem;margin-bottom:2rem}}
.chart-card{{background:white;border:1px solid #E4DDD0;border-radius:8px;padding:1.25rem}}
.chart-card.full{{grid-column:1/-1}}
.chart-card img{{width:100%;border-radius:4px}}
.table-wrap{{background:white;border:1px solid #E4DDD0;border-radius:8px;overflow:hidden;margin-bottom:2rem}}
table{{width:100%;border-collapse:collapse;font-size:.82rem}}
th{{background:#1E1810;color:#FAF7F0;padding:.75rem 1rem;text-align:left;font-size:.7rem;letter-spacing:.08em;text-transform:uppercase}}
td{{padding:.65rem 1rem;border-bottom:1px solid #F0EDE7;color:#4A3D2A}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:#FDFAF3}}
.qa-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:2rem}}
.qa-card{{background:white;border:1px solid #E4DDD0;border-radius:8px;padding:1rem}}
.qa-title{{font-size:.68rem;text-transform:uppercase;letter-spacing:.1em;color:#8B7355;margin-bottom:.5rem}}
.qa-val{{font-size:1.2rem;font-weight:700;color:#4A7C6F}}
footer{{text-align:center;padding:1.5rem;font-size:.72rem;color:#8B7355;border-top:1px solid #E4DDD0;margin-top:2rem}}
</style>
</head>
<body>

<header>
  <div>
    <h1>{title}</h1>
    <p>Généré le {date} · Source : {source} · {nb_lignes} lignes · {nb_cols} colonnes</p>
  </div>
  <span class="badge">BI Report</span>
</header>

<div class="section-title">Indicateurs clés</div>
<div class="kpi-row">{kpi_html}</div>

<div class="section-title">Visualisations</div>
<div class="charts-grid">
  <div class="chart-card"><img src="data:image/png;base64,{chart_bar}" alt="Bar chart"></div>
  <div class="chart-card"><img src="data:image/png;base64,{chart_donut}" alt="Donut chart"></div>
  {chart_line_html}
  <div class="chart-card full"><img src="data:image/png;base64,{chart_topbot}" alt="Top/Bottom"></div>
</div>

<div class="section-title">Détail des données — aperçu</div>
<div class="table-wrap">{table_html}</div>

<div class="section-title">Qualité des données</div>
<div class="qa-grid">
  <div class="qa-card"><div class="qa-title">Total lignes</div><div class="qa-val">{nb_lignes}</div></div>
  <div class="qa-card"><div class="qa-title">Colonnes</div><div class="qa-val">{nb_cols}</div></div>
  <div class="qa-card"><div class="qa-title">Valeurs manquantes</div><div class="qa-val">{val_manq}</div></div>
</div>

<footer>
  Rapport généré automatiquement par <strong>BI Report Generator</strong> ·
  Projet académique · Jeanne Etoundi Ntsama · Master Humanités Numériques, UPHF 2025–2026
</footer>

</body>
</html>"""

# ──────────────────────────────────────────────
# 5. GÉNÉRATION RAPPORT
# ──────────────────────────────────────────────
def generate(filepath, output_path=None, title=None):
    print(f"📂 Chargement : {filepath}")
    df, numeric_cols, date_cols, cat_cols = load_and_detect(filepath)
    print(f"✅ {len(df)} lignes · {len(df.columns)} colonnes détectées")
    print(f"   Numériques : {numeric_cols}")
    print(f"   Dates      : {date_cols}")
    print(f"   Catégories : {cat_cols}")

    if not numeric_cols:
        print("❌ Aucune colonne numérique détectée. Vérifiez votre CSV.")
        sys.exit(1)

    kpis = compute_kpis(df, numeric_cols)
    num1 = numeric_cols[0]
    cat1 = cat_cols[0] if cat_cols else df.columns[0]

    print("📊 Génération des graphiques...")
    b64_bar    = chart_bar(df, cat1, num1)
    b64_donut  = chart_donut(df, cat1, num1)
    b64_topbot = chart_top_bottom(df, cat1, num1)

    b64_line = None
    chart_line_html = ''
    if date_cols:
        try:
            b64_line = chart_line(df, date_cols[0], num1)
            chart_line_html = f'<div class="chart-card full"><img src="data:image/png;base64,{b64_line}" alt="Courbe temporelle"></div>'
        except Exception as e:
            print(f"⚠️  Graphique temporel ignoré : {e}")

    # KPI HTML
    kpi_items = []
    for col in numeric_cols[:4]:
        v = kpis[col]
        kpi_items.append(f'<div class="kpi"><div class="kpi-num">{v["total"]:,.0f}</div><div class="kpi-lbl">Total {col}</div></div>')
    kpi_items.append(f'<div class="kpi"><div class="kpi-num">{kpis["_nb_lignes"]:,}</div><div class="kpi-lbl">Lignes</div></div>')
    kpi_html = ''.join(kpi_items)

    # Table HTML (top 20)
    table_html = df.head(20).to_html(index=False, border=0, classes='')

    # Titre
    if not title:
        title = f'Rapport BI — {os.path.basename(filepath)}'

    # Output
    if not output_path:
        base = os.path.splitext(filepath)[0]
        output_path = f'{base}_rapport.html'

    html = HTML_TEMPLATE.format(
        title=title,
        date=datetime.now().strftime('%d/%m/%Y à %H:%M'),
        source=os.path.basename(filepath),
        nb_lignes=f'{kpis["_nb_lignes"]:,}',
        nb_cols=kpis['_nb_colonnes'],
        val_manq=kpis['_valeurs_manquantes'],
        kpi_html=kpi_html,
        chart_bar=b64_bar,
        chart_donut=b64_donut,
        chart_line_html=chart_line_html,
        chart_topbot=b64_topbot,
        table_html=table_html,
    )

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Rapport généré : {output_path}")
    return output_path


# ──────────────────────────────────────────────
# 6. CLI
# ──────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='BI Report Generator — Génère un rapport HTML depuis un CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python generate_report.py data.csv
  python generate_report.py ventes.csv --output rapport_ventes.html
  python generate_report.py data.csv --title "Rapport Mensuel Juin 2025"
        """
    )
    parser.add_argument('input', help='Fichier CSV source')
    parser.add_argument('--output', '-o', help='Fichier HTML de sortie (optionnel)')
    parser.add_argument('--title', '-t', help='Titre du rapport (optionnel)')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ Fichier introuvable : {args.input}")
        sys.exit(1)

    generate(args.input, args.output, args.title)
