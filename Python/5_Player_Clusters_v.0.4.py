import os
os.environ["OMP_NUM_THREADS"] = "1"
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import Tuple


# Get the absolute path of the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define directories
INPUT_DIR = os.path.join(SCRIPT_DIR, os.environ.get("INPUT_DIR", "../Excel"))  # default is "../Excel"
OUTPUT_DIR = os.path.join( SCRIPT_DIR, os.environ.get("OUTPUT_DIR", "../HTML"))  # default is "../HTML"

def load_and_process_data(file_path: str) -> pd.DataFrame:
    """Load the data from a file and process it to get the aggregated data."""
    data = pd.read_excel(file_path)
    data = data[data["Season"]==1]

    agg_data = data.groupby('Player').agg({
        'Total Points': 'sum',
        'Goal Points': 'sum',
        'Defensive Score Points': 'sum',
        'Midfield Score': 'sum',
        'MVP Points': 'sum',
        'Date': 'count',
        'Position': lambda x: x.value_counts().index[0]
    }).rename(columns={'Date': 'Games Played'})

    agg_data['Average Points per Game'] = agg_data['Total Points'] / agg_data['Games Played']
    return agg_data

def determine_optimal_clusters(scaled_data: pd.DataFrame, min_clusters: int = 3, max_clusters: int = 5) -> int:
    """Determine the optimal number of clusters using the elbow method."""
    wcss = [KMeans(n_clusters=i, init='k-means++', n_init=10, random_state=42).fit(scaled_data).inertia_
            for i in range(min_clusters, max_clusters + 1)]
    diffs = np.diff(wcss)
    return np.argmin(diffs) + min_clusters + 1

def assign_clusters_and_prices(agg_data: pd.DataFrame, scaled_data: pd.DataFrame) -> pd.DataFrame:
    """Assign clusters and prices to the data."""
    optimal_clusters = determine_optimal_clusters(scaled_data)
    kmeans = KMeans(n_clusters=optimal_clusters, init='k-means++', n_init=10, random_state=42)
    agg_data['Cluster'] = kmeans.fit_predict(scaled_data)

    # Sort clusters by multiple criteria: Total Points, Games Played, and Average Points per Game.
    cluster_averages = agg_data.groupby('Cluster')[['Total Points', 'Games Played', 'Average Points per Game']].mean().sort_values(
        by=['Total Points', 'Games Played', 'Average Points per Game'], ascending=[False, False, False])

    prices = np.linspace(10, 2, num=optimal_clusters).round().astype(int)
    price_mapping = dict(zip(cluster_averages.index, prices))

    agg_data['Price (in $M)'] = agg_data['Cluster'].map(price_mapping)
    return agg_data

def cluster_summary(clustered_data: pd.DataFrame) -> pd.DataFrame:
    """Get a summary of the clustered data."""
    summary = clustered_data.groupby('Cluster').agg({
        'Total Points': ['count', 'mean'],
        'Games Played': ['mean'],
        'Average Points per Game': ['mean'],
        'Price (in $M)': 'first'
    }).reset_index()

    summary.columns = ['Cluster', 'Number of Players', 'Avg. Total Points', 'Average Games Played', 'Average Points/Game', 'Price (in $M)']
    return summary

def generate_html_table_for_cluster(cluster_id: int, summary: pd.Series, player_data: pd.DataFrame) -> str:
    """Generate HTML table for a specific cluster."""
    display_cluster_id = cluster_id + 1
    # Creating the summary table
    summary_table = f"""
    <table border="1">
        <thead>
            <tr>
                <th colspan="5">Group {display_cluster_id} - {summary.get('Price (in $M)', '')} $M </th>
            </tr>
            <tr>
                <th>N. Players</th>
                <th>Avg. Total Points</th>
                <th>Avg. Games </th>
                <th>Avg. Points xG</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>{summary.get('Number of Players', '')}</td>
                <td>{summary.get('Avg. Total Points', '')}</td>
                <td>{summary.get('Average Games Played', '')}</td>
                <td>{summary.get('Average Points/Game', '')}</td>
            </tr>
        </tbody>
    </table>
    """
    
    # Creating the players table
    players_rows = [
        f"<tr><td><a href='total_player_graphs/{player_name}.html'>{player_name}</a></td></tr>"
        for player_name in player_data['Player']
    ]
    
    players_table = f"""
    <table border="1" style="margin-top: 5px;">
        <thead>
            <tr>
                <th>Players in Group {display_cluster_id}</th>
            </tr>
        </thead>
        <tbody>
            {''.join(players_rows)}
        </tbody>
    </table>
    """
    
    return summary_table + players_table

def save_to_html(file_path: str, aggregated_data: pd.DataFrame) -> str:
    """Save the clustered data to an HTML file."""
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(aggregated_data.drop(columns='Position'))
    clustered_data = assign_clusters_and_prices(aggregated_data, scaled_data).reset_index().round(2)
    clustered_summary = cluster_summary(clustered_data).round(2)

    # Sort the summary by 'Price (in $M)' in ascending order
    clustered_summary = clustered_summary.sort_values(by='Price (in $M)', ascending=True)

    # Remap cluster IDs based on the sorted order.
    remap_dict = {old_cluster_id: new_cluster_id 
                  for new_cluster_id, old_cluster_id in enumerate(clustered_summary['Cluster'])}
    
    clustered_summary['Cluster'] = clustered_summary['Cluster'].map(remap_dict)
    clustered_data['Cluster'] = clustered_data['Cluster'].map(remap_dict)

    html_content = [
        '''<html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" type="text/css" href="../../Styles/styles_cluster.css">
            <link href="Images/favicon_32.png" rel="icon" type="image/png"/>
            <title>SPL Market</title>
        </head>
        <body>
        <div id="table-container">'''   # Start of the table container
    ]
    
    for _, summary_row in clustered_summary.iterrows():
        cluster_id = int(summary_row['Cluster'])
        players_in_cluster = clustered_data[clustered_data['Cluster'] == cluster_id]
        html_content.append(generate_html_table_for_cluster(cluster_id, summary_row, players_in_cluster))

    html_content.append("</div></body></html>")  # End of the table container
    final_html = '\n'.join(html_content)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(final_html)
    
    return file_path


output_path = os.path.join(OUTPUT_DIR, "Milano", "clustered_data_web.html")
# Ensure the output directory exists
os.makedirs(os.path.dirname(output_path), exist_ok=True)

if __name__ == '__main__':
    # Input and output paths based on directories
    file_path = os.path.join(INPUT_DIR, "Milano", "points_Milano.xlsx")
    
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"File {file_path} not found!")
    else:
        # Load and process data
        aggregated_data = load_and_process_data(file_path)
        print(aggregated_data)
        # Output path
        output_path = os.path.join(OUTPUT_DIR, "Milano", "clustered_data_web.html")

        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Generate and save the HTML output
        saved_path = save_to_html(output_path, aggregated_data)
        print(f"Clustered data saved to {saved_path}")
