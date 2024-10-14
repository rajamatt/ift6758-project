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
        
        self.general_output = widgets.Output()
        self.game_info_output = widgets.Output()
        self.event_output = widgets.Output()


    def get_general_output(self):
        return self.general_output
    

    def get_game_info_output(self):
        return self.game_info_output


    def get_event_output(self):
        return self.event_output


    def event_summary(self, plays: dict, n_event: int, home_team: str, away_team: str):
        """Displays play/event specific information for a specific game

        Args:
            home_team (str): Abbreviation for Home Team
            away_team (str): Abbreviation for Away Team
            plays (dict): The play by play data from the JSON file as a dictonary
            n_event (int): The event id of the play/event being inspected
        """
        self.event_output.clear_output(True)

        # Extract Info about the play
        play = plays[n_event-1]
        play_type = play['typeDescKey']
        play_period =play['periodDescriptor']['number']
        play_period_type = play['periodDescriptor']['periodType']
        play_period_time = play['timeInPeriod']
        
        # Create layout for widgets and display the info
        grid = widgets.GridspecLayout(2,4,grid_gap='0',width='30%',align_items='center')
        grid[0,0]= widgets.HTML(value='Play Type')
        grid[0,1]= widgets.HTML(value='Period')
        grid[0,2]= widgets.HTML(value='Period Type')
        grid[0,3]= widgets.HTML(value='Time')
        grid[1,0]= widgets.HTML(value= play_type)
        grid[1,1]= widgets.HTML(value= str(play_period))
        grid[1,2]= widgets.HTML(value=play_period_type )
        grid[1,3]= widgets.HTML(value =play_period_time)
        
        with self.event_output:
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

        with self.event_output:
            plt.show()
        

    def __display_game_number_error(self, n_game: int):
        with self.game_info_output:
            self.game_info_output.clear_output()
            error_text = f"Game {n_game} couldn't be found. Please select a different game."
            display(widgets.HTML(value=f"<span style='color: red; font-size: 16px;'>{error_text}</span>"))

    
    def summary_regular_season(self, season: int, n_game: int):
        """Displays a summary for a regular season game.

        Args:
            season (int): The season of the NHL
            n_game (int): Game number.
        """
        game_id = self.helper.construct_regular_season_game_id(season, n_game)

        if not self.data_fetcher.game_already_fetched(game_id):
            self.data_fetcher.fetch_raw_game_data(game_id)

        try:
            with open(self.data_fetcher.get_game_local_path(game_id), 'r') as file:
                game_data = json.load(file)
        except FileNotFoundError:
            self.__display_game_number_error(n_game)

        self.display_game_summary(game_data)


    def summary_playoffs(self, season: int, round_num: int, matchup: int, n_game: int):
        """Displays a summary for a playoff game.

        Args:
            season (int): The season of the NHL
            round_num (int): Round of playoffs.
            matchup (int): Matchup of playoffs.
            n_game (int): Game number.
        """
        game_id = self.helper.construct_playoff_season_game_id(season, round_num, matchup, n_game)

        if not self.data_fetcher.game_already_fetched(game_id):
            self.data_fetcher.fetch_raw_game_data(game_id)

        try:
            with open(self.data_fetcher.get_game_local_path(game_id), 'r') as file:
                game_data = json.load(file)
        except FileNotFoundError:
            self.__display_game_number_error(n_game)

        self.display_game_summary(game_data)


    def display_game_summary(self, game_data: dict):
        self.game_info_output.clear_output(True)

        date = game_data['gameDate']
        venue = game_data['venue']['default']
        home_team = game_data['homeTeam']['abbrev']
        away_team = game_data['awayTeam']['abbrev']
        home_score = game_data['homeTeam']['score']
        away_score = game_data['awayTeam']['score']

        with self.game_info_output:
            display(widgets.HTML(value=date))
            display(widgets.HTML(value=f"Venue: {venue}"))

        grid = widgets.GridspecLayout(3, 3, grid_gap='0', width='20%', align_items='center')
        grid[0, 1] = widgets.HTML(value="Home")
        grid[0, 2] = widgets.HTML(value="Away")
        grid[1, 1] = widgets.HTML(value=home_team)
        grid[1, 2] = widgets.HTML(value=away_team)
        grid[2, 0] = widgets.HTML(value='SCORE')
        grid[2, 1] = widgets.HTML(value=str(home_score))
        grid[2, 2] = widgets.HTML(value=str(away_score))

        with self.game_info_output:
            display(grid)

        # Event summary interaction
        plays_data = game_data['plays']
        w = widgets.interactive(
            self.event_summary,
            plays=widgets.fixed(plays_data),
            n_event=widgets.IntSlider(min=1, max=len(plays_data), description='Event'),
            home_team=widgets.fixed(home_team),
            away_team=widgets.fixed(away_team)
        )

        with self.game_info_output:
            display(w)


    def update_widgets(self, season_type: str, season: int):
        self.general_output.clear_output(True)

        if season_type == 'Regular season':
            w = widgets.interactive(
                self.summary_regular_season,
                season=widgets.fixed(season),
                season_type=widgets.fixed(season_type),
                n_game=widgets.IntSlider(min=1, max=1312, description='Game')
            )
        else:
            round_slider = widgets.IntSlider(min=1, max=4, description='Round')
            matchup_slider = widgets.IntSlider(min=1, max=8, description='Matchup')
            
            def update_matchup_slider(*args):
                round_value = round_slider.value
                if round_value == 1:
                    matchup_slider.max = 8
                elif round_value == 2:
                    matchup_slider.max = 4
                elif round_value == 3:
                    matchup_slider.max = 2
                else:
                    matchup_slider.max = 1

            round_slider.observe(update_matchup_slider, names='value')

            w = widgets.interactive(
                self.summary_playoffs,
                season=widgets.fixed(season),
                round_num=round_slider,
                matchup=matchup_slider,
                n_game=widgets.IntSlider(min=1, max=7, description='Game')
            )

        with self.general_output:
            display(w)
