import streamlit as st
import pandas as pd
import altair as alt
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Retail Analytics", page_icon="📊", layout="wide")
session = get_active_session()

COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
          "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]

@st.cache_data(ttl=600)
def load_fact():
    return session.sql("""
        SELECT ORDER_ID, CUSTOMER_ID, PRODUCT_ID, ORDER_DATE,
               QUANTITY, UNIT_PRICE, TOTAL_AMOUNT, YEAR, QUARTER
        FROM RETAIL_ANALYTICS.GOLD.FACT_SALES
    """).to_pandas()

@st.cache_data(ttl=600)
def load_customers():
    return session.sql("""
        SELECT CUSTOMER_ID, FIRST_NAME, LAST_NAME, COUNTRY, CITY
        FROM RETAIL_ANALYTICS.GOLD.DIM_CUSTOMER
    """).to_pandas()

@st.cache_data(ttl=600)
def load_products():
    return session.sql("""
        SELECT PRODUCT_ID, PRODUCT_NAME, CATEGORY, UNIT_PRICE
        FROM RETAIL_ANALYTICS.GOLD.DIM_PRODUCT
    """).to_pandas()

with st.spinner("Chargement..."):
    fact = load_fact()
    customers = load_customers()
    products = load_products()

fact["ORDER_DATE"] = pd.to_datetime(fact["ORDER_DATE"])
df_all = fact.merge(customers, on="CUSTOMER_ID", how="left") \
             .merge(products, on="PRODUCT_ID", how="left", suffixes=("", "_prod"))

# Filtres
st.sidebar.header("🔎 Filtres")
years = sorted(df_all["YEAR"].dropna().unique().tolist())
sel_years = st.sidebar.multiselect("Année", years, default=years)
quarters = sorted(df_all["QUARTER"].dropna().unique().tolist())
sel_quarters = st.sidebar.multiselect("Trimestre", quarters, default=quarters)
countries = sorted(df_all["COUNTRY"].dropna().unique().tolist())
sel_countries = st.sidebar.multiselect("Pays", countries, default=countries)
categories = sorted(df_all["CATEGORY"].dropna().unique().tolist())
sel_categories = st.sidebar.multiselect("Catégorie", categories, default=categories)

mask = (df_all["YEAR"].isin(sel_years) & df_all["QUARTER"].isin(sel_quarters)
        & df_all["COUNTRY"].isin(sel_countries) & df_all["CATEGORY"].isin(sel_categories))
df = df_all[mask].copy()

if df.empty:
    st.warning("Aucune donnée pour ces filtres.")
    st.stop()

st.title("📊 Retail Analytics — Executive Dashboard")
st.caption(f"{df['ORDER_DATE'].min():%d/%m/%Y} → {df['ORDER_DATE'].max():%d/%m/%Y} | "
           f"{df['ORDER_ID'].nunique():,} commandes")

# KPI
total_sales = df["TOTAL_AMOUNT"].sum()
total_orders = df["ORDER_ID"].nunique()
total_units = df["QUANTITY"].sum()
avg_basket = total_sales / total_orders if total_orders else 0
total_customers = df["CUSTOMER_ID"].nunique()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 CA total", f"${total_sales:,.0f}")
c2.metric("🧾 Commandes", f"{total_orders:,}")
c3.metric("📦 Unités", f"{total_units:,}")
c4.metric("🛒 Panier moyen", f"${avg_basket:,.2f}")
c5.metric("👥 Clients", f"{total_customers:,}")

st.divider()

# Ligne 1 : tendance + catégories
col1, col2 = st.columns((2, 1))

with col1:
    st.subheader("📈 Ventes mensuelles")
    monthly = (df.groupby(df["ORDER_DATE"].dt.to_period("M").astype(str))
                 .agg(CA=("TOTAL_AMOUNT", "sum"), Commandes=("ORDER_ID", "nunique"))
                 .reset_index().rename(columns={"ORDER_DATE": "Mois"}))
    st.line_chart(monthly.set_index("Mois")[["CA"]], color="#1f77b4")
    st.bar_chart(monthly.set_index("Mois")[["Commandes"]], color="#ff7f0e")

