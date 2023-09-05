import os
from io import BytesIO

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Constants
RGB_COLOR_PALETTE = {
    'background': 'rgb(255, 255, 255)',
    'text': 'rgb(0, 0, 139)',
    'alternate': 'rgb(217, 89, 98)',
    'line': ['rgb(0, 0, 139)', 'rgb(135, 206, 235)', 'rgb(70, 130, 180)'],
    'bar': ['rgb(10, 116, 138)', 'rgb(10, 140, 120)', 'rgb(10, 165, 100)'],
    'pie': ['rgb(50, 205, 50)', 'rgb(152, 251, 152)', 'rgb(0, 128, 0)']
}

def plot_graph(fig, row, col, x_data, y_data, name, plot_type, color_index):
    """Utility function to plot graph based on the plot_type."""
    if plot_type == 'scatter':
        fig.add_trace(go.Scatter(x=x_data, y=y_data, mode='lines+markers', name=name,
                                 line_color=RGB_COLOR_PALETTE['line'][color_index]), row=row, col=col)
    elif plot_type == 'bar':
        fig.add_trace(go.Bar(x=x_data, y=y_data, name=name,
                             marker_color=RGB_COLOR_PALETTE['bar'][color_index]), row=row, col=col)


def save_and_plot_total_player_graphs_and_tables(city_name, total_points, total_sorted):
    """Generate and save player graphs and tables for a given city for all seasons."""
    directory_path = os.path.join("HTML", city_name, "total_player_graphs")
    os.makedirs(directory_path, exist_ok=True)
    
    players = total_points['Player'].unique()

    for player in players:
        player_data = total_points[total_points['Player'] == player].copy()
        
        if total_sorted is None or player_data.empty:
            continue

        player_summary = total_sorted[total_sorted['Player'] == player].drop(columns=['Player']).T
        player_summary.columns = [player]
        
        # Create gameweek identifier across seasons
        player_data['Gameweek_Season'] = player_data['Gameweek'].astype(str) + '.' + player_data['Season'].astype(str)

        fig = make_subplots(
            rows=5, cols=1,
            shared_xaxes=True,
            subplot_titles=('Summary Table', 'Total Points per Gameweek', 'Goals per Gameweek', 'Game Outcomes', 'Defensive and Midfield Scores per Gameweek'),
            vertical_spacing=0.05,
            row_heights=[0.3, 0.2, 0.2, 0.1, 0.2],
            specs=[[{'type': 'table'}], [{}], [{}], [{}], [{}]]
        )

        fig.add_trace(go.Table(
            header=dict(
                values=['Metrics', player],
                fill_color=RGB_COLOR_PALETTE['background'],
                font_color=RGB_COLOR_PALETTE['text'],
                font=dict(size=16)
            ),
            cells=dict(
                values=[player_summary.index, player_summary[player]],
                fill_color=[RGB_COLOR_PALETTE['background'], 'white'],
                font_color=[RGB_COLOR_PALETTE['text'], 'black'],
                font=dict(size=14)
            )
        ), row=1, col=1)

        plot_graph(fig, 2, 1, player_data['Gameweek_Season'], player_data['Total Points'], 'Total Points', 'scatter', 0)
        plot_graph(fig, 3, 1, player_data['Gameweek_Season'], player_data['Goal Points'], 'Goals', 'bar', 0)
        game_outcomes = player_data['Game Outcome'].value_counts()
        plot_graph(fig, 4, 1, game_outcomes.index, game_outcomes, 'Game Outcomes', 'bar', 1)
        plot_graph(fig, 5, 1, player_data['Gameweek_Season'], player_data['Defensive Score Points'], 'Defensive Score', 'scatter', 1)
        plot_graph(fig, 5, 1, player_data['Gameweek_Season'], player_data['Midfield Score'], 'Midfield Score', 'scatter', 2)

        fig.update_layout(
            title=f"Total Performance of {player}",
            title_font=dict(size=20),
            hovermode="x",
            plot_bgcolor=RGB_COLOR_PALETTE['background'],
            paper_bgcolor=RGB_COLOR_PALETTE['background'],
            font_color=RGB_COLOR_PALETTE['text']
        )

        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True, title_text="Points", row=2, col=1)
        fig.update_yaxes(fixedrange=True, title_text="Goals", row=3, col=1)
        fig.update_yaxes(fixedrange=True, title_text="Game Outcomes", row=4, col=1)
        fig.update_yaxes(fixedrange=True, title_text="Points", row=5, col=1)

        fig.write_html(f"{directory_path}/{player}.html")
    return f"Combined graphs and tables for all seasons are saved successfully."

# Main function
def main():
    city_name = 'Milano'
    total_points = pd.read_excel(os.path.join('Excel', 'Milano', 'points_Milano.xlsx'))
    total_sorted = pd.read_excel(os.path.join('Excel', 'Milano', 'total_Milano.xlsx'))
    save_and_plot_total_player_graphs_and_tables(city_name, total_points, total_sorted)

# Run main function
if __name__ == '__main__':
    main()