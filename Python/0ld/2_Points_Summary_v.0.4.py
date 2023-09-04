import os
import pandas as pd

def compute_player_summaries(points_df):
    """Compute player summaries based on the provided data."""
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
    player_summary = points_df.groupby('Player').agg(aggregations)
    player_summary.columns = ['_'.join(col).strip() for col in player_summary.columns.values]
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
    games_won = points_df[points_df['Team'] == points_df['Winning Team']].groupby('Player').size()
    player_summary['Games Won'] = games_won
    player_summary['Games Won'].fillna(0, inplace=True)
    player_summary['Win Ratio'] = player_summary['Games Won'] / player_summary['Games Played']
    return player_summary

def calculate_cumulative_points_and_rank(points_df):
    """Calculate cumulative points and rank changes for each player."""
    data_copy = points_df.copy()
    data_copy['Cumulative Points'] = data_copy.groupby('Player')['Total Points'].cumsum()
    data_copy['Rank'] = data_copy.groupby('Date')['Cumulative Points'].rank(method="first", ascending=False)
    data_sorted = data_copy.sort_values(by=['Player', 'Date'])
    data_sorted['Rank Change'] = data_sorted.groupby('Player')['Rank'].diff().fillna(0)
    latest_rank_change = data_sorted.groupby('Player').apply(lambda x: x.iloc[-1])['Rank Change']
    return latest_rank_change

def generate_summary(points_df):
    """Generate the final summary."""
    player_summary = compute_player_summaries(points_df)
    latest_rank_change = calculate_cumulative_points_and_rank(points_df)
    player_summary['Rank Change'] = latest_rank_change
    player_summary = player_summary.fillna(0)
    cols_to_int = ['Games Won', 'MVP', 'SPL Bonus', 'Rank Change']
    player_summary[cols_to_int] = player_summary[cols_to_int].astype(int)
    player_summary['Rank'] = player_summary['Total'].rank(method="min", ascending=False).astype(int)
    column_order = ['Rank'] + [col for col in player_summary if col != 'Rank']
    final_summary = player_summary[column_order]
    sorted_summary = final_summary.sort_values(by='Rank')
    for col in sorted_summary.columns:
        if sorted_summary[col].dtype == 'float64':
            sorted_summary[col] = sorted_summary[col].round(2)
    sorted_summary['Win Ratio'] = (sorted_summary['Win Ratio'] * 100).round(0).astype(int).astype(str) + '%'
    sorted_summary = sorted_summary.reset_index()
    desired_column_order = [
        "Player", "Rank", "Games Played", "Games Won", "Win Ratio", "Penalties", 
        "Friend Referrals", "Own Goals", "Goals Conceded", "MVP", "SPL Bonus",
        "GoalxG", "Total Goals", "PointsxG", 
        "Total", "Rank Change"
    ]
    sorted_summary = sorted_summary[desired_column_order]
    return sorted_summary

if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    INPUT_DIR = os.path.join(SCRIPT_DIR, "..", "Excel")
    OUTPUT_DIR = os.path.join( SCRIPT_DIR, "..", "Excel")

    for city_name in os.listdir(INPUT_DIR):
        city_path = os.path.join(INPUT_DIR, city_name)
        if not os.path.isdir(city_path):
            continue
        for file_name in os.listdir(city_path):
            if file_name.startswith("points_") and file_name.endswith(".xlsx"):
                file_path = os.path.join(city_path, file_name)
                points = pd.read_excel(file_path)
                data_S1 = points[points["Season"] == 1]
                data_S2 = points[points["Season"] == 2]
                season1_sorted = generate_summary(data_S1)
                season2_sorted = generate_summary(data_S2)
                output_folder_path = os.path.join(OUTPUT_DIR, city_name)
                if not os.path.exists(output_folder_path):
                    os.makedirs(output_folder_path)
                season1_excel = os.path.join(output_folder_path, f"season1_{city_name}.xlsx")
                season1_sorted.to_excel(season1_excel, index=False)
                season2_excel = os.path.join(output_folder_path, f"season2_{city_name}.xlsx")
                season2_sorted.to_excel(season2_excel, index=False)
