from ift6758.data.shared_constants import (
    MAX_GAMES_PER_REGULAR_SEASON,
    MATCHUPS_PER_PLAYOFF_ROUND,
    MAX_GAMES_PER_PLAYOFF_ROUND
)

class NHLHelper:
    def get_game_ids_for_season(self, season: str, for_regular_season: bool) -> list:
        """Generates a list of game IDs for a season in the NHL

        Args:
            season (str): Season year
            for_regular_season (bool): Regular season: True or playoff season: False

        Returns:
            list: List of all the game IDs for a regular season or playoff season
        """
        game_ids = []

        if for_regular_season:
            for game_number in range(1, MAX_GAMES_PER_REGULAR_SEASON):
                game_ids.append(self.construct_regular_season_game_id(season, game_number))
        else:
            for round_num in range(0, 4):
                matchups = MATCHUPS_PER_PLAYOFF_ROUND[round_num]
                for match_num in range(1, matchups + 1):
                    for game_num in range(1, MAX_GAMES_PER_PLAYOFF_ROUND + 1):
                        game_ids.append(self.construct_playoff_season_game_id(
                            season,
                            round=round_num,
                            matchup=match_num,
                            game=game_num
                        ))

        return game_ids
    

    def construct_regular_season_game_id(self, season: str, game: int) -> str:
        """Generates game ID string for a regular season NHL game

        Args:
            season (str): Season year
            game (int): Game number (max in 2024 is 1312)

        Returns:
            str: Game ID
        """
        if game > 0 and game <= MAX_GAMES_PER_REGULAR_SEASON:
            return f'{season}02{str(game).zfill(4)}'
    

    def construct_playoff_season_game_id(self, season: str, round: int, matchup: int, game: int) -> str:
        """Generates game ID string for a playoff NHL game

        Args:
            season (str): Season year
            round (int): Round number (round 1 has 8 matchups, round 2 has 4 matchups, ...)
            matchup (int): Matchup number
            game (int): Game number (a specific matchup has a maximum of 7 games)

        Returns:
            str: Game ID
        """
        if round > 0 and round <= 4:
            if matchup > 0 and matchup <= MATCHUPS_PER_PLAYOFF_ROUND[round - 1]:
                return f"{season}030{round}{matchup}{game}"
        
        return None
    