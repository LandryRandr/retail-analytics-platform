import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from snowflake.snowpark.context import get_active_session

# ==========================================================
# CONFIGURATION & THÈME
# ==========================================================
st.set_page_config(page_title="Retail Intelligence", page_icon="🧠", layout="wide")

# Palette de couleurs professionnelle (inspirée des dashboards type Tableau/PowerBI)
PALETTE = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2", "#EECA3B", "#B279A2", "#FF9DA6"]
BG_COLOR = "#ffffff"
GRID_COLOR = "#e0e0e0"

session = get_active_session()

# ==========================================================
# CHARGEMENT & ENRICHISSEMENT
# ==========================================================
@st.cache_data(ttl=600)
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

with st.spinner("Connexion à Snowflake..."):
    fact, customers, products = load_data()

fact["ORDER_DATE"] = pd.to_datetime(fact["ORDER_DATE"])
df = (fact.merge(customers, on="CUSTOMER_ID", how="left")
          .merge(products, on="PRODUCT_ID", how="left", suffixes=("", "_prod")))

# ==========================================================
# FILTRES (Sidebar)
# ==========================================================
st.sidebar.header("🎯 Filtres Stratégiques")

years = sorted(df["YEAR"].dropna().unique().tolist())
sel_years = st.sidebar.multiselect("Année", years, default=years)

countries = sorted(df["COUNTRY"].dropna().unique().tolist())
sel_countries = st.sidebar.multiselect("Pays", countries, default=countries)

categories = sorted(df["CATEGORY"].dropna().unique().tolist())
sel_categories = st.sidebar.multiselect("Catégorie", categories, default=categories)

mask = (
    df["YEAR"].isin(sel_years)
    & df["COUNTRY"].isin(sel_countries)
    & df["CATEGORY"].isin(sel_categories)
)
filtered = df[mask].copy()

if filtered.empty:
    st.warning("Aucune donnée pour ces filtres.")
    st.stop()

# ==========================================================
# HEADER & KPI AVANCÉS
# ==========================================================
st.title("🧠 Retail Intelligence Dashboard")
st.caption(
    f"Période : {filtered['ORDER_DATE'].min():%d/%m/%Y} → {filtered['ORDER_DATE'].max():%d/%m/%Y} | "
    f"{filtered['ORDER_ID'].nunique():,} commandes | {filtered['CUSTOMER_ID'].nunique():,} clients"
)

# --- Calcul des KPI de base ---
total_rev = filtered["TOTAL_AMOUNT"].sum()
total_orders = filtered["ORDER_ID"].nunique()
total_cust = filtered["CUSTOMER_ID"].nunique()
avg_basket = total_rev / total_orders if total_orders else 0

# --- KPI Avancé : Croissance MoM (Month-over-Month) ---
monthly_rev = filtered.groupby(filtered["ORDER_DATE"].dt.to_period("M"))["TOTAL_AMOUNT"].sum().sort_index()
if len(monthly_rev) >= 2:
    last_month = monthly_rev.iloc[-1]
    prev_month = monthly_rev.iloc[-2]
    mom_growth = ((last_month - prev_month) / prev_month * 100) if prev_month else 0
else:
    mom_growth = 0

# --- KPI Avancé : Taux de réachat (Repeat Rate) ---
orders_per_cust = filtered.groupby("CUSTOMER_ID")["ORDER_ID"].nunique()
repeat_customers = (orders_per_cust > 1).sum()
repeat_rate = (repeat_customers / total_cust * 100) if total_cust else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("💰 CA Total", f"${total_rev:,.0f}")
c2.metric("🧾 Commandes", f"{total_orders:,}")
c3.metric("🛒 Panier Moyen", f"${avg_basket:,.0f}")
c4.metric("📈 Croissance MoM", f"{mom_growth:+.1f}%", delta_color="normal")
c5.metric("👥 Clients Uniques", f"{total_cust:,}")
c6.metric("🔄 Taux de Réachat", f"{repeat_rate:.1f}%")

st.divider()

# ==========================================================
# SECTION 1 : ANALYSE DE LA TENDANCE & SAISONNALITÉ
# ==========================================================
st.subheader("📈 Tendance & Saisonnalité")

