import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gspread
from google.oauth2.service_account import Credentials
import json
import os

# --- Set Up Page ---
st.set_page_config(page_title="Vehicle Booking Calendar (Turo)", layout="wide")

# --- Load Google Sheets Credentials from Streamlit Secrets ---
if "google_sheets" not in st.secrets:
    st.error("Google Sheets credentials are missing. Please check Streamlit Secrets.")
    st.stop()

google_sheets_secrets = json.loads(st.secrets["google_sheets"])
credentials = Credentials.from_service_account_info(google_sheets_secrets, scopes=["https://www.googleapis.com/auth/spreadsheets"])
client = gspread.authorize(credentials)

# --- Google Sheets Information ---
SHEET_ID = "19lV8X78x7sXJNdgKNqMhZuLdZRk4wnvMS3__mIFqStQ"
SHEET_NAME = "Turo Data"  # Modify if you named the sheet differently

# --- Load Data from Google Sheets ---
def load_data():
    try:
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error loading data from Google Sheets: {e}")
        return pd.DataFrame()

# --- Save Data to Google Sheets ---
def save_data(df):
    try:
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
        st.success("✅ Data saved successfully to Google Sheets!")
    except Exception as e:
        st.error(f"❌ Failed to save data: {e}")

# --- Streamlit UI ---
st.title("📅 Vehicle Booking Calendar (Turo)")

# --- Upload CSV Section ---
tab1, tab2 = st.tabs(["📂 Upload CSV Files", "📅 View Calendar"])

with tab1:
    st.header("📂 Upload CSV Files")
    uploaded_files = st.file_uploader("Upload your Turo CSV exports", type=["csv"], accept_multiple_files=True)

    if uploaded_files:
        df_list = [pd.read_csv(file) for file in uploaded_files]
        df = pd.concat(df_list)
        df["Trip start"] = pd.to_datetime(df["Trip start"], errors="coerce")
        df["Trip end"] = pd.to_datetime(df["Trip end"], errors="coerce")
        df["Total earnings"] = df["Total earnings"].replace("[\$,]", "", regex=True).astype(float)
        save_data(df)  # Save to Google Sheets

# --- View Calendar Section ---
with tab2:
    st.header("📅 View Calendar")
    df = load_data()

    if df.empty:
        st.warning("No data available. Please upload CSV files first.")
    else:
        selected_vehicle = st.selectbox("Select a Vehicle:", df["Vehicle"].unique())
        selected_month = st.selectbox("Select a Month:", sorted(df["Trip start"].dt.strftime("%Y-%m").unique()))

        filtered_df = df[(df["Vehicle"] == selected_vehicle) & (df["Trip start"].dt.strftime("%Y-%m") == selected_month)]
        
        fig, ax = plt.subplots(figsize=(10, 4))
        for _, row in filtered_df.iterrows():
            ax.barh(row["Vehicle"], (row["Trip end"] - row["Trip start"]).days, left=row["Trip start"].day)
        ax.set_xlabel("Days of the Month")
        ax.set_title(f"Booking Calendar for {selected_vehicle} ({selected_month})")
        st.pyplot(fig)
 