with col2:
    st.subheader("🥧 Par catégorie")
    cat_sales = df.groupby("CATEGORY")["TOTAL_AMOUNT"].sum().reset_index()
    donut = alt.Chart(cat_sales).mark_arc(innerRadius=60).encode(
        theta=alt.Theta("TOTAL_AMOUNT:Q"),
        color=alt.Color("CATEGORY:N", scale=alt.Scale(range=COLORS)),
        tooltip=["CATEGORY", alt.Tooltip("TOTAL_AMOUNT", format="$,.0f")]
    ).properties(height=350)
    st.altair_chart(donut, use_container_width=True)

# Ligne 2 : top produits + top clients
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 Top 10 produits")
    top_p = (df.groupby(["PRODUCT_NAME", "CATEGORY"])["TOTAL_AMOUNT"].sum()
               .reset_index().sort_values("TOTAL_AMOUNT").tail(10))
    bars = alt.Chart(top_p).mark_bar().encode(
        x=alt.X("TOTAL_AMOUNT:Q", title="CA ($)"),
        y=alt.Y("PRODUCT_NAME:N", sort="-x", title=""),
        color=alt.Color("CATEGORY:N", scale=alt.Scale(range=COLORS)),
        tooltip=["PRODUCT_NAME", "CATEGORY", alt.Tooltip("TOTAL_AMOUNT", format="$,.0f")]
    ).properties(height=400)
    st.altair_chart(bars, use_container_width=True)

with col2:
    st.subheader("👑 Top 10 clients")
    top_c = (df.groupby(["CUSTOMER_ID", "FIRST_NAME", "LAST_NAME", "COUNTRY"])
               .agg(CA=("TOTAL_AMOUNT", "sum")).reset_index()
               .sort_values("CA").tail(10))
    top_c["Client"] = top_c["FIRST_NAME"] + " " + top_c["LAST_NAME"]
    bars = alt.Chart(top_c).mark_bar().encode(
        x=alt.X("CA:Q", title="CA ($)"),
        y=alt.Y("Client:N", sort="-x", title=""),
        color=alt.Color("COUNTRY:N", scale=alt.Scale(range=COLORS)),
        tooltip=["Client", "COUNTRY", alt.Tooltip("CA", format="$,.0f")]
    ).properties(height=400)
    st.altair_chart(bars, use_container_width=True)

# Ligne 3 : pays + distribution panier
col1, col2 = st.columns(2)

with col1:
    st.subheader("🌍 CA par pays")
    country = df.groupby("COUNTRY")["TOTAL_AMOUNT"].sum().reset_index().sort_values("TOTAL_AMOUNT", ascending=False)
    st.bar_chart(country.set_index("COUNTRY")[["TOTAL_AMOUNT"]], color="#2ca02c")

with col2:
    st.subheader("💵 Distribution du panier")
    basket = df.groupby("ORDER_ID")["TOTAL_AMOUNT"].sum().reset_index()
    hist = alt.Chart(basket).mark_bar(color="#2ca02c").encode(
        x=alt.X("TOTAL_AMOUNT:Q", bin=alt.Bin(maxbins=30), title="Montant commande ($)"),
        y=alt.Y("count():Q", title="Nb commandes"),
        tooltip=[alt.Tooltip("count():Q", title="Commandes")]
    ).properties(height=350)
    median_val = basket["TOTAL_AMOUNT"].median()
    rule = alt.Chart(pd.DataFrame({"m": [median_val]})).mark_rule(
        color="#ff7f0e", strokeDash=[5, 5]
    ).encode(x="m:Q")
    st.altair_chart(hist + rule, use_container_width=True)
    st.caption(f"Médiane : ${median_val:,.0f}")

# Tableau détaillé
st.subheader("📋 Top 100 ventes")
detail = (df.sort_values("TOTAL_AMOUNT", ascending=False).head(100)
            [["ORDER_ID", "ORDER_DATE", "FIRST_NAME", "LAST_NAME", "COUNTRY",
              "PRODUCT_NAME", "CATEGORY", "QUANTITY", "UNIT_PRICE", "TOTAL_AMOUNT"]]
            .rename(columns={"ORDER_ID": "Commande", "ORDER_DATE": "Date",
                             "FIRST_NAME": "Prénom", "LAST_NAME": "Nom",
                             "COUNTRY": "Pays", "PRODUCT_NAME": "Produit",
                             "CATEGORY": "Catégorie", "QUANTITY": "Qté",
                             "UNIT_PRICE": "Prix", "TOTAL_AMOUNT": "Total"}))
st.dataframe(detail, use_container_width=True, hide_index=True)

st.caption("Dashboard sans dépendance PyPI — Streamlit natif + Altair uniquement.")