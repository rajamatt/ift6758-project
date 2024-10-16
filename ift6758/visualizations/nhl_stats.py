from ift6758.data.nhl_data_parser import NHLDataParser
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from PIL import Image
from scipy.ndimage import gaussian_filter
season_range = [2016,2017,2018,2019,2020,2021,2022,2023]
shot_types = ['wrist', 'slap', 'backhand', 'snap', 'tip-in', 'deflected','wrap-around','poke', 'bat', 'between-legs', 'cradle']
team_list = ['Lightning', 'Penguins', 'Kraken', 'Golden Knights', 'Canadiens','Maple Leafs', 'Rangers', 'Capitals', 'Avalanche', 'Blackhawks',
             'Canucks', 'Oilers', 'Sabres', 'Senators', 'Red Wings', 'Panthers','Stars', 'Islanders', 'Hurricanes', 'Blue Jackets', 'Coyotes',
             'Predators', 'Jets', 'Ducks', 'Kings', 'Devils', 'Flyers', 'Wild','Bruins', 'Blues', 'Flames', 'Sharks']

class NHLStats:
    def __init__(self):
        self.data_parser = NHLDataParser()
    
    def plot_shot_type_distribution(self,start_season:int,end_season:int = 0):
        """Plots the Distrbution of Shot Types over a range of seasons. 
        Plots for one season if start_season = end_season or if end_season = default value
        
        ARGS:
        start_season (int): First season in range to plot 
        end_season (int, optional): Last season in range to plot. Defaults to 0.
        """
        df = self.data_parser.get_shot_and_goal_pbp_df_for_seasons(start_season,end_season)
        shot_counts = sns.countplot(x='shotType',data=df,hue='isGoal',order=df['shotType'].value_counts().index)
        plt.legend(title='Outcome', loc='center right', labels=['No Goal', 'Goal'])
        plt.xticks(rotation=90)
        if end_season==0 or start_season==end_season:
            plt.suptitle(f"Shot Type Distribution ({start_season})")
        else:
            plt.suptitle(f"Shot Type Distribution ({start_season}-{end_season})")
        for container in shot_counts.containers:
            shot_counts.bar_label(container,rotation=90,padding=5)
        shot_counts.spines[['right', 'top']].set_visible(False)

    def plot_shot_distance_distribution(self,start_season:int,end_season:int = 0,by_type=False,by_goal=False):
        """Plots the Distribution of Shot Distance over a range of seasons.
        Plots for one season if start_season = end_season or if end_season = default value
        
        ARGS:
        start_season (int): First season to start getting the play-by-play data for.
        end_season (int, optional): Last season to start getting the play-by-play data for. Defaults to 0.
        by_type (boolean): if True plot distribution over different Shot Types. default = False
        by_goal (boolean): if True plot distribution over succesful/unsuccessful. default = False
        """
        hue = None
        col = None
        if by_type:
            hue ='shotType'
        if by_goal:
            col = 'isGoal'
        df = self.data_parser.get_shot_and_goal_pbp_df_for_seasons(start_season,end_season)
        sns.displot(df,x="shotDistance",kind='hist',hue=hue,col=col,kde=True,binwidth =2,element='step')
        plt.xlabel('Shot Distance (feet)')
        if end_season==0 or start_season==end_season:
            plt.suptitle(f"Shot Distance Distribution ({start_season})",fontsize='medium')
        else:
            plt.suptitle(f"Shot Distance Distribution ({start_season}-{end_season})",fontsize='medium')

    def plot_shot_distance_probability(self,start_season:int,end_season:int=0,bin_width:float=1,norm:bool=False):
        """Plots the probability of a Shot being a goal vs Distance over a range of seasons.
        Plots for one season if start_season = end_season or if end_season = default value
        
        ARGS:
        start_season (int): First season to start getting the play-by-play data for.
        end_season (int, optional): Last season to start getting the play-by-play data for. Defaults to 0.
        bin_width (float): The width of the bins to consider when plotting the probability. Smaller bins will need more compute time
        norm (bool): decided whether to get joint or conditional probability. Set to True for joint probability
        """
        df = self.data_parser.get_shot_and_goal_pbp_df_for_seasons(start_season,end_season)
        distance_max = df['shotDistance'].max()
        distance_min = df['shotDistance'].min()
        bins = pd.interval_range(distance_min ,distance_max,freq=bin_width)
        bin_probabilty=[]
        for bin in bins:
            df_bin = df[df["shotDistance"].apply(lambda x: x in bin)]
            if norm:
                shot_count = df.shape[0]
            else:
                shot_count = df_bin.shape[0]
            goal_count = sum(df_bin['isGoal']==1)
            if shot_count != 0:
                bin_probabilty.append(goal_count/shot_count)
            else:
                bin_probabilty.append(np.nan)
        plt.plot(bins.mid,bin_probabilty)
        plt.xlabel('Shot Distance (feet)')
        plt.ylabel('Probability')
        if end_season==0 or start_season==end_season:
            plt.suptitle(f"Goal Probability vs Shot Distance({start_season})",fontsize='medium')
        else:
            plt.suptitle(f"Goal Probability vs Shot Distance ({start_season}-{end_season})",fontsize='medium')

    def plot_shot_distance_type_probability(self,start_season:int,end_season:int=0,bin_width:float=1,shot_types:list=None,norm:bool=True):
        """Plots the probability/percentage of a Shot being a goal vs Distance for different shot types over a range of seasons.
        Plots for one season if start_season = end_season or if end_season = default value
            
        ARGS:
        start_season (int): First season to start getting the play-by-play data for.
        end_season (int, optional): Last season to start getting the play-by-play data for. Defaults to 0.
        bin_width (float): The width of the bins to consider when plotting the probability. Smaller bins will need more compute time
        shot_types (list): list of shot types to plot for
        norm (bool): decided whether to get joint or conditional probability. Set to True for joint probability
        """ 
        df = self.data_parser.get_shot_and_goal_pbp_df_for_seasons(start_season,end_season)
        ax =plt.subplot()
        if shot_types:
            for shot in shot_types:
                df_shot = df[df["shotType"]==shot]
                distance_max = df_shot['shotDistance'].max()
                distance_min = df_shot['shotDistance'].min()
                bins = pd.interval_range(distance_min ,distance_max,freq=bin_width)
                bin_probabilty=[]
                for bin in bins:
                    df_bin = df_shot[df_shot["shotDistance"].apply(lambda x: x in bin)]
                    if norm:
                        shot_count = df.shape[0]
                    else:
                        shot_count = df_bin.shape[0]
                    goal_count = sum(df_bin['isGoal']==1)
                    if shot_count != 0:
                        bin_probabilty.append(goal_count/shot_count)
                    else:
                        bin_probabilty.append(np.nan)
                line = ax.plot(bins.mid,np.array(bin_probabilty)*100,label= shot)
                    
            ax.legend()
            plt.xlabel('Shot Distance (feet)')
            plt.ylabel('Goal Percentage')
            if end_season==0 or start_season==end_season:
                plt.suptitle(f"Goal Percentage vs Shot Distance({start_season})",fontsize='medium')
            else:
                plt.suptitle(f"Goal Percentage vs Shot Distance ({start_season}-{end_season})",fontsize='medium')
        else:
            self.plot_shot_distance_probability(start_season,end_season,bin_width,norm=norm)
        
    def plot_shot_team_rate(self,season:int,team:str,xbin:int,ybin:int,sigma:float)-> tuple[pd.DataFrame,go.Figure]:
        """Plots the excess shot rate per hour in the offensive zone for a team based on location over a regular season of NHL 
        ARGS:
        season (int): The season to consider for the statistics
        team (str): The team to plot for
        
        RETURNS:
        pd.Dataframe: Data frame with excess shot rate for all the teams and league average shot rate by lcoation
        go.Figure: The plotly figure object with the plot details"""
        

        df = self.data_parser.get_shot_and_goal_pbp_df_for_seasons(season)

        #Filter The dataframe for the regular season.
        df = df[df['gameId'].apply(lambda x: str(x)[5]=='2')]

        #Filter the dataframe to consider only the offensive zone stats
        df = df[(df['zoneCode']=='O')|(df['zoneCode']=='N')]

        #Mirror the coordinates of the shots for one side of the field to get all coordinates in one half of the field
        df.loc[df['xCoord']<0,'yCoord']=-df.loc[df['xCoord']<0,'yCoord']
        df.loc[:,'xCoord']=df.loc[:,'xCoord'].abs()

        #Group the shots by location
        df_shot_loc = df.groupby(['xCoord','yCoord']).size().reset_index().rename(columns={0:'league_ShotCount'})

        #Calculate shot rate per hour for each team over the coordinates    
        for name in team_list:
            df_team = df[df['shootingTeam']==name]
            df_team_loc = df_team.groupby(['xCoord','yCoord']).size().reset_index().rename(columns={0:name})
            df_team_loc[name] = df_team_loc[name].div(82)
            df_shot_loc=pd.merge(left=df_shot_loc,right=df_team_loc,how='left',on=['xCoord','yCoord'])
            df_shot_loc[name] = df_shot_loc[name].fillna(0)
        
        #Calculate League Average Shot Rate over the coordinates 
        df_shot_loc['league_shotRate']=df_shot_loc[team_list].sum(axis=1)/32

        #Calculate the difference in shot rate per hour for all teams over the coordinates
        for name in team_list:
            df_shot_loc[name]=df_shot_loc[name].sub(df_shot_loc['league_shotRate'])
        
        #Plot the density contours for the chosen team
        local_data_path = os.getenv('RINK_IMG_PATH')
        rink_image_path = os.path.join(local_data_path, f'nhl_rink.png')
        rink_image = Image.open(rink_image_path)
        crop_rink_image = rink_image.crop((550,0,1100,467)).rotate(90,expand=1)
        fig = go.Figure()
        fig.add_trace(
            go.Histogram2dContour(y = df_shot_loc['xCoord'],
                                  x = -df_shot_loc['yCoord'],
                                  z = gaussian_filter(df_shot_loc[team],sigma=sigma),
                                  colorscale = 'RdBu',
                                  histfunc='sum',
                                  xbins=dict(size=xbin),
                                  ybins=dict(size=ybin),
                                  contours=dict(start=-1,end=1,size=0.1)
                                                )
        )
        fig.update_layout(autosize =False,
                        width = 700.5,
                        height = 825)
        fig.add_layout_image(
                dict(
                    source=crop_rink_image,
                    xref="paper",
                    yref="paper",
                    x=0,
                    y=1,
                    sizex=1,
                    sizey=1,
                    sizing="stretch",
                    opacity=0.5,
                    layer="above")
        )
        fig.show()
        return df_shot_loc,fig
        
    
