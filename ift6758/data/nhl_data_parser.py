from ift6758.data.nhl_data_fetcher import NHLDataFetcher
import json
import pandas as pd

USEFUL_TYPES = ['shot-on-goal', 'goal']
UNECESSARY_PBP_COLUMNS = ['eventId', 'typeCode', 'situationCode', 'sortOrder']
SHOT_AND_GOAL_COMMON_COLUMNS = ['shotType', 'xCoord', 'yCoord', 'goalieInNetId']
PERIOD_COMMON_COLUMNS = ['number', 'periodType']
UNECESSARY_EXTRA_COLUMNS = ['periodDescriptor', 'details']
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

        game_data = []

        with open(self.data_fetcher.get_game_local_path(game_id), 'r') as file:
            game_data = json.load(file)

        all_plays = pd.DataFrame(game_data.get('plays', []))
        rosters = pd.DataFrame(game_data.get('rosterSpots', []))

        shot_and_goal_plays = all_plays[all_plays['typeDescKey'].isin(USEFUL_TYPES)].copy()
        shot_and_goal_plays.drop(UNECESSARY_PBP_COLUMNS, axis=1, inplace=True)
        
        shot_and_goal_plays.rename(columns={'typeDescKey': 'eventType'}, inplace=True)
        shot_and_goal_plays['eventType'] = shot_and_goal_plays['eventType'].map(
            {'shot-on-goal': 0, 'goal': 1}
        )

        for col in PERIOD_COMMON_COLUMNS:
            shot_and_goal_plays[col] = shot_and_goal_plays['periodDescriptor'].apply(lambda x: x.get(col) if col in x else None)

        for col in SHOT_AND_GOAL_COMMON_COLUMNS:
            shot_and_goal_plays[col] = shot_and_goal_plays['details'].apply(lambda x: x.get(col) if col in x else None)
        
        shot_and_goal_plays['shootingPlayerId'] = shot_and_goal_plays.apply(
            lambda row: row['details'].get('scoringPlayerId') if row['eventType'] == 1
                else row['details'].get('shootingPlayerId') if row['eventType'] == 0 
                else None,
            axis=1
        )

        player_name_map = rosters.set_index('playerId').apply(
            lambda row: f"{row['firstName']['default']} {row['lastName']['default']}",
            axis=1
        ).to_dict()

        home_team = game_data['homeTeam']['name']['default']
        home_team_id = game_data['homeTeam']['id']

        away_team = game_data['awayTeam']['name']['default']
        away_team_id = game_data['awayTeam']['id']

        team_id_map = {
            home_team_id: home_team,
            away_team_id: away_team
        }

        shot_and_goal_plays['teamId'] = shot_and_goal_plays['shootingPlayerId'].map(
            rosters.set_index('playerId')['teamId'].to_dict()
        )

        shot_and_goal_plays['shootingTeam'] = shot_and_goal_plays['teamId'].map(team_id_map)
        shot_and_goal_plays = shot_and_goal_plays.drop(columns=['teamId'])
    
        shot_and_goal_plays['shootingPlayerId'] = shot_and_goal_plays['shootingPlayerId'].map(player_name_map).fillna(shot_and_goal_plays['shootingPlayerId'])
        shot_and_goal_plays['goalieInNetId'] = shot_and_goal_plays['goalieInNetId'].map(player_name_map).fillna(shot_and_goal_plays['goalieInNetId'])

        shot_and_goal_plays = shot_and_goal_plays.rename(columns={'shootingPlayerId': 'shootingPlayer'})
        shot_and_goal_plays = shot_and_goal_plays.rename(columns={'goalieInNetId': 'goalieInNet'})
        shot_and_goal_plays = shot_and_goal_plays.rename(columns={'number': 'periodNumber'})

        shot_and_goal_plays['gameId'] = game_id
        shot_and_goal_plays = shot_and_goal_plays.drop(UNECESSARY_EXTRA_COLUMNS, axis=1)

        shot_and_goal_plays = shot_and_goal_plays[FINAL_COLUMN_ORDER]

        return shot_and_goal_plays
