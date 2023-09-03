import pandas as pd
import os

# Get the absolute path of the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define directories
INPUT_DIR = os.path.join(SCRIPT_DIR, "../Input")
EXCEL_DIR = os.path.join(SCRIPT_DIR, "../Excel")
OUTPUT_DIR = os.path.join( SCRIPT_DIR, "../HTML")

def load_and_process_data_inclusive():
    # Paths for the data files
    fanta_spl_path = os.path.join(INPUT_DIR, "FantaSquadre", "FantaSquadre_Milano.xlsx")
    season_points_path = os.path.join(EXCEL_DIR, "Milano", "points_Milano.xlsx")
    
    # Load the data
    fanta_spl_data = pd.read_excel(fanta_spl_path)
    player_points = pd.read_excel(season_points_path)
    player_points = player_points[player_points["Season"]==2]
    
    player_selection = (
        fanta_spl_data
        .melt(id_vars=['Nome e Cognome', 'Nome della tua squadra FantaSPL'], 
            value_vars=fanta_spl_data.columns[3:],
            value_name='Selection')
        .drop(columns="variable")
        .assign(Selection=lambda x: x['Selection'].str.split(', '))
        .explode('Selection')
        .reset_index(drop=True)
    )
    
    # Merge player_selection with player_points
    team_data_points = (
        player_selection
        .merge(player_points[['Player', 'Total Points']], left_on='Selection', right_on='Player', how='left')
    )
    
    # Compute total points for each fantasy team
    team_summary_points = (
        team_data_points.groupby(['Nome e Cognome', 'Nome della tua squadra FantaSPL'])
        .agg({'Total Points': 'sum'})
        .reset_index()
        .sort_values(by='Total Points', ascending=False)
        .reset_index(drop=True)
    )
    
    # Add Rank column based on Total Points
    team_summary_points['Rank'] = team_summary_points['Total Points'].rank(method='min', ascending=False).astype(int)
    
    # Rename columns for clarity
    column_name_mapping = {
        'Nome e Cognome': 'Player Name',
        'Nome della tua squadra FantaSPL': 'Fantasy Team Name',
        'Total Points': 'Total Points Scored'
    }
    team_summary_points.rename(columns=column_name_mapping, inplace=True)
    
    return team_summary_points

# Running the function
team_summary_inclusive_data = load_and_process_data_inclusive()

# Ensure the Excel output directory exists
excel_output_folder_path = os.path.join(EXCEL_DIR, "Milano")
os.makedirs(excel_output_folder_path, exist_ok=True)

team_summary_inclusive_data_excel = os.path.join(excel_output_folder_path, "FantaSPL_Classifica.xlsx")
team_summary_inclusive_data.to_excel(team_summary_inclusive_data_excel, index=False)

def generate_html_from_dataframe(df):
    # Create the basic structure for the HTML content
    html_string = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Team Summary</title>
        <link href="Styles/styles_table2.css" rel="stylesheet"/>
    </head>
    <body>
        <table border="1" class="dataframe">
    """
    
    # Add the table headers
    html_string += "  <thead>\n    <tr style=\"text-align: right;\">\n"
    for column in df.columns:
        html_string += f"      <th>{column}</th>\n"
    html_string += "    </tr>\n  </thead>\n"
    
    # Add the table rows
    html_string += "  <tbody>\n"
    for _, row in df.iterrows():
        html_string += "    <tr>\n"
        for value in row:
            html_string += f"      <td>{value}</td>\n"
        html_string += "    </tr>\n"
    html_string += "  </tbody>\n"
    
    # Close the table and HTML tags
    html_string += """
        </table>
    </body>
    </html>
    """
    
    return html_string

def save_html_to_file(html_content, filename):
    with open(filename, "w") as file:
        file.write(html_content)

# Ensure the HTML output directory exists
html_output_folder_path = os.path.join(OUTPUT_DIR, "Milano")
os.makedirs(html_output_folder_path, exist_ok=True)

# Saving the generated HTML content to a file
generated_html_content = generate_html_from_dataframe(team_summary_inclusive_data)
save_html_to_file(generated_html_content, os.path.join(html_output_folder_path, "FantaSPL_Classifica.html"))