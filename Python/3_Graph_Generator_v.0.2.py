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
OUTPUT_DIR = os.path.join( SCRIPT_DIR, "..", "HTML")

# Adjusting the color palette
rgb_color_palette = {
    'background-color': 'rgb(255, 255, 255)', 
    'color': 'rgb(0, 0, 139)',  # dark blue
    'alternate-color': 'rgb(217, 89, 98)',
    'line-colors': ['rgb(0, 0, 139)', 'rgb(135, 206, 235)', 'rgb(70, 130, 180)'],  # shades of blue
    'bar-colors': ['rgb(10, 116, 138)', 'rgb(10, 140, 120)', 'rgb(10, 165, 100)'],  # shades of orange/red
    'pie-colors': ['rgb(50, 205, 50)', 'rgb(152, 251, 152)', 'rgb(0, 128, 0)']  # shades of green
}

def save_and_plot_player_graphs_and_tables(city_name, season_points, season, season_sorted_dict):
    directory_path = os.path.join(OUTPUT_DIR, city_name, f"s{season}", "player_graphs")
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    points = season_points[season_points['Season'] == season]
    players = points['Player'].unique()

    for player in players:
        # Create player performance table
        player_data_season = season_points[season_points['Season'] == season]
        player_data = player_data_season[player_data_season['Player'] == player]
        season_sorted = season_sorted_dict.get(season)

        if season_sorted is not None and not player_data.empty:
            player_summary = season_sorted[season_sorted['Player'] == player]
            player_summary_df = player_summary.drop(columns=['Player']).T
            player_summary_df.columns = [player]
            
            # Create player performance graph
            fig = make_subplots(
                rows=5, cols=1,
                shared_xaxes=True,
                subplot_titles=('Summary Table', 'Total Points per Gameweek', 'Goals per Gameweek', 'Game Outcomes', 'Defensive and Midfield Scores per Gameweek'),
                vertical_spacing=0.05,
                row_heights=[0.3, 0.2, 0.2, 0.1, 0.2],
                specs=[[{'type': 'table'}], [{}], [{}], [{}], [{}]]
            )

            # Add table to the subplot figure
            fig.add_trace(go.Table(
                header=dict(values=['Metrics', player],
                            fill_color=rgb_color_palette['background-color'],
                            font_color=rgb_color_palette['color'],
                            font=dict(size=16)),
                cells=dict(values=[player_summary_df.index, player_summary_df[player]],
                        fill_color=[rgb_color_palette['background-color'], 'white'],
                        font_color=[rgb_color_palette['color'], 'black'],
                        font=dict(size=14)),
            ), row=1, col=1)

            # Add other plots to the subplot figure
            fig.add_trace(go.Scatter(x=player_data['Gameweek'], y=player_data['Total Points'], mode='lines+markers', name='Total Points', line_color=rgb_color_palette['line-colors'][0]), row=2, col=1)
            fig.add_trace(go.Bar(x=player_data['Gameweek'], y=player_data['Goal Points'], name='Goals', marker_color=rgb_color_palette['bar-colors'][0]), row=3, col=1)
            game_outcomes = player_data['Game Outcome'].value_counts()
            fig.add_trace(go.Bar(y=game_outcomes.index, x=game_outcomes, name='Game Outcomes', orientation='h', marker_color=rgb_color_palette['bar-colors']), row=4, col=1)
            fig.add_trace(go.Scatter(x=player_data['Gameweek'], y=player_data['Defensive Score Points'], mode='lines+markers', name='Defensive Score', line_color=rgb_color_palette['line-colors'][1]), row=5, col=1)
            fig.add_trace(go.Scatter(x=player_data['Gameweek'], y=player_data['Midfield Score'], mode='lines+markers', name='Midfield Score', line_color=rgb_color_palette['line-colors'][2]), row=5, col=1)
            
            # Update layout
            fig.update_layout(
                title=f"Performance of {player} in Season {season}",
                title_font=dict(size=20),
                hovermode="x",
                plot_bgcolor=rgb_color_palette['background-color'],
                paper_bgcolor=rgb_color_palette['background-color'],
                font_color=rgb_color_palette['color']
            )
            #fig.update_xaxes(title_text="Gameweek")
            fig.update_xaxes(fixedrange=True)
            fig.update_yaxes(fixedrange=True, title_text="Points", row=2, col=1)
            fig.update_yaxes(fixedrange=True, title_text="Goals", row=3, col=1)
            fig.update_yaxes(fixedrange=True, title_text="Game Outcomes", row=4, col=1)
            fig.update_yaxes(fixedrange=True, title_text="Points", row=5, col=1)
            fig.update_yaxes(gridcolor='rgb(200, 200, 200)', zerolinecolor='rgb(200, 200, 200)')

            # Save graph to HTML
            fig.write_html(f"{directory_path}/{player}.html")

    return f"Combined graphs and tables for Season {season} are saved successfully."

if os.path.exists(INPUT_DIR):
    for city_folder in os.listdir(INPUT_DIR):
        city_folder_path = os.path.join(INPUT_DIR, city_folder)
        if os.path.isdir(city_folder_path):
            city_name = city_folder

            points_path = os.path.join(city_folder_path, f"points_{city_name}.xlsx")
            season1_path = os.path.join(city_folder_path, f"season1_{city_name}.xlsx")
            season2_path = os.path.join(city_folder_path, f"season2_{city_name}.xlsx")

            if all(os.path.exists(p) for p in [points_path, season1_path, season2_path]):
                points = pd.read_excel(points_path)
                season1_sorted = pd.read_excel(season1_path)
                season2_sorted = pd.read_excel(season2_path)

                # Initialize season_sorted_dict for this city
                local_season_sorted_dict = {
                    1: season1_sorted,
                    2: season2_sorted,
                }

                save_and_plot_player_graphs_and_tables(city_name, points, 1, local_season_sorted_dict)
                save_and_plot_player_graphs_and_tables(city_name, points, 2, local_season_sorted_dict)
else:
    print(f"Input directory {INPUT_DIR} does not exist.")