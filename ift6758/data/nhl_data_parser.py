from ift6758.data.nhl_data_fetcher import NHLDataFetcher
from ift6758.data.shared_constants import (
    MAX_GAMES_PER_REGULAR_SEASON,
    MATCHUPS_PER_PLAYOFF_ROUND,
    MAX_GAMES_PER_PLAYOFF_ROUND
)
import json
from math import sqrt
import os
import pandas as pd

USEFUL_EVENT_TYPES = ['shot-on-goal', 'goal']
EVENT_TYPE_MAP = {'shot-on-goal': 0, 'goal': 1}

UNECESSARY_PBP_COLUMNS = ['eventId', 'typeCode', 'situationCode', 'sortOrder']
UNECESSARY_EXTRA_COLUMNS = ['periodDescriptor', 'details']

SHOT_AND_GOAL_COMMON_COLUMNS = ['shotType', 'xCoord', 'yCoord', 'goalieInNetId']
PERIOD_COMMON_COLUMNS = ['number', 'periodType']

FINAL_COLUMN_ORDER = [
    'gameId',
    'timeRemaining',
    'periodNumber',
    'timeInPeriod',
    'eventType',
    'shotType',
    'xCoord',
    'yCoord',
    'zoneCode',
    'shootingTeam',
    'shotDistance',
    'shootingTeamSide',
    'shootingPlayer',
    'goalieInNet'
    ]

