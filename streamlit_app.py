import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import ift6758.client as client

"""
General template for your streamlit app. 
Feel free to experiment with layout and adding functionality!
Just make sure that the required functionality is included as well
"""

# Get the service URL from environment variables
MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://localhost:5000")

serving_client = client.ServingClient()
st.title("Live Game Dashboard")

with st.sidebar:
    workspace = st.write('Workspace: IFT6758.2024-B08')
    model = st.selectbox("Model", ["Logarithmic(Distance)", "Logarithmic(Distance and Angle)"])
    version = st.selectbox("Version", ["latest"])
    if st.button("Download model"):
        # Code to download the model from CometML

        if model == "Logarithmic(Distance)":
            serving_client.download_registry_model(workspace = 'IFT6758.2024-B08',model='lg_distance',version=version)
        else:
            serving_client.download_registry_model(workspace = 'IFT6758.2024-B08',model='lg_angle_distance',version=version)
       
        st.success("Model downloaded successfully")

with st.container():
    game_id = st.text_input("Game ID")
    if st.button("Ping game"):
        # Code to ping the game client and get game data
        # Example:
        # X, idx, ... = game_client.ping_game(game_id, idx, ...)
        # r = requests.post("http://127.0.0.1:<PORT>/predict", json=json.loads(X.to_json()))
        # predictions = r.json()
        # Display game info and predictions
        st.write("Home Team: ...")
        st.write("Away Team: ...")
        st.write("Period: ...")
        st.write("Time Left: ...")
        # Display sum of expected goals for each team
        st.write("Expected Goals - Home Team: ...")
        st.write("Expected Goals - Away Team: ...")

with st.container():
    # TODO: Add data used for predictions
    pass