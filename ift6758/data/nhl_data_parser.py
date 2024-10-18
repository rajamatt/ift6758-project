from ift6758.data.nhl_data_fetcher import NHLDataFetcher
from ift6758.data.nhl_helper import NHLHelper
from ift6758.data.shared_constants import (
    MAX_GAMES_PER_REGULAR_SEASON,
    MATCHUPS_PER_PLAYOFF_ROUND,
    MAX_GAMES_PER_PLAYOFF_ROUND
)
import json
from math import sqrt
import numpy as np
import os
import pandas as pd

RELEVANT_EVENT_TYPES = ['shot-on-goal', 'goal']

UNECESSARY_PBP_COLUMNS = ['eventId', 'typeCode', 'situationCode', 'sortOrder']
UNECESSARY_EXTRA_COLUMNS = ['periodDescriptor', 'details']

SHOT_AND_GOAL_COMMON_COLUMNS = ['shotType', 'xCoord', 'yCoord', 'goalieInNetId']
PERIOD_COMMON_COLUMNS = ['number', 'periodType']

FINAL_COLUMN_ORDER = [
    'gameId',
    'timeRemaining',
    'periodNumber',
    'timeInPeriod',
    'isGoal',
    'shotType',
    'xCoord',
    'yCoord',
    'shootingTeam',
    'shotDistance',
    'shootingTeamSide',
    'shootingPlayer',
    'goalieInNet',
    'zoneCode'
    
    ]

