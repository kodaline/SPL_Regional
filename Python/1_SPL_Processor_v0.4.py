import pandas as pd
import math
import os

# Constants
# Use os.path.abspath to get the absolute path of the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, "..", "Input")
OUTPUT_DIR = os.path.join( SCRIPT_DIR, "..", "Excel")
SHEET_NAMES = ['Games', 'Parameters', 'Points', 'Players']

# Load Data
def load_data(file_path, sheet_names):
    return pd.read_excel(file_path, sheet_name=sheet_names)

# Preprocessing Games Data
def preprocess_games_df(games_df, points_df):
    games_df['Winning Team'] = games_df.apply(calculate_winning_team, axis=1)
    games_df['Season'] = games_df['Date'].apply(lambda x: 1 if 1 <= x.month <= 7 and x.year == 2023 else 2)
    games_df['Gameweek'] = games_df.groupby('Season').cumcount() + 1
    games_df = games_df.merge(points_df.groupby('Date').size().rename('Number of Players'), left_on='Date', right_index=True, how='left')
    games_df['Match Type'] = games_df['Number of Players'].apply(determine_match_type)
    return games_df[['Date', 'Season', 'Gameweek', 'Match Type', 'Winning Team', 'Team A Goals', 'Team B Goals', 'Number of Players']]

# Helper Functions
def calculate_winning_team(row):
    if row['Team A Goals'] > row['Team B Goals']:
        return 'Team A'
    elif row['Team A Goals'] < row['Team B Goals']:
        return 'Team B'
    else:
        return 'Draw'

def determine_match_type(num_players):
    if num_players <= 10:
        return '5-a-side'
    elif 10 < num_players < 17:
        return '7-a-side'
    else:
        return '11-a-side'

def get_game_outcome(goal_diff):
    return 'Draw' if goal_diff == 0 else ('Win' if goal_diff > 0 else 'Loss')

# Point Calculations
def calculate_points(points_df, games_df, players_df, parameters_dict):
    position_dict = {
        '5-a-side': players_df.set_index('Player')['Position 5 a-side'].to_dict(),
        '7-a-side': players_df.set_index('Player')['Position 7-a-side'].to_dict(),
        '11-a-side': players_df.set_index('Player')['Position 11-a-side'].to_dict()
    }
    
    points_df = points_df.merge(games_df, on='Date', how='left')
    
    points_df['Position'] = points_df.apply(lambda row: row['Game Position'] if pd.notna(row['Game Position']) else position_dict[row['Match Type']].get(row['Player'], 'Unknown'), axis=1)
    points_df.drop("Game Position", axis=1, inplace=True)
    
    # Additional calculations
    points_df['Goal Difference'] = points_df.apply(calculate_goal_difference, axis=1)
    points_df['Game Outcome'] = points_df['Goal Difference'].apply(get_game_outcome)
    points_df = calculate_scores(points_df, parameters_dict)
    
    return points_df

def calculate_goal_difference(row):
    if row['Team'] == 'Team A':
        return row['Team A Goals'] - row['Team B Goals']
    return row['Team B Goals'] - row['Team A Goals']

def calculate_scores(df, parameters_dict):
    # Participation Points
    df['Participation Points'] = df['Match Type'].apply(lambda x: parameters_dict[x]['Participation'])

    # Points based on parameters
    for column, param in [('Goals', 'Goal'), ('Own Goals', 'Own Goal'), ('SPL Bonus', 'SPL Bonus'),
                          ('MVP', 'MVP'), ('Friend Referrals', 'Friend Referrals'), ('Penalty', 'Penalty')]:
        df[f'{param} Points'] = df.apply(lambda row: row[column] * parameters_dict[row['Match Type']][param], axis=1)

    df['Goalkeeper Points'] = df.apply(lambda row: parameters_dict[row['Match Type']]['Goalkeeper Score'] if row['Position'] == 'Goalkeeper' else 0, axis=1)
    df['Goals Conceded'] = df.apply(lambda row: row['Team B Goals'] if row['Team'] == 'Team A' else row['Team A Goals'], axis=1)
    df['Defensive Score Points'] = df.apply(calculate_defensive_score, axis=1)
    df['Midfield Score'] = df.apply(calculate_midfield_score, axis=1)
    df['Game Outcome Points'] = df.apply(lambda row: parameters_dict[row['Match Type']][row['Game Outcome']], axis=1)

    # Sum all points
    columns_to_sum = ['Participation Points', 'Goal Points', 'Own Goal Points', 'SPL Bonus Points', 
                      'MVP Points', 'Friend Referrals Points', 'Goalkeeper Points', 'Defensive Score Points', 'Midfield Score', 'Penalty Points', 'Game Outcome Points']
    df['Total Points'] = df[columns_to_sum].sum(axis=1)
    
    return df

def calculate_defensive_score(row):
    base_score = parameters_dict[row['Match Type']]['Defensive Score'] - row['Goals Conceded']
    if row['Position'] in ['Goalkeeper', 'Defender', 'Defensive']:
        return max(base_score, 0)
    if row['Position'] in ['Midfielder', 'Outfield']:
        return max(math.ceil(base_score / 2), 0)
    if row['Position'] in ['Forward', 'Offensive']:
        return 0
    return 'Unknown'

def calculate_midfield_score(row):
    if row['Position'] in ['Midfielder', 'Offensive', 'Outfield']:
        return max(row['Goal Difference'], 0)
    if row['Position'] == 'Forward':
        return max(math.ceil(row['Goal Difference'] / 2), 0)
    return 0

# Main code
if __name__ == "__main__":
    for file_name in os.listdir(INPUT_DIR):
        if file_name.endswith(".xlsx"):
            FILE_PATH = os.path.join(INPUT_DIR, file_name)

            # Extract the city name
            city_name = file_name.split('_')[1].replace('.xlsx', '')

            # Main Execution for each file
            all_dfs = load_data(FILE_PATH, SHEET_NAMES)
            games_df = preprocess_games_df(all_dfs['Games'], all_dfs['Points'])
            parameters_dict = all_dfs['Parameters'].set_index('Parameter').to_dict()
            points_calculation = calculate_points(all_dfs['Points'], games_df, all_dfs['Players'], parameters_dict)

            # Create an output directory for the city
            output_folder_path = os.path.join(OUTPUT_DIR, city_name)
            if not os.path.exists(output_folder_path):
                os.makedirs(output_folder_path)

            # Save the points DataFrame as an Excel file in the new directory
            points_excel = os.path.join(output_folder_path, f"points_{city_name}.xlsx")
            points_calculation.to_excel(points_excel, index=False)

            # Save the games_df DataFrame as an Excel file in the new directory
            games_excel = os.path.join(output_folder_path, f"games_{city_name}.xlsx")
            games_df.to_excel(games_excel, index=False)
