#!/usr/bin/env python3
"""
Example usage of the NBA Player Stats MCP Server

This script demonstrates how to use the basketball_reference_scraper library
with the fixes applied for retrieving NBA player statistics.
"""

# Import the fix first
import fix_basketball_reference
from basketball_reference_scraper.players import get_stats, get_player_headshot
import pandas as pd

def demonstrate_player_stats():
    """Demonstrate various player statistics queries"""
    
    print("=== NBA Player Stats Examples ===\n")
    
    # 1. Career statistics
    print("1. LeBron James Career Stats (Per Game)")
    lebron_stats = get_stats('LeBron James', stat_type='PER_GAME', ask_matches=False)
    career_row = lebron_stats[lebron_stats['SEASON'] == 'Career']
    if not career_row.empty:
        print(f"Career PPG: {career_row['PTS'].values[0]}")
        print(f"Career RPG: {career_row['TRB'].values[0]}")
        print(f"Career APG: {career_row['AST'].values[0]}")
    print()
    
    # 2. Specific season stats
    print("2. Stephen Curry 2015-16 Season (MVP Season)")
    curry_stats = get_stats('Stephen Curry', stat_type='PER_GAME', ask_matches=False)
    mvp_season = curry_stats[curry_stats['SEASON'] == '2015-16']
    if not mvp_season.empty:
        print(f"PPG: {mvp_season['PTS'].values[0]}")
        print(f"3P%: {mvp_season['3P%'].values[0]}")
        print(f"3PM per game: {mvp_season['3P'].values[0]}")
    print()
    
    # 3. Advanced stats
    print("3. Nikola Jokić Advanced Stats (2022-23)")
    jokic_advanced = get_stats('Nikola Jokić', stat_type='ADVANCED', ask_matches=False)
    jokic_2023 = jokic_advanced[jokic_advanced['SEASON'] == '2022-23']
    if not jokic_2023.empty:
        print(f"PER: {jokic_2023['PER'].values[0]}")
        print(f"Win Shares: {jokic_2023['WS'].values[0]}")
        print(f"BPM: {jokic_2023['BPM'].values[0]}")
    print()
    
    # 4. Playoff vs Regular Season
    print("4. Kawhi Leonard Playoff Performance")
    kawhi_regular = get_stats('Kawhi Leonard', stat_type='PER_GAME', playoffs=False, ask_matches=False)
    kawhi_playoffs = get_stats('Kawhi Leonard', stat_type='PER_GAME', playoffs=True, ask_matches=False)
    
    regular_career = kawhi_regular[kawhi_regular['SEASON'] == 'Career']
    playoff_career = kawhi_playoffs[kawhi_playoffs['SEASON'] == 'Career']
    
    if not regular_career.empty and not playoff_career.empty:
        print(f"Regular Season PPG: {regular_career['PTS'].values[0]}")
        print(f"Playoff PPG: {playoff_career['PTS'].values[0]}")
        print(f"Playoff PPG increase: +{float(playoff_career['PTS'].values[0]) - float(regular_career['PTS'].values[0]):.1f}")
    print()
    
    # 5. Career totals
    print("5. Kareem Abdul-Jabbar Career Totals")
    kareem_totals = get_stats('Kareem Abdul-Jabbar', stat_type='TOTALS', ask_matches=False)
    career_totals = kareem_totals[kareem_totals['SEASON'] == 'Career']
    if not career_totals.empty:
        print(f"Total Points: {career_totals['PTS'].values[0]:,}")
        print(f"Total Rebounds: {career_totals['TRB'].values[0]:,}")
        print(f"Games Played: {career_totals['G'].values[0]:,}")
    print()
    
    # 6. Per-36 minute stats
    print("6. Giannis Antetokounmpo Per-36 Stats (2022-23)")
    giannis_per36 = get_stats('Giannis Antetokounmpo', stat_type='PER_MINUTE', ask_matches=False)
    giannis_2023 = giannis_per36[giannis_per36['SEASON'] == '2022-23']
    if not giannis_2023.empty:
        print(f"Points per 36 min: {giannis_2023['PTS'].values[0]}")
        print(f"Rebounds per 36 min: {giannis_2023['TRB'].values[0]}")
        print(f"Assists per 36 min: {giannis_2023['AST'].values[0]}")
    print()

def compare_players():
    """Compare two players"""
    print("=== Player Comparison: LeBron vs Jordan ===\n")
    
    lebron = get_stats('LeBron James', stat_type='PER_GAME', career=True, ask_matches=False)
    jordan = get_stats('Michael Jordan', stat_type='PER_GAME', career=True, ask_matches=False)
    
    print(f"{'Stat':<15} {'LeBron':<10} {'Jordan':<10}")
    print("-" * 35)
    print(f"{'PPG':<15} {lebron['PTS'].values[0]:<10} {jordan['PTS'].values[0]:<10}")
    print(f"{'RPG':<15} {lebron['TRB'].values[0]:<10} {jordan['TRB'].values[0]:<10}")
    print(f"{'APG':<15} {lebron['AST'].values[0]:<10} {jordan['AST'].values[0]:<10}")
    print(f"{'FG%':<15} {lebron['FG%'].values[0]:<10} {jordan['FG%'].values[0]:<10}")
    print(f"{'3P%':<15} {lebron['3P%'].values[0]:<10} {jordan['3P%'].values[0]:<10}")
    print()