class NHLDataParser:
    def __init__(self):
        self.data_fetcher = NHLDataFetcher()
        self.helper = NHLHelper()

    
    def raw_season_data_to_df(self, season: int) -> pd.DataFrame:
        """Turns CSV of raw season data into DataFrame.

        Args:
            full_local_data_path (str): System path for the parsed local season data.

        Returns:
            pd.DataFrame: DataFrame containing the already parsed season.
        """
        full_local_data_path = os.path.join(self.data_fetcher.local_data_path, f'season_{season}.csv')
        return pd.read_csv(full_local_data_path, index_col=False)


    def season_already_parsed(self, season: int) -> bool:
        """Checks if the season was already parsed or not.

        Args:
            season (int): Season for which we want to check if was already parsed.

        Returns:
            bool: True if season exists in local data path, false if not.
        """
        full_local_data_path = os.path.join(self.data_fetcher.local_data_path, f'season_{season}.csv')
        return os.path.exists(full_local_data_path)


    def __get_team_id_name_map(self, game_data: dict) -> dict:
        """Creates a dict that maps the team ID to the team name

        Args:
            game_data (dict): Raw game data JSON

        Returns:
            dict: Map for team ID to team name
        """
        home_team = game_data['homeTeam']['name']['default']
        away_team = game_data['awayTeam']['name']['default']

        return {game_data['homeTeam']['id']: home_team, game_data['awayTeam']['id']: away_team}


    def __extract_info_to_columns(self, columns: list, source: str, df: pd.DataFrame) -> pd.DataFrame:
        """Extract useful info from the raw game data.

        Args:
            columns (list): List of columns to create in the DataFrame.
            source (str): Source of the info in the raw game data.
            df (pd.DataFrame): Raw game DataFrame.

        Returns:
            pd.DataFrame: DataFrame that contains the useful info as columns.
        """
        for col in columns:
            df[col] = df[source].apply(lambda x: x.get(col))
        
        return df
    

    def __get_shooting_team_side_during_p1(self, df: pd.DataFrame) -> tuple:
        """Gets the shooting team and their side (left or right) during the first period of play

        Args:
            df (pd.DataFrame): The play-by-play shot DataFrame

        Returns:
            tuple: The shooting team's name and their starting side (shooting team: str, side: {0, 1})
        """
        period1_df = df[df['periodNumber'] == 1]

        offensive_zone_events = period1_df[period1_df['zoneCode'] == 'O']

        if not offensive_zone_events.empty:
            first_offense = offensive_zone_events.iloc[0]
            shooting_team_net_side_p1 = 1 if first_offense['xCoord'] < 0 else 0
            return first_offense['shootingTeam'], shooting_team_net_side_p1

        defensive_zone_events = period1_df[period1_df['zoneCode'] == 'D']

        if not defensive_zone_events.empty:
            first_defense = defensive_zone_events.iloc[0]
            shooting_team_net_side_p1 = 0 if first_defense['xCoord'] < 0 else 1
            return first_defense['shootingTeam'], shooting_team_net_side_p1
        
        return None, None


    def __set_shooting_team_side(self, first_shooting_team: str, side: int, df: pd.DataFrame) -> pd.DataFrame:
        """Sets the shooting team side based on the first shooting team's side in period 1.

        Args:
            first_shooting_team (str): First team to shoot in the offensive/defensive zone in period 1.
            side (int): Side which the team was on: {left: 0, right: 1}.
            df (pd.DataFrame): DataFrame to add the shooting team side column to.

        Returns:
            pd.DataFrame: DataFrame that contains a column for what side of the rink the shooting team's net is.
        """
        isPeriodOdd = df['periodNumber'] % 2 == 1

        df['shootingTeamSide'] = np.where(
            (df['shootingTeam'] == first_shooting_team) & isPeriodOdd, side,
            np.where(
                (df['shootingTeam'] != first_shooting_team) & isPeriodOdd, 1 - side,
                np.where(
                    (df['shootingTeam'] == first_shooting_team) & ~isPeriodOdd, 1 - side, side
                )
            )
        )

        return df


    def __calculate_shot_distance(self, xCoord: int, yCoord: int, net_coords: tuple) -> float:
        """Calculates the euclidian distance between (xCoord, yCoord) and net_coords

        Args:
            xCoord (int): The x coordinate of the first point
            yCoord (int): The y coordinate of the first point
            net_coords (tuple): The (x,y) coordinates of the net

        Returns:
            float: The floating value distance between the first point and the net coordinates
        """
        x_net, y_net = net_coords

        return sqrt((xCoord - x_net) ** 2 + (yCoord - y_net) ** 2)


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

        shot_and_goal_plays = all_plays[all_plays['typeDescKey'].isin(RELEVANT_EVENT_TYPES)].copy()

        shot_and_goal_plays.rename(columns={'typeDescKey': 'isGoal'}, inplace=True)
        shot_and_goal_plays['isGoal'] = shot_and_goal_plays['isGoal'].map({'shot-on-goal': 0, 'goal': 1})

        shot_and_goal_plays = self.__extract_info_to_columns(
            columns=PERIOD_COMMON_COLUMNS,
            source='periodDescriptor',
            df=shot_and_goal_plays
        ).rename(columns={'number': 'periodNumber'})
        
        shot_and_goal_plays = self.__extract_info_to_columns(
            columns=SHOT_AND_GOAL_COMMON_COLUMNS,
            source='details',
            df=shot_and_goal_plays
        )

        shot_and_goal_plays['zoneCode'] = shot_and_goal_plays['details'].apply(lambda x: x.get('zoneCode'))

        shot_and_goal_plays['shootingPlayerId'] = shot_and_goal_plays.apply(
            lambda event: event['details'].get('scoringPlayerId') if event['isGoal'] == 1
                else event['details'].get('shootingPlayerId'),
            axis=1
        )

        player_name_map = rosters.set_index('playerId').apply(
            lambda p: f"{p['firstName']['default']} {p['lastName']['default']}",
            axis=1
        ).to_dict()

        shot_and_goal_plays['teamId'] = shot_and_goal_plays['shootingPlayerId'].map(
            rosters.set_index('playerId')['teamId'].to_dict()
        )

        team_id_map = self.__get_team_id_name_map(game_data)
        shot_and_goal_plays['teamId'] = shot_and_goal_plays['teamId'].map(team_id_map)
        shot_and_goal_plays.rename(columns={'teamId': 'shootingTeam'}, inplace=True)

        shot_and_goal_plays['shootingPlayerId'] = shot_and_goal_plays['shootingPlayerId'].map(player_name_map)
        shot_and_goal_plays['goalieInNetId'] = shot_and_goal_plays['goalieInNetId'].map(player_name_map)

        shot_and_goal_plays.rename(columns={'shootingPlayerId': 'shootingPlayer', 'goalieInNetId': 'goalieInNet'}, inplace=True)

        shot_and_goal_plays['shootingTeamSide'] = None
        first_shooting_team, first_shooting_team_net_side_p1 = self.__get_shooting_team_side_during_p1(shot_and_goal_plays)

        shot_and_goal_plays = self.__set_shooting_team_side(
            first_shooting_team=first_shooting_team,
            side=first_shooting_team_net_side_p1,
            df=shot_and_goal_plays
        )

        shot_and_goal_plays['shotDistance'] = None

        for index, row in shot_and_goal_plays.iterrows():
            shooting_on_net_side = 1 - row['shootingTeamSide'] # the side of the rink the where the net is

            net_coords = None
            if shooting_on_net_side == 0:
                net_coords = (-89, 0)
            else:
                net_coords = (89, 0)
            
            shot_and_goal_plays.at[index, 'shotDistance'] = self.__calculate_shot_distance(row['xCoord'], row['yCoord'], net_coords)

        shot_and_goal_plays['gameId'] = game_id

        return shot_and_goal_plays.drop(UNECESSARY_PBP_COLUMNS + UNECESSARY_EXTRA_COLUMNS, axis=1)[FINAL_COLUMN_ORDER]


    def get_shot_and_goal_pbp_df_for_season(self, season: int) -> pd.DataFrame:
        """Transforms the raw JSON data for play-by-play events of a particular season into a tidied DataFrame.

        Args:
            season (int): Season to get the play-by-play data for.

        Returns:
            pd.DataFrame: DataFrame that contains tidied play-by-play data for the season specified.
        """
        if self.season_already_parsed(season):
            return self.raw_season_data_to_df(season)
        
        season_dfs = []

        # Regular season
        for game_id in self.helper.get_game_ids_for_season(season, True):
            try:
                season_dfs.append(self.get_shot_and_goal_pbp_df(game_id))
            except FileNotFoundError:
                continue

        # Playoff season
        for game_id in self.helper.get_game_ids_for_season(season, False):
            try:
                season_dfs.append(self.get_shot_and_goal_pbp_df(game_id))
            except FileNotFoundError:
                continue

        season_df = pd.concat(season_dfs, ignore_index=True)
        
        full_local_data_path = os.path.join(self.data_fetcher.local_data_path, f'season_{season}.csv')
        season_df.to_csv(full_local_data_path, index=False)

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
