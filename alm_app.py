"""
ALM Dashboard — Analyse des risques de taux
CNP Assurances vs Generali Vie | 2021-2024
Sources : SFCR publics, QRT S.02.01.02 + S.23.01
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────
# CONFIG PAGE
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="ALM Dashboard — Risque de Taux",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# PALETTE
# ─────────────────────────────────────────────
CNP_COLOR   = "#1f6fa8"
GEN_COLOR   = "#e05a3a"
GOLD        = "#f0a500"
LIGHT_BG    = "#f7f9fc"

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
  .main { background:#f7f9fc; }
  .metric-card {
    background:#ffffff; border-radius:10px;
    padding:18px 22px; margin:6px 0;
    border-left:4px solid #1f6fa8;
    box-shadow:0 2px 6px rgba(0,0,0,.07);
  }
  .metric-card.gen { border-left-color:#e05a3a; }
  .metric-label { font-size:.78rem; color:#888; font-weight:600; text-transform:uppercase; letter-spacing:.05em; }
  .metric-value { font-size:1.6rem; font-weight:700; color:#1a1a2e; }
  .metric-delta { font-size:.82rem; margin-top:2px; }
  .delta-pos { color:#2e9e5b; } .delta-neg { color:#e05a3a; }
  .section-title {
    font-size:1.05rem; font-weight:700; color:#1a1a2e;
    border-bottom:2px solid #1f6fa8; padding-bottom:4px;
    margin:18px 0 12px;
  }
  .insight-box {
    background:#eef4fb; border-radius:8px;
    padding:14px 18px; margin:10px 0;
    border-left:4px solid #1f6fa8; font-size:.88rem;
  }
  .insight-box.warning { background:#fff4e5; border-left-color:#f0a500; }
  .insight-box.success { background:#e8f5ee; border-left-color:#2e9e5b; }
  .stTabs [data-baseweb="tab"] { font-size:.92rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DONNÉES
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    # ── CNP ──
    data_cnp = {
        'Annee' : [2021, 2022, 2023, 2024],
        'R0070' : [362649889, 298871501, 301675219, 295213931],
        'R0130' : [233851887, 190987269, 199276020, 195248666],
        'R0140' : [133929562, 100387556,  99683090,  99284428],
        'R0150' : [ 81945553,  70046215,  74861795,  70443647],
        'R0180' : [ 90083868,  72638268,  71333465,  71324216],
        'R0220' : [ 84966816,  84648804,  98493766, 103478396],
        'R0100' : [ 32696256,  24405705,  22026592,  20719379],
        'R0500' : [487180872, 408263376, 424009943, 424421533],
        'SCR_pct': [217, 230, 253, 237],
        'SCR_mde': [39.1, 36.4, 15.1, 16.2],
        'BE'     : [395900000, 319600000, 334100000, 339900000],
    }
    df_cnp = pd.DataFrame(data_cnp)

    # ── Generali ──
    data_gen = {
        'Annee' : [2021, 2022, 2023, 2024],
        'R0070' : [86619227, 54516947, 52243515, 52469705],
        'R0130' : [64334300, 35234589, 32229827, 34015157],
        'R0140' : [39035248, 19004310, 15762400, 15799438],
        'R0150' : [22291755, 14325301, 14082392, 15226389],
        'R0180' : [ 9154192,  7915487,  9352327,  8265712],
        'R0220' : [29923248, 25744566, 29734562, 33152422],
        'R0100' : [ 2905707,  2196992,  2154812,  2460052],
        'R0500' : [126661146, 89732234, 90382476, 94995155],
        'SCR_pct': [186.69, 156.77, 150.50, 159.65],
        'SCR_mde': [4.751, 4.010, 3.908, 3.724],
        'BE'     : [80466855, 49905744, 49070260, 50709811],
    }
    df_gen = pd.DataFrame(data_gen)

    # Conversion → Md€
    cols = ['R0070','R0130','R0140','R0150','R0180','R0220','R0100','R0500','BE']
    for df in [df_cnp, df_gen]:
        for c in cols:
            df[c] = df[c] / 1_000_000

    # Ratios
    def add_ratios(df):
        df['expo_directe'] = df['R0130'] / df['R0070'] * 100
        df['expo_totale']  = (df['R0130'] + df['R0180']) / df['R0070'] * 100
        df['pct_gov']      = df['R0140'] / df['R0070'] * 100
        df['pct_UC']       = df['R0220'] / df['R0500'] * 100
        return df

    df_cnp = add_ratios(df_cnp)
    df_gen = add_ratios(df_gen)
    return df_cnp, df_gen

df_cnp, df_gen = load_data()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Warning.svg/32px-Warning.svg.png", width=20)
    st.markdown("### ⚙️ Paramètres ALM")
    D_actif  = st.slider("Duration modifiée actif (ans)", 5.0, 12.0, 8.0, 0.5)
    D_passif = st.slider("Duration modifiée passif (ans)", 10.0, 20.0, 15.0, 0.5)
    choc_bps = st.selectbox("Choc de taux (bps)", [25, 50, 75, 100, 150, 200], index=3)

    st.markdown("---")
    st.markdown("""
    **Sources**
    - QRT S.02.01.02 — Bilan S2
    - QRT S.23.01 — Ratio SCR
    - SFCR CNP Assurances 2021-2024
    - SFCR Generali Vie 2021-2024

    **Hypothèses**
    - Portefeuille 100% obligations (R0130)
    - BE hors UC (R0670 + R0630)
    - Convexité ignorée (erreur < 1% pour chocs ≤ 100bps)
    """)
    st.markdown("---")
    st.caption("M1 Actuariat — ISUP Sorbonne Université")

choc = choc_bps / 10000  # en décimal

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("📊 Analyse ALM — Risque de Taux")
st.markdown(
    "**CNP Assurances vs Generali Vie** | 2021-2024 | "
    "Sources : SFCR publics — QRT S.02.01 & S.23.01"
)
st.markdown("---")

# ─────────────────────────────────────────────
# KPI ROW
# ─────────────────────────────────────────────
col1, col2, col3, col4, col5, col6 = st.columns(6)

def kpi(col, label, value, delta=None, gen=False):
    card_cls = "metric-card gen" if gen else "metric-card"
    delta_html = ""
    if delta is not None:
        cls = "delta-pos" if delta >= 0 else "delta-neg"
        sign = "▲" if delta >= 0 else "▼"
        delta_html = f'<div class="metric-delta {cls}">{sign} {abs(delta):.1f}</div>'
    col.markdown(f"""
    <div class="{card_cls}">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}</div>
      {delta_html}
    </div>""", unsafe_allow_html=True)

# CNP 2024 actuals
kpi(col1, "CNP — Oblig. 2024", f"{df_cnp.iloc[-1]['R0130']:.0f} Md€")
kpi(col2, "CNP — Ratio SCR 2024", f"{df_cnp.iloc[-1]['SCR_pct']:.0f}%",
    df_cnp.iloc[-1]['SCR_pct'] - df_cnp.iloc[0]['SCR_pct'])
kpi(col3, "CNP — Expo. taux totale", f"{df_cnp.iloc[-1]['expo_totale']:.1f}%")
kpi(col4, "Generali — Oblig. 2024", f"{df_gen.iloc[-1]['R0130']:.1f} Md€", gen=True)
kpi(col5, "Generali — Ratio SCR 2024", f"{df_gen.iloc[-1]['SCR_pct']:.0f}%",
    df_gen.iloc[-1]['SCR_pct'] - df_gen.iloc[0]['SCR_pct'], gen=True)
kpi(col6, "Generali — Part UC 2024", f"{df_gen.iloc[-1]['pct_UC']:.1f}%", gen=True)

st.markdown("---")

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tabs = st.tabs([
    "📁 Données brutes",
    "📐 Ratios d'exposition",
    "⚡ Stress tests",
    "🏦 Immunisation & Duration Gap",
    "📈 Comparatif SCR",
])

# ══════════════════════════════════════════════
# TAB 1 — DONNÉES BRUTES
# ══════════════════════════════════════════════
with tabs[0]:
    st.markdown('<div class="section-title">Bilan Solvabilité II — QRT S.02.01 (en Md€)</div>',
                unsafe_allow_html=True)

    assureur = st.radio("Sélectionner l'assureur", ["CNP Assurances", "Generali Vie"],
                        horizontal=True)
    df_sel = df_cnp if assureur == "CNP Assurances" else df_gen
    color  = CNP_COLOR if assureur == "CNP Assurances" else GEN_COLOR

    cols_display = {
        'Annee':'Année','R0070':'Inv. hors UC','R0130':'Obligations',
        'R0140':'Gov. Bonds','R0150':'Corp. Bonds','R0180':'OPC/Fonds',
        'R0220':'UC','R0100':'Actions','R0500':'Total actifs',
        'SCR_pct':'SCR (%)','SCR_mde':'SCR (Md€)'
    }
    st.dataframe(
        df_sel[[c for c in cols_display if c in df_sel.columns]]
        .rename(columns=cols_display)
        .set_index('Année')
        .round(1),
        use_container_width=True
    )

    st.markdown('<div class="section-title">Composition du portefeuille (% hors UC)</div>',
                unsafe_allow_html=True)

    annees_str = [str(a) for a in df_sel['Annee']]
    fig_stack = go.Figure()
    fig_stack.add_trace(go.Bar(name='Gov. Bonds', x=annees_str,
        y=df_sel['pct_gov'], marker_color='#1f6fa8'))
    fig_stack.add_trace(go.Bar(name='Corp. Bonds', x=annees_str,
        y=df_sel['R0150']/df_sel['R0070']*100, marker_color='#4db8ff'))
    fig_stack.add_trace(go.Bar(name='OPC indirect', x=annees_str,
        y=df_sel['R0180']/df_sel['R0070']*100, marker_color='#f0a500'))
    fig_stack.add_trace(go.Bar(name='Actions', x=annees_str,
        y=df_sel['R0100']/df_sel['R0070']*100, marker_color='#e05a3a'))
    fig_stack.update_layout(
        barmode='stack', height=380,
        title=f"{assureur} — Composition exposition taux 2021-2024",
        yaxis_title="% portefeuille hors UC",
        legend=dict(orientation='h', y=1.1, x=.5, xanchor='center'),
        plot_bgcolor='white', paper_bgcolor='white'
    )
    st.plotly_chart(fig_stack, use_container_width=True)

    st.markdown("""
    <div class="insight-box">
    <b>Lecture des lignes QRT :</b> R0070 = investissements hors UC (dénominateur de tous les ratios) ;
    R0130 = obligations directes (Government + Corporate + structurés) ;
    R0180 = OPC/fonds (ajoutés car contiennent des obligations en sous-jacent) ;
    R0220 = actifs en UC (exclus car risque porté par l'assuré sous S2).
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TAB 2 — RATIOS
# ══════════════════════════════════════════════
with tabs[1]:
    st.markdown('<div class="section-title">Quatre indicateurs d\'exposition — QRT S.02.01</div>',
                unsafe_allow_html=True)

    annees_str_cnp = [str(a) for a in df_cnp['Annee']]
    annees_str_gen = [str(a) for a in df_gen['Annee']]

    fig_ratios = make_subplots(rows=2, cols=2,
        subplot_titles=[
            "① Exposition directe (Oblig / Inv. hors UC)",
            "② Exposition totale (Oblig + OPC / Inv. hors UC)",
            "③ Concentration souveraine (Gov. Bonds / Inv. hors UC)",
            "④ Transfert risque UC (UC / Total actifs)",
        ])

    for col_idx, (col_name, title_short) in enumerate([
        ('expo_directe', 'Expo directe'),
        ('expo_totale',  'Expo totale'),
        ('pct_gov',      'Souverain'),
        ('pct_UC',       'Part UC'),
    ]):
        r, c = divmod(col_idx, 2)
        r += 1; c += 1
        fig_ratios.add_trace(go.Scatter(
            name='CNP', x=annees_str_cnp, y=df_cnp[col_name],
            mode='lines+markers+text',
            text=[f"{v:.1f}%" for v in df_cnp[col_name]],
            textposition='top center',
            line=dict(color=CNP_COLOR, width=2),
            marker=dict(size=8),
            showlegend=(col_idx == 0)
        ), row=r, col=c)
        fig_ratios.add_trace(go.Scatter(
            name='Generali', x=annees_str_gen, y=df_gen[col_name],
            mode='lines+markers+text',
            text=[f"{v:.1f}%" for v in df_gen[col_name]],
            textposition='bottom center',
            line=dict(color=GEN_COLOR, width=2),
            marker=dict(size=8),
            showlegend=(col_idx == 0)
        ), row=r, col=c)

    fig_ratios.update_layout(height=560, plot_bgcolor='white', paper_bgcolor='white',
        legend=dict(orientation='h', y=1.04, x=.5, xanchor='center'))
    fig_ratios.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig_ratios, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="insight-box">
        <b>① Expo directe :</b> CNP stable ~64-66% ; Generali passe de 74% → 65%
        (réduction de la poche obligataire directe au profit des UC).
        </div>
        <div class="insight-box">
        <b>② Expo totale :</b> CNP très élevée (~90%) car les OPC restent
        stables ; Generali se réduit de 85% → 81%.
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="insight-box">
        <b>③ Souverain :</b> Les deux assureurs réduisent leur exposition
        souveraine après 2021 (choc de spread sur OAT françaises en 2022).
        </div>
        <div class="insight-box success">
        <b>④ Part UC :</b> Generali monte de 24% → 35% (+11 pts) :
        transfert du risque de marché vers les assurés, réduction du SCR de marché.
        CNP progresse plus modestement : 17% → 24%.
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TAB 3 — STRESS TESTS
# ══════════════════════════════════════════════
with tabs[2]:
    st.markdown(f'<div class="section-title">Simulation — Choc de taux : {choc_bps:+d} bps '
                f'| D_actif = {D_actif} ans | D_passif = {D_passif} ans</div>',
                unsafe_allow_html=True)

    st.markdown("""
    <div class="insight-box warning">
    <b>Formule :</b> ΔP/P ≈ −D_mod × Δr → Perte = −D_mod × Δr × V_portefeuille
    (approximation du 1er ordre ; convexité ignorée car erreur < 1% pour Δr ≤ 100bps)
    </div>
    """, unsafe_allow_html=True)

    chocs_sim = [choc, -choc, choc/2, -choc/2]
    chocs_labels = [f"{int(c*10000):+d}bps" for c in chocs_sim]

    def simulate(df, name, SCR_ref):
        rows = []
        for _, row in df.iterrows():
            annee = int(row['Annee'])
            V_A   = row['R0130']
            V_BE  = row['BE']
            for c, lbl in zip(chocs_sim, chocs_labels):
                dA  = -D_actif  * c * V_A
                dBE = -D_passif * c * V_BE
                dFP = dA - dBE
                rows.append({
                    'Année': annee, 'Choc': lbl,
                    'ΔActif': round(dA, 2),
                    'ΔBE':    round(dBE, 2),
                    'ΔFP net': round(dFP, 2),
                    '% SCR ref': round(abs(dFP) / SCR_ref * 100, 1)
                })
        return pd.DataFrame(rows)

    df_sc_cnp = simulate(df_cnp, 'CNP', df_cnp.iloc[-1]['SCR_mde'])
    df_sc_gen = simulate(df_gen, 'Generali', df_gen.iloc[-1]['SCR_mde'])

    col_sc1, col_sc2 = st.columns(2)

    with col_sc1:
        st.markdown("**CNP Assurances**")
        pivot_cnp = df_sc_cnp.pivot_table(
            values='ΔFP net', index='Choc', columns='Année', aggfunc='first')
        st.dataframe(pivot_cnp.round(1), use_container_width=True)

    with col_sc2:
        st.markdown("**Generali Vie**")
        pivot_gen = df_sc_gen.pivot_table(
            values='ΔFP net', index='Choc', columns='Année', aggfunc='first')
        st.dataframe(pivot_gen.round(1), use_container_width=True)

    # Graphique ΔFP net pour le choc sélectionné
    st.markdown('<div class="section-title">Impact ΔFP net — choc sélectionné par année</div>',
                unsafe_allow_html=True)

    choc_pos_lbl = f"{choc_bps:+d}bps"
    choc_neg_lbl = f"{-choc_bps:+d}bps"

    fig_stress = go.Figure()
    for lbl, color, df_s in [(choc_pos_lbl, CNP_COLOR, df_sc_cnp),
                              (choc_neg_lbl, '#4db8ff', df_sc_cnp)]:
        sub = df_s[df_s['Choc'] == lbl]
        fig_stress.add_trace(go.Bar(
            name=f"CNP {lbl}", x=[str(a) for a in sub['Année']],
            y=sub['ΔFP net'], marker_color=color,
            text=[f"{v:+.1f}" for v in sub['ΔFP net']], textposition='outside'
        ))
    for lbl, color, df_s in [(choc_pos_lbl, GEN_COLOR, df_sc_gen),
                              (choc_neg_lbl, '#f0a500', df_sc_gen)]:
        sub = df_s[df_s['Choc'] == lbl]
        fig_stress.add_trace(go.Bar(
            name=f"Generali {lbl}", x=[str(a) for a in sub['Année']],
            y=sub['ΔFP net'], marker_color=color,
            text=[f"{v:+.1f}" for v in sub['ΔFP net']], textposition='outside'
        ))

    fig_stress.add_hline(y=0, line_dash='dash', line_color='black', line_width=1)
    fig_stress.update_layout(
        barmode='group', height=420,
        title=f"ΔFP net (Md€) — D_actif={D_actif}a | D_passif={D_passif}a",
        yaxis_title="ΔFP net (Md€)",
        legend=dict(orientation='h', y=1.1, x=.5, xanchor='center'),
        plot_bgcolor='white', paper_bgcolor='white'
    )
    st.plotly_chart(fig_stress, use_container_width=True)

    st.markdown(f"""
    <div class="insight-box success">
    <b>Lecture clé :</b> Pour un choc <b>+{choc_bps}bps</b>, Generali enregistre un <b>ΔFP positif</b>
    (les passifs baissent plus que les actifs car D_passif={D_passif}a > D_actif={D_actif}a).
    CNP présente le même profil mais en valeurs absolues 8-10× plus élevées,
    reflétant la taille du bilan.
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TAB 4 — IMMUNISATION & DURATION GAP
# ══════════════════════════════════════════════
with tabs[3]:
    st.markdown('<div class="section-title">Condition d\'immunisation de Redington (1952)</div>',
                unsafe_allow_html=True)

    st.markdown("""
    <div class="insight-box warning">
    <b>Condition nécessaire :</b> D_actif × V_actif ≥ D_passif × V_BE<br>
    <b>Duration Gap :</b> DG = D_actif − (V_BE / V_actif) × D_passif<br>
    DG < 0 → passifs plus sensibles aux taux → hausse des taux améliore les FP
    </div>
    """, unsafe_allow_html=True)

    def calc_immunisation(df):
        rows = []
        for _, row in df.iterrows():
            V_A  = row['R0130']
            V_BE = row['BE']
            DA_VA  = D_actif  * V_A
            DP_VBE = D_passif * V_BE
            DG = D_actif - (V_BE / V_A) * D_passif
            rows.append({
                'Année'       : int(row['Annee']),
                'D_A × V_A'  : round(DA_VA,  1),
                'D_P × V_BE' : round(DP_VBE, 1),
                'Ratio A/P'  : round(DA_VA / DP_VBE, 2),
                'Duration Gap': round(DG, 2),
                'Immunisé ?'  : '✅' if DA_VA >= DP_VBE else '❌',
            })
        return pd.DataFrame(rows)

    df_imm_cnp = calc_immunisation(df_cnp)
    df_imm_gen = calc_immunisation(df_gen)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**CNP Assurances**")
        st.dataframe(df_imm_cnp.set_index('Année'), use_container_width=True)
    with c2:
        st.markdown("**Generali Vie**")
        st.dataframe(df_imm_gen.set_index('Année'), use_container_width=True)

    # Graphique Duration Gap comparatif
    st.markdown('<div class="section-title">Duration Gap 2021-2024</div>',
                unsafe_allow_html=True)

    fig_dg = go.Figure()
    fig_dg.add_trace(go.Scatter(
        name='CNP', x=[str(a) for a in df_imm_cnp['Année']],
        y=df_imm_cnp['Duration Gap'],
        mode='lines+markers+text',
        text=[f"{v:.1f}" for v in df_imm_cnp['Duration Gap']],
        textposition='top center',
        line=dict(color=CNP_COLOR, width=3), marker=dict(size=9)
    ))
    fig_dg.add_trace(go.Scatter(
        name='Generali', x=[str(a) for a in df_imm_gen['Année']],
        y=df_imm_gen['Duration Gap'],
        mode='lines+markers+text',
        text=[f"{v:.1f}" for v in df_imm_gen['Duration Gap']],
        textposition='bottom center',
        line=dict(color=GEN_COLOR, width=3), marker=dict(size=9)
    ))
    fig_dg.add_hline(y=0, line_dash='dash', line_color='black',
                     annotation_text="Seuil d'immunisation (DG = 0)")
    fig_dg.add_hrect(y0=min(df_imm_cnp['Duration Gap'].min(),
                             df_imm_gen['Duration Gap'].min()) - 1,
                      y1=0, fillcolor='rgba(31,111,168,0.07)', line_width=0,
                      annotation_text="Zone : hausse taux = gain FP",
                      annotation_position="bottom left")
    fig_dg.update_layout(
        height=400,
        title=f"Duration Gap (D_actif={D_actif}a | D_passif={D_passif}a)",
        yaxis_title="Duration Gap (années)",
        legend=dict(orientation='h', y=1.1, x=.5, xanchor='center'),
        plot_bgcolor='white', paper_bgcolor='white'
    )
    st.plotly_chart(fig_dg, use_container_width=True)

    # Waterfall CNP 2024
    st.markdown('<div class="section-title">Décomposition CNP 2024 — Pourquoi non immunisé ?</div>',
                unsafe_allow_html=True)

    row2024 = df_imm_cnp[df_imm_cnp['Année'] == 2024].iloc[0]
    fig_wf = go.Figure(go.Waterfall(
        orientation='v',
        measure=['absolute', 'absolute', 'relative'],
        x=['D_A × V_A\n(actifs)', 'D_P × V_BE\n(passifs)', 'Écart\n(mismatch)'],
        y=[row2024['D_A × V_A'], row2024['D_P × V_BE'],
           row2024['D_A × V_A'] - row2024['D_P × V_BE']],
        text=[f"{row2024['D_A × V_A']:.0f} Md€·an",
              f"{row2024['D_P × V_BE']:.0f} Md€·an",
              f"{row2024['D_A × V_A'] - row2024['D_P × V_BE']:.0f} Md€·an"],
        textposition='outside',
        connector=dict(line=dict(color='#ccc')),
        increasing=dict(marker_color='#2e9e5b'),
        decreasing=dict(marker_color='#e05a3a'),
    ))
    fig_wf.update_layout(
        height=360,
        title="CNP 2024 : D_A × V_A vs D_P × V_BE (Md€·an)",
        yaxis_title="Md€ × années",
        plot_bgcolor='white', paper_bgcolor='white'
    )
    st.plotly_chart(fig_wf, use_container_width=True)

    dg_cnp_2024 = df_imm_cnp.iloc[-1]['Duration Gap']
    dg_gen_2024 = df_imm_gen.iloc[-1]['Duration Gap']
    st.markdown(f"""
    <div class="insight-box">
    <b>CNP 2024</b> — Duration Gap = <b>{dg_cnp_2024:.2f} ans</b> :
    les passifs sont ~3.3× plus sensibles aux taux que les actifs.
    Un choc +{choc_bps}bps améliore les FP S2 (effet positif net).
    </div>
    <div class="insight-box gen" style="border-left-color:#e05a3a; background:#fdf1ee;">
    <b>Generali 2024</b> — Duration Gap = <b>{dg_gen_2024:.2f} ans</b> :
    passifs 2.8× plus sensibles. Le gap s'est creusé depuis 2021 (−10.8 → −14.4)
    en raison de la montée des UC qui réduit V_actif obligataire sans réduire le BE proportionnellement.
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TAB 5 — COMPARATIF SCR
# ══════════════════════════════════════════════
with tabs[4]:
    st.markdown('<div class="section-title">Ratio SCR 2021-2024 — Formule standard vs Modèle interne</div>',
                unsafe_allow_html=True)

    taux_rfr = {2021: 0.2, 2022: 3.2, 2023: 3.8, 2024: 3.4}

    fig_scr = make_subplots(
        rows=2, cols=1, row_heights=[0.65, 0.35],
        subplot_titles=["Ratio SCR (%)", "Taux RFR EIOPA (proxy OIS 10 ans, %)"],
        shared_xaxes=True, vertical_spacing=0.12
    )

    annees_str = [str(a) for a in df_cnp['Annee']]

    fig_scr.add_trace(go.Scatter(
        name='CNP (formule standard)', x=annees_str, y=df_cnp['SCR_pct'],
        mode='lines+markers+text',
        text=[f"{v:.0f}%" for v in df_cnp['SCR_pct']],
        textposition='top center',
        line=dict(color=CNP_COLOR, width=3), marker=dict(size=10)
    ), row=1, col=1)

    fig_scr.add_trace(go.Scatter(
        name='Generali (modèle interne)', x=annees_str, y=df_gen['SCR_pct'],
        mode='lines+markers+text',
        text=[f"{v:.0f}%" for v in df_gen['SCR_pct']],
        textposition='bottom center',
        line=dict(color=GEN_COLOR, width=3), marker=dict(size=10)
    ), row=1, col=1)

    fig_scr.add_hline(y=100, line_dash='dash', line_color='red',
                      annotation_text="Minimum réglementaire 100%", row=1, col=1)

    fig_scr.add_trace(go.Bar(
        name='RFR EIOPA', x=annees_str,
        y=list(taux_rfr.values()),
        marker_color=GOLD,
        text=[f"{v:.1f}%" for v in taux_rfr.values()],
        textposition='outside', showlegend=True
    ), row=2, col=1)

    # Annotations contextuelles
    fig_scr.add_annotation(x='2022', y=230, row=1, col=1,
        text="<b>CNP ↑</b><br>Formule standard :<br>baisse BE > baisse actif",
        showarrow=True, arrowhead=2, ax=-70, ay=30,
        font=dict(color=CNP_COLOR, size=11))
    fig_scr.add_annotation(x='2023', y=157, row=1, col=1,
        text="<b>Generali ↓</b><br>Modèle interne :<br>lapse risk + spread",
        showarrow=True, arrowhead=2, ax=70, ay=-30,
        font=dict(color=GEN_COLOR, size=11))

    fig_scr.update_layout(
        height=600, plot_bgcolor='white', paper_bgcolor='white',
        legend=dict(orientation='h', y=1.04, x=.5, xanchor='center')
    )
    fig_scr.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig_scr, use_container_width=True)

    st.markdown('<div class="section-title">Analyse — Effet réinvestissement post-2022</div>',
                unsafe_allow_html=True)

    data_narrative = [
        ("2021→2022", "Taux 0.2% → 3.2%",
         "Chute des actifs obligataires CNP : −23% (234→191 Md€). "
         "Mais ratio SCR monte (217→230%) car sous formule standard, "
         "la baisse du BE compense largement la baisse des actifs (D_passif > D_actif)."),
        ("2022→2023", "Taux 3.2% → 3.8%",
         "Stabilisation des taux à haut niveau. Réinvestissement des coupons "
         "et échéances à meilleure rentabilité. BE continue de baisser. "
         "Ratio SCR CNP atteint son pic : 253%."),
        ("2023→2024", "Taux 3.8% → 3.4%",
         "Légère détente des taux. BE remonte légèrement. "
         "Ratio SCR CNP recule à 237% — encore bien au-dessus du minimum réglementaire."),
        ("Generali", "Modèle interne",
         "Chute de 187% (2021) à 150% (2023). Le modèle interne capture des risques "
         "absents de la formule standard : lapse risk (rachats si taux montent), "
         "risque de spread, concentration obligataire. → Ratio plus bas ≠ moins solide."),
    ]

    for periode, taux_label, texte in data_narrative:
        col_a, col_b = st.columns([1, 4])
        with col_a:
            st.markdown(f"**{periode}**  \n`{taux_label}`")
        with col_b:
            st.markdown(f'<div class="insight-box">{texte}</div>',
                        unsafe_allow_html=True)

    # Fonds propres éligibles 2024
    st.markdown('<div class="section-title">Fonds propres éligibles (FPE) — Formule SCR</div>',
                unsafe_allow_html=True)

    fpe_cnp = df_cnp.iloc[-1]['SCR_pct'] / 100 * df_cnp.iloc[-1]['SCR_mde']
    fpe_gen = df_gen.iloc[-1]['SCR_pct'] / 100 * df_gen.iloc[-1]['SCR_mde']
    perte_cnp_2024 = D_actif * choc * df_cnp.iloc[-1]['R0130']
    pct_fpe_cnp = perte_cnp_2024 / fpe_cnp * 100

    c1, c2, c3 = st.columns(3)
    c1.metric("FPE CNP 2024", f"{fpe_cnp:.1f} Md€",
              help="Ratio SCR × SCR total")
    c2.metric("Perte actif CNP +100bps", f"{perte_cnp_2024:.1f} Md€")
    c3.metric("Perte / FPE CNP", f"{pct_fpe_cnp:.0f}%",
              help="Part des FP détruits par le choc")

    st.markdown(f"""
    <div class="insight-box warning">
    <b>Interprétation 2024 :</b> Un choc +{choc_bps}bps détruirait
    ~{perte_cnp_2024:.1f} Md€ d'actifs obligataires CNP, soit {pct_fpe_cnp:.0f}% des fonds propres éligibles.
    Mais cet impact actif est plus que compensé par la baisse simultanée du Best Estimate
    (D_passif=15 > D_actif=8), d'où un ΔFP net positif.
    C'est le mécanisme central de l'ALM assureur vie.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Projet ALM — M1 Actuariat ISUP Sorbonne Université | "
    "Sources : SFCR publics CNP Assurances & Generali Vie 2021-2024 | "
    "QRT S.02.01.02 + S.23.01 | Hypothèses : D_actif=8a, D_passif=15a, convexité ignorée"
)
