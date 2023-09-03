import os
import pandas as pd

def get_directory_paths():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to the 'SPL_Regional' directory
    parent_dir = os.path.dirname(script_dir)
    input_dir = os.path.join(parent_dir, "Input", "FantaSquadre")
    excel_dir = os.path.join(parent_dir, "Excel", "Milano")
    output_dir = os.path.join(parent_dir, "HTML", "Milano", "FantaTeams")
    return input_dir, excel_dir, output_dir

input_dir, excel_dir, draft_output_dir = get_directory_paths()

def load_and_process_detailed_data():
    # Path to the data files
    fanta_spl_path = os.path.join(input_dir, "FantaSquadre_Milano.xlsx")
    season_points_path = os.path.join(excel_dir, "points_Milano.xlsx")
    
    if not os.path.exists(fanta_spl_path):
        raise FileNotFoundError(f"File not found: {fanta_spl_path}")

    if not os.path.exists(season_points_path):
        raise FileNotFoundError(f"File not found: {season_points_path}")
    
    # Load the data
    fanta_spl_data = pd.read_excel(fanta_spl_path)
    season_points = pd.read_excel(season_points_path)
    season_points = season_points[season_points["Season"] == 2]
    
    # Melt and explode the fanta_spl_data to get one row for each player in each team
    player_selection = (
        fanta_spl_data.melt(
            id_vars=['Nome e Cognome', 'Nome della tua squadra FantaSPL'],
            value_vars=fanta_spl_data.columns[3:],
            value_name='Selection')
        .drop(columns="variable")
        .assign(Selection=lambda x: x['Selection'].str.split(', '))
        .explode('Selection')
        .reset_index(drop=True)
    )
    
    # Merge the data to get stats for each selected player
    merged_data = player_selection.merge(
        season_points, left_on='Selection', right_on='Player', how='left'
    )
    
    # Fill NaN values with zero for stats
    stats_columns = season_points.columns.difference(['Player', 'Season'])
    merged_data[stats_columns] = merged_data[stats_columns].fillna(0)
    
    # Drop duplicate columns
    merged_data.drop(columns=["Player"], inplace=True)
    
    # Group by team, owner, and player, then sum up the points for each player under each team
    aggregated_data = (
        merged_data.groupby(['Nome e Cognome', 'Nome della tua squadra FantaSPL', 'Selection'])
        .agg({'Total Points': 'sum'})
        .reset_index()
    )
    
    # Now aggregate again to create a list of players and their total points under each team
    aggregated_data = (
        aggregated_data.groupby(['Nome e Cognome', 'Nome della tua squadra FantaSPL'])
        .agg({
            'Selection': list,
            'Total Points': list,
        })
        .reset_index()
    )
    
    return aggregated_data

# Function to generate HTML content for a DataFrame specific to this use-case
def generate_team_html_from_dataframe(df, team_name, owner_name):
    # Calculating summary statistics
    total_points = df['Total Points'].sum()  # Sum up the points of all players in the team
    avg_points = df['Total Points'].mean()  # Calculate the average points per player in the team
    
    html_start = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{team_name} Summary</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
        }}
        .container {{
            max-width: 100%;
            overflow-x: auto;
        }}
        .header {{
            background-color: #f1f1f1;
            padding: 20px;
            text-align: center;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            border: 1px solid black;
            text-align: left;
            padding: 8px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{team_name}</h1>
        <h2>Owned by {owner_name}</h2>
    </div>
    <div class="container">
        <h3>Team Summary:</h3>
        <p>Total Points: {total_points}</p>
        <p>Average Points per Player: {avg_points:.2f}</p>
        <table class="dataframe">
    """
    
    html_headers = "  <thead>\n    <tr>\n" + \
                   "".join([f"      <th>{col}</th>\n" for col in df.columns]) + \
                   "    </tr>\n  </thead>\n"
    
    html_body = "  <tbody>\n" + \
                "".join([
                    "    <tr>\n" +
                    "".join([
                        f"      <td>{val}</td>\n"
                        for val in row]) +
                    "    </tr>\n"
                    for _, row in df.iterrows()
                ]) + \
                "  </tbody>\n"
    
    html_end = """
        </table>
    </div>
</body>
</html>
"""
    
    return html_start + html_headers + html_body + html_end



# Function to save each team's data as an HTML file
def save_team_html_files(aggregated_data, output_dir):
    for _, row in aggregated_data.iterrows():
        team_name = row['Nome della tua squadra FantaSPL']
        owner_name = row['Nome e Cognome']
        
        # Create DataFrame for this specific team
        team_df = pd.DataFrame({
            'Player': row['Selection'],
            'Total Points': row['Total Points']
        })
        
        # Generate HTML content
        html_content = generate_team_html_from_dataframe(team_df, team_name, owner_name)
        
        # Save HTML file
        output_path = os.path.join(output_dir, f"{team_name}.html")
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(html_content)


# Creating a draft directory for saving the HTML files
os.makedirs(draft_output_dir, exist_ok=True)

# Saving HTML files for each team
detailed_data_aggregated = load_and_process_detailed_data()
save_team_html_files(detailed_data_aggregated, draft_output_dir)






    