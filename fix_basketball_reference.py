"""
Basketball Reference Scraper Fix
This module fixes the table parsing issue in basketball_reference_scraper
caused by changes in the basketball-reference.com website structure.

Usage:
    import fix_basketball_reference  # Import this at the beginning of your script
    from basketball_reference_scraper.players import get_stats
    
    # Now you can use get_stats normally
    stats = get_stats('LeBron James', ask_matches=False)
"""

import pandas as pd
from basketball_reference_scraper.utils import get_player_suffix
from basketball_reference_scraper.lookup import lookup
from basketball_reference_scraper.request_utils import get_wrapper, get_selenium_wrapper
from bs4 import BeautifulSoup
from io import StringIO
import basketball_reference_scraper.players as players

def get_stats_fixed(_name, stat_type='PER_GAME', playoffs=False, career=False, ask_matches=True):
    """Fixed version of get_stats that handles the new table IDs on basketball-reference.com"""
    name = lookup(_name, ask_matches)
    suffix = get_player_suffix(name)
    if not suffix:
        return pd.DataFrame()
    
    stat_type = stat_type.lower()
    table = None
    
    # Map old table IDs to new ones
    table_id_map = {
        'per_game': 'per_game_stats',
        'totals': 'totals_stats',
        'per_minute': 'per_minute_stats',
        'per_poss': 'per_poss_stats',
        'advanced': 'advanced'
    }
    
    # Add playoff prefix if needed
    if playoffs:
        table_id = f"{table_id_map.get(stat_type, stat_type)}_post"
    else:
        table_id = table_id_map.get(stat_type, stat_type)
    
    if stat_type in ['per_game', 'totals', 'advanced'] and not playoffs:
        r = get_wrapper(f'https://www.basketball-reference.com/{suffix}')
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            table = soup.find('table', {'id': table_id})
            table = str(table)
        else:
            raise ConnectionError('Request to basketball reference failed')
    elif stat_type in ['per_minute', 'per_poss'] or playoffs:
        xpath = f"//table[@id='{table_id}']"
        table = get_selenium_wrapper(f'https://www.basketball-reference.com/{suffix}', xpath)
    
    if table is None:
        return pd.DataFrame()
    
    df = pd.read_html(StringIO(table))[0]
    df.rename(columns={'Season': 'SEASON', 'Age': 'AGE',
                'Tm': 'TEAM', 'Lg': 'LEAGUE', 'Pos': 'POS', 'Awards': 'AWARDS'}, inplace=True)
    if 'FG.1' in df.columns:
        df.rename(columns={'FG.1': 'FG%'}, inplace=True)
    if 'eFG' in df.columns:
        df.rename(columns={'eFG': 'eFG%'}, inplace=True)
    if 'FT.1' in df.columns:
        df.rename(columns={'FT.1': 'FT%'}, inplace=True)

    # Check if Career row exists
    career_rows = df[df['SEASON']=='Career'].index
    if len(career_rows) > 0:
        career_index = career_rows[0]
        if career:
            df = df.iloc[career_index+2:, :]
        else:
            df = df.iloc[:career_index, :]
    
    # Handle percentage columns
    if len(df) > 0:
        index = df.index[0]
        for column in df.columns:
            if pd.isna(df[column][index]):
                df.rename(columns={column: f'{column.upper()}%'}, inplace=True)

    if stat_type.endswith('_advanced') or stat_type == 'advanced':
        df = df.drop(['G', 'MP'], axis=1)

    if not career:
        df = df.reset_index().drop('index', axis=1)

    return df

# Monkey patch the original function
players.get_stats = get_stats_fixed