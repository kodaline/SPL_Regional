import pandas as pd
import math
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pandas.plotting import table
from matplotlib.table import table
from bs4 import BeautifulSoup
import base64
from io import BytesIO
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Use os.path.abspath to get the absolute path of the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, "..", "Excel")
OUTPUT_DIR = os.path.join( SCRIPT_DIR, "..", "Excel")

def compute_player_summaries(points_df):
    """
    Compute player summaries based on the provided data.
    
    Args:
    - points_df (pd.DataFrame): The input data containing player details and performance metrics.
    
    Returns:
    - pd.DataFrame: A summary dataframe containing computed metrics for each player.
    """
    # Define aggregation functions for the columns of interest
    aggregations = {
        'Date': 'count',
        'Penalty': 'sum',
        'Friend Referrals': 'sum',
        'Own Goals': 'sum',
        'Goals Conceded': 'sum',
        'Goals': ['mean', 'sum'],
        'Total Points': ['mean', 'sum'],
        'MVP': 'sum',
        'SPL Bonus': 'sum'
    }
    
    # Use groupby with multiple aggregation functions
    player_summary = points_df.groupby('Player').agg(aggregations)
    
    # Flatten hierarchical columns
    player_summary.columns = ['_'.join(col).strip() for col in player_summary.columns.values]
    
    # Rename columns for clarity
    columns_rename = {
        'Date_count': 'Games Played',
        'Penalty_sum': 'Penalties',
        'Friend Referrals_sum': 'Friend Referrals',
        'Own Goals_sum': 'Own Goals',
        'Goals Conceded_sum': 'Goals Conceded',
        'Goals_mean': 'GoalxG',
        'Goals_sum': 'Total Goals',
        'Total Points_mean': 'PointsxG',
        'Total Points_sum': 'Total',
        'MVP_sum': 'MVP',
        'SPL Bonus_sum': 'SPL Bonus'
    }
    player_summary.rename(columns=columns_rename, inplace=True)
    
    # Calculate games won
    games_won = points_df[points_df['Team'] == points_df['Winning Team']].groupby('Player').size()
    player_summary['Games Won'] = games_won
    player_summary['Games Won'].fillna(0, inplace=True)
    
    # Calculate win ratio
    player_summary['Win Ratio'] = player_summary['Games Won'] / player_summary['Games Played']
    
    return player_summary

def calculate_cumulative_points_and_rank(points_df):
    """
    Calculate cumulative points and rank changes for each player.
    
    Args:
    - points_df (pd.DataFrame): The input data containing player details and performance metrics.
    
    Returns:
    - pd.DataFrame: A dataframe containing the 'Rank Change' for the latest game for each player.
    """
    # Work with a deep copy to avoid modifying the original dataframe
    data_copy = points_df.copy()
    
    # Calculate cumulative Total Points for each player after each game
    data_copy['Cumulative Points'] = data_copy.groupby('Player')['Total Points'].cumsum()
    
    # Determine the player's rank based on these cumulative points after each game
    data_copy['Rank'] = data_copy.groupby('Date')['Cumulative Points'].rank(method="first", ascending=False)
    
    # Sort data to ensure we process in chronological order for each player
    data_sorted = data_copy.sort_values(by=['Player', 'Date'])
    
    # Calculate the change in rank between each game for every player
    data_sorted['Rank Change'] = data_sorted.groupby('Player')['Rank'].diff().fillna(0)
    
    # Extract the latest rank change for each player
    latest_rank_change = data_sorted.groupby('Player').apply(lambda x: x.iloc[-1])['Rank Change']
    
    return latest_rank_change
def generate_summary(points_df):
    # Integrate functions to generate the final summary
    player_summary = compute_player_summaries(points_df)
    latest_rank_change = calculate_cumulative_points_and_rank(points_df)

    # Add 'Rank Change' to the summary
    player_summary['Rank Change'] = latest_rank_change

    # Fill NaN values with 0
    player_summary = player_summary.fillna(0)

    # Convert specific columns to integer type
    cols_to_int = ['Games Won', 'MVP', 'SPL Bonus', 'Rank Change']
    player_summary[cols_to_int] = player_summary[cols_to_int].astype(int)

    # Calculate the overall rank based on the 'Total Points'
    player_summary['Rank'] = player_summary['Total'].rank(method="min", ascending=False).astype(int)

    # Reorder columns to have 'Rank' at the front
    column_order = ['Rank'] + [col for col in player_summary if col != 'Rank']
    final_summary = player_summary[column_order]

    # Sorting the final_summary DataFrame by 'Rank' in ascending order
    sorted_summary = final_summary.sort_values(by='Rank')

    # Reordering the columns as specified
    desired_column_order = [
        "Player", "Rank", "Games Played", "Games Won", "Win Ratio", "Penalties", 
        "Friend Referrals", "Own Goals", "Goals Conceded", "MVP", "SPL Bonus",
        "GoalxG", "Total Goals", "PointsxG", 
        "Total", "Rank Change"
    ]

    for col in sorted_summary.columns:
        if sorted_summary[col].dtype == 'float64':
            sorted_summary[col] = sorted_summary[col].round(2)
    sorted_summary['Win Ratio'] = (sorted_summary['Win Ratio'] * 100).round(0).astype(int).astype(str) + '%'
    
    # Reset index to get the "Player" column and then reorder columns
    sorted_summary = sorted_summary.reset_index()
    sorted_summary = sorted_summary[desired_column_order]
    
    return sorted_summary

if __name__ == "__main__":
    # Loop through each city directory inside the Excel folder
    for city_name in os.listdir(INPUT_DIR):
        city_path = os.path.join(INPUT_DIR, city_name)
        
        # Skip if it's not a directory
        if not os.path.isdir(city_path):
            continue
        
        # Loop through each points_xxx.xlsx file in the city directory
        for file_name in os.listdir(city_path):
            if file_name.startswith("points_") and file_name.endswith(".xlsx"):
                
                # Read the points file
                file_path = os.path.join(city_path, file_name)
                points = pd.read_excel(file_path)
                
                # Filter data by season
                data_S1 = points[points["Season"] == 1]
                data_S2 = points[points["Season"] == 2]
                
                # Generate summary data
                season1_sorted = generate_summary(data_S1)
                season2_sorted = generate_summary(data_S2)
                
                # Create an output directory for the city if it doesn't exist
                output_folder_path = os.path.join(OUTPUT_DIR, city_name)
                if not os.path.exists(output_folder_path):
                    os.makedirs(output_folder_path)
                
                # Save the summary files
                season1_excel = os.path.join(output_folder_path, f"season1_{city_name}.xlsx")
                season1_sorted.to_excel(season1_excel, index=False)
                
                season2_excel = os.path.join(output_folder_path, f"season2_{city_name}.xlsx")
                season2_sorted.to_excel(season2_excel, index=False)
