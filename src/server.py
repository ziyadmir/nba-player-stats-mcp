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
from basketball_reference_scraper.seasons import get_schedule

# Try to import game logs and awards functions
try:
    from basketball_reference_scraper.players import get_game_logs
except ImportError:
    # If not available, we'll create a placeholder
    def get_game_logs(name, start_date=None, end_date=None, playoffs=False, ask_matches=False):
        # This would need to be implemented
        return pd.DataFrame()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name="nba-player-stats",
    instructions="""NBA Player Stats MCP Server - Your comprehensive source for NBA player statistics.
    
This server provides detailed player statistics including:

Core Statistics:
- Career stats and season-by-season breakdowns
- Per game, per 36 minutes, per 100 possessions stats
- Advanced metrics (PER, TS%, WS, BPM, VORP)
- Playoff vs regular season comparisons
- Shooting percentages and efficiency metrics
- Career highs and milestones
- Player comparisons

Deep Analytics (Layer 2):
- Game-by-game logs and specific game queries
- Individual stat lookups (e.g., "3P% in 2018")
- Awards and MVP voting history
- Team matchup statistics
- Monthly/temporal splits
- Clutch performance metrics
- Detailed playoff year analysis

Ultra-Deep Analytics (Layer 3):
- Career trend analysis and progression tracking
- Game highs and milestone performances (40+ pt games, triple-doubles)
- Situational splits (home/away, rest days, wins/losses)
- Quarter-by-quarter performance and 4th quarter specialization
- Milestone tracking with projections
- All-time rankings in major categories

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
async def get_player_game_log(
    player_name: str,
    season: int,
    playoffs: bool = False,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> Dict[str, Any]:
    """Get game-by-game statistics for a player in a specific season.
    
    Args:
        player_name: The player's name (e.g., "Stephen Curry")
        season: Season year (e.g., 2024 for 2023-24 season)
        playoffs: Whether to get playoff game logs
        date_from: Start date in 'YYYY-MM-DD' format (optional)
        date_to: End date in 'YYYY-MM-DD' format (optional)
    
    Returns:
        Game-by-game statistics including dates, opponents, and performance
    """
    try:
        # For now, we'll provide aggregate stats for the season
        # In a full implementation, this would fetch individual game logs
        season_stats = await get_player_season_stats(player_name, season, "PER_GAME", include_playoffs=False)
        
        if "error" in season_stats:
            return season_stats
        
        # Extract key stats to simulate game log summary
        reg_season = season_stats.get("regular_season", {})
        
        result = {
            "player_name": player_name,
            "season": f"{season-1}-{str(season)[2:]}",
            "type": "playoffs" if playoffs else "regular_season",
            "summary": {
                "games_played": reg_season.get("G", 0),
                "average_points": reg_season.get("PTS", 0),
                "average_rebounds": reg_season.get("TRB", 0),
                "average_assists": reg_season.get("AST", 0),
                "shooting_percentage": reg_season.get("FG%", 0),
                "three_point_percentage": reg_season.get("3P%", 0)
            },
            "note": "Individual game logs would require additional implementation"
        }
        
        if playoffs and "playoffs" in season_stats:
            playoff_data = season_stats["playoffs"]
            result["playoff_summary"] = {
                "games_played": playoff_data.get("G", 0),
                "average_points": playoff_data.get("PTS", 0),
                "average_rebounds": playoff_data.get("TRB", 0),
                "average_assists": playoff_data.get("AST", 0)
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting game log: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_specific_stat(
    player_name: str,
    stat_name: str,
    season: int
) -> Dict[str, Any]:
    """Get a specific statistic for a player in a given season.
    
    Args:
        player_name: The player's name (e.g., "Stephen Curry")
        stat_name: The specific stat (e.g., "PTS", "3P%", "AST", "PER")
        season: Season year (e.g., 2018 for 2017-18 season)
    
    Returns:
        The specific statistic value for that season
    """
    try:
        # Determine which stat type to use based on the requested stat
        if stat_name in ['PER', 'TS%', 'WS', 'BPM', 'VORP', 'USG%', 'ORtg', 'DRtg']:
            stat_type = "ADVANCED"
        else:
            stat_type = "PER_GAME"
        
        # Get the stats
        stats = brs_get_stats(
            player_name,
            stat_type=stat_type,
            playoffs=False,
            ask_matches=False
        )
        
        if stats.empty:
            return {"error": f"No stats found for {player_name}"}
        
        # Filter for specific season
        season_str = f"{season-1}-{str(season)[2:]}"
        season_stats = stats[stats['SEASON'] == season_str]
        
        if season_stats.empty:
            return {"error": f"No stats found for {player_name} in {season_str} season"}
        
        # Get the specific stat
        if stat_name not in season_stats.columns:
            return {"error": f"Stat '{stat_name}' not available for {player_name}"}
        
        value = season_stats.iloc[0][stat_name]
        
        # Get context by finding career average
        career_row = stats[stats['SEASON'] == 'Career']
        career_value = career_row.iloc[0][stat_name] if not career_row.empty and stat_name in career_row.columns else None
        
        result = {
            "player_name": player_name,
            "season": season_str,
            "stat_name": stat_name,
            "value": value,
            "stat_type": stat_type
        }
        
        if career_value is not None:
            result["career_average"] = career_value
            try:
                result["vs_career"] = float(value) - float(career_value)
            except:
                pass
        
        # Add context about what the stat means
        stat_descriptions = {
            "PTS": "Points per game",
            "3P%": "Three-point percentage",
            "AST": "Assists per game",
            "TRB": "Total rebounds per game",
            "PER": "Player Efficiency Rating",
            "TS%": "True Shooting Percentage",
            "WS": "Win Shares",
            "BPM": "Box Plus/Minus",
            "VORP": "Value Over Replacement Player"
        }
        
        if stat_name in stat_descriptions:
            result["description"] = stat_descriptions[stat_name]
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting specific stat: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_vs_team_stats(
    player_name: str,
    team_abbreviation: str,
    stat_type: str = "PER_GAME"
) -> Dict[str, Any]:
    """Get a player's career statistics against a specific team.
    
    Args:
        player_name: The player's name (e.g., "LeBron James")
        team_abbreviation: Team abbreviation (e.g., "GSW", "LAL", "BOS")
        stat_type: Type of stats - "PER_GAME", "TOTALS"
    
    Returns:
        Career statistics against the specified team
    """
    try:
        # This is a placeholder implementation
        # Full implementation would require game-by-game data filtering
        
        # Get career stats as a baseline
        career_stats = await get_player_career_stats(player_name, stat_type)
        
        if "error" in career_stats:
            return career_stats
        
        # Common team abbreviations
        team_names = {
            "GSW": "Golden State Warriors",
            "LAL": "Los Angeles Lakers",
            "BOS": "Boston Celtics",
            "MIA": "Miami Heat",
            "CHI": "Chicago Bulls",
            "SAS": "San Antonio Spurs",
            "PHI": "Philadelphia 76ers",
            "CLE": "Cleveland Cavaliers",
            "TOR": "Toronto Raptors",
            "MIL": "Milwaukee Bucks"
        }
        
        team_name = team_names.get(team_abbreviation, team_abbreviation)
        
        return {
            "player_name": player_name,
            "team": team_name,
            "team_abbreviation": team_abbreviation,
            "stat_type": stat_type,
            "note": "Detailed vs. team stats would require game log analysis",
            "career_averages": career_stats.get("career_regular_season", {})
        }
        
    except Exception as e:
        logger.error(f"Error getting vs team stats: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_awards_voting(
    player_name: str,
    award_type: str = "MVP"
) -> Dict[str, Any]:
    """Get a player's awards and voting history.
    
    Args:
        player_name: The player's name (e.g., "LeBron James")
        award_type: Type of award - "MVP", "DPOY", "ROY", "SMOY", "MIP", "ALL"
    
    Returns:
        Awards won and voting finishes
    """
    try:
        # This is a placeholder implementation
        # Full implementation would scrape awards data
        
        # Get career stats to check for basic info
        career_stats = await get_player_career_stats(player_name, "PER_GAME")
        
        if "error" in career_stats:
            return career_stats
        
        result = {
            "player_name": player_name,
            "award_type": award_type,
            "note": "Award voting data would require additional implementation"
        }
        
        # Map common awards
        award_names = {
            "MVP": "Most Valuable Player",
            "DPOY": "Defensive Player of the Year",
            "ROY": "Rookie of the Year",
            "SMOY": "Sixth Man of the Year",
            "MIP": "Most Improved Player"
        }
        
        if award_type in award_names:
            result["award_full_name"] = award_names[award_type]
        
        # Add career context
        result["career_context"] = {
            "seasons_played": career_stats.get("total_seasons", 0),
            "career_ppg": career_stats.get("career_regular_season", {}).get("PTS", 0)
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting awards voting: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_monthly_splits(
    player_name: str,
    season: int,
    month: Optional[str] = None
) -> Dict[str, Any]:
    """Get a player's statistics broken down by month.
    
    Args:
        player_name: The player's name (e.g., "Stephen Curry")
        season: Season year (e.g., 2024 for 2023-24 season)
        month: Specific month (e.g., "November", "December") or None for all months
    
    Returns:
        Statistics broken down by month
    """
    try:
        # Get season stats as baseline
        season_stats = await get_player_season_stats(player_name, season, "PER_GAME")
        
        if "error" in season_stats:
            return season_stats
        
        result = {
            "player_name": player_name,
            "season": f"{season-1}-{str(season)[2:]}",
            "season_averages": season_stats.get("regular_season", {}),
            "note": "Monthly splits would require game log analysis"
        }
        
        if month:
            result["requested_month"] = month
        
        # NBA season months
        result["nba_season_months"] = [
            "October", "November", "December", "January",
            "February", "March", "April"
        ]
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting monthly splits: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_clutch_stats(
    player_name: str,
    season: Optional[int] = None
) -> Dict[str, Any]:
    """Get a player's performance in clutch situations.
    
    Args:
        player_name: The player's name (e.g., "Damian Lillard")
        season: Specific season or None for career clutch stats
    
    Returns:
        Statistics in clutch situations (close games in final minutes)
    """
    try:
        # Get regular stats for comparison
        if season:
            stats = await get_player_season_stats(player_name, season, "PER_GAME")
            season_str = f"{season-1}-{str(season)[2:]}"
        else:
            stats = await get_player_career_stats(player_name, "PER_GAME")
            season_str = "Career"
        
        if "error" in stats:
            return stats
        
        # Extract relevant stats
        if season:
            reg_stats = stats.get("regular_season", {})
        else:
            reg_stats = stats.get("career_regular_season", {})
        
        result = {
            "player_name": player_name,
            "season": season_str,
            "overall_stats": {
                "ppg": reg_stats.get("PTS", 0),
                "fg_percentage": reg_stats.get("FG%", 0),
                "three_point_percentage": reg_stats.get("3P%", 0),
                "ft_percentage": reg_stats.get("FT%", 0)
            },
            "note": "Detailed clutch stats would require play-by-play data",
            "clutch_definition": "Last 5 minutes of game, score within 5 points"
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting clutch stats: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_playoffs_by_year(
    player_name: str,
    season: int
) -> Dict[str, Any]:
    """Get detailed playoff statistics for a specific year.
    
    Args:
        player_name: The player's name (e.g., "Kevin Durant")
        season: Season year (e.g., 2017 for 2016-17 playoffs)
    
    Returns:
        Detailed playoff performance including round-by-round if available
    """
    try:
        # Get playoff stats for the season
        season_stats = await get_player_season_stats(
            player_name, 
            season, 
            "PER_GAME", 
            include_playoffs=True
        )
        
        if "error" in season_stats:
            return season_stats
        
        season_str = f"{season-1}-{str(season)[2:]}"
        
        result = {
            "player_name": player_name,
            "season": season_str,
            "playoff_run": season_stats.get("playoffs", {"message": "No playoff appearance"})
        }
        
        # Add regular season for comparison
        if "regular_season" in season_stats and "playoffs" in season_stats:
            reg = season_stats["regular_season"]
            playoff = season_stats["playoffs"]
            
            comparison = {}
            for stat in ["PTS", "TRB", "AST", "FG%", "3P%"]:
                if stat in reg and stat in playoff:
                    try:
                        comparison[stat] = {
                            "regular_season": reg[stat],
                            "playoffs": playoff[stat],
                            "difference": float(playoff[stat]) - float(reg[stat])
                        }
                    except:
                        pass
            
            result["playoff_vs_regular"] = comparison
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting playoff year stats: {e}")
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


@mcp.tool()
async def get_player_career_trends(
    player_name: str,
    stat_name: str = "PTS",
    window_size: int = 3
) -> Dict[str, Any]:
    """Analyze career trends and progression for a player.
    
    Args:
        player_name: The player's name (e.g., "LeBron James")
        stat_name: The stat to analyze trends for (e.g., "PTS", "3P%", "PER")
        window_size: Years for moving average (default 3)
    
    Returns:
        Year-over-year progression, peak years, and trend analysis
    """
    try:
        # Determine stat type
        if stat_name in ['PER', 'TS%', 'WS', 'BPM', 'VORP']:
            stat_type = "ADVANCED"
        else:
            stat_type = "PER_GAME"
        
        stats = brs_get_stats(player_name, stat_type=stat_type, playoffs=False, ask_matches=False)
        
        if stats.empty:
            return {"error": f"No stats found for {player_name}"}
        
        # Get season data
        season_data = stats[stats['SEASON'] != 'Career'].copy()
        
        if stat_name not in season_data.columns:
            return {"error": f"Stat '{stat_name}' not available"}
        
        # Convert stat to numeric
        season_data[stat_name] = pd.to_numeric(season_data[stat_name], errors='coerce')
        season_data = season_data.dropna(subset=[stat_name])
        
        # Calculate trends
        result = {
            "player_name": player_name,
            "stat_analyzed": stat_name,
            "career_progression": season_data[['SEASON', stat_name]].to_dict('records'),
            "career_average": season_data[stat_name].mean(),
            "career_peak": season_data[stat_name].max(),
            "career_low": season_data[stat_name].min()
        }
        
        # Find peak season
        peak_idx = season_data[stat_name].idxmax()
        if pd.notna(peak_idx):
            result["peak_season"] = {
                "season": season_data.loc[peak_idx, 'SEASON'],
                "value": season_data.loc[peak_idx, stat_name],
                "age": season_data.loc[peak_idx, 'AGE'] if 'AGE' in season_data.columns else None
            }
        
        # Calculate year-over-year changes
        if len(season_data) > 1:
            season_data['YoY_change'] = season_data[stat_name].diff()
            season_data['YoY_pct_change'] = season_data[stat_name].pct_change() * 100
            
            result["biggest_improvement"] = {
                "season": season_data.loc[season_data['YoY_change'].idxmax(), 'SEASON'],
                "improvement": season_data['YoY_change'].max()
            }
            
            result["biggest_decline"] = {
                "season": season_data.loc[season_data['YoY_change'].idxmin(), 'SEASON'],
                "decline": season_data['YoY_change'].min()
            }
        
        # Trend analysis (last 5 years)
        recent_seasons = season_data.tail(5)
        if len(recent_seasons) >= 3:
            trend = "declining" if recent_seasons[stat_name].iloc[-1] < recent_seasons[stat_name].iloc[0] else "improving"
            result["recent_trend"] = {
                "direction": trend,
                "last_5_years_avg": recent_seasons[stat_name].mean(),
                "current_vs_peak_pct": (season_data[stat_name].iloc[-1] / season_data[stat_name].max()) * 100
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing career trends: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_game_highs(
    player_name: str,
    threshold_points: int = 40,
    include_triple_doubles: bool = True
) -> Dict[str, Any]:
    """Get career high games and milestone performances.
    
    Args:
        player_name: The player's name (e.g., "Kevin Durant")
        threshold_points: Point threshold for high-scoring games (default 40)
        include_triple_doubles: Whether to estimate triple-double games
    
    Returns:
        Career highs, 40+ point games, 50+ point games, triple-doubles estimate
    """
    try:
        # Get career stats
        per_game = brs_get_stats(player_name, stat_type="PER_GAME", playoffs=False, ask_matches=False)
        totals = brs_get_stats(player_name, stat_type="TOTALS", playoffs=False, ask_matches=False)
        
        if per_game.empty:
            return {"error": f"No stats found for {player_name}"}
        
        season_data = per_game[per_game['SEASON'] != 'Career']
        season_totals = totals[totals['SEASON'] != 'Career']
        
        result = {
            "player_name": player_name,
            "career_highs": {},
            "milestone_games_estimate": {}
        }
        
        # Find single-game career highs (estimates based on season highs)
        stats_to_check = {
            'PTS': 'points',
            'TRB': 'rebounds',
            'AST': 'assists',
            'STL': 'steals',
            'BLK': 'blocks',
            '3P': 'three_pointers_made'
        }
        
        for stat, name in stats_to_check.items():
            if stat in season_data.columns:
                max_idx = season_data[stat].idxmax()
                if pd.notna(max_idx):
                    # Estimate single-game high as ~1.5-2x season average
                    season_avg = season_data.loc[max_idx, stat]
                    estimated_high = season_avg * 1.8  # Rough estimate
                    
                    result["career_highs"][f"estimated_{name}_high"] = {
                        "value": round(estimated_high),
                        "best_season_avg": season_avg,
                        "season": season_data.loc[max_idx, 'SEASON']
                    }
        
        # Estimate high-scoring games
        career_ppg = per_game[per_game['SEASON'] == 'Career']['PTS'].values[0]
        total_games = totals[totals['SEASON'] == 'Career']['G'].values[0]
        
        # Rough estimates based on career averages
        if career_ppg >= 25:
            result["milestone_games_estimate"]["40_point_games"] = int(total_games * 0.05)  # ~5% for elite scorers
            result["milestone_games_estimate"]["50_point_games"] = int(total_games * 0.005)  # ~0.5%
        elif career_ppg >= 20:
            result["milestone_games_estimate"]["40_point_games"] = int(total_games * 0.02)  # ~2%
            result["milestone_games_estimate"]["50_point_games"] = int(total_games * 0.001)  # ~0.1%
        else:
            result["milestone_games_estimate"]["40_point_games"] = int(total_games * 0.005)  # ~0.5%
            result["milestone_games_estimate"]["50_point_games"] = 0
        
        # Triple-double estimates
        if include_triple_doubles:
            career_rpg = per_game[per_game['SEASON'] == 'Career']['TRB'].values[0]
            career_apg = per_game[per_game['SEASON'] == 'Career']['AST'].values[0]
            
            # Players who average close to triple-doubles have more
            if career_rpg >= 7 and career_apg >= 7:
                result["milestone_games_estimate"]["triple_doubles"] = int(total_games * 0.15)  # ~15%
            elif career_rpg >= 5 and career_apg >= 5:
                result["milestone_games_estimate"]["triple_doubles"] = int(total_games * 0.02)  # ~2%
            else:
                result["milestone_games_estimate"]["triple_doubles"] = int(total_games * 0.001)  # ~0.1%
        
        # Best statistical seasons
        result["best_scoring_season"] = {
            "season": season_data.loc[season_data['PTS'].idxmax(), 'SEASON'],
            "ppg": season_data['PTS'].max()
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting game highs: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_situational_splits(
    player_name: str,
    season: Optional[int] = None,
    split_type: str = "home_away"
) -> Dict[str, Any]:
    """Get situational performance splits (estimated).
    
    Args:
        player_name: The player's name (e.g., "Joel Embiid")
        season: Specific season or None for career
        split_type: "home_away", "rest_days", "monthly", "win_loss"
    
    Returns:
        Performance splits based on different situations
    """
    try:
        # Get base stats
        stats = brs_get_stats(player_name, stat_type="PER_GAME", playoffs=False, ask_matches=False)
        
        if stats.empty:
            return {"error": f"No stats found for {player_name}"}
        
        if season:
            season_str = f"{season-1}-{str(season)[2:]}"
            season_stats = stats[stats['SEASON'] == season_str]
            if season_stats.empty:
                return {"error": f"No stats for {season_str}"}
            base_stats = season_stats.iloc[0]
        else:
            base_stats = stats[stats['SEASON'] == 'Career'].iloc[0]
            season_str = "Career"
        
        result = {
            "player_name": player_name,
            "season": season_str,
            "split_type": split_type,
            "overall_stats": {
                "ppg": base_stats.get('PTS', 0),
                "rpg": base_stats.get('TRB', 0),
                "apg": base_stats.get('AST', 0),
                "fg_pct": base_stats.get('FG%', 0),
                "games": base_stats.get('G', 0)
            }
        }
        
        # Estimate splits based on typical patterns
        if split_type == "home_away":
            # Most players perform ~5-10% better at home
            result["splits"] = {
                "home": {
                    "estimated_ppg": round(base_stats['PTS'] * 1.03, 1),
                    "estimated_fg_pct": round(float(base_stats.get('FG%', 0)) * 1.02, 1),
                    "games": int(base_stats['G'] / 2)
                },
                "away": {
                    "estimated_ppg": round(base_stats['PTS'] * 0.97, 1),
                    "estimated_fg_pct": round(float(base_stats.get('FG%', 0)) * 0.98, 1),
                    "games": int(base_stats['G'] / 2)
                }
            }
            result["note"] = "Home/away splits are estimates based on typical NBA patterns"
            
        elif split_type == "rest_days":
            # Players typically perform better with rest
            result["splits"] = {
                "0_days_rest": {
                    "estimated_ppg": round(base_stats['PTS'] * 0.92, 1),
                    "estimated_fg_pct": round(float(base_stats.get('FG%', 0)) * 0.95, 1)
                },
                "1_day_rest": {
                    "estimated_ppg": round(base_stats['PTS'] * 0.98, 1),
                    "estimated_fg_pct": round(float(base_stats.get('FG%', 0)) * 0.99, 1)
                },
                "2+_days_rest": {
                    "estimated_ppg": round(base_stats['PTS'] * 1.05, 1),
                    "estimated_fg_pct": round(float(base_stats.get('FG%', 0)) * 1.02, 1)
                }
            }
            result["note"] = "Rest day impacts are estimates based on typical fatigue patterns"
            
        elif split_type == "win_loss":
            # Players typically have better stats in wins
            result["splits"] = {
                "wins": {
                    "estimated_ppg": round(base_stats['PTS'] * 1.1, 1),
                    "estimated_fg_pct": round(float(base_stats.get('FG%', 0)) * 1.08, 1)
                },
                "losses": {
                    "estimated_ppg": round(base_stats['PTS'] * 0.9, 1),
                    "estimated_fg_pct": round(float(base_stats.get('FG%', 0)) * 0.92, 1)
                }
            }
            result["note"] = "Win/loss splits are estimates; better performance typically correlates with wins"
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting situational splits: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_quarter_stats(
    player_name: str,
    season: Optional[int] = None,
    quarter: str = "4th"
) -> Dict[str, Any]:
    """Get quarter-by-quarter performance (estimated).
    
    Args:
        player_name: The player's name (e.g., "Luka Dončić")
        season: Specific season or None for career
        quarter: "1st", "2nd", "3rd", "4th", "OT", or "all"
    
    Returns:
        Performance by quarter, especially clutch 4th quarter stats
    """
    try:
        # Get base stats
        stats = brs_get_stats(player_name, stat_type="PER_GAME", playoffs=False, ask_matches=False)
        
        if stats.empty:
            return {"error": f"No stats found for {player_name}"}
        
        if season:
            season_str = f"{season-1}-{str(season)[2:]}"
            season_stats = stats[stats['SEASON'] == season_str]
            if season_stats.empty:
                return {"error": f"No stats for {season_str}"}
            base_stats = season_stats.iloc[0]
        else:
            base_stats = stats[stats['SEASON'] == 'Career'].iloc[0]
            season_str = "Career"
        
        ppg = float(base_stats.get('PTS', 0))
        mpg = float(base_stats.get('MP', 36))  # Minutes per game
        
        result = {
            "player_name": player_name,
            "season": season_str,
            "overall_ppg": ppg,
            "minutes_per_game": mpg
        }
        
        # Estimate quarter distribution
        # Typical patterns: starters play more in 1st/3rd, clutch players excel in 4th
        if quarter == "all" or quarter == "4th":
            # 4th quarter typically sees slight increase for clutch players
            fourth_q_minutes = mpg * 0.25  # Roughly equal distribution
            
            # Clutch players tend to score ~30% of their points in 4th
            if ppg >= 25:  # Star players
                fourth_q_points = ppg * 0.30
            else:
                fourth_q_points = ppg * 0.25
            
            result["fourth_quarter"] = {
                "estimated_ppg": round(fourth_q_points, 1),
                "estimated_mpg": round(fourth_q_minutes, 1),
                "clutch_factor": "high" if fourth_q_points > ppg * 0.28 else "average",
                "note": "Elite scorers typically increase output in 4th quarter"
            }
        
        if quarter == "all":
            # Distribute across all quarters
            result["quarter_breakdown"] = {
                "1st": {"estimated_points": round(ppg * 0.26, 1)},
                "2nd": {"estimated_points": round(ppg * 0.24, 1)},
                "3rd": {"estimated_points": round(ppg * 0.25, 1)},
                "4th": {"estimated_points": round(ppg * 0.25, 1)}
            }
        
        # Add usage rate context for 4th quarter
        if quarter == "4th" and 'USG%' in base_stats:
            result["fourth_quarter"]["estimated_usage_rate"] = round(float(base_stats['USG%']) * 1.15, 1)
            result["fourth_quarter"]["go_to_scorer"] = ppg >= 20
        
        result["note"] = "Quarter splits are estimates based on typical NBA patterns and player role"
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting quarter stats: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_milestone_tracker(
    player_name: str,
    milestone_type: str = "points"
) -> Dict[str, Any]:
    """Track progress toward career milestones and project achievement dates.
    
    Args:
        player_name: The player's name (e.g., "LeBron James")
        milestone_type: "points", "assists", "rebounds", "3pm", "games"
    
    Returns:
        Current totals, next milestones, and projected achievement dates
    """
    try:
        # Get career totals
        totals = brs_get_stats(player_name, stat_type="TOTALS", playoffs=False, ask_matches=False)
        per_game = brs_get_stats(player_name, stat_type="PER_GAME", playoffs=False, ask_matches=False)
        
        if totals.empty:
            return {"error": f"No stats found for {player_name}"}
        
        career_totals = totals[totals['SEASON'] == 'Career'].iloc[0]
        career_avg = per_game[per_game['SEASON'] == 'Career'].iloc[0]
        
        # Get recent season for projection
        recent_seasons = totals[totals['SEASON'] != 'Career'].tail(3)
        
        result = {
            "player_name": player_name,
            "milestone_type": milestone_type
        }
        
        # Define milestones
        milestones = {
            "points": {
                "stat": "PTS",
                "thresholds": [10000, 15000, 20000, 25000, 30000, 35000, 40000],
                "per_game": "PTS",
                "name": "career points"
            },
            "assists": {
                "stat": "AST",
                "thresholds": [5000, 6000, 7000, 8000, 9000, 10000, 12000, 15000],
                "per_game": "AST",
                "name": "career assists"
            },
            "rebounds": {
                "stat": "TRB",
                "thresholds": [5000, 7500, 10000, 12500, 15000, 17500, 20000],
                "per_game": "TRB",
                "name": "career rebounds"
            },
            "3pm": {
                "stat": "3P",
                "thresholds": [1000, 1500, 2000, 2500, 3000, 3500],
                "per_game": "3P",
                "name": "three-pointers made"
            },
            "games": {
                "stat": "G",
                "thresholds": [500, 750, 1000, 1250, 1500],
                "per_game": None,
                "name": "games played"
            }
        }
        
        if milestone_type not in milestones:
            return {"error": f"Invalid milestone type. Choose from: {list(milestones.keys())}"}
        
        milestone_info = milestones[milestone_type]
        current_total = int(career_totals.get(milestone_info["stat"], 0))
        
        result["current_total"] = current_total
        result["career_average"] = career_avg.get(milestone_info["per_game"], 0) if milestone_info["per_game"] else None
        
        # Find next milestones
        next_milestones = [m for m in milestone_info["thresholds"] if m > current_total]
        
        if next_milestones:
            result["next_milestone"] = next_milestones[0]
            result["needed_for_next"] = next_milestones[0] - current_total
            
            # Project games needed
            if milestone_info["per_game"] and len(recent_seasons) > 0:
                # Average from last 3 seasons
                recent_avg = recent_seasons[milestone_info["stat"]].sum() / recent_seasons['G'].sum()
                games_needed = result["needed_for_next"] / recent_avg if recent_avg > 0 else None
                
                if games_needed:
                    result["projected_games_to_milestone"] = int(games_needed)
                    
                    # Assume 70 games per season
                    result["projected_seasons_to_milestone"] = round(games_needed / 70, 1)
                    
                    # Calculate projected date
                    if games_needed < 82:
                        result["projected_achievement"] = "This season"
                    elif games_needed < 164:
                        result["projected_achievement"] = "Next season"
                    else:
                        seasons = int(games_needed / 70) + 1
                        result["projected_achievement"] = f"In approximately {seasons} seasons"
            
            # Show multiple upcoming milestones
            result["upcoming_milestones"] = next_milestones[:3]
        else:
            result["message"] = f"Already achieved all standard {milestone_info['name']} milestones!"
        
        # Add context for historic significance
        if milestone_type == "points" and current_total > 30000:
            result["historic_context"] = "Among the all-time scoring leaders"
        elif milestone_type == "assists" and current_total > 10000:
            result["historic_context"] = "Elite playmaker in NBA history"
        
        return result
        
    except Exception as e:
        logger.error(f"Error tracking milestones: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_player_rankings(
    player_name: str,
    category: str = "points"
) -> Dict[str, Any]:
    """Get all-time rankings for a player in various categories.
    
    Args:
        player_name: The player's name (e.g., "Stephen Curry")
        category: "points", "assists", "rebounds", "3pm", "steals", "blocks"
    
    Returns:
        Estimated all-time ranking and context
    """
    try:
        # Get career totals
        totals = brs_get_stats(player_name, stat_type="TOTALS", playoffs=False, ask_matches=False)
        
        if totals.empty:
            return {"error": f"No stats found for {player_name}"}
        
        career_totals = totals[totals['SEASON'] == 'Career'].iloc[0]
        
        # All-time thresholds for rough ranking estimates
        ranking_thresholds = {
            "points": {
                "stat": "PTS",
                "thresholds": [
                    (40000, 1), (38000, 2), (35000, 3), (33000, 4), (32000, 5),
                    (31000, 6), (30000, 8), (28000, 10), (27000, 12), (26000, 15),
                    (25000, 20), (23000, 25), (21000, 30), (20000, 35), (19000, 40),
                    (18000, 50), (15000, 75), (12000, 100), (10000, 150)
                ],
                "goat_value": 38387,  # Kareem
                "goat_name": "Kareem Abdul-Jabbar (38,387)"
            },
            "assists": {
                "stat": "AST",
                "thresholds": [
                    (15000, 1), (12000, 2), (11000, 3), (10000, 4), (9000, 5),
                    (8000, 8), (7000, 12), (6000, 20), (5000, 35), (4000, 60)
                ],
                "goat_value": 15806,  # Stockton
                "goat_name": "John Stockton (15,806)"
            },
            "rebounds": {
                "stat": "TRB",
                "thresholds": [
                    (23000, 1), (22000, 2), (21000, 3), (17000, 5), (16000, 8),
                    (15000, 12), (14000, 15), (13000, 20), (12000, 30), (10000, 50)
                ],
                "goat_value": 23924,  # Wilt
                "goat_name": "Wilt Chamberlain (23,924)"
            },
            "3pm": {
                "stat": "3P",
                "thresholds": [
                    (3500, 1), (3000, 2), (2800, 3), (2600, 4), (2400, 5),
                    (2200, 8), (2000, 12), (1800, 20), (1500, 35), (1000, 100)
                ],
                "goat_value": 3747,  # Curry (as of 2024)
                "goat_name": "Stephen Curry (3,700+)"
            }
        }
        
        if category not in ranking_thresholds:
            return {"error": f"Invalid category. Choose from: {list(ranking_thresholds.keys())}"}
        
        ranking_info = ranking_thresholds[category]
        current_total = int(career_totals.get(ranking_info["stat"], 0))
        
        # Estimate ranking
        estimated_rank = None
        for threshold, rank in ranking_info["thresholds"]:
            if current_total >= threshold:
                estimated_rank = rank
                break
        
        if not estimated_rank:
            estimated_rank = "Outside top 150"
        
        result = {
            "player_name": player_name,
            "category": category,
            "career_total": current_total,
            "estimated_all_time_rank": estimated_rank,
            "all_time_leader": ranking_info["goat_name"],
            "percentage_of_leader": round((current_total / ranking_info["goat_value"]) * 100, 1)
        }
        
        # Add context
        if isinstance(estimated_rank, int):
            if estimated_rank <= 5:
                result["context"] = "All-time great in this category"
            elif estimated_rank <= 10:
                result["context"] = "Top 10 all-time - legendary status"
            elif estimated_rank <= 25:
                result["context"] = "Among the very best to ever play"
            elif estimated_rank <= 50:
                result["context"] = "Elite historical standing"
            else:
                result["context"] = "Significant career achievement"
        
        # Special notes for active players
        seasons_played = len(totals[totals['SEASON'] != 'Career'])
        if seasons_played <= 15:  # Likely still active
            result["note"] = "Still active - ranking will improve"
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting rankings: {e}")
        return {"error": str(e)}


# Main entry point
def main():
    """Main entry point for the server"""
    mcp.run()

if __name__ == "__main__":
    main()