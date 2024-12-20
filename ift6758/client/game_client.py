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
        self.processed_events = {}  

    def get_new_events(self, game_id: str) -> pd.DataFrame:
        """
        Get game data for a given game_id. Only process events that haven't been 
        seen before. Extract the required basic features.

        Args:
            game_id (str): ID of the game to fetch events from

        Returns:
            pd.DataFrame: DataFrame containing the required features for new events
        """
        try:
            # latest game data
            self.data_fetcher.fetch_raw_game_data(game_id)
            
            # all events and features
            all_events_df = self.data_parser.get_shot_and_goal_pbp_df(game_id)
            
            # Initialize
            if game_id not in self.processed_events:
                self.processed_events[game_id] = set()
            
            # events we haven't processed yet
            new_events_mask = ~all_events_df.index.isin(self.processed_events[game_id])
            new_events_df = all_events_df[new_events_mask]
            
            # event under processing 
            self.processed_events[game_id].update(new_events_df.index)
            


            if not new_events_df.empty:
                return new_events_df[['shotDistance', 'shotAngle', 'emptyNet', 'isGoal']]
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error getting new events for game {game_id}: {e}")
            return pd.DataFrame()