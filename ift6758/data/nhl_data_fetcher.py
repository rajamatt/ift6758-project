import json
import os
import requests

API_URL = 'https://api-web.nhle.com'
PLAY_BY_PLAY_ENDPOINT = '/v1/gamecenter/{game-id}/play-by-play'

MAX_GAMES_PER_REGULAR_SEASON = 1312
PLAYOFF_ROUNDS = 4
MATCHUPS_PER_PLAYOFF_ROUND = [8, 4, 2, 1]
MAX_GAMES_PER_PLAYOFF_ROUND = 7

class NHLDataFetcher:
    def __init__(self):
        self.local_data_path = os.getenv('NHL_DATA_PATH')


    def get_game_local_path(self, game_id: str):
        return os.path.join(self.local_data_path, f'game_{game_id}.json')


    def game_already_fetched(self, game_id: str):
        return os.path.exists(self.get_game_local_path(game_id))


    def fetch_raw_game_data(self, game_id: str):
        """Fetches and locally stores the raw JSON data from the play-by-play endpoint for a specific game_id.
        If the file is already stored at the NHL_DATA_PATH location then the game_id is skipped.

        How the game ID is constructed:
        - First four digits = year of start of season (ie: 2022-2023 season would just be 2022)
        - Two next digits = regular season (02) and playoffs (03)
        - Four last digits = game number (for playoffs there's extra rules here)
        
        See here for more info: https://gitlab.com/dword4/nhlapi/-/blob/master/stats-api.md#game-ids

        Args:
            game_id (str): Game ID to fetch the play-by-play data for.
        """
        game_local_path = self.get_game_local_path(game_id)

        if self.game_already_fetched(game_id):
            return

        pbp_endpoint = PLAY_BY_PLAY_ENDPOINT.replace('{game-id}', game_id)
        full_endpoint = API_URL + pbp_endpoint
        response = requests.get(full_endpoint)

        if response.status_code == 200:
            json_data = response.json()

            with open(game_local_path, 'w') as f:
                json.dump(json_data, f)            
        else:
            print(f'GET {full_endpoint} could not complete. Response status: {response.status_code}')


    def fetch_raw_regular_season_data(self, season: int):
        """Fetches and locally stores the raw JSON data from the play-by-play endpoint for a specific regular season.

        Args:
            season (int): Regular season to fetch the play-by-play data for.
        """
        for game_number in range(1, MAX_GAMES_PER_REGULAR_SEASON):
                game_id = f'{season}02{str(game_number).zfill(4)}'
                self.fetch_raw_game_data(game_id)


    def fetch_raw_playoff_season_data(self, season: int):
        """Fetches and locally stores the raw JSON data from the play-by-play endpoint for a specific playoff season.

        Args:
            season (int): Playoff season to fetch the play-by-play data for.
        """
        for round_num in range(0, 4):
            matchups = MATCHUPS_PER_PLAYOFF_ROUND[round_num]
            for match_num in range(1, matchups + 1):
                for game_num in range(1, MAX_GAMES_PER_PLAYOFF_ROUND + 1):
                    game_id = f"{season}030{round_num + 1}{match_num}{game_num}"
                    self.fetch_raw_game_data(game_id)


    def fetch_raw_season_data(self, start_season: int, end_season: int = 0):
        """Fetches and locally stores the raw JSON data from the play-by-play endpoint for a whole season (regular + playoffs).
        An end season can also be provided to fetch data from a range of seasons.

        Args:
            start_season (int): First season to start fetch the play-by-play data for.
            end_season (int, optional): Last season to fetch the play-by-play data for. Defaults to 0.
        """
        if end_season == 0:
            self.fetch_raw_regular_season_data(start_season)
            self.fetch_raw_playoff_season_data(start_season)
        else:
            for season in list(range(start_season, end_season + 1)):
                self.fetch_raw_regular_season_data(season)
                self.fetch_raw_playoff_season_data(season)
        
        for season in list(range(start_season, end_season + 1)):
            self.convert_seasons_to_df
