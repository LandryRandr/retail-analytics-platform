import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from snowflake.snowpark.context import get_active_session

# ==========================================================
# CONFIGURATION
# ==========================================================
st.set_page_config(
    page_title="Retail Intelligence",
    page_icon="🧠",
    layout="centered",  # "centered" est plus adapté au mobile que "wide"
    initial_sidebar_state="collapsed",
)

PALETTE = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2", "#EECA3B", "#B279A2", "#FF9DA6"]
session = get_active_session()

# ==========================================================
# DÉTECTION MOBILE (via user-agent / largeur)
# ==========================================================
# Streamlit ne fournit pas directement la largeur. On utilise une astuce :
# on injecte un composant JS qui écrit la largeur dans un paramètre d'URL.
# Alternative plus simple : on propose un toggle "Mode mobile".
st.sidebar.header("⚙️ Affichage")
mode = st.sidebar.radio(
    "Choisir le mode",
    ["📱 Mobile", "💻 Desktop"],
    index=0,
    help="Le mode mobile empile les sections et agrandit les KPI."
)
IS_MOBILE = mode == "📱 Mobile"

# ==========================================================
# STYLE CSS PERSONNALISÉ (mobile-first)
# ==========================================================
if IS_MOBILE:
    st.markdown("""
    <style>
    /* Réduire les marges */
    .block-container { padding: 1rem 0.5rem; }
    /* Agrandir les KPI */
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
    /* Réduire la hauteur des graphiques */
    .stAltairChart { margin-bottom: 0.5rem; }
    /* Cacher la sidebar par défaut */
    [data-testid="collapsedControl"] { display: block; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .block-container { padding: 2rem 3rem; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# CHARGEMENT
# ==========================================================
@st.cache_data(ttl=600)
def load_data():
    fact = session.sql("""
        SELECT ORDER_ID, CUSTOMER_ID, PRODUCT_ID, ORDER_DATE,
               QUANTITY, UNIT_PRICE, TOTAL_AMOUNT, YEAR, QUARTER
        FROM RETAIL_ANALYTICS.GOLD.FACT_SALES
    """).to_pandas()
    cust = session.sql("""
        SELECT CUSTOMER_ID, FIRST_NAME, LAST_NAME, COUNTRY
        FROM RETAIL_ANALYTICS.GOLD.DIM_CUSTOMER
    """).to_pandas()
    prod = session.sql("""
        SELECT PRODUCT_ID, PRODUCT_NAME, CATEGORY
        FROM RETAIL_ANALYTICS.GOLD.DIM_PRODUCT
    """).to_pandas()
    return fact, cust, prod

with st.spinner("Chargement..."):
    fact, customers, products = load_data()

fact["ORDER_DATE"] = pd.to_datetime(fact["ORDER_DATE"])
df = (fact.merge(customers, on="CUSTOMER_ID", how="left")
          .merge(products, on="PRODUCT_ID", how="left", suffixes=("", "_prod")))

# ==========================================================
# FILTRES (sidebar, mais compacts)
# ==========================================================
with st.sidebar:
    st.header("🎯 Filtres")
    years = sorted(df["YEAR"].dropna().unique().tolist())
    sel_years = st.multiselect("Année", years, default=years)
    countries = sorted(df["COUNTRY"].dropna().unique().tolist())
    sel_countries = st.multiselect("Pays", countries, default=countries)
    categories = sorted(df["CATEGORY"].dropna().unique().tolist())
    sel_categories = st.multiselect("Catégorie", categories, default=categories)

mask = (df["YEAR"].isin(sel_years)
        & df["COUNTRY"].isin(sel_countries)
        & df["CATEGORY"].isin(sel_categories))
filtered = df[mask].copy()

if filtered.empty:
    st.warning("Aucune donnée pour ces filtres.")
    st.stop()

# ==========================================================
# HEADER
# ==========================================================
st.title("🧠 Retail Intelligence")
st.caption(f"{filtered['ORDER_DATE'].min():%d/%m/%Y} → {filtered['ORDER_DATE'].max():%d/%m/%Y}")

# ==========================================================
# KPI (2 colonnes sur mobile, 6 sur desktop)
# ==========================================================
total_rev = filtered["TOTAL_AMOUNT"].sum()
total_orders = filtered["ORDER_ID"].nunique()
total_cust = filtered["CUSTOMER_ID"].nunique()
avg_basket = total_rev / total_orders if total_orders else 0

monthly_rev = filtered.groupby(filtered["ORDER_DATE"].dt.to_period("M"))["TOTAL_AMOUNT"].sum().sort_index()
mom_growth = 0
if len(monthly_rev) >= 2:
    last, prev = monthly_rev.iloc[-1], monthly_rev.iloc[-2]
    mom_growth = ((last - prev) / prev * 100) if prev else 0

orders_per_cust = filtered.groupby("CUSTOMER_ID")["ORDER_ID"].nunique()
repeat_rate = ((orders_per_cust > 1).sum() / total_cust * 100) if total_cust else 0

if IS_MOBILE:
    # 2 colonnes x 3 lignes sur mobile
    r1c1, r1c2 = st.columns(2)
    r1c1.metric("💰 CA", f"${total_rev/1000:,.1f}k")
    r1c2.metric("🧾 Commandes", f"{total_orders:,}")
    r2c1, r2c2 = st.columns(2)
    r2c1.metric("🛒 Panier", f"${avg_basket:,.0f}")
    r2c2.metric("📈 MoM", f"{mom_growth:+.1f}%")
    r3c1, r3c2 = st.columns(2)
    r3c1.metric("👥 Clients", f"{total_cust:,}")
    r3c2.metric("🔄 Réachat", f"{repeat_rate:.1f}%")
else:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("💰 CA Total", f"${total_rev:,.0f}")
    c2.metric("🧾 Commandes", f"{total_orders:,}")
    c3.metric("🛒 Panier Moyen", f"${avg_basket:,.0f}")
    c4.metric("📈 Croissance MoM", f"{mom_growth:+.1f}%")
    c5.metric("👥 Clients Uniques", f"{total_cust:,}")
    c6.metric("🔄 Taux de Réachat", f"{repeat_rate:.1f}%")

st.divider()

# ==========================================================
# CONTENU PRINCIPAL — ONGLETS SUR MOBILE, COLONNES SUR DESKTOP
# ==========================================================
def chart_trend():
    daily = filtered.groupby("ORDER_DATE")["TOTAL_AMOUNT"].sum().reset_index()
    daily["MA7"] = daily["TOTAL_AMOUNT"].rolling(7, min_periods=1).mean()
    base = alt.Chart(daily).encode(x=alt.X("ORDER_DATE:T", title=""))
    area = base.mark_area(opacity=0.3, color=PALETTE[0]).encode(y=alt.Y("TOTAL_AMOUNT:Q", title="CA ($)"))
    line = base.mark_line(color=PALETTE[0]).encode(y="TOTAL_AMOUNT:Q")
    ma = base.mark_line(color=PALETTE[1], strokeDash=[5, 3]).encode(y="MA7:Q")
    h = 220 if IS_MOBILE else 320
    return (area + line + ma).properties(height=h, title="CA Quotidien & MA7")

def chart_heatmap():
    filtered["Month"] = filtered["ORDER_DATE"].dt.month
    heat = filtered.groupby(["YEAR", "Month"])["TOTAL_AMOUNT"].sum().reset_index()
    h = 220 if IS_MOBILE else 320
    return alt.Chart(heat).mark_rect().encode(
        x=alt.X("Month:O", title="Mois"),
        y=alt.Y("YEAR:O", title=""),
        color=alt.Color("TOTAL_AMOUNT:Q", scale=alt.Scale(scheme="blues"), title="CA"),
        tooltip=["YEAR", "Month", alt.Tooltip("TOTAL_AMOUNT", format="$,.0f")]
    ).properties(height=h, title="Saisonnalité")

def chart_top_products():
    top = (filtered.groupby("PRODUCT_NAME")["TOTAL_AMOUNT"].sum()
           .reset_index().nlargest(10, "TOTAL_AMOUNT").sort_values("TOTAL_AMOUNT"))
    h = 280 if IS_MOBILE else 400
    return alt.Chart(top).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
        x=alt.X("TOTAL_AMOUNT:Q", title="CA ($)"),
        y=alt.Y("PRODUCT_NAME:N", sort="-x", title=""),
        color=alt.Color("TOTAL_AMOUNT:Q", scale=alt.Scale(scheme="tealblues"), legend=None),
        tooltip=["PRODUCT_NAME", alt.Tooltip("TOTAL_AMOUNT", format="$,.0f")]
    ).properties(height=h, title="Top 10 Produits")

def chart_scatter():
    cat = filtered.groupby("CATEGORY").agg(
        CA=("TOTAL_AMOUNT", "sum"), Qty=("QUANTITY", "sum"), Orders=("ORDER_ID", "nunique")
    ).reset_index()
    h = 280 if IS_MOBILE else 400
    scatter = alt.Chart(cat).mark_circle(size=200, opacity=0.7).encode(
        x=alt.X("Qty:Q", title="Unités"),
        y=alt.Y("CA:Q", title="CA ($)"),
        size=alt.Size("Orders:Q", scale=alt.Scale(range=[100, 800]), legend=None),
        color=alt.Color("CATEGORY:N", scale=alt.Scale(range=PALETTE)),
        tooltip=["CATEGORY", alt.Tooltip("CA", format="$,.0f"), "Qty"]
    )
    text = scatter.mark_text(dy=-15, fontSize=10).encode(text="CATEGORY:N")
    return (scatter + text).properties(height=h, title="Matrice Catégories")

def chart_anomalies():
    daily = filtered.groupby("ORDER_DATE")["TOTAL_AMOUNT"].sum().reset_index()
    mu, sigma = daily["TOTAL_AMOUNT"].mean(), daily["TOTAL_AMOUNT"].std()
    daily["Z"] = (daily["TOTAL_AMOUNT"] - mu) / sigma
    h = 220 if IS_MOBILE else 300
    base = alt.Chart(daily).encode(x=alt.X("ORDER_DATE:T", title=""))
    line = base.mark_line(color=PALETTE[0]).encode(y="TOTAL_AMOUNT:Q")
    pts = base.mark_circle(size=80, color=PALETTE[3]).encode(
        y="TOTAL_AMOUNT:Q",
        tooltip=["ORDER_DATE", alt.Tooltip("TOTAL_AMOUNT", format="$,.0f"), alt.Tooltip("Z", format=".2f")]
    ).transform_filter(alt.datum.Z > 2)
    return (line + pts).properties(height=h, title="Anomalies (Z > 2)")

def chart_rfm():
    max_date = filtered["ORDER_DATE"].max()
    rfm = filtered.groupby("CUSTOMER_ID").agg(
        Recency=("ORDER_DATE", lambda x: (max_date - x.max()).days),
        Frequency=("ORDER_ID", "nunique"),
        Monetary=("TOTAL_AMOUNT", "sum")
    ).reset_index()
    rfm["R"] = pd.cut(rfm["Recency"], bins=[-1, 30, 90, 180, 9999], labels=["R1", "R2", "R3", "R4"])
    rfm["F"] = pd.cut(rfm["Frequency"], bins=[0, 1, 3, 5, 9999], labels=["F1", "F2", "F3", "F4"])
    rfm["Segment"] = rfm["R"].astype(str) + "-" + rfm["F"].astype(str)
    seg = rfm.groupby("Segment").agg(Clients=("CUSTOMER_ID", "count"), CA=("Monetary", "sum")).reset_index()
    h = 280 if IS_MOBILE else 350
    return alt.Chart(seg).mark_bar(cornerRadiusTopRight=4).encode(
        x=alt.X("Segment:N", title=""),
        y=alt.Y("CA:Q", title="CA ($)"),
        color=alt.Color("Segment:N", scale=alt.Scale(range=PALETTE), legend=None),
        tooltip=["Segment", "Clients", alt.Tooltip("CA", format="$,.0f")]
    ).properties(height=h, title="CA par Segment RFM")

if IS_MOBILE:
    # === MODE MOBILE : onglets ===
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Tendance", "📦 Produits", "👥 Clients", "🚨 Alertes"])
    with tab1:
        st.altair_chart(chart_trend(), use_container_width=True)
        st.altair_chart(chart_heatmap(), use_container_width=True)
    with tab2:
        st.altair_chart(chart_top_products(), use_container_width=True)
        st.altair_chart(chart_scatter(), use_container_width=True)
    with tab3:
        st.altair_chart(chart_rfm(), use_container_width=True)
        # Tableau simplifié sur mobile
        top_c = (filtered.groupby(["FIRST_NAME", "LAST_NAME"])["TOTAL_AMOUNT"].sum()
                 .reset_index().nlargest(10, "TOTAL_AMOUNT"))
        top_c["Client"] = top_c["FIRST_NAME"] + " " + top_c["LAST_NAME"]
        st.dataframe(top_c[["Client", "TOTAL_AMOUNT"]].rename(columns={"TOTAL_AMOUNT": "CA ($)"}),
                     hide_index=True, use_container_width=True)
    with tab4:
        st.altair_chart(chart_anomalies(), use_container_width=True)
        daily = filtered.groupby("ORDER_DATE")["TOTAL_AMOUNT"].sum().reset_index()
        mu, sigma = daily["TOTAL_AMOUNT"].mean(), daily["TOTAL_AMOUNT"].std()
        daily["Z"] = (daily["TOTAL_AMOUNT"] - mu) / sigma
        anom = daily[daily["Z"] > 2]
        if not anom.empty:
            st.caption(f"⚠️ {len(anom)} jour(s) atypique(s) détecté(s).")
        else:
            st.caption("✅ Aucune anomalie majeure.")
else:
    # === MODE DESKTOP : layout large classique ===
    col1, col2 = st.columns((2, 1))
    with col1:
        st.altair_chart(chart_trend(), use_container_width=True)
    with col2:
        st.altair_chart(chart_heatmap(), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(chart_top_products(), use_container_width=True)
    with col2:
        st.altair_chart(chart_scatter(), use_container_width=True)

    col1, col2 = st.columns((2, 1))
    with col1:
        st.altair_chart(chart_rfm(), use_container_width=True)
    with col2:
        st.altair_chart(chart_anomalies(), use_container_width=True)

st.divider()
st.caption("Dashboard optimisé mobile — Streamlit natif + Altair, sans dépendance externe.")