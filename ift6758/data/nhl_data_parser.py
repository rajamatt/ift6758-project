from ift6758.data.nhl_data_fetcher import NHLDataFetcher
import json
import pandas as pd

class NHLDataParser:
    def __init__(self):
        self.data_fetcher = NHLDataFetcher()


    def convert_game_json_to_raw_pbp_df(self, game_id: str) -> pd.DataFrame:
        """Converts the JSON play-by-play game data to a pandas DataFrame.
        If the game isn't already fetched, the NHLDataFetcher will fetch it using the API, then convert the JSON.

        Args:
            game_id (str): Game ID of the game we want to convert to a DataFrame 

        Returns:
            pd.DataFrame: Dataframe of the raw play-by-play data
        """
        if not self.data_fetcher.game_already_fetched(game_id):
            self.data_fetcher.fetch_raw_game_data(game_id)

        game_data = []

        with open(self.data_fetcher.get_game_local_path(game_id), 'r') as file:
            game_data = json.load(file)

        plays = game_data.get('plays', [])

        return pd.DataFrame(plays)
