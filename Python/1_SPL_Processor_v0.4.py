import math
import os
import pandas as pd
import warnings  # <-- Add this line

# Suppress specific warnings from 'openpyxl' 
warnings.filterwarnings(action='ignore', message='Data Validation extension is not supported and will be removed', module='openpyxl')


# Define constants for directory paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, "..", "Input")
OUTPUT_DIR = os.path.join( SCRIPT_DIR, "..", "Excel")

# Sheet names to be loaded
SHEET_NAMES = ['Games', 'Parameters', 'Points', 'Players']


def load_data(file_path, sheet_names):
    """
    Load data from Excel file.

    Parameters:
        file_path (str): Path to the Excel file.
        sheet_names (list): List of sheet names to load.

    Returns:
        dict: A dictionary containing dataframes for each sheet.
    """
    return pd.read_excel(file_path, sheet_name=sheet_names)


def preprocess_games_df(games_df, points_df):
    """
    Preprocess the games DataFrame.

    Parameters:
        games_df (DataFrame): The games DataFrame.
        points_df (DataFrame): The points DataFrame.

    Returns:
        DataFrame: The preprocessed games DataFrame.
    """
    # Calculate the winning team for each game
    games_df['Winning Team'] = games_df.apply(calculate_winning_team, axis=1)
    # Determine the season for each game
    games_df['Season'] = games_df['Date'].apply(lambda x: 1 if 1 <= x.month <= 7 and x.year == 2023 else 2)
    # Label gameweeks
    games_df['Gameweek'] = games_df.groupby('Season').cumcount() + 1
    # Merge with points_df to get the number of players for each date
    games_df = games_df.merge(points_df.groupby('Date').size().rename('Number of Players'), left_on='Date', right_index=True, how='left')
    # Determine match type based on number of players
    games_df['Match Type'] = games_df['Number of Players'].apply(determine_match_type)
    # Return only the relevant columns
    return games_df[['Date', 'Season', 'Gameweek', 'Match Type', 'Winning Team', 'Team A Goals', 'Team B Goals', 'Number of Players']]


def calculate_winning_team(row):
    """
    Determine the winning team.

    Parameters:
        row (Series): A row from the games DataFrame.

    Returns:
        str: 'Team A', 'Team B', or 'Draw'.
    """
    if row['Team A Goals'] > row['Team B Goals']:
        return 'Team A'
    elif row['Team A Goals'] < row['Team B Goals']:
        return 'Team B'
    else:
        return 'Draw'


def determine_match_type(num_players):
    """
    Determine the type of match based on the number of players.

    Parameters:
        num_players (int): The number of players.

    Returns:
        str: '5-a-side', '7-a-side', or '11-a-side'.
    """
    if num_players <= 10:
        return '5-a-side'
    elif 10 < num_players < 17:
        return '7-a-side'
    else:
        return '11-a-side'

def get_game_outcome(goal_diff):
    """
    Determine the game outcome based on goal difference.

    Parameters:
        goal_diff (int): The goal difference for the team.

    Returns:
        str: 'Draw', 'Win', or 'Loss'.
    """
    return 'Draw' if goal_diff == 0 else ('Win' if goal_diff > 0 else 'Loss')


def calculate_points(points_df, games_df, players_df, parameters_dict):
    """
    Calculate points for each player based on multiple factors.

    Parameters:
        points_df (DataFrame): The points DataFrame.
        games_df (DataFrame): The games DataFrame.
        players_df (DataFrame): The players DataFrame.
        parameters_dict (dict): Scoring parameters.

    Returns:
        DataFrame: The DataFrame with calculated points.
    """
    # Create a dictionary to hold player positions for different match types
    position_dict = {
        '5-a-side': players_df.set_index('Player')['Position 5 a-side'].to_dict(),
        '7-a-side': players_df.set_index('Player')['Position 7-a-side'].to_dict(),
        '11-a-side': players_df.set_index('Player')['Position 11-a-side'].to_dict()
    }
    
    # Merge the points DataFrame with the games DataFrame based on the 'Date' column
    points_df = points_df.merge(games_df, on='Date', how='left')
    
    # Assign positions to players
    points_df['Position'] = points_df.apply(
        lambda row: row['Game Position'] if pd.notna(row['Game Position']) else position_dict[row['Match Type']].get(row['Player'], 'Unknown'), 
        axis=1
    )
    
    # Drop the now redundant 'Game Position' column
    points_df.drop("Game Position", axis=1, inplace=True)
    
    # Additional point calculations
    # Calculate the goal difference for the team
    points_df['Goal Difference'] = points_df.apply(calculate_goal_difference, axis=1)
    # Determine the outcome of the game
    points_df['Game Outcome'] = points_df['Goal Difference'].apply(get_game_outcome)
    # Calculate the total score based on various factors
    points_df = calculate_scores(points_df, parameters_dict)
    
    return points_df


