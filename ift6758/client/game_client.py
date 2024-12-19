import math
import pandas as pd
import requests
import logging
from typing import Tuple, Dict, Optional
from serving_client import ServingClient


logger = logging.getLogger(__name__)

class GameClient:
    def __init__(self):
        self.api_url = 'https://api-web.nhle.com/v1/gamecenter'
        self.processed_events = {}  
        
    def _get_game_data(self, game_id: str) -> dict:
        """Fetches game data from NHL API"""
        url = f"{self.api_url}/{game_id}/play-by-play"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def _calculate_shot_features(self, x: float, y: float, net_side: int) -> Tuple[float, float]:
        """Calculate distance and angle from net"""
        net_x = 89 if net_side == 1 else -89
        net_y = 0
        
        distance = ((x - net_x) ** 2 + (y - net_y) ** 2) ** 0.5
        
        angle = abs(math.degrees(math.atan2(abs(y - net_y), abs(x - net_x))))
        
        return distance, angle

    def _process_event(self, event: dict, shooting_team_id: int, home_team_id: int) -> Optional[Dict]:
        """Process a single event into features"""
        event_type = event.get('typeDescKey')
        
        if event_type not in ['shot-on-goal', 'goal']:
            return None
            
        details = event.get('details', {})
        x_coord = details.get('xCoord')
        y_coord = details.get('yCoord')
        
        if x_coord is None or y_coord is None:
            return None

        is_home = shooting_team_id == home_team_id
        period = event.get('periodNumber', 0)
        shooting_towards_right = (is_home == (period % 2 == 0))
        net_side = 1 if shooting_towards_right else 0
        
        distance, angle = self._calculate_shot_features(x_coord, y_coord, net_side)
        
        situation_code = event.get('situationCode', '1111')
        defending_team_has_goalie = int(situation_code[3]) if is_home else int(situation_code[0])
        empty_net = 1 - defending_team_has_goalie
        
        return {
            'distance': distance,
            'angle': angle,
            'empty_net': empty_net,
            'is_goal': 1 if event_type == 'goal' else 0
        }

    def get_new_events(self, game_id: str) -> pd.DataFrame:
        """
        Get new events from the game that haven't been processed yet.
        Returns a DataFrame with the necessary features for prediction.
        """
        try:
            # Get game data
            game_data = self._get_game_data(game_id)
            
            # Get all plays
            all_plays = game_data.get('plays', [])
            if not all_plays:
                return pd.DataFrame()
                
            # Initialize processed events tracker for this game if needed
            if game_id not in self.processed_events:
                self.processed_events[game_id] = set()
            
            # Process only new events
            new_events = []
            for play in all_plays:
                event_id = play.get('eventId')
                
                # Skip if we've already processed this event
                if event_id in self.processed_events[game_id]:
                    continue
                    
                # Process the event
                home_team_id = game_data.get('homeTeam', {}).get('id')
                shooting_team_id = play.get('details', {}).get('eventOwnerTeamId')
                
                if home_team_id is None or shooting_team_id is None:
                    continue
                    
                processed_event = self._process_event(play, shooting_team_id, home_team_id)
                
                if processed_event:
                    new_events.append(processed_event)
                    self.processed_events[game_id].add(event_id)
            
            # Convert to DataFrame
            if new_events:
                return pd.DataFrame(new_events)
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error processing game {game_id}: {e}")
            return pd.DataFrame()
        
"""
#Usage example:
game_client = GameClient()
serving_client = ServingClient()


game_id = "2023020329"  
new_events_df = game_client.get_new_events(game_id)
if not new_events_df.empty:
    predictions = serving_client.predict(new_events_df)
"""