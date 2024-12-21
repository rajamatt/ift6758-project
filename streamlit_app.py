import streamlit as st
import pandas as pd
import numpy as np
import requests
from wandb import Api
import pickle
import requests
import os
import ift6758.client as client

st.title("Live Game Dashboard")
api = Api()
MODEL_DIR = 'models'
API_URL = 'https://api-web.nhle.com'
PLAY_BY_PLAY_ENDPOINT = '/v1/gamecenter/{game-id}/play-by-play'
api_key = os.getenv('WANDB_API_KEY', None)
if not api_key:
    st.text("WANDB_API_KEY is not set. Please set your WandB API key in the environment variables.")

# Initialize session state for model, game client, and game data
if 'model' not in st.session_state:
    st.session_state.model = None
if 'game_client' not in st.session_state:
    st.session_state.game_client = client.GameClient()
if 'game_data' not in st.session_state:
    st.session_state.game_data = pd.DataFrame()

with st.sidebar:
    st.write('Workspace: IFT6758.2024-B08')
    workspace = 'IFT6758.2024-B08'
    model_version = st.selectbox("Model", ["Logarithmic(Distance)", "Logarithmic(Distance and Angle)"])
    if model_version == "Logarithmic(Distance)":
        model_version = "lg_distance"
    else:
        model_version = "lg_distance_angle"
    version = st.selectbox("Version", ["latest"])
    if st.button("Download model"):
        try:
            model_path = os.path.join(MODEL_DIR, f"{model_version}.pkl")
            if os.path.exists(model_path):
                st.session_state.model = pickle.load(open(model_path, 'rb'))
            else:
                artifact = api.artifact(f"team08/{workspace}/{model_version}:{version}")
                artifact_dir = artifact.download(MODEL_DIR)
                model_file_path = os.path.join(artifact_dir, f"{model_version}.pkl")
                st.session_state.model = pickle.load(open(model_file_path, 'rb'))
            st.success(f"Model loaded successfully")
                
        except Exception as e:
            st.session_state.model = None
            st.write(f"Failed to download/load model {model_version} version {version}: {e}")

with st.container():
    game_id = st.text_input("Game ID")
    try:
        pbp_endpoint = PLAY_BY_PLAY_ENDPOINT.replace('{game-id}', game_id)
        full_endpoint = API_URL + pbp_endpoint
        response = requests.get(full_endpoint)
        if response.status_code == 200:
            json_data = response.json()
        home_score = json_data['homeTeam']['score']
        away_score = json_data['awayTeam']['score']
        home_team = json_data['homeTeam']['commonName']['default']
        away_team = json_data['awayTeam']['commonName']['default']
    except:
        st.text("Enter a valid Game ID")
    
    
    if st.button("Ping game"):
        if st.session_state.model:
            # Code to ping the game client and get game data
            # Display game info and predictions
            new_data = st.session_state.game_client.get_new_events(game_id)
            if not new_data.empty:
                if model_version == "lg_distance":
                    new_data['goal_probability'] = st.session_state.model.predict_proba(new_data[['shotDistance']])[:, 1]
                else:
                    new_data['goal_probability'] = st.session_state.model.predict_proba(new_data[['shotDistance', 'shotAngle']])[:, 1]
               
                st.session_state.game_data = pd.concat([st.session_state.game_data, new_data])
            
            period = st.session_state.game_data['periodNumber'].iloc[-1]
            if period > 3:
                period = f"OT{period-3}"
            st.write(f"Period: {period}")
            minutes, seconds = divmod(st.session_state.game_data['timeRemaining'].iloc[-1], 60)
            st.write(f"Time Left in Period: {minutes}:{seconds}")
            
            # Display sum of expected goals for each team
            expected_goals_home = st.session_state.game_data[st.session_state.game_data['shootingTeam'] == home_team]['goal_probability'].sum()
            expected_goals_away = st.session_state.game_data[st.session_state.game_data['shootingTeam'] == away_team]['goal_probability'].sum()

            # Display scoreboard
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<h3 style='text-align: left;'>Home</h3>", unsafe_allow_html=True)
                st.markdown(f"<h1 style='text-align: left; font-size: 72px;'>{home_score}</h1>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='text-align: left;'>{home_team}</h2>", unsafe_allow_html=True)
                st.metric(label="XG", value=f"{expected_goals_home:.2f}", delta=f"{expected_goals_home - home_score:.2f}")
            with col2:
                st.markdown(f"<h3 style='text-align: left;'>Away</h3>", unsafe_allow_html=True)
                st.markdown(f"<h1 style='text-align: left; font-size: 72px;'>{away_score}</h1>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='text-align: left;'>{away_team}</h2>", unsafe_allow_html=True)
                st.metric(label="XG", value=f"{expected_goals_away:.2f}", delta=f"{expected_goals_away - away_score:.2f}")
        
            # Display table with all currently available game data
            st.write("Game Data")
            display_columns = ['periodNumber','timeInPeriod', 'isGoal', 'shotType', 'emptyNet', 'xCoord', 'yCoord',
        'zoneCode', 'shootingTeam', 'shotDistance', 'shotAngle', 'shootingPlayer', 'goalieInNet',
            'rebound', 'speed', 'goal_probability']
            st.dataframe(st.session_state.game_data[display_columns])
        else:
            st.write("Model not loaded")


