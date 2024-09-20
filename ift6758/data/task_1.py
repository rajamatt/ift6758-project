import pandas as pd
import os

API_URL = "https://api-web.nhle.com"
PLAY_BY_PLAY_ENDPOINT = "/v1/gamecenter/{game-id}/play-by-play"

REGULAR_SEASON_PLAYOFF_TUPLE = ("02", "03")
MAX_GAMES_PER_REGULAR_SEASON = 1312
PLAYOFF_ROUNDS = 4
MATCHUPS_PER_PLAYOFF_ROUND = [8, 4, 2, 1]
MAX_GAMES_PER_PLAYOFF_ROUND = 7

class NHLDataFetcher:
    def __init__(self):
        self.local_data_path = os.getenv("NHL_DATA_PATH")


    def get_raw_game_data(self, game_id: str):
        pbp_endpoint = PLAY_BY_PLAY_ENDPOINT.replace("{game-id}", game_id)
        full_endpoint = API_URL + pbp_endpoint

        print(full_endpoint)


    def get_raw_regular_season_data(self, season: int):
        for game_number in range(1, MAX_GAMES_PER_REGULAR_SEASON):
                game_id = f"{season}02{str(game_number).zfill(4)}"
                try:
                    self.get_raw_game_data(game_id)
                except ValueError:
                    print(f"Game ID {game_id} does not exist, skipping...")


    def get_raw_playoff_season_data(self, season: int):
        for round_num in range(0, 4):
            matchups = MATCHUPS_PER_PLAYOFF_ROUND[round_num]

            for match_num in range(1, matchups + 1):
                for game_num in range(1, MAX_GAMES_PER_PLAYOFF_ROUND + 1):
                    game_id = f"{season}030{round_num + 1}{match_num}{game_num}"
                    try:
                        self.get_raw_game_data(game_id)
                    except ValueError:
                        print(f"Game ID {game_id} does not exist, skipping...")


    def get_raw_season_data(self, start_season: int, end_season: int) -> pd.DataFrame:
        # First four digits = year of start of season
        # Two next digits = regular season (02) and playoffs (03)
        # Four last digits = game number (for playoffs there's extra rules here)
        for season in list(range(start_season, end_season + 1)):
            self.get_raw_regular_season_data(season)
            self.get_raw_playoff_season_data(season)
