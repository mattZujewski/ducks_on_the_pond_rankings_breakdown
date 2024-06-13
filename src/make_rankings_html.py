
import pandas as pd
import difflib
import plotly.graph_objects as go

fantasy_teams = {}
filters_colors = {1:"Starters",2:"Backup",3:"3rd String",4:"Deep Bench",5:"Deeper Bench"}
team_mapping = {"Geezers":"A Few Old Men",
                "LIAM":"Boot & Raleigh",
                "BARTO":"Gho-Strider",
                "reed":"Heimlich Maneuver",
                "BEIM":"Hold Me Closer, Ohtani Dancer",
                "PAP":"Mojo Dojo Casas House",
                "Tino":"Quentin Pasquantino",
                "JGC":"Rates & Carrolls",
                "Kirby":"The Kirby Superstars",
                "owenhern":"The New Murderers' Row",
                "Bird":"The Wire Nation",
                "DT":"Yoshi's Riland"}

def load_data(player_csv_path, ranking_csv_path):
    # Load the player and ranking data
    players = pd.read_csv(player_csv_path)
    rankings = pd.read_excel(ranking_csv_path)
    
    # Clean and merge the data
    players['Player Name'] = players['Player Name'].str.strip()
    rankings['Player Name'] = rankings['Player Name'].str.strip()
    merged_data = pd.merge(players, rankings[['Player Name', 'RANK']], on='Player Name', how='left')
    merged_data['RANK'] = merged_data['RANK'].fillna(500).astype(int)
    
    return merged_data

def match_closest_name(player_name, reference_list):
    # Find the closest match for the player name
    matches = difflib.get_close_matches(player_name, reference_list, n=1, cutoff=0.8)
    return matches[0] if matches else None

def assign_rankings(merged_data, rankings):
    # Assign closest matching rank to players
    reference_list = rankings['Player Name'].tolist()
    merged_data['RANK'] = merged_data.apply(
        lambda row: row['RANK'] if row['RANK'] != 500 else (
            rankings.loc[rankings['Player Name'] == match_closest_name(row['Player Name'], reference_list), 'RANK'].values[0]
            if match_closest_name(row['Player Name'], reference_list) else 500), axis=1
    )
    return merged_data



def assign_positions(merged_data):
    # Define the positions format
    positions_format = {
        'C': ['C-1', 'C-2'],
        '1B': ['1B'],
        '2B': ['2B'],
        '3B': ['3B'],
        'SS': ['SS'],
        'OF': ['OF-1', 'OF-2', 'OF-3', 'OF-4'],
        'UT': ['UT-1', 'UT-2'],
        'SP': ['SP-1', 'SP-2', 'SP-3', 'SP-4', 'SP-5', 'SP-6'],
        'RP': ['RP-1', 'RP-2', 'RP-3', 'RP-4']
    }

    # Initialize a list to store the assigned positions
    assigned_positions = []

    # Sort the merged data by rank and group by status
    merged_data = merged_data.sort_values(by=['Status', 'RANK'], ascending=[True, True])
    grouped_data = merged_data.groupby('Status')

    for status, group in grouped_data:
        # Initialize a dictionary to track filled positions
        positions = {slot: [] for pos_list in positions_format.values() for slot in pos_list}
        position_counters = {pos: 0 for pos in positions_format.keys()}  # Counter for each position type
        
        for _, row in group.iterrows():
            former_positions = row['Position'].split(',')
            assigned = False

            # Try to assign to one of the player's positions
            for pos in former_positions:
                if pos in positions_format:
                    start_idx = position_counters[pos] % len(positions_format[pos])
                    for i in range(len(positions_format[pos])):
                        slot = positions_format[pos][(start_idx + i) % len(positions_format[pos])]
                        if len(positions[slot]) == 0:  # Check if slot is empty
                            assigned_positions.append({
                                'Player Name': row['Player Name'],
                                'Position': row['Position'],
                                'roster_slot': slot,
                                'RANK': row['RANK'],
                                'Status': row['Status']
                            })
                            positions[slot].append({
                                'Player Name': row['Player Name'],
                                'roster_slot': slot,
                                'RANK': row['RANK'],
                                'Status': row['Status']
                            })
                            position_counters[pos] += 1
                            assigned = True
                            break
                if assigned:
                    break

            # If no slots are available in the player's positions, try to assign to UT
            if not assigned:
                for slot in positions_format['UT']:
                    if len(positions[slot]) == 0:  # Check if UT slot is empty
                        assigned_positions.append({
                            'Player Name': row['Player Name'],
                            'Position': row['Position'],
                            'roster_slot': slot,
                            'RANK': row['RANK'],
                            'Status': row['Status']
                        })
                        positions[slot].append({
                            'Player Name': row['Player Name'],
                            'roster_slot': slot,
                            'RANK': row['RANK'],
                            'Status': row['Status']
                        })
                        assigned = True
                        break

            # If no UT slots are available, add to the next eligible slot
            if not assigned:
                for pos in former_positions:
                    if pos in positions_format:
                        start_idx = position_counters[pos] % len(positions_format[pos])
                        for i in range(len(positions_format[pos])):
                            slot = positions_format[pos][(start_idx + i) % len(positions_format[pos])]
                            assigned_positions.append({
                                'Player Name': row['Player Name'],
                                'Position': row['Position'],
                                'roster_slot': slot,
                                'RANK': row['RANK'],
                                'Status': row['Status']
                            })
                            positions[slot].append({
                                'Player Name': row['Player Name'],
                                'roster_slot': slot,
                                'RANK': row['RANK'],
                                'Status': row['Status']
                            })
                            position_counters[pos] += 1
                            assigned = True
                            break
                    if assigned:
                        break

    # Convert the list of assigned positions to a DataFrame
    assigned_positions_df = pd.DataFrame(assigned_positions)
    
    return assigned_positions_df

