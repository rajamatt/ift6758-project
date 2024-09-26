from ift6758.data.nhl_data_fetcher import NHLDataFetcher
from matplotlib import image 
from matplotlib import pyplot as plt 
from IPython.display import display
import json
from ipywidgets import widgets
import os
import numpy as np

class debugger:
    def __init__(self):
        self.data_fetcher = NHLDataFetcher()
        self.local_data_path = os.getenv('RINK_IMG_PATH')
        self.rink_image_path = os.path.join(self.local_data_path, f'nhl_rink.png')

    def event_summary(self,plays:dict,n_event:int):
        """Displays play/event specific information for a specific game

        ARGS:
            plays(dict): the play by play data from the JSON file as a dictonary
            n_event(int): The event id of the play/event being inspected
        """
        #Extract Info about the play
        self.play_idx = plays[n_event-1]
        self.play_type = self.play_idx['typeDescKey']
        self.play_period =self.play_idx['periodDescriptor']['number']
        self.play_period_type = self.play_idx['periodDescriptor']['periodType']
        self.play_period_time = self.play_idx['timeInPeriod']
        
        #create layout for widgets and display the info
        grid = widgets.GridspecLayout(2,4,grid_gap='0',width='25%',align_items='center')
        grid[0,0]= widgets.HTML(value='Play Type')
        grid[0,1]= widgets.HTML(value='Period')
        grid[0,2]= widgets.HTML(value='Period Type')
        grid[0,3]= widgets.HTML(value='Time')
        grid[1,0]= widgets.HTML(value= self.play_type)
        grid[1,1]= widgets.HTML(value= str(self.play_period))
        grid[1,2]= widgets.HTML(value=self.play_period_type )
        grid[1,3]= widgets.HTML(value =self.play_period_time)
        display(grid)
        
        #Pre 2019 the JSON Files did not specify which side the teams where on for each play
        if 'homeTeamDefendingSide' in self.play_idx.keys():
            self.play_homeside = self.play_idx['homeTeamDefendingSide']
            homesticker = widgets.HTML(value = self.home_team)
            awaysticker = widgets.HTML(value = self.away_team)
            if self.play_homeside == 'right':
                plt.text(37.5, 0, self.home_team, fontsize = 10, bbox = dict(facecolor = 'red', alpha = 0.5))
                plt.text(-50, 0, self.away_team, fontsize = 10, bbox = dict(facecolor = 'blue', alpha = 0.5))
            else:
                plt.text(37.5, 0, self.away_team, fontsize = 10, bbox = dict(facecolor = 'blue', alpha = 0.5))
                plt.text(-50, 0, self.home_team, fontsize = 10, bbox = dict(facecolor = 'red', alpha = 0.5))
        
        #Display Rink Image with coordinates of play. If there are none, just display the image
        rink_image = image.imread(self.rink_image_path)
        plt.imshow(rink_image,extent=[-100,100,-42.5,42.5])
        plt.xticks(np.linspace(-100,100,9))
        plt.yticks(np.linspace(-42.5,42.5,5))
        plt.xlabel('feet')
        plt.ylabel('feet')
        if 'details' in self.play_idx.keys():
            if 'xCoord' in self.play_idx['details']:
                x = self.play_idx['details']['xCoord']
                y = self.play_idx['details']['yCoord']
                plt.plot(x,y, marker='o', color="purple",markersize = 10) 
        
    
    def summary(self,season:int,type:str,n_game:int)-> dict:
        """Displays a summary of the Game Information:
        ARGS:
            season(int): The season of the NHL
            type(str):'regular' or 'playoff 
            n_game(int): game number (max possible: 1312)
        """
        #Create gameid from given info
        if type == 'regular':
            game_id = f'{season}02{str(n_game).zfill(4)}'
            
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
        self.venue = game_data['venue']['default']
        self.home_team = game_data['homeTeam']['abbrev']
        self.away_team = game_data['awayTeam']['abbrev']
        self.home_score = game_data['homeTeam']['score']
        self.away_score = game_data['awayTeam']['score']
        
        #create layout for widgets and display the info
        display(widgets.HTML(value=self.venue,description='Venue:'))
        grid = widgets.GridspecLayout(3,3,grid_gap='0',width='25%',align_items='center')
        grid[0,1]= widgets.HTML(value="Home")
        grid[0,2]= widgets.HTML(value="Away")
        grid[1,1]= widgets.HTML(value=self.home_team)
        grid[1,2]= widgets.HTML(value=self.away_team)
        grid[2,0]= widgets.HTML(value='SCORE')
        grid[2,1]= widgets.HTML(value=str(self.home_score))
        grid[2,2]= widgets.HTML(value=str(self.away_score))
        display(grid)

        #Extract play by play data and run a widget over the max number of plays =length of play by play data
        plays_data = game_data['plays']
        widgets.interact(self.event_summary,plays=widgets.fixed(plays_data),n_event= (1,len(plays_data),1) )
        
        return 
