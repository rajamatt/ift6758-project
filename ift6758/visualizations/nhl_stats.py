from ift6758.data.nhl_data_parser import NHLDataParser
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

class NHLStats:
    def __init__(self):
        self.data_parser = NHLDataParser()
    
    def plot_shot_type_distribution(self,start_season:int,end_season:int = 0):
        """Plots the Distrbution of Shot Types over a range of seasons. 
        Plots for one season if start_season = end_season or id end_season = default value
        
        ARGS:
        start_season (int): First season in range to plot 
        end_season (int, optional): Last season in range to plot. Defaults to 0.
        """
        df = self.data_parser.get_shot_and_goal_pbp_df_for_seasons(start_season,end_season)
        shot_counts = sns.countplot(x='shotType',data=df,hue='eventType',order=df['shotType'].value_counts().index)
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
        Plots for one season if start_season = end_season or id end_season = default value
        
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
            col = 'eventType'
        df = self.data_parser.get_shot_and_goal_pbp_df_for_seasons(start_season,end_season)
        sns.displot(df,x="shotDistance",kind='hist',hue=hue,col=col,kde=True,binwidth =2,element='step')
        plt.xlabel('Shot Distance (feet)')
        if end_season==0 or start_season==end_season:
            plt.suptitle(f"Shot Distance Distribution ({start_season})",fontsize='medium')
        else:
            plt.suptitle(f"Shot Distance Distribution ({start_season}-{end_season})",fontsize='medium')

    def plot_shot_distance_probability(self,start_season:int,end_season:int=0,bin_width:float=1,norm:bool=False):
        """Plots the probability of a Shot being a goal vs Distance over a range of seasons.
        Plots for one season if start_season = end_season or id end_season = default value
        
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
            goal_count = sum(df_bin['eventType']==1)
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
        """Plots the probability/percentage of a Shot being a goal vs Distance over a range of seasons.
        Plots for one season if start_season = end_season or id end_season = default value
            
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
                    goal_count = sum(df_bin['eventType']==1)
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
        
    
