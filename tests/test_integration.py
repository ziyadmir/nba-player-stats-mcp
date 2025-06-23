#!/usr/bin/env python3
"""Integration tests for NBA Player Stats MCP Server

These tests verify that the MCP server can fetch real player data from basketball-reference.com
"""

import pytest
import asyncio
import os
import sys

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the fix first
import fix_basketball_reference

from src.server import (
    get_player_career_stats,
    get_player_season_stats,
    get_player_advanced_stats,
    get_player_per36_stats,
    compare_players,
    get_player_shooting_splits,
    get_player_totals,
    get_player_playoff_stats,
    get_player_headshot_url,
    get_player_career_highlights
)

# Access the underlying functions from FunctionTool objects
get_player_career_stats = get_player_career_stats.fn
get_player_season_stats = get_player_season_stats.fn
get_player_advanced_stats = get_player_advanced_stats.fn
get_player_per36_stats = get_player_per36_stats.fn
compare_players = compare_players.fn
get_player_shooting_splits = get_player_shooting_splits.fn
get_player_totals = get_player_totals.fn
get_player_playoff_stats = get_player_playoff_stats.fn
get_player_headshot_url = get_player_headshot_url.fn
get_player_career_highlights = get_player_career_highlights.fn


class TestPlayerCareerStats:
    """Test career statistics functions"""
    
    @pytest.mark.asyncio
    async def test_lebron_career_stats(self):
        """Test fetching LeBron James' career statistics"""
        stats = await get_player_career_stats("LeBron James")
        
        assert "player_name" in stats
        assert stats["player_name"] == "LeBron James"
        assert "career_regular_season" in stats
        assert "seasons" in stats
        assert "total_seasons" in stats
        assert stats["total_seasons"] >= 20  # LeBron has played 20+ seasons
        
        # Check career averages
        career = stats["career_regular_season"]
        assert float(career["PTS"]) > 25  # LeBron averages over 25 PPG
        assert float(career["AST"]) > 7   # Over 7 assists per game
        assert float(career["TRB"]) > 7   # Over 7 rebounds per game
    
    @pytest.mark.asyncio
    async def test_curry_career_shooting(self):
        """Test Stephen Curry's career stats with focus on shooting"""
        stats = await get_player_career_stats("Stephen Curry", stat_type="PER_GAME")
        
        assert "career_regular_season" in stats
        career = stats["career_regular_season"]
        
        # Curry should have exceptional 3P%
        assert float(career["3P%"]) > 0.42  # Career 42%+ from three
        assert float(career["FT%"]) > 0.90  # Elite free throw shooter


class TestPlayerSeasonStats:
    """Test season-specific statistics"""
    
    @pytest.mark.asyncio
    async def test_giannis_mvp_season(self):
        """Test Giannis' 2019 MVP season stats"""
        stats = await get_player_season_stats("Giannis Antetokounmpo", season=2019)
        
        assert stats["season"] == "2018-19"
        assert "regular_season" in stats
        
        # MVP season stats
        season_stats = stats["regular_season"]
        assert float(season_stats["PTS"]) > 27  # 27.7 PPG in MVP season
        assert float(season_stats["TRB"]) > 12  # 12.5 RPG
    
    @pytest.mark.asyncio
    async def test_jokic_recent_season(self):
        """Test Nikola Jokić's recent season with playoffs"""
        stats = await get_player_season_stats("Nikola Jokić", season=2023, include_playoffs=True)
        
        assert stats["season"] == "2022-23"
        assert "regular_season" in stats
        
        # Check if playoff stats are included (if he made playoffs)
        if "playoffs" in stats:
            assert "PTS" in stats["playoffs"]


class TestAdvancedStats:
    """Test advanced statistics functions"""
    
    @pytest.mark.asyncio
    async def test_jokic_advanced_stats(self):
        """Test Nikola Jokić's advanced stats (high PER)"""
        stats = await get_player_advanced_stats("Nikola Jokić", season=2022)
        
        assert stats["season"] == "2021-22"
        assert "advanced_stats" in stats
        
        adv = stats["advanced_stats"]
        assert float(adv["PER"]) > 31  # Historic MVP season PER
    
    @pytest.mark.asyncio
    async def test_career_advanced_stats(self):
        """Test career advanced stats with best seasons"""
        stats = await get_player_advanced_stats("LeBron James")
        
        assert "career_advanced" in stats
        assert "best_seasons" in stats
        assert "best_PER_season" in stats["best_seasons"]