col_trend, col_heat = st.columns((2, 1))

with col_trend:
    # Graphique en aire avec ligne de moyenne mobile (Altair)
    daily_rev = filtered.groupby("ORDER_DATE")["TOTAL_AMOUNT"].sum().reset_index()
    daily_rev["MA7"] = daily_rev["TOTAL_AMOUNT"].rolling(7, min_periods=1).mean()

    base = alt.Chart(daily_rev).encode(x=alt.X("ORDER_DATE:T", title=""))
    area = base.mark_area(opacity=0.3, color=PALETTE[0]).encode(y=alt.Y("TOTAL_AMOUNT:Q", title="CA Journalier ($)"))
    line = base.mark_line(color=PALETTE[0], strokeWidth=2).encode(y="TOTAL_AMOUNT:Q")
    ma_line = base.mark_line(color=PALETTE[1], strokeWidth=2, strokeDash=[5, 3]).encode(y="MA7:Q")

    st.altair_chart((area + line + ma_line).properties(height=320, title="CA Quotidien & Moyenne Mobile 7j"), use_container_width=True)

with col_heat:
    # Heatmap Saisonnalité (Année vs Mois)
    filtered["Month"] = filtered["ORDER_DATE"].dt.month
    heat_data = filtered.groupby(["YEAR", "Month"])["TOTAL_AMOUNT"].sum().reset_index()
    heatmap = alt.Chart(heat_data).mark_rect().encode(
        x=alt.X("Month:O", title="Mois"),
        y=alt.Y("YEAR:O", title="Année"),
        color=alt.Color("TOTAL_AMOUNT:Q", scale=alt.Scale(scheme="blues"), title="CA ($)"),
        tooltip=["YEAR", "Month", alt.Tooltip("TOTAL_AMOUNT", format="$,.0f")]
    ).properties(height=320, title="Heatmap Saisonnalité")
    st.altair_chart(heatmap, use_container_width=True)

# ==========================================================
# SECTION 2 : ANALYSE PRODUIT & MIX
# ==========================================================
st.subheader("📦 Performance Produit & Mix")

col_prod, col_mix = st.columns(2)

with col_prod:
    # Top 15 Produits avec barres horizontales et labels
    top_prod = (filtered.groupby("PRODUCT_NAME")["TOTAL_AMOUNT"].sum()
                .reset_index().nlargest(15, "TOTAL_AMOUNT").sort_values("TOTAL_AMOUNT"))
    bars = alt.Chart(top_prod).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
        x=alt.X("TOTAL_AMOUNT:Q", title="CA ($)"),
        y=alt.Y("PRODUCT_NAME:N", sort="-x", title=""),
        color=alt.Color("TOTAL_AMOUNT:Q", scale=alt.Scale(scheme="tealblues"), legend=None),
        tooltip=["PRODUCT_NAME", alt.Tooltip("TOTAL_AMOUNT", format="$,.0f")]
    ).properties(height=400, title="Top 15 Produits (CA)")
    st.altair_chart(bars, use_container_width=True)

with col_mix:
    # Scatter Plot : CA vs Quantité par Catégorie (détection de "locomotives")
    cat_stats = filtered.groupby("CATEGORY").agg(
        CA=("TOTAL_AMOUNT", "sum"),
        Qty=("QUANTITY", "sum"),
        Orders=("ORDER_ID", "nunique")
    ).reset_index()
    scatter = alt.Chart(cat_stats).mark_circle(size=200, opacity=0.7).encode(
        x=alt.X("Qty:Q", title="Unités Vendues"),
        y=alt.Y("CA:Q", title="Chiffre d'Affaires ($)"),
        size=alt.Size("Orders:Q", scale=alt.Scale(range=[100, 800]), legend=None),
        color=alt.Color("CATEGORY:N", scale=alt.Scale(range=PALETTE)),
        tooltip=["CATEGORY", alt.Tooltip("CA", format="$,.0f"), "Qty", "Orders"]
    ).properties(height=400, title="Matrice Catégories (Volume vs Valeur)")
    # Ajout de labels
    text = scatter.mark_text(dy=-15, fontSize=11).encode(text="CATEGORY:N")
    st.altair_chart((scatter + text), use_container_width=True)

