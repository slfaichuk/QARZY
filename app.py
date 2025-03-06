import streamlit as st

# Debug: Check if we can read secrets
st.write("🔍 Checking Streamlit Secrets...")

if "google" in st.secrets:
    st.success("✅ Streamlit Secrets are loaded correctly!")
    st.json(st.secrets["google"])  # Display secrets to confirm they are available
else:
    st.error("❌ Streamlit Secrets are NOT found!")

import streamlit as st
import pandas as pd
import calendar
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# --- Streamlit Page Setup ---
st.set_page_config(page_title="Turo Vehicle Calendar", layout="wide")

st.title("📅 Vehicle Booking Calendar (Turo)")

# --- Sidebar for Navigation ---
tab1, tab2 = st.tabs(["📂 Upload CSV Files", "📆 View Calendar"])

# --- CSV Upload Section (in a separate tab) ---
with tab1:
    st.header("📂 Upload CSV Files")
    uploaded_files = st.file_uploader("Upload your Turo CSV exports", type=["csv"], accept_multiple_files=True)
    
    if uploaded_files:
        st.success("✅ Files uploaded successfully! Switch to 'View Calendar' tab.")

# --- Calendar Section ---
with tab2:
    if uploaded_files:
        # Read all CSV files and combine into one DataFrame
        df_list = [pd.read_csv(file) for file in uploaded_files]
        df = pd.concat(df_list)

        # Convert date columns to datetime
        df["Trip start"] = pd.to_datetime(df["Trip start"], errors='coerce')
        df["Trip end"] = pd.to_datetime(df["Trip end"], errors='coerce')
        df["Total earnings"] = df["Total earnings"].replace('[\$,]', '', regex=True).astype(float)

        # --- Filters ---
        vehicles = df["Vehicle"].unique()
        selected_vehicle = st.sidebar.selectbox("🚗 Select a Vehicle", vehicles)

        years = df["Trip start"].dt.year.unique()
        selected_year = st.sidebar.selectbox("📅 Select a Year", years, index=len(years)-1)

        months = list(calendar.month_name[1:])
        selected_month = st.sidebar.selectbox("📆 Select a Month", months, index=2)
        month_num = months.index(selected_month) + 1

        # --- Fix Filtering Logic ---
        filtered_df = df[
            (df["Vehicle"] == selected_vehicle) &
            (~df["Trip status"].isin(["Guest cancellation", "Host cancellation"])) &  # Ignore cancellations
            (
                (df["Trip start"].dt.year == selected_year) & (df["Trip start"].dt.month == month_num) |  # Trip starts in the month
                (df["Trip end"].dt.year == selected_year) & (df["Trip end"].dt.month == month_num) |  # Trip ends in the month
                ((df["Trip start"] < pd.Timestamp(selected_year, month_num, 1)) &  # Trip started before this month
                 (df["Trip end"] > pd.Timestamp(selected_year, month_num, calendar.monthrange(selected_year, month_num)[1])))  # Trip ends after this month
            )
        ]

        # --- Calendar Display ---
        st.write(f"### 📅 {selected_vehicle} - {selected_month} {selected_year}")

        cal = calendar.monthcalendar(selected_year, month_num)
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_xticks(range(7))
        ax.set_xticklabels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])

        # Define colors for different statuses
        status_colors = {
            "Completed": "lightblue",
            "In-progress": "lightgreen",
            "Booked": "yellow"
        }

        # Loop through calendar days
        for week_idx, week in enumerate(cal):
            for day_idx, day in enumerate(week):
                if day == 0:
                    continue  # Skip empty days

                day_date = pd.Timestamp(selected_year, month_num, day)
                day_trips = filtered_df[(filtered_df["Trip start"] <= day_date) & (filtered_df["Trip end"] >= day_date)]

                if not day_trips.empty:
                    # If multiple bookings exist on the same day, split the cell
                    num_trips = len(day_trips)
                    for i, (_, trip) in enumerate(day_trips.iterrows()):
                        total_days = (trip["Trip end"] - trip["Trip start"]).days + 1
                        daily_price = trip["Total earnings"] / total_days  # Divide earnings over trip duration
                        color = status_colors.get(trip["Trip status"], "white")

                        # Adjust cell for multiple bookings
                        y_offset = (i / num_trips) if num_trips > 1 else 0
                        height = (1 / num_trips) if num_trips > 1 else 1

                        ax.add_patch(plt.Rectangle((day_idx, week_idx + y_offset), 1, height, color=color, edgecolor="black"))
                        ax.text(day_idx + 0.5, week_idx + y_offset + (height / 2), f"${daily_price:.2f}", ha="center", va="center", fontsize=9)

        ax.set_xlim(0, 7)
        ax.set_ylim(len(cal), 0)
        plt.title(f"Booking Calendar - {selected_vehicle} ({selected_month}/{selected_year})")
        plt.grid(axis="x", linestyle="--", alpha=0.7)
        st.pyplot(fig)

        # --- Legend for Colors ---
        st.write("### Booking Status Legend")
        legend_patches = [
            mpatches.Patch(color="lightblue", label="Completed"),
            mpatches.Patch(color="lightgreen", label="In-progress"),
            mpatches.Patch(color="yellow", label="Booked")
        ]
        fig_legend, ax_legend = plt.subplots(figsize=(4, 1))
        ax_legend.legend(handles=legend_patches, loc="center")
        ax_legend.axis("off")
        st.pyplot(fig_legend)

    else:
        st.warning("🔺 Please upload CSV files in the 'Upload CSV Files' tab first.")