def shooting_analysis():
    """Analyze shooting stats for elite shooters"""
    print("=== Elite Shooters Analysis ===\n")
    
    shooters = ['Stephen Curry', 'Ray Allen', 'Reggie Miller']
    
    for shooter in shooters:
        stats = get_stats(shooter, stat_type='PER_GAME', ask_matches=False)
        career = stats[stats['SEASON'] == 'Career']
        
        if not career.empty:
            print(f"{shooter}:")
            print(f"  Career 3P%: {career['3P%'].values[0]}")
            print(f"  Career 3PM/game: {career['3P'].values[0]}")
            print(f"  Career 3PA/game: {career['3PA'].values[0]}")
            
            # Find best 3P% season (minimum 100 attempts)
            seasons = stats[stats['SEASON'] != 'Career']
            seasons_filtered = seasons[seasons['3PA'] > 2.0]  # At least 2 attempts per game
            if not seasons_filtered.empty:
                best_season_idx = seasons_filtered['3P%'].idxmax()
                best_season = seasons_filtered.loc[best_season_idx]
                print(f"  Best 3P% Season: {best_season['SEASON']} ({best_season['3P%']})")
            print()

def demonstrate_deep_analytics():
    """Demonstrate the new Layer 2 deep analytics capabilities"""
    print("=== Layer 2 Deep Analytics Examples ===\n")
    
    # 1. Specific stat query
    print("1. Specific Stat Query: Steph Curry's 3P% in 2018")
    curry_stats = get_stats('Stephen Curry', stat_type='PER_GAME', ask_matches=False)
    curry_2018 = curry_stats[curry_stats['SEASON'] == '2017-18']
    if not curry_2018.empty:
        print(f"   3P% in 2017-18: {curry_2018['3P%'].values[0]}")
        print(f"   3PM per game: {curry_2018['3P'].values[0]}")
        print(f"   3PA per game: {curry_2018['3PA'].values[0]}")
    print()
    
    # 2. Points in a specific year
    print("2. Points Query: How many points did Steph Curry average in 2024?")
    curry_2024 = curry_stats[curry_stats['SEASON'] == '2023-24']
    if not curry_2024.empty:
        print(f"   PPG in 2023-24: {curry_2024['PTS'].values[0]}")
        print(f"   Games played: {curry_2024['G'].values[0]}")
    print()
    
    # 3. Advanced stat lookup
    print("3. MVP-caliber Season: Giannis Antetokounmpo's PER in 2020")
    giannis_advanced = get_stats('Giannis Antetokounmpo', stat_type='ADVANCED', ask_matches=False)
    giannis_2020 = giannis_advanced[giannis_advanced['SEASON'] == '2019-20']
    if not giannis_2020.empty:
        print(f"   PER: {giannis_2020['PER'].values[0]}")
        print(f"   Win Shares: {giannis_2020['WS'].values[0]}")
        print(f"   VORP: {giannis_2020['VORP'].values[0]}")
    print()
    
    # 4. Playoff performance by year
    print("4. Playoff Year Analysis: Jimmy Butler 2020 Bubble Run")
    butler_playoffs = get_stats('Jimmy Butler', stat_type='PER_GAME', playoffs=True, ask_matches=False)
    butler_2020 = butler_playoffs[butler_playoffs['SEASON'] == '2019-20']
    if not butler_2020.empty:
        print(f"   Playoff PPG: {butler_2020['PTS'].values[0]}")
        print(f"   Playoff APG: {butler_2020['AST'].values[0]}")
        print(f"   Games played: {butler_2020['G'].values[0]}")
    print()
    
    # 5. Efficiency stats
    print("5. Efficiency Query: Nikola Jokić's True Shooting % in 2023")
    jokic_2023 = get_stats('Nikola Jokić', stat_type='ADVANCED', ask_matches=False)
    jokic_season = jokic_2023[jokic_2023['SEASON'] == '2022-23']
    if not jokic_season.empty:
        print(f"   TS%: {jokic_season['TS%'].values[0]}")
        print(f"   eFG%: {jokic_season['eFG%'].values[0]}")
    print()


if __name__ == "__main__":
    try:
        demonstrate_player_stats()
        compare_players()
        shooting_analysis()
        demonstrate_deep_analytics()
        print("\n=== Test Complete ===")
        print("All examples ran successfully!")
        print("\nNBA Player Stats MCP Server now includes 17 tools:")
        print("- 10 Core statistical tools")
        print("- 7 Deep analytics Layer 2 tools")
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have installed all requirements:")
        print("pip install -r requirements.txt")