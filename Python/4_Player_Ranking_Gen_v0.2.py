import pandas as pd
import os
from bs4 import BeautifulSoup

# Use os.path.abspath to get the absolute path of the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, os.environ.get("INPUT_DIR", os.path.join("..", "Excel")))  # default is "../Excel"
OUTPUT_DIR = os.path.join( SCRIPT_DIR, os.environ.get("OUTPUT_DIR", os.path.join("..", "HTML")))  # default is "../HTML"


def update_player_summary(city_name, season_number, file_sorted):
    df = pd.read_excel(file_sorted)

    # Updated URL for GitHub Pages (use relative URLs)
    df['Player'] = df['Player'].apply(
        lambda x: f'<a href="./{city_name}/s{season_number}/player_graphs/{x}.html">{x}</a>'
    )
    
    html_string = df.to_html(escape=False, index=False)
    html_complete = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Players Summary</title>
        <!-- Updated URL for GitHub Pages -->
        <link rel="stylesheet" href="./Styles/styles_table.css">
    </head>
    <body>
        <div id="table-container">
            {html_string}
        </div>
    </body>
    </html>
    """
    
    city_output_dir = os.path.join(OUTPUT_DIR, city_name, f"s{season_number}")
    os.makedirs(city_output_dir, exist_ok=True)
    
    output_path = os.path.join(city_output_dir, f"players_summary_s{season_number}.html")
    
    with open(output_path, 'w') as f:
        f.write(html_complete)
        
    return f"HTML updated for season {season_number} and saved to {output_path}"

# Loop through each directory (each representing a city)
for city_folder in os.listdir(INPUT_DIR):
    city_folder_path = os.path.join(INPUT_DIR, city_folder)

    if os.path.isdir(city_folder_path):
        city_name = city_folder
        
        season1_path = os.path.join(city_folder_path, f"season1_{city_name}.xlsx")
        season2_path = os.path.join(city_folder_path, f"season2_{city_name}.xlsx")
        
        if all(os.path.exists(p) for p in [season1_path, season2_path]):
            update_player_summary(city_name, 1, season1_path)
            update_player_summary(city_name, 2, season2_path)
