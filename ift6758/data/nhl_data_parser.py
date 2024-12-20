from ift6758.data.nhl_data_fetcher import NHLDataFetcher
from ift6758.data.nhl_helper import NHLHelper
import json
import math
import numpy as np
import os
import pandas as pd

RELEVANT_EVENT_TYPES = ['shot-on-goal', 'goal']

UNECESSARY_PBP_COLUMNS = ['eventId', 'typeCode', 'situationCode', 'sortOrder']
UNECESSARY_EXTRA_COLUMNS = ['periodDescriptor', 'details']

EVENT_COMMON_COLUMNS = ['xCoord', 'yCoord']
SHOT_AND_GOAL_COMMON_COLUMNS = ['shotType', 'goalieInNetId']
PERIOD_COMMON_COLUMNS = ['number', 'periodType']

COLUMNS_TO_DROP_IF_NAN = ['shotType', 'xCoord', 'yCoord', 'zoneCode']

FINAL_COLUMN_ORDER = [
    'gameId',
    'timeRemaining',
    'periodNumber',
    'timeInPeriod',
    'isGoal',
    'shotType',
    'emptyNet',
    'xCoord',
    'yCoord',
    'zoneCode',
    'shootingTeam',
    'shotDistance',
    'shotAngle',
    'shootingTeamSide',
    'shootingPlayer',
    'goalieInNet',
    'previousEvent',
    'timeDiff',
    'previousEventX',
    'previousEventY',
    'rebound',
    'distanceDiff',
    'shotAngleDiff',
    'speed'
    ]

