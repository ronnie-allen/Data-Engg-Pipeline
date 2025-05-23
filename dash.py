import streamlit as st
import pandas as pd
from urllib.parse import quote_plus
import plotly.express as px
from pymongo import MongoClient

# DNS Override to fix resolution errors
import dns.resolver
dns.resolver.default_resolver = dns.resolver.Resolver()
dns.resolver.default_resolver.nameservers = ['8.8.8.8', '1.1.1.1']

# MongoDB Connection
username = quote_plus("ronnieallen")
password = quote_plus("ronnie")

uri = f"mongodb+srv://{username}:{password}@ia3-data-engg.dtimim2.mongodb.net/?retryWrites=true&w=majority&appName=ia3-data-engg"
client = MongoClient(uri)
db = client["WaterDataDB"]
collection = db["WaterQuality"]

# App Config
st.set_page_config(page_title="Water Quality Dashboard", layout="wide")
st.title("💧 Water Quality Monitoring Dashboard")

# ---------- ADD DATA FORM ----------
with st.expander("➕ Add New Water Quality Record"):
    with st.form("add_record"):
        col1, col2, col3 = st.columns(3)

        with col1:
            station_code = st.text_input("Station Code")
            state = st.text_input("State")
            year = st.number_input("Year", min_value=2000, max_value=2100, step=1)

        with col2:
            location = st.text_input("Location")
            temp = st.number_input("Temperature (°C)", value=25.0)
            ph = st.number_input("pH", value=7.0)

        with col3:
            do = st.number_input("D.O. (mg/l)", value=6.5)
            conductivity = st.number_input("Conductivity (µmhos/cm)", value=200)
            nitrate = st.number_input("Nitrate+Nitrite (mg/l)", value=0.1)

        fecal = st.number_input("Fecal Coliform (MPN/100ml)", value=10)
        total_coliform = st.number_input("Total Coliform (MPN/100ml)", value=25)
        bod = st.number_input("B.O.D. (mg/l)", value=2.0)

        submitted = st.form_submit_button("Add Record")

        if submitted:
            record = {
                "STATION CODE": station_code,
                "LOCATIONS": location,
                "STATE": state,
                "Temp": temp,
                "PH": ph,
                "D.O. (mg/l)": do,
                "CONDUCTIVITY (µmhos/cm)": conductivity,
                "B.O.D. (mg/l)": bod,
                "NITRATENAN N+ NITRITENANN (mg/l)": nitrate,
                "FECAL COLIFORM (MPN/100ml)": fecal,
                "TOTAL COLIFORM (MPN/100ml)Mean": total_coliform,
                "year": year
            }
            collection.insert_one(record)
            st.success("✅ New record added to the database!")

# ---------- FETCH DATA ----------
data = list(collection.find({}, {"_id": 0}))
df = pd.DataFrame(data)

# ---------- DATA CLEANUP ----------
numeric_cols = [
    'Temp', 'D.O. (mg/l)', 'PH', 'CONDUCTIVITY (µmhos/cm)',
    'B.O.D. (mg/l)', 'NITRATENAN N+ NITRITENANN (mg/l)',
    'FECAL COLIFORM (MPN/100ml)', 'TOTAL COLIFORM (MPN/100ml)Mean'
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

if 'year' in df.columns:
    df['year'] = pd.to_numeric(df['year'], errors='coerce')

# ... [KEEP THE PREVIOUS IMPORTS AND CONNECTION SETUP UNCHANGED]

# ---------- FILTERS (Only states in sidebar now) ----------
st.sidebar.header("📌 Filters")
states = sorted(df['STATE'].dropna().unique()) if 'STATE' in df else []
selected_state = st.sidebar.selectbox("Select State", states) if len(states) > 0 else None

# ---------- FILTERED DATA ----------
filtered_df = df.copy()
if selected_state is not None:
    filtered_df = filtered_df[filtered_df['STATE'] == selected_state]

# ---------- SELECT YEAR AFTER STATE ----------
years = sorted(filtered_df['year'].dropna().unique()) if 'year' in filtered_df else []
selected_year = st.selectbox("Select Year", years) if len(years) > 0 else None

if selected_year is not None:
    filtered_df = filtered_df[filtered_df['year'] == selected_year]

# ---------- SUMMARY & VISUALS ----------
if not filtered_df.empty:
    st.subheader(f"📊 Summary for {selected_state} in {selected_year}")
    st.metric("Average pH", round(filtered_df['PH'].mean(), 2))
    st.metric("Avg Temperature (°C)", round(filtered_df['Temp'].mean(), 2))
    st.metric("Avg D.O. (mg/l)", round(filtered_df['D.O. (mg/l)'].mean(), 2))

    # ---------- CHARTS ----------
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.bar(
            filtered_df, x="LOCATIONS", y="PH", title="pH Level by Location",
            color="PH", color_continuous_scale="Blues"
        ), use_container_width=True)

    with col2:
        st.plotly_chart(px.bar(
            filtered_df, x="LOCATIONS", y="D.O. (mg/l)", title="Dissolved Oxygen by Location",
            color="D.O. (mg/l)", color_continuous_scale="Greens"
        ), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(px.bar(
            filtered_df, x="LOCATIONS", y="B.O.D. (mg/l)", title="B.O.D. by Location",
            color="B.O.D. (mg/l)", color_continuous_scale="Oranges"
        ), use_container_width=True)

    with col4:
        st.plotly_chart(px.bar(
            filtered_df, x="LOCATIONS", y="CONDUCTIVITY (µmhos/cm)", title="Conductivity by Location",
            color="CONDUCTIVITY (µmhos/cm)", color_continuous_scale="Purples"
        ), use_container_width=True)

    # Scatter comparison for Coliforms
    st.plotly_chart(px.scatter(
        filtered_df,
        x="FECAL COLIFORM (MPN/100ml)",
        y="TOTAL COLIFORM (MPN/100ml)Mean",
        color="LOCATIONS",
        size="PH",
        title="Fecal vs Total Coliform",
        labels={"FECAL COLIFORM (MPN/100ml)": "Fecal Coliform", "TOTAL COLIFORM (MPN/100ml)Mean": "Total Coliform"}
    ), use_container_width=True)

# ---------- TREND ANALYSIS ----------
if 'year' in df:
    st.subheader("📈 Parameter Trends Over the Years")
    trend_cols = ["PH", "D.O. (mg/l)", "B.O.D. (mg/l)", "Temp"]
    melted = df[df["STATE"] == selected_state][["year"] + trend_cols].melt(id_vars="year")
    fig_trend = px.line(
        melted, x="year", y="value", color="variable", markers=True,
        title=f"Yearly Trend of Water Quality Parameters - {selected_state}"
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# ---------- RAW DATA ----------
st.subheader("🔍 Raw Data")
st.dataframe(filtered_df if not filtered_df.empty else df, use_container_width=True)
