import os
import logging
import pandas as pd

from ift6758.data.nhl_data_fetcher import NHLDataFetcher
from ift6758.data.nhl_data_parser import NHLDataParser

logger = logging.getLogger(__name__)

class GameClient:
    def __init__(self):
        """
        Initialize the game client with the NHL data fetcher and parser.
        Keeps track of processed events to only return new ones.
        """
        self.data_fetcher = NHLDataFetcher()
        self.data_parser = NHLDataParser()
        self.processed_events = pd.DataFrame()
        self.current_game_id = None  

    def get_new_events(self, game_id: str) -> pd.DataFrame:
        """
        Get game data for a given game_id. Only process events that haven't been 
        seen before. Extract the required basic features.

        Args:
            game_id (str): ID of the game to fetch events from

        Returns:
            pd.DataFrame: DataFrame containing the required features for new events
        """
        # IF new gameid, reset processed events
        if self.current_game_id != game_id:
            self.processed_events = pd.DataFrame()
            self.current_game_id = game_id
        # all events and features
        all_events_df = self.data_parser.get_shot_and_goal_pbp_df(game_id)

        # only get new events
        self.processed_events = pd.concat([self.processed_events, all_events_df]).drop_duplicates(keep=False)

        return self.processed_events