class TestPlayerComparisons:
    """Test player comparison functions"""
    
    @pytest.mark.asyncio
    async def test_lebron_vs_jordan(self):
        """Test comparing LeBron James vs Michael Jordan"""
        comparison = await compare_players("LeBron James", "Michael Jordan")
        
        assert comparison["comparison_type"] == "career"
        assert "player1" in comparison
        assert "player2" in comparison
        assert "statistical_comparison" in comparison
        
        # Both should have impressive career stats
        assert float(comparison["player1"]["career_stats"]["PTS"]) > 25
        assert float(comparison["player2"]["career_stats"]["PTS"]) > 30
    
    @pytest.mark.asyncio
    async def test_curry_vs_allen_shooting(self):
        """Test comparing shooters"""
        comparison = await compare_players("Stephen Curry", "Ray Allen", stat_type="PER_GAME")
        
        assert "statistical_comparison" in comparison
        assert "3P%" in comparison["statistical_comparison"]


class TestShootingStats:
    """Test shooting statistics functions"""
    
    @pytest.mark.asyncio
    async def test_curry_shooting_splits(self):
        """Test Stephen Curry's shooting splits"""
        stats = await get_player_shooting_splits("Stephen Curry")
        
        assert "career_shooting" in stats
        shooting = stats["career_shooting"]
        
        assert "three_pointers" in shooting
        assert float(shooting["three_pointers"]["percentage"]) > 0.42
        assert "best_shooting_seasons" in stats
    
    @pytest.mark.asyncio
    async def test_durant_shooting_efficiency(self):
        """Test Kevin Durant's shooting efficiency"""
        stats = await get_player_shooting_splits("Kevin Durant", season=2014)
        
        assert stats["season"] == "2013-14"
        assert "shooting_stats" in stats
        
        # Durant's MVP season with elite efficiency
        shooting = stats["shooting_stats"]
        assert float(shooting["field_goals"]["percentage"]) > 0.50


class TestPlayerTotals:
    """Test total statistics functions"""
    
    @pytest.mark.asyncio
    async def test_kareem_career_totals(self):
        """Test Kareem Abdul-Jabbar's career totals (all-time leading scorer)"""
        stats = await get_player_totals("Kareem Abdul-Jabbar")
        
        assert "career_totals" in stats
        totals = stats["career_totals"]
        
        # Kareem was the all-time leading scorer before LeBron
        assert int(totals["PTS"]) > 38000
        assert "milestones" in stats
    
    @pytest.mark.asyncio
    async def test_season_totals(self):
        """Test single season totals"""
        stats = await get_player_totals("James Harden", season=2019)
        
        assert stats["season"] == "2018-19"
        assert "totals" in stats
        
        # Harden's high-scoring season
        totals = stats["totals"]
        assert int(totals["PTS"]) > 2800  # Scored over 2800 points


class TestPlayoffStats:
    """Test playoff statistics"""
    
    @pytest.mark.asyncio
    async def test_lebron_playoff_dominance(self):
        """Test LeBron's playoff statistics"""
        stats = await get_player_playoff_stats("LeBron James")
        
        assert "career_playoff_stats" in stats
        assert "playoff_appearances" in stats
        assert stats["playoff_appearances"] >= 13  # Many playoff appearances
        
        # Check playoff vs regular season comparison
        assert "playoff_vs_regular_season" in stats
        comparison = stats["playoff_vs_regular_season"]
        if "PTS" in comparison:
            # LeBron typically scores more in playoffs
            assert comparison["PTS"]["difference"] > 0


class TestMiscellaneous:
    """Test other functions"""
    
    @pytest.mark.asyncio
    async def test_player_headshot(self):
        """Test getting player headshot URL"""
        result = await get_player_headshot_url("Kevin Durant")
        
        assert "headshot_url" in result
        assert result["headshot_url"].startswith("http")
        assert "basketball-reference.com" in result["source"]
    
    @pytest.mark.asyncio
    async def test_career_highlights(self):
        """Test career highlights function"""
        highlights = await get_player_career_highlights("Tim Duncan")
        
        assert "career_overview" in highlights
        assert "single_season_highs" in highlights
        assert highlights["career_overview"]["seasons_played"] >= 19  # Duncan played 19 seasons
        
        # Duncan was a consistent 20+ PPG scorer
        if "seasons_20plus_ppg" in highlights:
            assert highlights["seasons_20plus_ppg"] > 0


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_retired_player(self):
        """Test getting stats for a retired player"""
        stats = await get_player_career_stats("Kobe Bryant")
        
        assert "player_name" in stats
        assert stats["total_seasons"] == 20  # Kobe played exactly 20 seasons
    
    @pytest.mark.asyncio
    async def test_player_no_playoffs(self):
        """Test player with limited/no playoff experience"""
        stats = await get_player_playoff_stats("Karl-Anthony Towns")
        
        # Should handle gracefully whether he has playoff stats or not
        assert "player_name" in stats
        if stats.get("playoff_appearances", 0) == 0:
            assert "message" in stats
    
    @pytest.mark.asyncio
    async def test_historical_player(self):
        """Test historical player (limited advanced stats)"""
        stats = await get_player_advanced_stats("Bill Russell")
        
        # Bill Russell played before many advanced stats were tracked
        assert "player_name" in stats or "error" in stats


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])