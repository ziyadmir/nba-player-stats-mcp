#!/usr/bin/env python3
"""NBA Player Stats MCP Server

A focused MCP server for retrieving comprehensive NBA player statistics from basketball-reference.com.
This server provides detailed player stats including career stats, season comparisons, advanced metrics,
shooting stats, and more.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
import pandas as pd
from io import StringIO

from fastmcp import FastMCP

# Fix for basketball_reference_scraper
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the fix first
try:
    import fix_basketball_reference
except:
    pass

from basketball_reference_scraper.players import get_stats as brs_get_stats, get_player_headshot
from basketball_reference_scraper.utils import get_player_suffix
from basketball_reference_scraper.lookup import lookup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name="nba-player-stats",
    instructions="""NBA Player Stats MCP Server - Your comprehensive source for NBA player statistics.
    
This server provides detailed player statistics including:
- Career stats and season-by-season breakdowns
- Per game, per 36 minutes, per 100 possessions stats
- Advanced metrics (PER, TS%, WS, BPM, VORP)
- Playoff vs regular season comparisons
- Shooting percentages and efficiency metrics
- Career highs and milestones
- Player comparisons

All data is sourced from basketball-reference.com"""
)


@mcp.tool()
async def get_player_career_stats(
    player_name: str,
    stat_type: str = "PER_GAME"
) -> Dict[str, Any]:
    """Get complete career statistics for an NBA player.
    
    Args:
        player_name: The player's name (e.g., "LeBron James")
        stat_type: Type of stats - "PER_GAME", "TOTALS", "PER_MINUTE", "PER_POSS", "ADVANCED"
    
    Returns:
        Complete career statistics including season-by-season breakdown
    """
    try:
        # Get regular season stats
        regular_stats = brs_get_stats(
            player_name,
            stat_type=stat_type,
            playoffs=False,
            ask_matches=False
        )
        
        # Get playoff stats
        playoff_stats = brs_get_stats(
            player_name,
            stat_type=stat_type,
            playoffs=True,
            ask_matches=False
        )
        
        if regular_stats.empty:
            return {"error": f"No stats found for {player_name}"}
        
        # Calculate career averages
        career_row = regular_stats[regular_stats['SEASON'] == 'Career']
        career_stats = career_row.to_dict('records')[0] if not career_row.empty else {}
        
        # Get best season based on PTS for per_game stats
        if stat_type == "PER_GAME" and 'PTS' in regular_stats.columns:
            season_data = regular_stats[regular_stats['SEASON'] != 'Career']
            if not season_data.empty:
                # Convert PTS to numeric, handling any non-numeric values
                season_data['PTS'] = pd.to_numeric(season_data['PTS'], errors='coerce')
                valid_pts = season_data.dropna(subset=['PTS'])
                if not valid_pts.empty:
                    best_season_idx = valid_pts['PTS'].idxmax()
                    best_season = regular_stats.loc[best_season_idx].to_dict()
                else:
                    best_season = {}
            else:
                best_season = {}
        else:
            best_season = {}
        
        result = {
            "player_name": player_name,
            "stat_type": stat_type,
            "career_regular_season": career_stats,
            "seasons": regular_stats[regular_stats['SEASON'] != 'Career'].to_dict('records'),
            "total_seasons": len(regular_stats[regular_stats['SEASON'] != 'Career']),
            "best_scoring_season": best_season if best_season else None
        }
        
        # Add playoff stats if available
        if not playoff_stats.empty:
            playoff_career = playoff_stats[playoff_stats['SEASON'] == 'Career']
            result["career_playoffs"] = playoff_career.to_dict('records')[0] if not playoff_career.empty else {}
            result["playoff_seasons"] = playoff_stats[playoff_stats['SEASON'] != 'Career'].to_dict('records')
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting career stats: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_season_stats(
    player_name: str,
    season: int,
    stat_type: str = "PER_GAME",
    include_playoffs: bool = True
) -> Dict[str, Any]:
    """Get statistics for a specific season.
    
    Args:
        player_name: The player's name (e.g., "LeBron James")
        season: Season year (e.g., 2023 for 2022-23 season)
        stat_type: Type of stats - "PER_GAME", "TOTALS", "PER_MINUTE", "PER_POSS", "ADVANCED"
        include_playoffs: Whether to include playoff stats if available
    
    Returns:
        Detailed statistics for the specified season
    """
    try:
        # Get regular season stats
        regular_stats = brs_get_stats(
            player_name,
            stat_type=stat_type,
            playoffs=False,
            ask_matches=False
        )
        
        if regular_stats.empty:
            return {"error": f"No stats found for {player_name}"}
        
        # Filter for specific season
        season_str = f"{season-1}-{str(season)[2:]}"
        season_stats = regular_stats[regular_stats['SEASON'] == season_str]
        
        if season_stats.empty:
            return {"error": f"No stats found for {player_name} in {season_str} season"}
        
        result = {
            "player_name": player_name,
            "season": season_str,
            "stat_type": stat_type,
            "regular_season": season_stats.to_dict('records')[0]
        }
        
        # Get playoff stats if requested
        if include_playoffs:
            playoff_stats = brs_get_stats(
                player_name,
                stat_type=stat_type,
                playoffs=True,
                ask_matches=False
            )
            
            if not playoff_stats.empty:
                playoff_season = playoff_stats[playoff_stats['SEASON'] == season_str]
                if not playoff_season.empty:
                    result["playoffs"] = playoff_season.to_dict('records')[0]
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting season stats: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_advanced_stats(
    player_name: str,
    season: Optional[int] = None
) -> Dict[str, Any]:
    """Get advanced statistics for a player (PER, TS%, WS, BPM, VORP, etc.).
    
    Args:
        player_name: The player's name (e.g., "LeBron James")
        season: Specific season (e.g., 2023). If None, returns all seasons.
    
    Returns:
        Advanced statistics including efficiency metrics
    """
    try:
        # Get advanced stats
        advanced_stats = brs_get_stats(
            player_name,
            stat_type="ADVANCED",
            playoffs=False,
            ask_matches=False
        )
        
        if advanced_stats.empty:
            return {"error": f"No advanced stats found for {player_name}"}
        
        if season:
            season_str = f"{season-1}-{str(season)[2:]}"
            advanced_stats = advanced_stats[advanced_stats['SEASON'] == season_str]
            
            if advanced_stats.empty:
                return {"error": f"No advanced stats found for {player_name} in {season_str}"}
            
            return {
                "player_name": player_name,
                "season": season_str,
                "advanced_stats": advanced_stats.to_dict('records')[0]
            }
        else:
            # Get career totals
            career_row = advanced_stats[advanced_stats['SEASON'] == 'Career']
            
            # Find best seasons by different metrics
            season_data = advanced_stats[advanced_stats['SEASON'] != 'Career']
            
            best_seasons = {}
            for metric in ['PER', 'TS%', 'WS', 'BPM', 'VORP']:
                if metric in season_data.columns:
                    best_idx = season_data[metric].idxmax()
                    if pd.notna(best_idx):
                        best_seasons[f"best_{metric}_season"] = {
                            "season": season_data.loc[best_idx, 'SEASON'],
                            "value": season_data.loc[best_idx, metric]
                        }
            
            return {
                "player_name": player_name,
                "career_advanced": career_row.to_dict('records')[0] if not career_row.empty else {},
                "seasons": season_data.to_dict('records'),
                "best_seasons": best_seasons
            }
        
    except Exception as e:
        logger.error(f"Error getting advanced stats: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_per36_stats(
    player_name: str,
    season: Optional[int] = None
) -> Dict[str, Any]:
    """Get per-36-minute statistics for a player.
    
    Args:
        player_name: The player's name (e.g., "LeBron James")
        season: Specific season (e.g., 2023). If None, returns all seasons.
    
    Returns:
        Per-36-minute statistics (pace-adjusted)
    """
    try:
        # Get per minute stats
        per_min_stats = brs_get_stats(
            player_name,
            stat_type="PER_MINUTE",
            playoffs=False,
            ask_matches=False
        )
        
        if per_min_stats.empty:
            return {"error": f"No per-36 stats found for {player_name}"}
        
        if season:
            season_str = f"{season-1}-{str(season)[2:]}"
            season_stats = per_min_stats[per_min_stats['SEASON'] == season_str]
            
            if season_stats.empty:
                return {"error": f"No per-36 stats found for {player_name} in {season_str}"}
            
            return {
                "player_name": player_name,
                "season": season_str,
                "per_36_stats": season_stats.to_dict('records')[0]
            }
        else:
            # Career averages
            career_row = per_min_stats[per_min_stats['SEASON'] == 'Career']
            
            return {
                "player_name": player_name,
                "career_per_36": career_row.to_dict('records')[0] if not career_row.empty else {},
                "seasons": per_min_stats[per_min_stats['SEASON'] != 'Career'].to_dict('records')
            }
        
    except Exception as e:
        logger.error(f"Error getting per-36 stats: {e}")
        return {"error": str(e)}


@mcp.tool()
async def compare_players(
    player1_name: str,
    player2_name: str,
    stat_type: str = "PER_GAME",
    season: Optional[int] = None
) -> Dict[str, Any]:
    """Compare statistics between two NBA players.
    
    Args:
        player1_name: First player's name (e.g., "LeBron James")
        player2_name: Second player's name (e.g., "Kevin Durant")
        stat_type: Type of stats - "PER_GAME", "TOTALS", "PER_MINUTE", "ADVANCED"
        season: Specific season to compare. If None, compares career stats.
    
    Returns:
        Side-by-side comparison of the two players
    """
    try:
        # Get stats for both players
        player1_stats = brs_get_stats(
            player1_name,
            stat_type=stat_type,
            playoffs=False,
            ask_matches=False
        )
        
        player2_stats = brs_get_stats(
            player2_name,
            stat_type=stat_type,
            playoffs=False,
            ask_matches=False
        )
        
        if player1_stats.empty or player2_stats.empty:
            return {"error": "Could not find stats for one or both players"}
        
        if season:
            season_str = f"{season-1}-{str(season)[2:]}"
            p1_season = player1_stats[player1_stats['SEASON'] == season_str]
            p2_season = player2_stats[player2_stats['SEASON'] == season_str]
            
            if p1_season.empty or p2_season.empty:
                return {"error": f"One or both players didn't play in {season_str}"}
            
            return {
                "season": season_str,
                "stat_type": stat_type,
                "player1": {
                    "name": player1_name,
                    "stats": p1_season.to_dict('records')[0]
                },
                "player2": {
                    "name": player2_name,
                    "stats": p2_season.to_dict('records')[0]
                }
            }
        else:
            # Career comparison
            p1_career = player1_stats[player1_stats['SEASON'] == 'Career']
            p2_career = player2_stats[player2_stats['SEASON'] == 'Career']
            
            # Calculate some key differences for per_game stats
            comparison = {}
            if stat_type == "PER_GAME" and not p1_career.empty and not p2_career.empty:
                p1_dict = p1_career.to_dict('records')[0]
                p2_dict = p2_career.to_dict('records')[0]
                
                for stat in ['PTS', 'AST', 'TRB', 'STL', 'BLK', 'FG%', 'FT%', '3P%']:
                    if stat in p1_dict and stat in p2_dict:
                        try:
                            comparison[stat] = {
                                player1_name: p1_dict[stat],
                                player2_name: p2_dict[stat],
                                "difference": float(p1_dict[stat]) - float(p2_dict[stat])
                            }
                        except:
                            pass
            
            return {
                "comparison_type": "career",
                "stat_type": stat_type,
                "player1": {
                    "name": player1_name,
                    "career_stats": p1_career.to_dict('records')[0] if not p1_career.empty else {},
                    "total_seasons": len(player1_stats[player1_stats['SEASON'] != 'Career'])
                },
                "player2": {
                    "name": player2_name,
                    "career_stats": p2_career.to_dict('records')[0] if not p2_career.empty else {},
                    "total_seasons": len(player2_stats[player2_stats['SEASON'] != 'Career'])
                },
                "statistical_comparison": comparison
            }
        
    except Exception as e:
        logger.error(f"Error comparing players: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_shooting_splits(
    player_name: str,
    season: Optional[int] = None
) -> Dict[str, Any]:
    """Get detailed shooting statistics and splits for a player.
    
    Args:
        player_name: The player's name (e.g., "Stephen Curry")
        season: Specific season (e.g., 2023). If None, returns career shooting stats.
    
    Returns:
        Detailed shooting percentages and volume stats
    """
    try:
        # Get per game stats which include shooting percentages
        stats = brs_get_stats(
            player_name,
            stat_type="PER_GAME",
            playoffs=False,
            ask_matches=False
        )
        
        if stats.empty:
            return {"error": f"No stats found for {player_name}"}
        
        if season:
            season_str = f"{season-1}-{str(season)[2:]}"
            season_stats = stats[stats['SEASON'] == season_str]
            
            if season_stats.empty:
                return {"error": f"No stats found for {player_name} in {season_str}"}
            
            row = season_stats.iloc[0]
            
            return {
                "player_name": player_name,
                "season": season_str,
                "shooting_stats": {
                    "field_goals": {
                        "percentage": row.get('FG%', 0),
                        "made_per_game": row.get('FG', 0),
                        "attempted_per_game": row.get('FGA', 0)
                    },
                    "three_pointers": {
                        "percentage": row.get('3P%', 0),
                        "made_per_game": row.get('3P', 0),
                        "attempted_per_game": row.get('3PA', 0)
                    },
                    "two_pointers": {
                        "percentage": row.get('2P%', 0),
                        "made_per_game": row.get('2P', 0),
                        "attempted_per_game": row.get('2PA', 0)
                    },
                    "free_throws": {
                        "percentage": row.get('FT%', 0),
                        "made_per_game": row.get('FT', 0),
                        "attempted_per_game": row.get('FTA', 0)
                    },
                    "effective_fg_percentage": row.get('eFG%', 0),
                    "true_shooting_percentage": row.get('TS%', 0) if 'TS%' in row else None
                }
            }
        else:
            # Career shooting stats
            career_row = stats[stats['SEASON'] == 'Career']
            
            if career_row.empty:
                return {"error": "No career stats found"}
            
            row = career_row.iloc[0]
            
            # Find best shooting seasons
            season_data = stats[stats['SEASON'] != 'Career']
            best_seasons = {}
            
            for stat, name in [('FG%', 'field_goal'), ('3P%', 'three_point'), ('FT%', 'free_throw')]:
                if stat in season_data.columns:
                    # Filter out seasons with very few attempts
                    if stat == '3P%':
                        filtered = season_data[season_data['3PA'] > 1.0]
                    else:
                        filtered = season_data
                    
                    if not filtered.empty:
                        best_idx = filtered[stat].idxmax()
                        if pd.notna(best_idx):
                            best_seasons[f"best_{name}_season"] = {
                                "season": filtered.loc[best_idx, 'SEASON'],
                                "percentage": filtered.loc[best_idx, stat],
                                "attempts_per_game": filtered.loc[best_idx, stat.replace('%', 'A')]
                            }
            
            return {
                "player_name": player_name,
                "career_shooting": {
                    "field_goals": {
                        "percentage": row.get('FG%', 0),
                        "made_per_game": row.get('FG', 0),
                        "attempted_per_game": row.get('FGA', 0)
                    },
                    "three_pointers": {
                        "percentage": row.get('3P%', 0),
                        "made_per_game": row.get('3P', 0),
                        "attempted_per_game": row.get('3PA', 0)
                    },
                    "two_pointers": {
                        "percentage": row.get('2P%', 0),
                        "made_per_game": row.get('2P', 0),
                        "attempted_per_game": row.get('2PA', 0)
                    },
                    "free_throws": {
                        "percentage": row.get('FT%', 0),
                        "made_per_game": row.get('FT', 0),
                        "attempted_per_game": row.get('FTA', 0)
                    },
                    "effective_fg_percentage": row.get('eFG%', 0)
                },
                "best_shooting_seasons": best_seasons
            }
        
    except Exception as e:
        logger.error(f"Error getting shooting splits: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_totals(
    player_name: str,
    season: Optional[int] = None
) -> Dict[str, Any]:
    """Get total statistics (not averages) for a player.
    
    Args:
        player_name: The player's name (e.g., "LeBron James")
        season: Specific season (e.g., 2023). If None, returns career totals.
    
    Returns:
        Total statistics including points, rebounds, assists, etc.
    """
    try:
        # Get totals stats
        totals = brs_get_stats(
            player_name,
            stat_type="TOTALS",
            playoffs=False,
            ask_matches=False
        )
        
        if totals.empty:
            return {"error": f"No stats found for {player_name}"}
        
        if season:
            season_str = f"{season-1}-{str(season)[2:]}"
            season_totals = totals[totals['SEASON'] == season_str]
            
            if season_totals.empty:
                return {"error": f"No stats found for {player_name} in {season_str}"}
            
            return {
                "player_name": player_name,
                "season": season_str,
                "totals": season_totals.to_dict('records')[0]
            }
        else:
            # Career totals
            career_row = totals[totals['SEASON'] == 'Career']
            
            # Find milestone seasons
            season_data = totals[totals['SEASON'] != 'Career']
            milestones = {}
            
            # First 1000+ point season
            thousand_pt_seasons = season_data[season_data['PTS'] >= 1000]
            if not thousand_pt_seasons.empty:
                milestones['first_1000_point_season'] = thousand_pt_seasons.iloc[0]['SEASON']
            
            # Highest scoring season
            if 'PTS' in season_data.columns:
                best_idx = season_data['PTS'].idxmax()
                if pd.notna(best_idx):
                    milestones['highest_scoring_season'] = {
                        "season": season_data.loc[best_idx, 'SEASON'],
                        "points": season_data.loc[best_idx, 'PTS']
                    }
            
            return {
                "player_name": player_name,
                "career_totals": career_row.to_dict('records')[0] if not career_row.empty else {},
                "seasons": season_data.to_dict('records'),
                "milestones": milestones
            }
        
    except Exception as e:
        logger.error(f"Error getting totals: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_playoff_stats(
    player_name: str,
    stat_type: str = "PER_GAME"
) -> Dict[str, Any]:
    """Get playoff statistics for a player.
    
    Args:
        player_name: The player's name (e.g., "LeBron James")
        stat_type: Type of stats - "PER_GAME", "TOTALS", "PER_MINUTE", "ADVANCED"
    
    Returns:
        Complete playoff statistics including season-by-season breakdown
    """
    try:
        # Get playoff stats
        playoff_stats = brs_get_stats(
            player_name,
            stat_type=stat_type,
            playoffs=True,
            ask_matches=False
        )
        
        if playoff_stats.empty:
            return {
                "player_name": player_name,
                "message": f"{player_name} has no playoff statistics",
                "playoff_appearances": 0
            }
        
        # Get career playoff totals
        career_row = playoff_stats[playoff_stats['SEASON'] == 'Career']
        career_stats = career_row.to_dict('records')[0] if not career_row.empty else {}
        
        # Get regular season for comparison
        regular_stats = brs_get_stats(
            player_name,
            stat_type=stat_type,
            playoffs=False,
            ask_matches=False
        )
        
        regular_career = regular_stats[regular_stats['SEASON'] == 'Career']
        regular_career_stats = regular_career.to_dict('records')[0] if not regular_career.empty else {}
        
        # Compare key stats if PER_GAME
        comparison = {}
        if stat_type == "PER_GAME" and career_stats and regular_career_stats:
            for stat in ['PTS', 'AST', 'TRB', 'FG%', '3P%', 'FT%']:
                if stat in career_stats and stat in regular_career_stats:
                    try:
                        comparison[stat] = {
                            "playoffs": float(career_stats[stat]),
                            "regular_season": float(regular_career_stats[stat]),
                            "difference": float(career_stats[stat]) - float(regular_career_stats[stat])
                        }
                    except:
                        pass
        
        return {
            "player_name": player_name,
            "stat_type": stat_type,
            "career_playoff_stats": career_stats,
            "playoff_appearances": len(playoff_stats[playoff_stats['SEASON'] != 'Career']),
            "playoff_seasons": playoff_stats[playoff_stats['SEASON'] != 'Career'].to_dict('records'),
            "playoff_vs_regular_season": comparison
        }
        
    except Exception as e:
        logger.error(f"Error getting playoff stats: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_headshot_url(player_name: str) -> Dict[str, Any]:
    """Get the basketball-reference.com headshot URL for a player.
    
    Args:
        player_name: The player's name (e.g., "LeBron James")
    
    Returns:
        URL to the player's headshot image
    """
    try:
        url = get_player_headshot(player_name)
        
        return {
            "player_name": player_name,
            "headshot_url": url,
            "source": "basketball-reference.com"
        }
    except Exception as e:
        logger.error(f"Error getting player headshot: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_career_highlights(player_name: str) -> Dict[str, Any]:
    """Get career highlights and achievements for a player.
    
    Args:
        player_name: The player's name (e.g., "LeBron James")
    
    Returns:
        Career highlights including best seasons, records, and achievements
    """
    try:
        # Get various stat types to compile highlights
        per_game = brs_get_stats(player_name, stat_type="PER_GAME", playoffs=False, ask_matches=False)
        totals = brs_get_stats(player_name, stat_type="TOTALS", playoffs=False, ask_matches=False)
        advanced = brs_get_stats(player_name, stat_type="ADVANCED", playoffs=False, ask_matches=False)
        
        if per_game.empty:
            return {"error": f"No stats found for {player_name}"}
        
        # Get career stats
        career_pg = per_game[per_game['SEASON'] == 'Career'].to_dict('records')[0] if not per_game[per_game['SEASON'] == 'Career'].empty else {}
        career_totals = totals[totals['SEASON'] == 'Career'].to_dict('records')[0] if not totals[totals['SEASON'] == 'Career'].empty else {}
        
        # Season data
        season_pg = per_game[per_game['SEASON'] != 'Career']
        season_totals = totals[totals['SEASON'] != 'Career']
        season_advanced = advanced[advanced['SEASON'] != 'Career']
        
        highlights = {
            "player_name": player_name,
            "career_overview": {
                "seasons_played": len(season_pg),
                "games_played": career_totals.get('G', 0),
                "career_ppg": career_pg.get('PTS', 0),
                "career_rpg": career_pg.get('TRB', 0),
                "career_apg": career_pg.get('AST', 0),
                "total_points": career_totals.get('PTS', 0)
            },
            "single_season_highs": {}
        }
        
        # Find single season highs
        stats_to_check = {
            'PTS': 'points_per_game',
            'TRB': 'rebounds_per_game',
            'AST': 'assists_per_game',
            'STL': 'steals_per_game',
            'BLK': 'blocks_per_game',
            'FG%': 'field_goal_percentage',
            '3P%': 'three_point_percentage'
        }
        
        for stat, name in stats_to_check.items():
            if stat in season_pg.columns:
                # For percentages, filter out seasons with low attempts
                if stat == '3P%':
                    filtered = season_pg[season_pg['3PA'] > 1.0]
                else:
                    filtered = season_pg
                
                if not filtered.empty and filtered[stat].notna().any():
                    best_idx = filtered[stat].idxmax()
                    if pd.notna(best_idx):
                        highlights["single_season_highs"][name] = {
                            "value": filtered.loc[best_idx, stat],
                            "season": filtered.loc[best_idx, 'SEASON']
                        }
        
        # Find 20+ PPG seasons
        twenty_ppg_seasons = season_pg[season_pg['PTS'] >= 20.0]
        highlights["seasons_20plus_ppg"] = len(twenty_ppg_seasons)
        
        # Find All-Star appearances (if AWARDS column exists)
        if 'AWARDS' in season_pg.columns:
            all_star_seasons = season_pg[season_pg['AWARDS'].notna() & season_pg['AWARDS'].str.contains('AS', na=False)]
            highlights["all_star_appearances"] = len(all_star_seasons)
        
        # Best advanced stat season
        if not season_advanced.empty and 'PER' in season_advanced.columns:
            best_per_idx = season_advanced['PER'].idxmax()
            if pd.notna(best_per_idx):
                highlights["best_per_season"] = {
                    "value": season_advanced.loc[best_per_idx, 'PER'],
                    "season": season_advanced.loc[best_per_idx, 'SEASON']
                }
        
        return highlights
        
    except Exception as e:
        logger.error(f"Error getting career highlights: {e}")
        return {"error": str(e)}


# Main entry point
def main():
    """Main entry point for the server"""
    mcp.run()

if __name__ == "__main__":
    main()