def calculate_goal_difference(row):
    """
    Calculate the goal difference for a team.

    Parameters:
        row (Series): A row from the points DataFrame.

    Returns:
        int: The goal difference for the team.
    """
    if row['Team'] == 'Team A':
        return row['Team A Goals'] - row['Team B Goals']
    return row['Team B Goals'] - row['Team A Goals']

def calculate_scores(df, parameters_dict):
    """
    Calculate various types of points for players.

    Parameters:
        df (DataFrame): DataFrame containing various scores for players.
        parameters_dict (dict): Dictionary containing scoring parameters.

    Returns:
        DataFrame: Updated DataFrame with calculated scores.
    """
    # Calculate Participation Points based on Match Type
    df['Participation Points'] = df['Match Type'].apply(lambda x: parameters_dict[x]['Participation'])
    
    # Calculate points based on various performance indicators like Goals, Own Goals, etc.
    for column, param in [('Goals', 'Goal'), ('Own Goals', 'Own Goal'), ('SPL Bonus', 'SPL Bonus'),
                          ('MVP', 'MVP'), ('Friend Referrals', 'Friend Referrals'), ('Penalty', 'Penalty')]:
        df[f'{param} Points'] = df.apply(lambda row: row[column] * parameters_dict[row['Match Type']][param], axis=1)
    
    # Calculate Goalkeeper Points
    df['Goalkeeper Points'] = df.apply(lambda row: parameters_dict[row['Match Type']]['Goalkeeper Score'] if row['Position'] == 'Goalkeeper' else 0, axis=1)
    
    # Calculate Goals Conceded
    df['Goals Conceded'] = df.apply(lambda row: row['Team B Goals'] if row['Team'] == 'Team A' else row['Team A Goals'], axis=1)
    
    # Calculate Defensive Score Points
    df['Defensive Score Points'] = df.apply(calculate_defensive_score, axis=1)
    
    # Calculate Midfield Score
    df['Midfield Score'] = df.apply(calculate_midfield_score, axis=1)
    
    # Calculate Game Outcome Points
    df['Game Outcome Points'] = df.apply(lambda row: parameters_dict[row['Match Type']][row['Game Outcome']], axis=1)
    
    # Sum all points to calculate the Total Points
    columns_to_sum = ['Participation Points', 'Goal Points', 'Own Goal Points', 'SPL Bonus Points', 
                      'MVP Points', 'Friend Referrals Points', 'Goalkeeper Points', 'Defensive Score Points', 'Midfield Score', 'Penalty Points', 'Game Outcome Points']
    df['Total Points'] = df[columns_to_sum].sum(axis=1)
    
    return df

def calculate_defensive_score(row):
    """
    Calculate the defensive score for a player.

    Parameters:
        row (Series): A row from the DataFrame.

    Returns:
        int or str: The defensive score or 'Unknown' if the position is not recognized.
    """
    # Initialize parameters dictionary (this should be defined elsewhere in the main script)
    # This is only for demonstration; remove this line in the real code
    # parameters_dict = ...
    
    base_score = parameters_dict[row['Match Type']]['Defensive Score'] - row['Goals Conceded']
    if row['Position'] in ['Goalkeeper', 'Defender', 'Defensive']:
        return max(base_score, 0)
    if row['Position'] in ['Midfielder', 'Outfield']:
        return max(math.ceil(base_score / 2), 0)
    if row['Position'] in ['Forward', 'Offensive']:
        return 0
    return 'Unknown'

def calculate_midfield_score(row):
    """
    Calculate the midfield score for a player.

    Parameters:
        row (Series): A row from the DataFrame.

    Returns:
        int: The midfield score.
    """
    if row['Position'] in ['Midfielder', 'Offensive', 'Outfield']:
        return max(row['Goal Difference'], 0)
    if row['Position'] == 'Forward':
        return max(math.ceil(row['Goal Difference'] / 2), 0)
    return 0

# Main code
if __name__ == "__main__":
    # Loop through each file in the directory
    for file_name in os.listdir(INPUT_DIR):
        if file_name.endswith(".xlsx"):
            FILE_PATH = os.path.join(INPUT_DIR, file_name)
            
            # Extract the city name from the filename
            city_name = file_name.split('_')[1].replace('.xlsx', '')
            
            # Load and preprocess data
            all_dfs = load_data(FILE_PATH, SHEET_NAMES)
            games_df = preprocess_games_df(all_dfs['Games'], all_dfs['Points'])
            parameters_dict = all_dfs['Parameters'].set_index('Parameter').to_dict()
            points_calculation = calculate_points(all_dfs['Points'], games_df, all_dfs['Players'], parameters_dict)
            
            # Create output directory for the city if it doesn't exist
            output_folder_path = os.path.join(OUTPUT_DIR, city_name)
            if not os.path.exists(output_folder_path):
                os.makedirs(output_folder_path)
            
            # Save calculated points and games data to Excel files
            points_excel = os.path.join(output_folder_path, f"points_{city_name}.xlsx")
            points_calculation.to_excel(points_excel, index=False)
            games_excel = os.path.join(output_folder_path, f"games_{city_name}.xlsx")
            games_df.to_excel(games_excel, index=False)