class NHLDataParser:
    def __init__(self):
        self.data_fetcher = NHLDataFetcher()

    
    def get_parsed_season(self, season: int) -> pd.DataFrame:
        """Turns CSV of parsed season into DataFrame.

        Args:
            full_local_data_path (str): System path for the parsed local season data.

        Returns:
            pd.DataFrame: DataFrame containing the already parsed season.
        """
        full_local_data_path = os.path.join(self.data_fetcher.local_data_path, f'season_{season}.csv')
        return pd.read_csv(full_local_data_path)


    def season_already_parsed(self, season: int) -> bool:
        """Checks if the season was already parsed or not.

        Args:
            season (int): Season for which we want to check if was already parsed.

        Returns:
            bool: True if season exists in local data path, false if not.
        """
        full_local_data_path = os.path.join(self.data_fetcher.local_data_path, f'season_{season}.csv')
        return os.path.exists(full_local_data_path)


    def get_team_id_name_map(self, game_data: dict) -> dict:
        """Creates a dict that maps the team ID to the team name

        Args:
            game_data (dict): Raw game data JSON

        Returns:
            dict: Map for team ID to team name
        """
        home_team = game_data['homeTeam']['name']['default']
        away_team = game_data['awayTeam']['name']['default']

        return {game_data['homeTeam']['id']: home_team, game_data['awayTeam']['id']: away_team}


    def map_columns(self, df: pd.DataFrame, column: str, mapping: dict) -> pd.DataFrame:
        """Utility function to map items in a DataFrame column to another value.

        Args:
            df (pd.DataFrame): DataFrame for which we want to map values in.
            column (str): Column in which we want to map values in.
            mapping (dict): Map of values we want to change and their new values.

        Returns:
            pd.DataFrame: Resulting DataFrame of the mapping.
        """
        return df[column].map(mapping)


    def extract_period_info(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract useful period info from the raw game data.

        Args:
            df (pd.DataFrame): Raw game DataFrame.

        Returns:
            pd.DataFrame: DataFrame that contains the useful period info as columns.
        """
        for col in PERIOD_COMMON_COLUMNS:
            df[col] = df['periodDescriptor'].apply(lambda x: x.get(col))
        
        return df.rename(columns={'number': 'periodNumber'})


    def extract_shot_and_goal_info(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract useful shot and goal details from the raw game data.

        Args:
            df (pd.DataFrame): Raw game DataFrame.

        Returns:
            pd.DataFrame: DataFrame that contains the useful shot and goal details as columns.
        """
        for col in SHOT_AND_GOAL_COMMON_COLUMNS:
            df[col] = df['details'].apply(lambda x: x.get(col))
        
        return df
    

    def get_shooting_team_side_during_p1(self, df: pd.DataFrame) -> tuple:
        """Gets the shooting team and their side (left or right) during the first period of play

        Args:
            df (pd.DataFrame): The play-by-play shot DataFrame

        Returns:
            tuple: The shooting team's name and their starting side (shooting team: str, side: {0, 1})
        """
        shooting_team = None
        shooting_team_net_side_p1 = None
        
        for _, row in df.iterrows():
            if row['periodNumber'] == 1:
                zone_code = row['zoneCode']
                x_coord = row['xCoord']

                if zone_code == 'O':
                    shooting_team = row['shootingTeam']

                    if x_coord < 0:
                        shooting_team_net_side_p1 = 1
                    elif x_coord > 0:
                        shooting_team_net_side_p1 = 0
                elif zone_code == 'D':
                    shooting_team = row['shootingTeam']

                    if x_coord < 0:
                        shooting_team_net_side_p1 = 0
                    elif x_coord > 0:
                        shooting_team_net_side_p1 = 1

                if shooting_team is not None and shooting_team_net_side_p1 is not None:
                    break

        return shooting_team, shooting_team_net_side_p1
    

    def calculate_shot_distance(self, xCoord: int, yCoord: int, net_coords: tuple) -> float:
        """Calculates the euclidian distance between (xCoord, yCoord) and net_coords

        Args:
            xCoord (int): The x coordinate of the first point
            yCoord (int): The y coordinate of the first point
            net_coords (tuple): The (x,y) coordinates of the net

        Returns:
            float: The floating value distance between the first point and the net coordinates
        """
        x_net, y_net = net_coords
        distance = sqrt((xCoord - x_net) ** 2 + (yCoord - y_net) ** 2)

        return distance


    def get_shot_and_goal_pbp_df(self, game_id: str) -> pd.DataFrame:
        """Converts the JSON play-by-play game data to a pandas DataFrame containing shots-on-net and goals.
        If the game isn't already fetched, the NHLDataFetcher will fetch it using the API, then convert the JSON.

        Args:
            game_id (str): Game ID of the game we want to convert to a DataFrame 

        Returns:
            pd.DataFrame: Dataframe of the play-by-play data for shots-on-net and goals of a specific game

        DataFrame contents:
        - Game ID
        - Game time
        - Period info (time, number, type)
        - Shot or goal (0: shot, 1: goal)
        - Shot type
        - On-ice coords
        - Distance from net (ft)
        - Shooter team
        - Shooter name
        - Goalie name (None if empty net)
        """
        if not self.data_fetcher.game_already_fetched(game_id):
            self.data_fetcher.fetch_raw_game_data(game_id)

        with open(self.data_fetcher.get_game_local_path(game_id), 'r') as file:
            game_data = json.load(file)

        all_plays = pd.DataFrame(game_data.get('plays', []))
        rosters = pd.DataFrame(game_data.get('rosterSpots', []))

        shot_and_goal_plays = all_plays[all_plays['typeDescKey'].isin(USEFUL_EVENT_TYPES)].copy()
        shot_and_goal_plays.drop(UNECESSARY_PBP_COLUMNS, axis=1, inplace=True)

        shot_and_goal_plays.rename(columns={'typeDescKey': 'eventType'}, inplace=True)
        shot_and_goal_plays['eventType'] = shot_and_goal_plays['eventType'].map(EVENT_TYPE_MAP)

        shot_and_goal_plays = self.extract_period_info(shot_and_goal_plays)
        shot_and_goal_plays = self.extract_shot_and_goal_info(shot_and_goal_plays)

        shot_and_goal_plays['zoneCode'] = shot_and_goal_plays['details'].apply(lambda x: x.get('zoneCode'))

        shot_and_goal_plays['shootingPlayerId'] = shot_and_goal_plays.apply(
            lambda row: row['details'].get('scoringPlayerId') if row['eventType'] == 1
                else row['details'].get('shootingPlayerId'),
            axis=1
        )

        player_name_map = rosters.set_index('playerId').apply(
            lambda row: f"{row['firstName']['default']} {row['lastName']['default']}",
            axis=1
        ).to_dict()

        shot_and_goal_plays['teamId'] = shot_and_goal_plays['shootingPlayerId'].map(
            rosters.set_index('playerId')['teamId'].to_dict()
        )

        team_id_map = self.get_team_id_name_map(game_data)
        shot_and_goal_plays['teamId'] = shot_and_goal_plays['teamId'].map(team_id_map)
        shot_and_goal_plays.rename(columns={'teamId': 'shootingTeam'}, inplace=True)

        shot_and_goal_plays['shootingPlayerId'] = self.map_columns(shot_and_goal_plays, 'shootingPlayerId', player_name_map)
        shot_and_goal_plays['goalieInNetId'] = self.map_columns(shot_and_goal_plays, 'goalieInNetId', player_name_map)

        shot_and_goal_plays.rename(columns={'shootingPlayerId': 'shootingPlayer', 'goalieInNetId': 'goalieInNet'}, inplace=True)

        shot_and_goal_plays['shootingTeamSide'] = None
        first_shooting_team, first_shooting_team_net_side_p1 = self.get_shooting_team_side_during_p1(shot_and_goal_plays)

        for index, row in shot_and_goal_plays.iterrows():
            period = row['periodNumber']
            
            if period % 2 == 1: # period is odd (first team is on their starting side)
                if first_shooting_team == row['shootingTeam']:
                    shot_and_goal_plays.at[index, 'shootingTeamSide'] = first_shooting_team_net_side_p1
                else:
                    shot_and_goal_plays.at[index, 'shootingTeamSide'] = 1 - first_shooting_team_net_side_p1
            else: # period is even (first team is on their opposite to starting side)
                if first_shooting_team == row['shootingTeam']:
                    shot_and_goal_plays.at[index, 'shootingTeamSide'] = 1 - first_shooting_team_net_side_p1
                else:
                    shot_and_goal_plays.at[index, 'shootingTeamSide'] = first_shooting_team_net_side_p1

        shot_and_goal_plays['shotDistance'] = None

        for index, row in shot_and_goal_plays.iterrows():
            shooting_on_net_side = 1 - row['shootingTeamSide'] # the side of the rink the where the net the shooter is shooting onto

            net_coords = None
            if shooting_on_net_side == 0:
                net_coords = (-89, 0)
            else:
                net_coords = (89, 0)
            
            shot_and_goal_plays.at[index, 'shotDistance'] = self.calculate_shot_distance(row['xCoord'], row['yCoord'], net_coords)

        shot_and_goal_plays['gameId'] = game_id

        return shot_and_goal_plays.drop(UNECESSARY_EXTRA_COLUMNS, axis=1)[FINAL_COLUMN_ORDER]


    def get_shot_and_goal_pbp_df_for_season(self, season: int) -> pd.DataFrame:
        """Transforms the raw JSON data for play-by-play events of a particular season into a tidied DataFrame.

        Args:
            season (int): Season to get the play-by-play data for.

        Returns:
            pd.DataFrame: DataFrame that contains tidied play-by-play data for the season specified.
        """
        if self.season_already_parsed(season):
            return self.get_parsed_season(season)
        
        season_dfs = []

        # Regular season
        for game_number in range(1, MAX_GAMES_PER_REGULAR_SEASON):
            game_id = f'{season}02{str(game_number).zfill(4)}'
            try:
                season_dfs.append(self.get_shot_and_goal_pbp_df(game_id))
            except FileNotFoundError:
                continue

        # Playoff season
        for round_num in range(0, 4):
            matchups = MATCHUPS_PER_PLAYOFF_ROUND[round_num]
            for match_num in range(1, matchups + 1):
                for game_num in range(1, MAX_GAMES_PER_PLAYOFF_ROUND + 1):
                    game_id = f"{season}030{round_num + 1}{match_num}{game_num}"
                    try:
                        season_dfs.append(self.get_shot_and_goal_pbp_df(game_id))
                    except FileNotFoundError:
                        continue

        season_df = pd.concat(season_dfs, ignore_index=True)
        
        full_local_data_path = os.path.join(self.data_fetcher.local_data_path, f'season_{season}.csv')
        season_df.to_csv(full_local_data_path,index=False)

        return season_df


    def get_shot_and_goal_pbp_df_for_seasons(self, start_season: int, end_season: int = 0) -> pd.DataFrame:
        """Transforms the raw JSON data for play-by-play events across a range of seasons into a tidied DataFrame.

        Args:
            start_season (int): First season to start getting the play-by-play data for.
            end_season (int, optional): Last season to start getting the play-by-play data for. Defaults to 0.

        Returns:
            pd.DataFrame: DataFrame that contains tidied play-by-play data for range of seasons specified.
        """
        all_seasons_dfs = []

        if end_season == 0:
            return self.get_shot_and_goal_pbp_df_for_season(start_season)
        else:
            for season in list(range(start_season, end_season + 1)):
                all_seasons_dfs.append(self.get_shot_and_goal_pbp_df_for_season(season))

        return pd.concat(all_seasons_dfs, ignore_index=True)
