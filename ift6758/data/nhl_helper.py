from ift6758.data.shared_constants import (
    MAX_GAMES_PER_REGULAR_SEASON,
    MATCHUPS_PER_PLAYOFF_ROUND,
    MAX_GAMES_PER_PLAYOFF_ROUND
)

class NHLHelper:
    def get_game_ids_for_season(self, season: str, for_regular_season: bool) -> list:
        game_ids = []

        if (for_regular_season):
            for game_number in range(1, MAX_GAMES_PER_REGULAR_SEASON):
                game_ids.append(f'{season}02{str(game_number).zfill(4)}')
        else:
            for round_num in range(0, 4):
                matchups = MATCHUPS_PER_PLAYOFF_ROUND[round_num]
                for match_num in range(1, matchups + 1):
                    for game_num in range(1, MAX_GAMES_PER_PLAYOFF_ROUND + 1):
                        game_ids.append(f"{season}030{round_num + 1}{match_num}{game_num}")

        return game_ids
    