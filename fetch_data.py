from chessdotcom import get_player_game_archives, get_player_games_by_month, Client
import pandas as pd
import numpy as np
from datetime import datetime

# Set user-agent for the Chess.com API
Client.request_config["headers"]["User-Agent"] = (
    "Chess Analyzer App. Contact: mikayil.ahadli@gmail.com"
)

def fetch_games(username: str, start_date: str, end_date: str, time_class_filter: str = "all") -> pd.DataFrame:
    """
    Fetches and returns a DataFrame of games played by the given username
    between start_date and end_date, optionally filtered by time_class.
    Dates must be in 'YYYY-MM' format.
    """
    # Convert input dates
    start_dt = datetime.strptime(start_date, "%Y-%m")
    end_dt = datetime.strptime(end_date, "%Y-%m")

    # Get list of all played months
    archives_response = get_player_game_archives(username)
    all_months = [url[-7:].replace("/", "-") for url in archives_response.json['archives']]

    # Filter months within range
    selected_months = [
        month for month in all_months
        if start_date <= month <= end_date
    ]

    if not selected_months:
        raise ValueError("No games found in the selected date range or the user has no recorded games.")

    # Initialize empty DataFrame
    games_df = pd.DataFrame(columns=[
        'time_class', 'date', 'white', 'black', 'game_link',
        'opening_code', 'opening_name', 'opening_link', 'result',
        'white_elo', 'black_elo'
    ])

    # Fetch games for each month
    for month in selected_months:
        year, month_num = month.split("-")
        monthly_games = get_player_games_by_month(username, year=year, month=month_num)
        for game in monthly_games.json['games']:
            time_class = game['time_class']
            if time_class_filter != "all" and time_class != time_class_filter:
                continue

            pgn = game.get('pgn', '')
            if "ECOUrl" not in pgn:
                continue

            try:
                date = pgn[pgn.find("Date"):].split(" ")[1].split("]")[0].strip('\"')
                white = pgn[pgn.find("White"):].split(" ")[1].split("]")[0].strip('\"')
                black = pgn[pgn.find("Black"):].split(" ")[1].split("]")[0].strip('\"')
                game_link = pgn[pgn.find("Link"):].split(" ")[1].split("]")[0].strip('\"')
                opening_code = pgn[pgn.find("ECO"):].split(" ")[1].split("]")[0].strip('\"')
                opening_name = pgn[pgn.find("ECOUrl"):].split(" ")[1].split("]")[0].split("/")[-1].strip('\"')
                opening_link = pgn[pgn.find("ECOUrl"):].split(" ")[1].split("]")[0].strip('\"')
                termination = pgn[pgn.find("Termination"):].split(" ")[1].split("]")[0].strip('\"')
                result = 'Win' if username in termination else 'Loss'
                white_elo = int(pgn[pgn.find("WhiteElo"):].split(" ")[1].split("]")[0].strip('\"'))
                black_elo = int(pgn[pgn.find("BlackElo"):].split(" ")[1].split("]")[0].strip('\"'))
            except Exception:
                continue

            game_data = {
                'time_class': time_class,
                'date': date,
                'white': white,
                'black': black,
                'game_link': game_link,
                'opening_code': opening_code,
                'opening_name': opening_name,
                'opening_link': opening_link,
                'result': result,
                'white_elo': white_elo,
                'black_elo': black_elo
            }

            games_df = pd.concat([games_df, pd.DataFrame([game_data])], ignore_index=True)

    return games_df
