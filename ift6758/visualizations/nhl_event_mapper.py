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


    def event_summary(self,plays:dict,n_event:int,home_team:'str',away_team:'str'):
        """Displays play/event specific information for a specific game

        Args:
            home_team (str): Abbreviation for Home Team
            away_team (str): Abbreviation for Away Team
            plays (dict): The play by play data from the JSON file as a dictonary
            n_event (int): The event id of the play/event being inspected
        """
        #Extract Info about the play
        play = plays[n_event-1]
        play_type = play['typeDescKey']
        play_period =play['periodDescriptor']['number']
        play_period_type = play['periodDescriptor']['periodType']
        play_period_time = play['timeInPeriod']
        
        #create layout for widgets and display the info
        grid = widgets.GridspecLayout(2,4,grid_gap='0',width='25%',align_items='center')
        grid[0,0]= widgets.HTML(value='Play Type')
        grid[0,1]= widgets.HTML(value='Period')
        grid[0,2]= widgets.HTML(value='Period Type')
        grid[0,3]= widgets.HTML(value='Time')
        grid[1,0]= widgets.HTML(value= play_type)
        grid[1,1]= widgets.HTML(value= str(play_period))
        grid[1,2]= widgets.HTML(value=play_period_type )
        grid[1,3]= widgets.HTML(value =play_period_time)
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
        
    
    def summary(self,season:int,type:str,n_game:int):
        """Displays a summary of the game information

        Args:
            season (int): The season of the NHL
            type (str): 'regular' or 'playoff' 
            n_game (int): game number (max possible: 1312)
        """
        #Create gameid from given info
        game_id = None

        if type == 'regular':
            game_id = self.helper.construct_regular_season_game_id(season, n_game)
        else:
            display('under construction')

        #Fetch Data from API if it doesnt exist
        if not self.data_fetcher.game_already_fetched(game_id):
            self.data_fetcher.fetch_raw_game_data(game_id)

        #Load the JSON file into python
        game_data = []
        with open(self.data_fetcher.get_game_local_path(game_id), 'r') as file:
            game_data = json.load(file)

        #Extract Game Info
        venue = game_data['venue']['default']
        home_team = game_data['homeTeam']['abbrev']
        away_team = game_data['awayTeam']['abbrev']
        home_score = game_data['homeTeam']['score']
        away_score = game_data['awayTeam']['score']
        
        #create layout for widgets and display the info
        display(widgets.HTML(value=venue,description='Venue:'))
        grid = widgets.GridspecLayout(3,3,grid_gap='0',width='25%',align_items='center')
        grid[0,1]= widgets.HTML(value="Home")
        grid[0,2]= widgets.HTML(value="Away")
        grid[1,1]= widgets.HTML(value=home_team)
        grid[1,2]= widgets.HTML(value=away_team)
        grid[2,0]= widgets.HTML(value='SCORE')
        grid[2,1]= widgets.HTML(value=str(home_score))
        grid[2,2]= widgets.HTML(value=str(away_score))
        display(grid)

        #Extract play by play data and run a widget over the max number of plays =length of play by play data
        plays_data = game_data['plays']
        widgets.interact(self.event_summary,plays=widgets.fixed(plays_data),n_event= (1,len(plays_data),1),home_team= widgets.fixed(home_team) , away_team = widgets.fixed(away_team))
 