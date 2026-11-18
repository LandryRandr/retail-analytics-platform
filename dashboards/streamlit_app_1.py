import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from snowflake.snowpark.context import get_active_session

# ==========================================================
# CONFIGURATION & THÈME
# (uniquement streamlit, pandas, numpy, altair : tous disponibles
#  dans Streamlit in Snowflake, aucune dépendance externe)
# ==========================================================
st.set_page_config(page_title="Retail Intelligence", layout="wide")

PRIMARY = "#2563EB"
ACCENT = "#F59E0B"
POS = "#16A34A"
NEG = "#DC2626"
INK = "#111827"
MUTED = "#6B7280"
GRID = "#EEF0F3"
CAT_RANGE = ["#2563EB", "#0EA5E9", "#14B8A6", "#F59E0B", "#8B5CF6", "#EC4899", "#64748B", "#84CC16"]
MONTHS = ["Janv", "Févr", "Mars", "Avr", "Mai", "Juin", "Juil", "Août", "Sept", "Oct", "Nov", "Déc"]

st.markdown(
    """
    <style>
    .stApp { background-color: #F7F8FA; }
    .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1400px; }
    h1 { font-weight: 700; letter-spacing: -0.02em; color: #111827; }
    h3 { font-weight: 600; color: #111827; }

    /* Cartes KPI */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 14px 18px;
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #6B7280;
    }
    div[data-testid="stMetricValue"] { font-size: 1.65rem; font-weight: 600; color: #111827; }

    /* Onglets */
    .stTabs [data-baseweb="tab-list"] { gap: 28px; border-bottom: 1px solid #E5E7EB; }
    .stTabs [data-baseweb="tab"] { padding: 10px 2px; font-weight: 500; }

    /* Sous-titres de section */
    .section-title { font-size: 1rem; font-weight: 600; color: #111827; margin: 0.4rem 0 0.1rem 0; }
    .section-sub { font-size: 0.82rem; color: #6B7280; margin-bottom: 0.4rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

session = get_active_session()


# ==========================================================
# HELPERS
# ==========================================================
def money(x: float) -> str:
    if abs(x) >= 1e6:
        return f"${x / 1e6:,.2f}M"
    if abs(x) >= 1e4:
        return f"${x / 1e3:,.1f}K"
    return f"${x:,.0f}"


def section(title: str, subtitle: str = ""):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-sub">{subtitle}</div>', unsafe_allow_html=True)


def show(chart, height: int = 320):
    """Applique un style Altair homogène puis affiche le graphique."""
    chart = (
        chart.properties(height=height)
        .configure_view(stroke=None)
        .configure_axis(
            domain=False,
            tickSize=0,
            gridColor=GRID,
            labelColor=MUTED,
            titleColor=MUTED,
            labelFontSize=11,
            titleFontSize=11,
            titleFontWeight="normal",
            labelPadding=6,
        )
        .configure_legend(labelColor=MUTED, labelFontSize=11, titleColor=MUTED, symbolType="circle")
    )
    try:
        st.altair_chart(chart, use_container_width=True, theme=None)
    except TypeError:  # anciennes versions de Streamlit sans paramètre theme
        st.altair_chart(chart, use_container_width=True)


def hbar(data: pd.DataFrame, cat: str, val: str, color: str = PRIMARY, fmt: str = "$,.0f"):
    """Barres horizontales triées avec valeurs affichées au bout des barres."""
    vmax = float(data[val].max()) if len(data) else 1.0
    base = alt.Chart(data).encode(
        y=alt.Y(f"{cat}:N", sort="-x", title=None, axis=alt.Axis(labelLimit=220)),
        x=alt.X(f"{val}:Q", title=None, scale=alt.Scale(domain=[0, vmax * 1.18]), axis=alt.Axis(format="~s")),
    )
    bars = base.mark_bar(color=color, cornerRadiusTopRight=3, cornerRadiusBottomRight=3, size=16).encode(
        tooltip=[cat, alt.Tooltip(f"{val}:Q", format=fmt)]
    )
    labels = base.mark_text(align="left", dx=5, fontSize=11, color=INK).encode(
        text=alt.Text(f"{val}:Q", format=fmt)
    )
    return bars + labels


# ==========================================================
# CHARGEMENT & ENRICHISSEMENT
# ==========================================================
@st.cache_data(ttl=600, show_spinner="Chargement des données...")
def load_data():
    fact = session.sql("""
        SELECT ORDER_ID, CUSTOMER_ID, PRODUCT_ID, ORDER_DATE,
               QUANTITY, UNIT_PRICE, TOTAL_AMOUNT, YEAR, QUARTER
        FROM RETAIL_ANALYTICS.GOLD.FACT_SALES
    """).to_pandas()
    cust = session.sql("""
        SELECT CUSTOMER_ID, FIRST_NAME, LAST_NAME, COUNTRY, CITY
        FROM RETAIL_ANALYTICS.GOLD.DIM_CUSTOMER
    """).to_pandas()
    prod = session.sql("""
        SELECT PRODUCT_ID, PRODUCT_NAME, CATEGORY
        FROM RETAIL_ANALYTICS.GOLD.DIM_PRODUCT
    """).to_pandas()
    return fact, cust, prod


fact, customers, products = load_data()

fact["ORDER_DATE"] = pd.to_datetime(fact["ORDER_DATE"])
df = (
    fact.merge(customers, on="CUSTOMER_ID", how="left")
    .merge(products, on="PRODUCT_ID", how="left", suffixes=("", "_prod"))
)
df["CLIENT"] = (df["FIRST_NAME"].fillna("") + " " + df["LAST_NAME"].fillna("")).str.strip()
df["MONTH"] = df["ORDER_DATE"].dt.to_period("M").dt.to_timestamp()

# ==========================================================
# FILTRES (barre latérale)
# ==========================================================
st.sidebar.markdown("### Filtres")

dmin, dmax = df["ORDER_DATE"].min().date(), df["ORDER_DATE"].max().date()
date_range = st.sidebar.date_input("Période", (dmin, dmax), min_value=dmin, max_value=dmax)
if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.info("Sélectionnez une date de fin pour afficher les résultats.")
    st.stop()

countries = sorted(df["COUNTRY"].dropna().unique().tolist())
sel_countries = st.sidebar.multiselect("Pays", countries, default=countries)

categories = sorted(df["CATEGORY"].dropna().unique().tolist())
sel_categories = st.sidebar.multiselect("Catégorie", categories, default=categories)

st.sidebar.divider()
if st.sidebar.button("Actualiser les données"):
    st.cache_data.clear()

mask = (
    (df["ORDER_DATE"].dt.date >= date_range[0])
    & (df["ORDER_DATE"].dt.date <= date_range[1])
    & df["COUNTRY"].isin(sel_countries)
    & df["CATEGORY"].isin(sel_categories)
)
filtered = df[mask].copy()

if filtered.empty:
    st.warning("Aucune donnée pour ces filtres.")
    st.stop()

# ==========================================================
# EN-TÊTE & KPI
# ==========================================================
st.title("Retail Intelligence")
st.caption(
    f"Période du {filtered['ORDER_DATE'].min():%d/%m/%Y} au {filtered['ORDER_DATE'].max():%d/%m/%Y}"
    f"  ·  Source : RETAIL_ANALYTICS.GOLD"
)

total_rev = filtered["TOTAL_AMOUNT"].sum()
total_orders = filtered["ORDER_ID"].nunique()
total_cust = filtered["CUSTOMER_ID"].nunique()
avg_basket = total_rev / total_orders if total_orders else 0

orders_per_cust = filtered.groupby("CUSTOMER_ID")["ORDER_ID"].nunique()
repeat_rate = (orders_per_cust > 1).sum() / total_cust * 100 if total_cust else 0

# Croissance mensuelle calculée sur les mois COMPLETS uniquement
# (comparer un mois en cours à un mois entier fausserait le résultat)
monthly = filtered.groupby("MONTH")["TOTAL_AMOUNT"].sum().sort_index()
last_day = filtered["ORDER_DATE"].max().normalize()
if len(monthly) and last_day < (last_day + pd.offsets.MonthEnd(0)):
    monthly = monthly.iloc[:-1]

if len(monthly) >= 2 and monthly.iloc[-2] > 0:
    mom_growth = (monthly.iloc[-1] - monthly.iloc[-2]) / monthly.iloc[-2] * 100
    m1, m0 = monthly.index[-1], monthly.index[-2]
    mom_value = f"{mom_growth:+.1f}%"
    mom_label = f"{MONTHS[m1.month - 1]} vs {MONTHS[m0.month - 1]}"
else:
    mom_value, mom_label = "n/d", "Mois complets insuffisants"

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Chiffre d'affaires", money(total_rev))
k2.metric("Commandes", f"{total_orders:,}")
k3.metric("Panier moyen", f"${avg_basket:,.0f}")
k4.metric("Clients actifs", f"{total_cust:,}")
k5.metric("Taux de réachat", f"{repeat_rate:.1f}%")
k6.metric("Croissance mensuelle", mom_value, delta=mom_label, delta_color="off")

st.write("")

tab_overview, tab_products, tab_clients, tab_anomalies = st.tabs(
    ["Vue d'ensemble", "Produits", "Clients", "Anomalies"]
)

# ==========================================================
# ONGLET 1 : VUE D'ENSEMBLE
# ==========================================================
with tab_overview:
    head_l, head_r = st.columns([3, 1])
    with head_l:
        section("Évolution du chiffre d'affaires", "Courbe lissée par moyenne mobile pour faire ressortir la tendance")
    with head_r:
        gran = st.radio("Granularité", ["Jour", "Semaine", "Mois"], index=1, horizontal=True,
                        label_visibility="collapsed")

    freq, window = {"Jour": ("D", 7), "Semaine": ("W-MON", 4), "Mois": ("MS", 3)}[gran]
    ts = (
        filtered.set_index("ORDER_DATE")["TOTAL_AMOUNT"]
        .resample(freq, label="left", closed="left").sum()
        .rename("CA").reset_index()
    )
    ts["Moyenne mobile"] = ts["CA"].rolling(window, min_periods=1).mean()
    long = ts.melt("ORDER_DATE", ["CA", "Moyenne mobile"], var_name="Série", value_name="Valeur")

    x_axis = alt.X("ORDER_DATE:T", title=None)
    area = alt.Chart(ts).mark_area(opacity=0.12, color=PRIMARY).encode(
        x=x_axis, y=alt.Y("CA:Q", title=None, axis=alt.Axis(format="~s"))
    )
    lines = alt.Chart(long).mark_line(strokeWidth=2.2, interpolate="monotone").encode(
        x=x_axis,
        y=alt.Y("Valeur:Q", title=None),
        color=alt.Color(
            "Série:N",
            scale=alt.Scale(domain=["CA", "Moyenne mobile"], range=[PRIMARY, ACCENT]),
            legend=alt.Legend(orient="top", title=None),
        ),
        tooltip=[
            alt.Tooltip("ORDER_DATE:T", title="Date"),
            alt.Tooltip("Série:N"),
            alt.Tooltip("Valeur:Q", format="$,.0f", title="CA"),
        ],
    )
    show(area + lines, 320)

    col_heat, col_country = st.columns([3, 2])

    with col_heat:
        section("Saisonnalité", "Chiffre d'affaires par mois et par année")
        heat = (
            filtered.assign(Année=filtered["ORDER_DATE"].dt.year, Mois=filtered["ORDER_DATE"].dt.month)
            .groupby(["Année", "Mois"])["TOTAL_AMOUNT"].sum().reset_index(name="CA")
        )
        heat["Mois"] = heat["Mois"].map(lambda m: MONTHS[m - 1])
        threshold = heat["CA"].max() * 0.55
        base = alt.Chart(heat).encode(
            x=alt.X("Mois:O", sort=MONTHS, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Année:O", title=None),
        )
        rect = base.mark_rect(cornerRadius=3, stroke="white", strokeWidth=2).encode(
            color=alt.Color("CA:Q", scale=alt.Scale(scheme="blues"), legend=None),
            tooltip=["Année:O", "Mois:O", alt.Tooltip("CA:Q", format="$,.0f")],
        )
        txt = base.mark_text(fontSize=10).encode(
            text=alt.Text("CA:Q", format="~s"),
            color=alt.condition(alt.datum.CA > threshold, alt.value("white"), alt.value(INK)),
        )
        show(rect + txt, max(140, 52 * heat["Année"].nunique() + 40))

    with col_country:
        section("Répartition par pays", "Top 8 par chiffre d'affaires")
        by_country = (
            filtered.groupby("COUNTRY")["TOTAL_AMOUNT"].sum()
            .nlargest(8).reset_index().rename(columns={"COUNTRY": "Pays", "TOTAL_AMOUNT": "CA"})
        )
        show(hbar(by_country, "Pays", "CA", fmt="$,.0f"), max(180, 34 * len(by_country) + 20))

# ==========================================================
# ONGLET 2 : PRODUITS
# ==========================================================
with tab_products:
    col_top, col_cat = st.columns(2)

    with col_top:
        head_a, head_b = st.columns([2, 1])
        with head_a:
            section("Meilleurs produits", "Classés par chiffre d'affaires")
        with head_b:
            top_n = st.slider("Nombre de produits", 5, 30, 10, label_visibility="collapsed")
        top_prod = (
            filtered.groupby("PRODUCT_NAME")["TOTAL_AMOUNT"].sum()
            .nlargest(top_n).reset_index().rename(columns={"PRODUCT_NAME": "Produit", "TOTAL_AMOUNT": "CA"})
        )
        show(hbar(top_prod, "Produit", "CA"), max(260, 28 * top_n + 20))

    with col_cat:
        section("Poids des catégories", "Part du chiffre d'affaires")
        cat_ca = (
            filtered.groupby("CATEGORY")["TOTAL_AMOUNT"].sum()
            .reset_index().rename(columns={"CATEGORY": "Catégorie", "TOTAL_AMOUNT": "CA"})
        )
        cat_ca["Part"] = cat_ca["CA"] / cat_ca["CA"].sum()
        base = alt.Chart(cat_ca).encode(
            y=alt.Y("Catégorie:N", sort="-x", title=None, axis=alt.Axis(labelLimit=200)),
            x=alt.X("Part:Q", title=None, axis=alt.Axis(format="%"),
                    scale=alt.Scale(domain=[0, float(cat_ca["Part"].max()) * 1.2])),
        )
        bars = base.mark_bar(color=PRIMARY, cornerRadiusTopRight=3, cornerRadiusBottomRight=3, size=16).encode(
            tooltip=["Catégorie", alt.Tooltip("CA:Q", format="$,.0f"), alt.Tooltip("Part:Q", format=".1%")]
        )
        lbl = base.mark_text(align="left", dx=5, fontSize=11, color=INK).encode(text=alt.Text("Part:Q", format=".0%"))
        show(bars + lbl, max(260, 28 * top_n + 20))

    st.write("")
    col_sc, col_tab = st.columns([3, 2])

    with col_sc:
        section("Volume vs valeur", "Taille des bulles = nombre de commandes")
        cat_stats = filtered.groupby("CATEGORY").agg(
            CA=("TOTAL_AMOUNT", "sum"),
            Qty=("QUANTITY", "sum"),
            Orders=("ORDER_ID", "nunique"),
        ).reset_index()
        base = alt.Chart(cat_stats).encode(
            x=alt.X("Qty:Q", title="Unités vendues", axis=alt.Axis(format="~s")),
            y=alt.Y("CA:Q", title="Chiffre d'affaires", axis=alt.Axis(format="~s")),
        )
        pts = base.mark_circle(opacity=0.75).encode(
            size=alt.Size("Orders:Q", legend=None, scale=alt.Scale(range=[150, 1200])),
            color=alt.Color("CATEGORY:N", scale=alt.Scale(range=CAT_RANGE), legend=None),
            tooltip=[
                alt.Tooltip("CATEGORY:N", title="Catégorie"),
                alt.Tooltip("CA:Q", format="$,.0f"),
                alt.Tooltip("Qty:Q", title="Unités", format=",.0f"),
                alt.Tooltip("Orders:Q", title="Commandes", format=",.0f"),
            ],
        )
        names = base.mark_text(dy=-18, fontSize=11, color=INK).encode(text="CATEGORY:N")
        show(pts + names, 340)

    with col_tab:
        section("Détail par catégorie")
        cat_table = cat_stats.copy()
        cat_table["Prix moyen"] = cat_table["CA"] / cat_table["Qty"].replace(0, np.nan)
        cat_table["Part du CA"] = cat_table["CA"] / cat_table["CA"].sum()
        cat_table = cat_table.sort_values("CA", ascending=False).rename(columns={"CATEGORY": "Catégorie"})
        st.dataframe(
            cat_table[["Catégorie", "CA", "Part du CA", "Qty", "Prix moyen"]],
            column_config={
                "CA": st.column_config.NumberColumn("CA", format="$%.0f"),
                "Part du CA": st.column_config.ProgressColumn("Part du CA", format="%.0f%%", min_value=0, max_value=1),
                "Qty": st.column_config.NumberColumn("Unités", format="%d"),
                "Prix moyen": st.column_config.NumberColumn("Prix moyen", format="$%.2f"),
            },
            hide_index=True,
            use_container_width=True,
        )

# ==========================================================
# ONGLET 3 : CLIENTS (segmentation RFM)
# ==========================================================
with tab_clients:
    section(
        "Segmentation par récence et fréquence",
        "Un client est « actif » s'il a commandé récemment, « fidèle » s'il commande souvent. Ajustez les seuils ci-dessous.",
    )
    s1, s2, _ = st.columns([1, 1, 2])
    recency_max = s1.slider("Actif si dernière commande il y a moins de (jours)", 15, 365, 90, step=15)
    freq_min = s2.slider("Fidèle à partir de (commandes)", 2, 10, 3)

    snapshot = filtered["ORDER_DATE"].max() + pd.Timedelta(days=1)
    rfm = filtered.groupby("CUSTOMER_ID").agg(
        Client=("CLIENT", "first"),
        Pays=("COUNTRY", "first"),
        Dernière=("ORDER_DATE", "max"),
        Commandes=("ORDER_ID", "nunique"),
        CA=("TOTAL_AMOUNT", "sum"),
    ).reset_index()
    rfm["Récence"] = (snapshot - rfm["Dernière"]).dt.days

    active = rfm["Récence"] <= recency_max
    loyal = rfm["Commandes"] >= freq_min
    rfm["Segment"] = np.select(
        [active & loyal, active & ~loyal, ~active & loyal],
        ["Champions", "Actifs occasionnels", "À risque"],
        default="Inactifs",
    )

    SEG_ORDER = ["Champions", "Actifs occasionnels", "À risque", "Inactifs"]
    SEG_COLORS = [POS, PRIMARY, ACCENT, "#94A3B8"]

    seg = rfm.groupby("Segment").agg(Clients=("CUSTOMER_ID", "count"), CA=("CA", "sum")).reindex(SEG_ORDER).fillna(0).reset_index()
    seg["Part clients"] = seg["Clients"] / seg["Clients"].sum()
    seg["Part CA"] = seg["CA"] / seg["CA"].sum()

    c_a, c_b = st.columns(2)
    for col, metric, title, fmt in [
        (c_a, "Clients", "Nombre de clients par segment", ",.0f"),
        (c_b, "CA", "Chiffre d'affaires par segment", "$,.0f"),
    ]:
        with col:
            section(title)
            vmax = float(seg[metric].max()) or 1.0
            base = alt.Chart(seg).encode(
                y=alt.Y("Segment:N", sort=SEG_ORDER, title=None),
                x=alt.X(f"{metric}:Q", title=None, axis=alt.Axis(format="~s"),
                        scale=alt.Scale(domain=[0, vmax * 1.2])),
            )
            bars = base.mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3, size=22).encode(
                color=alt.Color("Segment:N", scale=alt.Scale(domain=SEG_ORDER, range=SEG_COLORS), legend=None),
                tooltip=["Segment", alt.Tooltip(f"{metric}:Q", format=fmt)],
            )
            labels = base.mark_text(align="left", dx=5, fontSize=11, color=INK).encode(
                text=alt.Text(f"{metric}:Q", format=fmt)
            )
            show(bars + labels, 200)

    col_seg, col_top = st.columns([2, 3])
    with col_seg:
        section("Synthèse des segments")
        st.dataframe(
            seg[["Segment", "Clients", "Part clients", "Part CA"]],
            column_config={
                "Clients": st.column_config.NumberColumn("Clients", format="%d"),
                "Part clients": st.column_config.ProgressColumn("% clients", format="%.0f%%", min_value=0, max_value=1),
                "Part CA": st.column_config.ProgressColumn("% CA", format="%.0f%%", min_value=0, max_value=1),
            },
            hide_index=True,
            use_container_width=True,
        )
    with col_top:
        section("Top 10 clients", "Par chiffre d'affaires sur la période")
        top_clients = rfm.nlargest(10, "CA")[["Client", "Pays", "Commandes", "Récence", "CA", "Segment"]]
        st.dataframe(
            top_clients,
            column_config={
                "Récence": st.column_config.NumberColumn("Dernier achat (j)", format="%d"),
                "CA": st.column_config.NumberColumn("CA", format="$%.0f"),
            },
            hide_index=True,
            use_container_width=True,
        )

# ==========================================================
# ONGLET 4 : ANOMALIES
# ==========================================================
with tab_anomalies:
    head_a, head_b = st.columns([3, 1])
    with head_a:
        section(
            "Jours atypiques",
            "Écart au CA journalier moyen, mesuré en nombre d'écarts-types (z-score). Les jours sans vente comptent pour 0.",
        )
    with head_b:
        k = st.slider("Seuil (écarts-types)", 1.5, 4.0, 2.0, step=0.5)

    daily = (
        filtered.groupby(filtered["ORDER_DATE"].dt.normalize())["TOTAL_AMOUNT"].sum()
        .asfreq("D", fill_value=0).rename("CA").rename_axis("Date").reset_index()
    )
    mean_rev, std_rev = daily["CA"].mean(), daily["CA"].std()

    if not std_rev or np.isnan(std_rev):
        st.info("Pas assez de variation dans les données pour détecter des anomalies.")
    else:
        daily["Z"] = (daily["CA"] - mean_rev) / std_rev
        daily["Type"] = np.where(daily["Z"] > k, "Hausse", np.where(daily["Z"] < -k, "Baisse", ""))
        anomalies = daily[daily["Type"] != ""].copy()

        band = daily.assign(Bas=max(mean_rev - k * std_rev, 0), Haut=mean_rev + k * std_rev)
        band_area = alt.Chart(band).mark_area(opacity=0.07, color=PRIMARY).encode(
            x=alt.X("Date:T", title=None), y=alt.Y("Bas:Q", title=None, axis=alt.Axis(format="~s")), y2="Haut:Q"
        )
        line = alt.Chart(daily).mark_line(color=PRIMARY, strokeWidth=1.5).encode(
            x="Date:T", y="CA:Q"
        )
        points = alt.Chart(anomalies).mark_circle(size=90, opacity=0.95).encode(
            x="Date:T",
            y="CA:Q",
            color=alt.Color(
                "Type:N",
                scale=alt.Scale(domain=["Hausse", "Baisse"], range=[POS, NEG]),
                legend=alt.Legend(orient="top", title=None),
            ),
            tooltip=[
                alt.Tooltip("Date:T"),
                alt.Tooltip("CA:Q", format="$,.0f"),
                alt.Tooltip("Z:Q", title="Z-score", format="+.2f"),
                "Type:N",
            ],
        )
        show(band_area + line + points, 320)

        if anomalies.empty:
            st.caption("Aucune anomalie détectée avec ce seuil.")
        else:
            n_up = int((anomalies["Type"] == "Hausse").sum())
            n_dn = int((anomalies["Type"] == "Baisse").sum())
            st.caption(
                f"{len(anomalies)} jour(s) atypique(s) : {n_up} en hausse, {n_dn} en baisse. "
                "À rapprocher des promotions, ruptures de stock ou jours fériés."
            )
            st.dataframe(
                anomalies.assign(Abs=anomalies["Z"].abs()).sort_values("Abs", ascending=False)[["Date", "Type", "CA", "Z"]],
                column_config={
                    "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                    "CA": st.column_config.NumberColumn("CA", format="$%.0f"),
                    "Z": st.column_config.NumberColumn("Z-score", format="%+.2f"),
                },
                hide_index=True,
                use_container_width=True,
            )
