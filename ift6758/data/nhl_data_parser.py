from ift6758.data.nhl_data_fetcher import NHLDataFetcher
import json
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
    'shootingTeam',
    'shootingPlayer',
    'goalieInNet'
    ]

class NHLDataParser:
    def __init__(self):
        self.data_fetcher = NHLDataFetcher()

    
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
        - TODO Strength (0: even, 1: shorthanded, 2: power-play)
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

        shot_and_goal_plays['gameId'] = game_id
        
        return shot_and_goal_plays.drop(UNECESSARY_EXTRA_COLUMNS, axis=1)[FINAL_COLUMN_ORDER]