# ==========================================================
# SECTION 3 : SEGMENTATION CLIENT (RFM Simplifié)
# ==========================================================
st.subheader("👥 Segmentation Client (RFM)")

# Calcul RFM simplifié
max_date = filtered["ORDER_DATE"].max()
rfm = filtered.groupby("CUSTOMER_ID").agg(
    Recency=("ORDER_DATE", lambda x: (max_date - x.max()).days),
    Frequency=("ORDER_ID", "nunique"),
    Monetary=("TOTAL_AMOUNT", "sum")
).reset_index()

# Attribution de segments simples (basé sur des seuils)
rfm["R_Score"] = pd.cut(rfm["Recency"], bins=[-1, 30, 90, 180, 9999], labels=["R1", "R2", "R3", "R4"])
rfm["F_Score"] = pd.cut(rfm["Frequency"], bins=[0, 1, 3, 5, 9999], labels=["F1", "F2", "F3", "F4"])
rfm["Segment"] = rfm["R_Score"].astype(str) + "-" + rfm["F_Score"].astype(str)

seg_stats = rfm.groupby("Segment").agg(
    Clients=("CUSTOMER_ID", "count"),
    CA=("Monetary", "sum")
).reset_index()

col_rfm_chart, col_rfm_table = st.columns((2, 1))

with col_rfm_chart:
    # Treemap Altair (simulé avec rect + text)
    treemap = alt.Chart(seg_stats).mark_rect().encode(
        x=alt.X("Segment:N", title="Segment (Récence - Fréquence)"),
        y=alt.Y("CA:Q", title="CA Total ($)"),
        color=alt.Color("Segment:N", scale=alt.Scale(range=PALETTE), legend=None),
        tooltip=["Segment", "Clients", alt.Tooltip("CA", format="$,.0f")]
    ).properties(height=350, title="CA par Segment RFM")
    # Alternative : Bar chart empilé ou groupé
    st.altair_chart(treemap, use_container_width=True)

with col_rfm_table:
    st.dataframe(
        seg_stats.sort_values("CA", ascending=False).head(10),
        column_config={
            "Segment": "Segment",
            "Clients": st.column_config.NumberColumn("Clients", format="%d"),
            "CA": st.column_config.NumberColumn("CA ($)", format="$%.0f")
        },
        hide_index=True, use_container_width=True
    )

# ==========================================================
# SECTION 4 : DÉTECTION D'ANOMALIES (Simple)
# ==========================================================
st.subheader("🚨 Détection d'Anomalies sur le CA Journalier")

# Utilisation de l'écart-type pour identifier les jours exceptionnels
daily = filtered.groupby("ORDER_DATE")["TOTAL_AMOUNT"].sum().reset_index()
mean_rev = daily["TOTAL_AMOUNT"].mean()
std_rev = daily["TOTAL_AMOUNT"].std()
daily["Z_Score"] = (daily["TOTAL_AMOUNT"] - mean_rev) / std_rev
anomalies = daily[abs(daily["Z_Score"]) > 2]

# Graphique avec points rouges pour anomalies
base_anom = alt.Chart(daily).encode(x=alt.X("ORDER_DATE:T", title=""))
line_anom = base_anom.mark_line(color=PALETTE[0]).encode(y="TOTAL_AMOUNT:Q")
points_anom = base_anom.mark_circle(size=80, color=PALETTE[3]).encode(
    y="TOTAL_AMOUNT:Q",
    tooltip=["ORDER_DATE", alt.Tooltip("TOTAL_AMOUNT", format="$,.0f"), alt.Tooltip("Z_Score", format=".2f")]
).transform_filter(alt.datum.Z_Score > 2)

st.altair_chart((line_anom + points_anom).properties(height=300, title="Anomalies (Z-Score > 2)"), use_container_width=True)
if not anomalies.empty:
    st.caption(f"{len(anomalies)} jour(s) atypique(s) détecté(s). Vérifiez les promotions ou ruptures de stock.")
else:
    st.caption("Aucune anomalie majeure détectée sur la période.")