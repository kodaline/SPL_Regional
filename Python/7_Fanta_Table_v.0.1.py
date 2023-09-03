import os
import pandas as pd


def get_directory_paths():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "../Input")
    excel_dir = os.path.join(script_dir, "../Excel")
    output_dir = os.path.join(script_dir, "../HTML")
    return input_dir, excel_dir, output_dir


def load_and_process_data():
    input_dir, excel_dir, _ = get_directory_paths()

    fanta_spl_path = os.path.join(input_dir, "FantaSquadre", "FantaSquadre_Milano.xlsx")
    season_points_path = os.path.join(excel_dir, "Milano", "points_Milano.xlsx")

    fanta_spl_data = pd.read_excel(fanta_spl_path)
    season_points = pd.read_excel(season_points_path)
    season_points = season_points[season_points["Season"] == 2]

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

    merged_data = player_selection.merge(
        season_points[['Player', 'Total Points']], left_on='Selection', right_on='Player', how='left'
    )

    summary_data = (
        merged_data.groupby(['Nome e Cognome', 'Nome della tua squadra FantaSPL'])
        .agg({'Total Points': 'sum'})
        .reset_index()
        .sort_values(by='Total Points', ascending=False)
        .reset_index(drop=True)
    )

    summary_data.rename(
        columns={
            'Nome e Cognome': 'Player Name',
            'Nome della tua squadra FantaSPL': 'Fantasy Team Name',
            'Total Points': 'Total Points Scored'
        },
        inplace=True
    )

    # Calculate Rank after renaming the 'Total Points' column
    summary_data['Rank'] = summary_data['Total Points Scored'].rank(method='min', ascending=False).astype(int)

    # Reorder the columns
    summary_data = summary_data[['Rank', 'Fantasy Team Name', 'Total Points Scored']]

    return summary_data


def save_excel(df, filename):
    df.to_excel(filename, index=False)


def generate_html_from_dataframe(df):
    html_start = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Team Summary</title>
    <link href="../../Styles/styles_table2.css" rel="stylesheet"/>
    <style>
        .container {
            max-width: 100%;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <table border="1" class="dataframe">
    """

    html_headers = "  <thead>\n    <tr style=\"text-align: right;\">\n" + \
                   "".join([f"      <th>{col}</th>\n" for col in df.columns]) + \
                   "    </tr>\n  </thead>\n"

    html_body = "  <tbody>\n" + \
                "".join([
                    "    <tr>\n" +
                    "".join([
                        f"      <td>{int(val) if pd.api.types.is_number(val) else val}</td>\n"
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


def save_html(html_content, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_content)


if __name__ == "__main__":
    input_dir, excel_dir, output_dir = get_directory_paths()

    summary_data = load_and_process_data()

    excel_output_path = os.path.join(excel_dir, "Milano", "FantaSPL_Classifica.xlsx")
    os.makedirs(os.path.dirname(excel_output_path), exist_ok=True)
    save_excel(summary_data, excel_output_path)

    html_output_path = os.path.join(output_dir, "Milano", "FantaSPL_Classifica.html")
    os.makedirs(os.path.dirname(html_output_path), exist_ok=True)
    generated_html = generate_html_from_dataframe(summary_data)
    save_html(generated_html, html_output_path)
