from ift6758.data.nhl_data_fetcher import NHLDataFetcher
from ift6758.data.nhl_helper import NHLHelper
from matplotlib import image, pyplot as plt
from IPython.display import display
from ipywidgets import widgets
import json
import os
import numpy as np

class NHLEventMapper:
    def __init__(self):
        self.data_fetcher = NHLDataFetcher()
        self.helper = NHLHelper()
        self.local_data_path = os.getenv('RINK_IMG_PATH')
        self.rink_image_path = os.path.join(self.local_data_path, f'nhl_rink.png')
        self.output_area = widgets.Output()


    def get_output_area(self):
        return self.output_area


    def event_summary(self,plays:dict,n_event:int,home_team:str,away_team:str):
        """Displays play/event specific information for a specific game

        Args:
            home_team (str): Abbreviation for Home Team
            away_team (str): Abbreviation for Away Team
            plays (dict): The play by play data from the JSON file as a dictonary
            n_event (int): The event id of the play/event being inspected
        """
        # Extract Info about the play
        play = plays[n_event-1]
        play_type = play['typeDescKey']
        play_period =play['periodDescriptor']['number']
        play_period_type = play['periodDescriptor']['periodType']
        play_period_time = play['timeInPeriod']
        
        # Create layout for widgets and display the info
        grid = widgets.GridspecLayout(2,4,grid_gap='0',width='25%',align_items='center')
        grid[0,0]= widgets.HTML(value='Play Type')
        grid[0,1]= widgets.HTML(value='Period')
        grid[0,2]= widgets.HTML(value='Period Type')
        grid[0,3]= widgets.HTML(value='Time')
        grid[1,0]= widgets.HTML(value= play_type)
        grid[1,1]= widgets.HTML(value= str(play_period))
        grid[1,2]= widgets.HTML(value=play_period_type )
        grid[1,3]= widgets.HTML(value =play_period_time)
        
        with self.output_area:
            display(grid)
        
        # Pre 2019 the JSON Files did not specify which side the teams where on for each play
        if 'homeTeamDefendingSide' in play.keys():
            play_homeside = play['homeTeamDefendingSide']
            if play_homeside == 'right':
                plt.text(37.5, 0, home_team, fontsize = 10, bbox = dict(facecolor = 'red', alpha = 0.5))
                plt.text(-50, 0, away_team, fontsize = 10, bbox = dict(facecolor = 'blue', alpha = 0.5))
            else:
                plt.text(37.5, 0, away_team, fontsize = 10, bbox = dict(facecolor = 'blue', alpha = 0.5))
                plt.text(-50, 0, home_team, fontsize = 10, bbox = dict(facecolor = 'red', alpha = 0.5))
        
        # Display Rink Image with coordinates of play. If there are none, just display the image
        rink_image = image.imread(self.rink_image_path)
        plt.imshow(rink_image,extent=[-100,100,-42.5,42.5])
        plt.xticks(np.linspace(-100,100,9))
        plt.yticks(np.linspace(-42.5,42.5,5))
        plt.xlabel('feet')
        plt.ylabel('feet')
        if 'details' in play.keys():
            if 'xCoord' in play['details']:
                x = play['details']['xCoord']
                y = play['details']['yCoord']
                plt.plot(x,y, marker='o', color="purple",markersize = 10)

        with self.output_area:
            plt.show()
        
    
    def summary(self, season: int, season_type: str, n_game: int, round_num: int = 1, matchup: int = 1):
        """Displays a summary of the game information.

        Args:
            season (int): The season of the NHL
            season_type (str): 'Regular season' or 'Playoffs' 
            n_game (int): Game number.
            round_num (int): Round of playoffs. Defaults to None.
            matchup (int): Matchup of playoffs. Defaults to None.
        """
        game_id = None

        if season_type == 'Regular season':
            game_id = self.helper.construct_regular_season_game_id(season, n_game)
        else:
            # Check if round and matchup are provided for playoffs
            if round_num is None or matchup is None:
                raise ValueError("Both 'round_num' and 'matchup' must be provided for playoffs.")
            
            game_id = self.helper.construct_playoff_season_game_id(season, round_num, matchup, n_game)

        if not self.data_fetcher.game_already_fetched(game_id):
            self.data_fetcher.fetch_raw_game_data(game_id)

        with open(self.data_fetcher.get_game_local_path(game_id), 'r') as file:
            game_data = json.load(file)

        # Extract and display game information
        venue = game_data['venue']['default']
        home_team = game_data['homeTeam']['abbrev']
        away_team = game_data['awayTeam']['abbrev']
        home_score = game_data['homeTeam']['score']
        away_score = game_data['awayTeam']['score']

        with self.output_area:
            display(widgets.HTML(value=f"Venue: {venue}"))

        grid = widgets.GridspecLayout(3, 3, grid_gap='0', width='25%', align_items='center')
        grid[0, 1] = widgets.HTML(value="Home")
        grid[0, 2] = widgets.HTML(value="Away")
        grid[1, 1] = widgets.HTML(value=home_team)
        grid[1, 2] = widgets.HTML(value=away_team)
        grid[2, 0] = widgets.HTML(value='SCORE')
        grid[2, 1] = widgets.HTML(value=str(home_score))
        grid[2, 2] = widgets.HTML(value=str(away_score))
        
        with self.output_area:
            display(grid)

        # Event summary interaction
        plays_data = game_data['plays']
        w = widgets.interactive(
            self.event_summary,
            plays=widgets.fixed(plays_data),
            n_event=(1, len(plays_data), 1),
            home_team=widgets.fixed(home_team),
            away_team=widgets.fixed(away_team)
        )

        with self.output_area:
            display(w)


    def create_widgets(self, season_type: str):
        if season_type == 'Playoffs':
            return {
                'round_num': widgets.IntSlider(min=1, max=4, description='Round'),
                'matchup': widgets.IntSlider(min=1, max=8, description='Matchup'),
                'n_game': widgets.IntSlider(min=1, max=7, description='Game')
            }
        else:
            return {
                'n_game': widgets.IntSlider(min=1, max=1312, description='Game')
            }


    def update_widgets(self, season_type: str, season: int):
        self.output_area.clear_output(True)
        widget_dict = self.create_widgets(season_type)

        if season_type == 'Regular season':
            w = widgets.interactive(
                self.summary,
                season=widgets.fixed(season),
                season_type=widgets.fixed(season_type),
                n_game=widget_dict['n_game']
            )
        else:
            w = widgets.interactive(
                self.summary,
                season=widgets.fixed(season),
                season_type=widgets.fixed(season_type),
                round_num=widget_dict['round_num'],
                matchup=widget_dict['matchup'],
                n_game=widget_dict['n_game']
            )

        with self.output_area:
            display(w)
