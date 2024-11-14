from ift6758.data.nhl_data_fetcher import NHLDataFetcher
from bs4 import BeautifulSoup
import pandas as pd

class NHLSummaryScraper:
    def __init__(self):
        self.data_fetcher = NHLDataFetcher()


    def parse_penalty_rows(self, rows: list, team: str) -> pd.DataFrame:
        """Transform penalty rows from an NHL game summary to a DataFrame for one team

        Args:
            rows (list): Penalty rows
            team (str): Team name

        Returns:
            pd.DataFrame: DataFrame containing relevant penalty information for one of the teams during an NHL game
        """
        penalties = []
        
        for row in rows:
            cells = row.find_all('td')
            
            if len(cells) < 6 or cells[0].text.strip() == "#":
                continue

            period = int(cells[1].text.strip())
            time_in_period = cells[2].text.strip()
            player = cells[3].find_all('td')[-1].text.strip()
            pim = int(cells[8].text.strip())
            penalty_type = cells[9].text.strip()

            minutes, seconds = map(int, time_in_period.split(':'))
            time_seconds = minutes * 60 + seconds

            penalties.append({
                'team': team,
                'period': period,
                'time': time_seconds,
                'player': player,
                'pim': pim,
                'penalty_type': penalty_type
            })

        return pd.DataFrame(penalties)


    def scrape_penalty_data(self, game_id: str) -> pd.DataFrame:
        """Scrapes the penalties for both teams of an NHL game.

        Args:
            game_id (str): Game ID to scrape penalties for.

        Returns:
            pd.DataFrame: DataFrame containing penalty information for both teams of an NHL game.
        """
        raw_penalty_data = self.data_fetcher.fetch_raw_penalty_data(game_id)
        soup = BeautifulSoup(raw_penalty_data, 'html.parser')

        team_cells = soup.find(id="VPenaltySummary").find_all("td", class_="teamHeading + border")
        team_tables = soup.find(id="PenaltySummary").find_all("td", valign="top", width="50%")

        team_left = team_cells[0].text.strip()
        team_right = team_cells[1].text.strip()

        penalties_left = self.parse_penalty_rows(team_tables[0].find_all("tr"), team_left)
        penalties_right = self.parse_penalty_rows(team_tables[1].find_all("tr"), team_right)

        return pd.concat([penalties_left, penalties_right], ignore_index=True)
    