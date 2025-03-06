 import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import calendar
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import datetime

# --- Load Google Sheets credentials from Streamlit Secrets ---
def get_google_creds():
    credentials_info = st.secrets["google"]
    return Credentials.from_service_account_info(credentials_info)

# --- Google Sheets Setup ---
SHEET_ID = "19lV8X78x7sXJNdgKNqMhZuLdZRk4wnvMS3__mIFqStQ"  # Your real Google Sheet ID
SHEET_NAME = "Sheet1"

def load_data():
    try:
        creds = get_google_creds()
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"❌ Failed to load data: {e}")
        return pd.DataFrame()

def save_data(df):
    try:
        creds = get_google_creds()
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
        st.success("✅ Data saved successfully to Google Sheets!")
    except Exception as e:
        st.error(f"❌ Failed to save data: {e}")

# --- Streamlit Page Setup ---
st.set_page_config(page_title="Turo Vehicle Calendar", layout="wide")
st.title("📅 Vehicle Booking Calendar (Turo)")

# --- Sidebar for Navigation ---
tab1, tab2 = st.tabs(["📂 Upload CSV Files", "📅 View Calendar"])

# --- CSV Upload Section ---
with tab1:
    st.header("📂 Upload CSV Files")
    uploaded_files = st.file_uploader("Upload your Turo CSV exports", type=["csv"], accept_multiple_files=True)

    if uploaded_files:
        df_list = [pd.read_csv(file) for file in uploaded_files]
        df = pd.concat(df_list)

        # Convert date columns to datetime
        df["Trip start"] = pd.to_datetime(df["Trip start"], errors="coerce")
        df["Trip end"] = pd.to_datetime(df["Trip end"], errors="coerce")
        df["Total earnings"] = df["Total earnings"].replace('[\$,]', '', regex=True).astype(float)

        # Save to Google Sheets
        save_data(df)

        st.success("✅ Files uploaded successfully! Switch to 'View Calendar' tab.")

# --- Calendar Section ---
with tab2:
    df = load_data()

    if not df.empty:
        # Filter for a specific vehicle
        vehicle_options = df["Vehicle"].unique()
        selected_vehicle = st.selectbox("🚗 Select a Vehicle:", vehicle_options)

        # Filter for a specific month
        today = datetime.date.today()
        months = [calendar.month_name[i] for i in range(1, 13)]
        selected_month = st.selectbox("📅 Select Month:", months, index=today.month - 1)

        # Get year dynamically
        selected_year = today.year

        # Filter data
        df_filtered = df[(df["Vehicle"] == selected_vehicle)]
        df_filtered = df_filtered[(df_filtered["Trip start"].dt.year == selected_year) & 
                                  (df_filtered["Trip start"].dt.month == months.index(selected_month) + 1)]

        # Create Calendar
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_xticks(range(1, 32))
        ax.set_yticks([])
        ax.set_xticklabels(range(1, 32))

        # Define colors for statuses
        color_map = {
            "Completed": "lightblue",
            "In-progress": "green",
            "Booked": "yellow"
        }

        # Plot each trip
        for _, row in df_filtered.iterrows():
            trip_start = row["Trip start"].day
            trip_end = row["Trip end"].day
            color = color_map.get(row["Status"], "white")

            ax.barh(0, trip_end - trip_start + 1, left=trip_start, color=color, edgecolor="black")

            # Show price inside the bar
            daily_rate = row["Total earnings"] / (trip_end - trip_start + 1)
            for day in range(trip_start, trip_end + 1):
                ax.text(day, 0, f"${daily_rate:.0f}", ha="center", va="center", fontsize=8, color="black")

        # Add legend
        legend_patches = [mpatches.Patch(color=color, label=status) for status, color in color_map.items()]
        ax.legend(handles=legend_patches, loc="upper right")

        st.pyplot(fig)

    else:
        st.warning("⚠️ No data available. Please upload CSV files first.")