def create_interactive_plot(assigned_positions_df):
    positions_format = {
        'C': ['C-1', 'C-2'],
        '1B': ['1B'],
        '2B': ['2B'],
        '3B': ['3B'],
        'SS': ['SS'],
        'OF': ['OF-1', 'OF-2', 'OF-3', 'OF-4'],
        'UT': ['UT-1', 'UT-2'],
        'SP': ['SP-1', 'SP-2', 'SP-3', 'SP-4', 'SP-5', 'SP-6'],
        'RP': ['RP-1', 'RP-2', 'RP-3', 'RP-4']
    }

    # Add the Inverted Rank column to the DataFrame
    assigned_positions_df['Inverted Rank'] = (14 - 12 * ((assigned_positions_df['RANK']) / 501))

    # Define a list of colors to cycle through for each slot position
    colors = ['#e6b800', '#b3b3b3', '#997300', '#e6e600', '#ffa64d']

    # Create the interactive plot with team dropdown and player list
    fig = go.Figure()
    dropdown_buttons = []
    team_names = assigned_positions_df['Status'].unique()

    # List to track the traces for each team
    traces = []
    trace_mapping = {}

    for status in team_names:
        slot_counts = {slot: 0 for pos_list in positions_format.values() for slot in pos_list}
        team_data = assigned_positions_df.loc[assigned_positions_df['Status'] == status]

        for pos_group in positions_format.values():
            for pos in pos_group:
                position_data = team_data.loc[team_data['roster_slot'] == pos]
                if not position_data.empty:
                    for _, player in position_data.iterrows():
                        slot_count = slot_counts[pos] 
                        trace_color = colors[slot_count % len(colors)]
                        trace = go.Bar(
                            x=[pos],
                            y=[player['Inverted Rank']],
                            name=f"{player['Player Name']} ({player['RANK']})",
                            hovertext=f"{player['Player Name']} - RANK: {player['RANK']}",
                            text=f"{player['Player Name']} ({player['RANK']})",
                            textposition='inside',
                            marker_color=trace_color,
                            visible=False  # All traces are initially hidden
                        )
                        traces.append(trace)
                        trace_mapping[(status, pos, player['Player Name'])] = trace
                        slot_counts[pos] += 1

    fig.add_traces(traces)

    # Create visibility masks for each team
    visibility_masks = {}
    for i, status in enumerate(team_names):
        visibility = [False] * len(traces)
        team_data = assigned_positions_df.loc[assigned_positions_df['Status'] == status]

        for pos_group in positions_format.values():
            for pos in pos_group:
                position_data = team_data.loc[team_data['roster_slot'] == pos]
                if not position_data.empty:
                    for _, player in position_data.iterrows():
                        visibility[traces.index(trace_mapping[(status, pos, player['Player Name'])])] = True

        visibility_masks[status] = visibility

    def get_toggle_color_buttons(status):
        color_buttons = []
        count = 0
        for color in colors:
            count += 1
            color_buttons.append(dict(
                label=f'{status}: {filters_colors[count]} <span style="color:{color}">&#9632;</span>',
                method='update',
                args=[{'visible': [trace.marker.color == color if visibility_masks[status][i] else False for i, trace in enumerate(traces)]},
                      {'title': f'{team_mapping[status]} Filtered {filters_colors[count]} '}]
            ))
        return color_buttons

    for status in team_names:
        visibility = visibility_masks[status]
        dropdown_buttons.append(dict(label=status,
                                     method='update',
                                     args=[{'visible': visibility},
                                           {'updatemenus': [dict(type="buttons", showactive=True, buttons=get_toggle_color_buttons(status))]},
                                           {'title': f"Team: {status} - Fantasy League Player Rankings by Position"}]))  # Update color toggle buttons

    # Add dropdown menu for teams
    team_dropdown_menu = {
        'buttons': dropdown_buttons,
        'direction': 'down',
        'showactive': True,
        'x': -0.2,  # x position (0 is far left)
        'y': 1,  # y position (1 is top, 0 is bottom)
        'xanchor': 'left',
        'yanchor': 'top'
    }

    # Add dropdown menu for toggling colors
    toggle_colors_menu = {
        'buttons': get_toggle_color_buttons(team_names[0]),
        'direction': 'down',
        'showactive': True,
        'x': 1,  # x position (0 is far left)
        'y': 1,  # y position (1 is top)
        'xanchor': 'right',
        'yanchor': 'top'
    }

    # Add dropdown menus to the layout
    fig.update_layout(
        updatemenus=[team_dropdown_menu],
        #title=f"Team: {status} - Fantasy League Player Rankings by Position",
        xaxis_title="Roster",
        yaxis_title="Dynasty Ranking",
        barmode='stack',
        xaxis={'categoryorder': 'array', 'categoryarray': [
            'C-1', 'C-2', '1B', '2B', '3B', 'SS', 'OF-1', 'OF-2', 'OF-3', 'OF-4', 'UT-1', 'UT-2',
            'SP-1', 'SP-2', 'SP-3', 'SP-4', 'SP-5', 'SP-6', 'RP-1', 'RP-2', 'RP-3', 'RP-4']},
        legend_title="Players",
        hovermode="closest",
        annotations=[{
            'text': f'Ducks on the Pond Dynasty Rankings by Position',
            'xref': 'paper',
            'yref': 'paper',
            'x': 0.5,
            'y': 1,
            'showarrow': False,
            'font': {'size': 16},
            'align': 'center',
            'xanchor': 'center'
        }]
    )

    # Save the combined HTML file
    combined_html_file_path = "../html/Ducks_Dynasty_Rankings_Breakdown.html"
    fig.write_html(combined_html_file_path)

    return combined_html_file_path

# Example usage:
# Load data
player_csv_path = "../data/Ducks_Players.csv"
ranking_csv_path = "../data/May_Dynasty_Baseball_Rankings.xlsx"

merged_data = load_data(player_csv_path, ranking_csv_path)

# Assign closest matching rankings
rankings = pd.read_excel(ranking_csv_path)
merged_data = assign_rankings(merged_data, rankings)
merged_data.to_csv("../data/merged_data.csv")
#populate_fantasy_teams_dict(merged_data)

# Assign positions
assigned_positions_df = assign_positions(merged_data)
assigned_positions_df.to_csv("../data/pos_merged_data.csv")

# Create interactive plot
combined_html_file_path = create_interactive_plot(assigned_positions_df)
print(f"Interactive plot saved to: {combined_html_file_path}")

