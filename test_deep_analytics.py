#!/usr/bin/env python3
"""Test script for Layer 2 deep analytics MCP tools"""

import asyncio
import json
from src.server import (
    get_player_specific_stat,
    get_player_game_log,
    get_player_vs_team_stats,
    get_player_awards_voting,
    get_player_monthly_splits,
    get_player_clutch_stats,
    get_player_playoffs_by_year
)


async def test_deep_analytics():
    """Test the new Layer 2 analytics tools"""
    
    print("Testing NBA Player Stats MCP - Layer 2 Deep Analytics\n")
    print("=" * 60)
    
    # Test 1: Specific stat query
    print("\n1. Testing specific stat query:")
    print("   Question: 'What was Steph Curry's 3-point percentage in 2018?'")
    result = await get_player_specific_stat("Stephen Curry", "3P%", 2018)
    if "error" not in result:
        print(f"   Answer: {result['value']}% in {result['season']}")
        if "career_average" in result:
            print(f"   Career average: {result['career_average']}%")
    else:
        print(f"   Error: {result['error']}")
    
    # Test 2: Points query
    print("\n2. Testing points query:")
    print("   Question: 'How many points did Stephen Curry average in 2024?'")
    result = await get_player_specific_stat("Stephen Curry", "PTS", 2024)
    if "error" not in result:
        print(f"   Answer: {result['value']} PPG in {result['season']}")
    else:
        print(f"   Error: {result['error']}")
    
    # Test 3: MVP voting
    print("\n3. Testing awards voting:")
    print("   Question: 'Where was LeBron James in MVP voting in 2020?'")
    result = await get_player_awards_voting("LeBron James", "MVP")
    print(f"   Note: {result.get('note', 'Award data available')}")
    
    # Test 4: Game log
    print("\n4. Testing game log:")
    print("   Question: 'Show me Damian Lillard's 2021 playoff games'")
    result = await get_player_game_log("Damian Lillard", 2021, playoffs=True)
    if "error" not in result:
        print(f"   Games played: {result['summary']['games_played']}")
        print(f"   Playoff PPG: {result.get('playoff_summary', {}).get('average_points', 'N/A')}")
    
    # Test 5: Vs team stats
    print("\n5. Testing vs team stats:")
    print("   Question: 'What are Kevin Durant's stats against the Lakers?'")
    result = await get_player_vs_team_stats("Kevin Durant", "LAL")
    print(f"   Team: {result['team']}")
    
    # Test 6: Monthly splits
    print("\n6. Testing monthly splits:")
    print("   Question: 'How did Jayson Tatum perform in December 2023?'")
    result = await get_player_monthly_splits("Jayson Tatum", 2024, "December")
    if "season_averages" in result:
        print(f"   Season PPG: {result['season_averages'].get('PTS', 'N/A')}")
    
    # Test 7: Clutch stats
    print("\n7. Testing clutch stats:")
    print("   Question: 'What are Kyrie Irving's career clutch stats?'")
    result = await get_player_clutch_stats("Kyrie Irving")
    if "overall_stats" in result:
        print(f"   Career PPG: {result['overall_stats']['ppg']}")
        print(f"   Clutch definition: {result['clutch_definition']}")
    
    # Test 8: Playoff year detail
    print("\n8. Testing playoff year detail:")
    print("   Question: 'How did Jimmy Butler perform in the 2020 playoffs?'")
    result = await get_player_playoffs_by_year("Jimmy Butler", 2020)
    if "playoff_run" in result and isinstance(result["playoff_run"], dict):
        print(f"   Playoff PPG: {result['playoff_run'].get('PTS', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("Deep Analytics Testing Complete!")
    
    # Summary of capabilities
    print("\nNew Layer 2 Capabilities:")
    print("✓ Specific stat queries (e.g., '3P% in 2018')")
    print("✓ Points/rebounds/assists for any season")
    print("✓ Awards and voting history")
    print("✓ Game-by-game logs")
    print("✓ Performance vs specific teams")
    print("✓ Monthly/temporal splits")
    print("✓ Clutch performance metrics")
    print("✓ Detailed playoff year analysis")


if __name__ == "__main__":
    asyncio.run(test_deep_analytics())