import streamlit as st
from fetch_data import fetch_games
import plotly.express as px
import numpy as np
import pandas as pd

st.set_page_config(page_title="Chess.com Game Analyzer", layout="wide")

st.title("♟️ Chess.com Game Analyzer")

# User input
username = st.text_input("Enter Chess.com username:", "mikayil94")

col1, col2 = st.columns(2)
with col1:
    start_date = st.text_input("Start date (YYYY-MM):", "2025-01")
with col2:
    end_date = st.text_input("End date (YYYY-MM):", "2025-12")

time_class = st.selectbox("Select time control:", ["all", "bullet", "blitz", "rapid", "daily"])

if st.button("Fetch Games"):
    with st.spinner("Fetching data..."):
        try:
            df = fetch_games(username, start_date, end_date, time_class_filter=time_class)
            st.success(f"Fetched {len(df)} games.")
            st.dataframe(df)

            # Add visualizations
            st.subheader("📊 Opening Performance")
            st.info(
                "The charts below show your top 10 most played openings as White and Black.\n\n"
                "These are determined based on the number of games played. "
                "They are then sorted by your win percentage to help identify which openings you perform best with.\n\n"
                "The format displayed is: **Opening Name (ECO Code)**."
            )

            # Assign color and win columns
            df["color"] = np.where(df["white"].str.lower() == username.lower(), "White", "Black")
            df["win"] = np.where(df["result"] == "Win", 1, 0)
            df["opening_name"] = df["opening_name"] + " (" + df["opening_code"] + ")"

            # Function to compute top openings with win % for a color
            def get_opening_stats(df_color, color_label):
                top_openings = df_color["opening_name"].value_counts().head(10).index
                filtered = df_color[df_color["opening_name"].isin(top_openings)]
                stats = (
                    filtered.groupby("opening_name")["win"]
                    .agg(["count", "sum"])
                    .reset_index()
                    .rename(columns={"count": "games", "sum": "wins"})
                )
                stats["win_rate"] = 100 * stats["wins"] / stats["games"]
                stats["color"] = color_label
                return stats.sort_values("win_rate", ascending=False)

            # Compute and plot
            white_stats = get_opening_stats(df[df["color"] == "White"], "White")
            black_stats = get_opening_stats(df[df["color"] == "Black"], "Black")

            fig_white_opening = px.bar(white_stats, y="opening_name", x="win_rate", orientation="h",
                                       title="Top 10 Openings as White (by Win %)",
                                       labels={"opening_name": "Opening", "win_rate": "Win %"},
                                       hover_data=["games"])
            fig_white_opening.update_layout(yaxis=dict(categoryorder='total ascending'))
            st.plotly_chart(fig_white_opening, use_container_width=True)

            fig_black_opening = px.bar(black_stats, y="opening_name", x="win_rate", orientation="h",
                                       title="Top 10 Openings as Black (by Win %)",
                                       labels={"opening_name": "Opening", "win_rate": "Win %"},
                                       hover_data=["games"])
            fig_black_opening.update_layout(yaxis=dict(categoryorder='total ascending'))
            st.plotly_chart(fig_black_opening, use_container_width=True)

            # Win rate by time control
            st.subheader("⏱️ Win Percentage by Time Control")

            time_stats = (
                df.groupby("time_class")["win"]
                .agg(["count", "sum"])
                .reset_index()
                .rename(columns={"count": "games", "sum": "wins"})
            )
            time_stats["win_rate"] = 100 * time_stats["wins"] / time_stats["games"]

            for _, row in time_stats.iterrows():
                st.markdown(
                    f"<span style='font-size:16px'><strong>{row['time_class'].capitalize()}:</strong> {row['win_rate']:.1f}% win rate</span>",
                    unsafe_allow_html=True
                )

            # Elo rating over time
            st.subheader("📈 Elo Rating Over Time")

            # Determine user color and corresponding Elo
            df["user_elo"] = np.where(df["white"].str.lower() == username.lower(), df["white_elo"], df["black_elo"])

            # Convert 'date' to datetime format
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

            # Filter valid dates
            df = df.dropna(subset=["date", "user_elo"])

            # Sort by date
            df = df.sort_values("date")

            # Line plot of Elo over time grouped by time control
            fig_elo = px.line(df, x="date", y="user_elo", color="time_class",
                              title="Elo Rating Over Time by Time Control",
                              labels={"date": "Date", "user_elo": "Elo", "time_class": "Time Control"})
            st.plotly_chart(fig_elo, use_container_width=True)
        except Exception as e:
            st.error(f"Error fetching data: {e}")
