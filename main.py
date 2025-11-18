import streamlit as st

st.title("AthleteIQ – World League Edition")

st.write("Use API to fetch team data.")

import requests
import pandas as pd

st.subheader("Search Team via TheSportsDB API")
team_query = st.text_input("Enter Team Name", "Arsenal")

if st.button("Search Team"):
    url = f"https://www.thesportsdb.com/api/v1/json/123/searchteams.php?t={team_query}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data and data.get("teams"):
            df = pd.DataFrame(data["teams"])
            st.dataframe(df)
        else:
            st.warning("Team not found.")
    else:
        st.error("Failed to fetch data from API.")("This is a basic Streamlit template. Add DLL logic and API integration here.")

menu = st.sidebar.selectbox("Menu", ["Home", "Add Match", "View Schedule", "Update Score"])

if menu == "Home":
    st.header("Welcome to AthleteIQ")
    st.write("Manage world league schedules using Double Linked List.")

elif menu == "Add Match":
    st.header("Add New Match")
    team_a = st.text_input("Team A")
    team_b = st.text_input("Team B")
    date = st.date_input("Match Date")
    location = st.text_input("Location")
    if st.button("Add Match"):
        st.success(f"Match {team_a} vs {team_b} added!")

elif menu == "View Schedule":
    st.header("Match Schedule (DLL Visualization Placeholder)")
    st.info("DLL traversal visualization will appear here.")

elif menu == "Update Score":
    st.header("Update Match Score")
    match_id = st.text_input("Match ID")
    score_a = st.number_input("Score Team A", min_value=0)
    score_b = st.number_input("Score Team B", min_value=0)
    if st.button("Update Score"):
        st.success(f"Score updated: {score_a} - {score_b}")