class NHLDataParser:
    def __init__(self):
        self.data_fetcher = NHLDataFetcher()
        self.helper = NHLHelper()

    
    def raw_season_data_to_df(self, season_file: str) -> pd.DataFrame:
        """Turns CSV of raw season data into DataFrame.

        Args:
            season_file (str): System path for the parsed local season data.

        Returns:
            pd.DataFrame: DataFrame containing the already parsed season.
        """
        full_local_data_path = os.path.join(self.data_fetcher.local_data_path, season_file)
        return pd.read_csv(full_local_data_path, index_col=False)


    def __get_season_file_name(self, season: int, with_regular_season: bool = True, with_playoff_season: bool = True) -> str:
        """Gets the season file name for a season. Only regular seasons end with "reg". Only playoff seasons end with "playoffs".

        Args:
            season (int): Season year.
            with_regular_season (bool, optional): If the season should contain regular season games. Defaults to True.
            with_playoff_season (bool, optional): If the season should contain playoff season games. Defaults to True.

        Returns:
            str: Season file name.
        """
        if with_regular_season and not with_playoff_season:
            return f'season_{season}_reg.csv'
        elif with_playoff_season and not with_regular_season:
            return f'season_{season}_playoffs.csv'
        
        return f'season_{season}.csv'


    def season_already_parsed(self, season: int, with_regular_season: bool = True, with_playoff_season: bool = True) -> bool:
        """Checks if the season was already parsed or not.

        Args:
            season (int): Season for which we want to check if was already parsed.
            with_regular_season (bool, optional): If the season should contain regular season games. Defaults to True.
            with_playoff_season (bool, optional): If the season should contain playoff season games. Defaults to True.

        Returns:
            bool: True if season exists in local data path, false if not.
        """
        season_file = self.__get_season_file_name(season, with_regular_season, with_playoff_season)
        full_local_data_path = os.path.join(self.data_fetcher.local_data_path, season_file)
        return os.path.exists(full_local_data_path)


    def __get_team_id_name_map(self, game_data: dict) -> dict:
        """Creates a dict that maps the team ID to the team name

        Args:
            game_data (dict): Raw game data JSON

        Returns:
            dict: Map for team ID to team name
        """
        home_team = game_data['homeTeam']['commonName']['default']
        away_team = game_data['awayTeam']['commonName']['default']

        return {game_data['homeTeam']['id']: home_team, game_data['awayTeam']['id']: away_team}


    def __try_extract_info(self, x: object, info: str):
        """Helper function that tries to extract a specific string from an object.

        Args:
            x (object): Object to extract from.
            info (str): String to extract value for.

        Returns:
            any: If string exists in the object and could be extracted then the value for that string, else None.
        """
        try:
            return x.get(info)
        except:
            return None 
        

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
            df[col] = df[source].apply(lambda x: self.__try_extract_info(x, col))
        
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


    def __calculate_distance(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Calculates the euclidian distance between (xCoord, yCoord) and net_coords

        Args:
            x1 (int): The x coordinate of the first point
            y1 (int): The y coordinate of the first point
            x2 (int): The x coordinate of the second point
            y2 (int): The y coordinate of the second point

        Returns:
            float: The floating value distance between the first point and the second point coordinates
        """
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


    def __calculate_angle(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Calculates the angle between two points, considering a right triangle.

        Args:
            x1 (int): The x coordinate of the first point
            y1 (int): The y coordinate of the first point
            x2 (int): The x coordinate of the second point
            y2 (int): The y coordinate of the second point

        Returns:
            float: The floating value angle between the two points
        """
        return math.degrees(math.atan2(abs(y2 - y1), abs(x2 - x1)))


    def get_shot_and_goal_pbp_df(self, game_id: str) -> pd.DataFrame:
        """Converts the JSON play-by-play game data to a pandas DataFrame containing shots-on-net and goals.
        If the game isn't already fetched, the NHLDataFetcher will fetch it using the API, then convert the JSON.

        Args:
            game_id (str): Game ID of the game we want to convert to a DataFrame 

        Returns:
            pd.DataFrame: Dataframe of the play-by-play data for shots-on-net and goals of a specific game

        DataFrame contents:
        - Game ID
        - Game time (s)
        - Period info (time, number, type)
        - Shot or goal (0: shot, 1: goal)
        - Shot type
        - Empty net (0: goalie present, 1: empty)
        - On-ice coords
        - Zone code
        - Distance from net (ft)
        - Shot angle (°)
        - Shooter team
        - Shooter name
        - Goalie name (None if empty net)
        - Previous event info (type, coords, time since, distance from, angle difference)
        - Rebound (0: no rebound, 1: rebound)
        - Speed (ft/s)
        """
        if not self.data_fetcher.game_already_fetched(game_id):
            self.data_fetcher.fetch_raw_game_data(game_id)

        if os.path.getsize(self.data_fetcher.get_game_local_path(game_id)) == 0:
            raise FileNotFoundError(f"Game data file for game_id {game_id} is empty.")

        with open(self.data_fetcher.get_game_local_path(game_id), 'r') as file:
            game_data = json.load(file)

        all_plays = pd.DataFrame(game_data.get('plays', []))
        rosters = pd.DataFrame(game_data.get('rosterSpots', []))

        all_plays['timeRemaining'] = all_plays['timeRemaining'].apply(lambda t: int(t.split(':')[0]) * 60 + int(t.split(':')[1]))
        
        all_plays['previousEvent'] = all_plays['typeDescKey'].shift(1)
        all_plays['timeDiff'] = all_plays['timeRemaining'].shift(1) - all_plays['timeRemaining']


        all_plays = self.__extract_info_to_columns(
            columns=EVENT_COMMON_COLUMNS,
            source='details',
            df=all_plays
        )

        all_plays['previousEventX'] = all_plays['xCoord'].shift(1)
        all_plays['previousEventY'] = all_plays['yCoord'].shift(1)

        all_plays['distanceDiff'] = all_plays.apply(
            lambda row: self.__calculate_distance(row['xCoord'], row['yCoord'], row['previousEventX'], row['previousEventY']),
            axis=1
        )

        shot_and_goal_plays = all_plays[all_plays['typeDescKey'].isin(RELEVANT_EVENT_TYPES)].copy()
        shot_and_goal_plays['rebound'] = shot_and_goal_plays['previousEvent'].apply(lambda x: 1 if x == 'shot-on-goal' else 0)

        shot_and_goal_plays['speed'] = shot_and_goal_plays.apply(
            lambda row: row['distanceDiff'] / row['timeDiff']
                if pd.notna(row['timeDiff']) and row['timeDiff'] > 0
                else -1,
            axis=1
        )

        mean_speed = shot_and_goal_plays[shot_and_goal_plays['speed'] != -1]['speed'].mean()
        shot_and_goal_plays['speed'] = shot_and_goal_plays['speed'].replace(-1, mean_speed)

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
        shot_and_goal_plays['emptyNet'] = np.where(shot_and_goal_plays['goalieInNet'].isna(), 1, 0)

        shot_and_goal_plays['shootingTeamSide'] = None
        first_shooting_team, first_shooting_team_net_side_p1 = self.__get_shooting_team_side_during_p1(shot_and_goal_plays)

        shot_and_goal_plays = self.__set_shooting_team_side(
            first_shooting_team=first_shooting_team,
            side=first_shooting_team_net_side_p1,
            df=shot_and_goal_plays
        )

        shot_and_goal_plays['shotDistance'] = None
        shot_and_goal_plays['shotAngle'] = None

        for index, row in shot_and_goal_plays.iterrows():
            shooting_on_net_side = 1 - row['shootingTeamSide'] # the side of the rink the where the net is
            net_coords = None

            if shooting_on_net_side == 0:
                net_coords = (-89, 0)
            else:
                net_coords = (89, 0)
            
            x_coord = row['xCoord']
            y_coord = row['yCoord']

            shot_and_goal_plays.at[index, 'shotDistance'] = self.__calculate_distance(x_coord, y_coord, net_coords[0], net_coords[1])
            shot_and_goal_plays.at[index, 'shotAngle'] = self.__calculate_angle(x_coord, y_coord, net_coords[0], net_coords[1])

        shot_and_goal_plays['previousShotAngle'] = shot_and_goal_plays['shotAngle'].shift(1)
        shot_and_goal_plays['shotAngleDiff'] = shot_and_goal_plays.apply(
            lambda shot: abs(shot['shotAngle'] - shot['previousShotAngle']) 
                if shot['rebound'] == 1 and pd.notna(row['previousEventX']) and pd.notna(row['previousEventY'])
                else 0,
            axis=1
        )

        # Over all seasons (around 400 000 shot/goal events), there's only about 100 events that contain missing or NaN info
        # Drop all rows that contain missing values, except for the 'goalieInNet' column (indicating an empty net)
        shot_and_goal_plays = shot_and_goal_plays.dropna(subset=COLUMNS_TO_DROP_IF_NAN)

        shot_and_goal_plays['gameId'] = game_id

        return shot_and_goal_plays.drop(UNECESSARY_PBP_COLUMNS + UNECESSARY_EXTRA_COLUMNS, axis=1)[FINAL_COLUMN_ORDER]


    def get_shot_and_goal_pbp_df_for_season(
            self, 
            season: int, 
            with_regular_season: bool = True, 
            with_playoff_season: bool = True
        ) -> pd.DataFrame:
        """Transforms the raw JSON data for play-by-play events of a particular season into a tidied DataFrame.
        
        Args:
            season (int): Season year.
            with_regular_season (bool, optional): If the season should contain regular season games. Defaults to True.
            with_playoff_season (bool, optional): If the season should contain playoff season games. Defaults to True.
        
        Returns:
            pd.DataFrame: DataFrame that contains tidied play-by-play data for the season specified.
        """
        if self.season_already_parsed(season, with_regular_season, with_playoff_season):
            return self.raw_season_data_to_df(self.__get_season_file_name(season, with_regular_season, with_playoff_season))
        
        season_dfs = []

        # Process regular season games
        if with_regular_season:
            for game_id in self.helper.get_game_ids_for_season(season, True):
                try:
                    season_dfs.append(self.get_shot_and_goal_pbp_df(game_id))
                except FileNotFoundError:
                    print(f"File not found for game_id: {game_id}, skipping.")
                    continue
                except ValueError as e:
                    print(f"ValueError for game_id {game_id}: {e}")
                    continue

        # Process playoff games
        if with_playoff_season:
            for game_id in self.helper.get_game_ids_for_season(season, False):
                try:
                    season_dfs.append(self.get_shot_and_goal_pbp_df(game_id))
                except FileNotFoundError:
                    continue
                except ValueError as e:
                    continue

        # Concatenate all game DataFrames
        if not season_dfs:
            raise ValueError(f"No valid game data found for season {season}.")

        season_df = pd.concat(season_dfs, ignore_index=True)
        season_file = self.__get_season_file_name(season, with_regular_season, with_playoff_season)
        
        full_local_data_path = os.path.join(self.data_fetcher.local_data_path, season_file)
        season_df.to_csv(full_local_data_path, index=False)

        return season_df


    def get_shot_and_goal_pbp_df_for_seasons(
            self,
            start_season: int,
            end_season: int = 0,
            with_regular_season: bool = True,
            with_playoff_season: bool = True
        ) -> pd.DataFrame:
        """Transforms the raw JSON data for play-by-play events across a range of seasons into a tidied DataFrame.
        
        Args:
            start_season (int): First season to start getting the play-by-play data for.
            end_season (int, optional): Last season to start getting the play-by-play data for. Defaults to 0.
            with_regular_season (bool, optional): If the season should contain regular season games. Defaults to True.
            with_playoff_season (bool, optional): If the season should contain playoff season games. Defaults to True.
        
        Returns:
            pd.DataFrame: DataFrame that contains tidied play-by-play data for range of seasons specified.
        """
        all_seasons_dfs = []

        if end_season == 0:
            return self.get_shot_and_goal_pbp_df_for_season(
                start_season,
                with_regular_season=with_regular_season,
                with_playoff_season=with_playoff_season
            )
        else:
            for season in range(start_season, end_season + 1):
                season_df = self.get_shot_and_goal_pbp_df_for_season(
                    season,
                    with_regular_season=with_regular_season,
                    with_playoff_season=with_playoff_season
                )
                all_seasons_dfs.append(season_df)


        # Ensure we have data to concatenate
        if not all_seasons_dfs:
            raise ValueError(f"No valid game data found for seasons {start_season} to {end_season}.")

        return pd.concat(all_seasons_dfs, ignore_index=True)