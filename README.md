# NBA Player Stats MCP Server

A focused Model Context Protocol (MCP) server that provides comprehensive NBA player statistics from basketball-reference.com. This server specializes in delivering detailed player stats including career stats, season comparisons, advanced metrics, shooting stats, and more.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Available Tools](#available-tools)
- [Examples](#examples)
- [Basketball Reference Scraper Fixes](#basketball-reference-scraper-fixes)
- [Development Guide](#development-guide)
- [Known Issues](#known-issues)
- [Contributing](#contributing)
- [License](#license)

## Features

This MCP server provides specialized NBA player statistics tools across three layers of depth:

### Layer 1: Core Statistics (Tools 1-10)
- **Career Stats**: Complete career statistics with season-by-season breakdowns
- **Season Stats**: Detailed stats for specific seasons including playoffs
- **Per-Game Averages**: Traditional per-game statistics
- **Total Statistics**: Season and career totals (not averages)
- **Per-36 Minutes**: Pace-adjusted per-36-minute statistics
- **Advanced Metrics**: PER, TS%, WS, BPM, VORP, and other efficiency metrics
- **Player Comparisons**: Side-by-side comparisons between two players
- **Shooting Splits**: Detailed shooting percentages and volume stats
- **Playoff Performance**: Complete playoff statistics with regular season comparisons
- **Career Highlights**: Best seasons, milestones, and achievements

### Layer 2: Deep Analytics (Tools 11-17)
- **Game Logs**: Game-by-game statistics for detailed analysis
- **Specific Stat Queries**: Get individual stats for any season (e.g., "Steph's 3P% in 2018")
- **Awards & Voting**: MVP, DPOY, and other award voting positions
- **Vs. Team Stats**: Career performance against specific teams
- **Monthly Splits**: Performance broken down by month
- **Clutch Stats**: Performance in close games and pressure situations
- **Playoff Details**: Year-by-year playoff performance

### Layer 3: Ultra-Deep Analytics (Tools 18-23)
- **Career Trends**: Year-over-year progression and decline analysis
- **Game Highs**: Career highs, 40+ point games, triple-doubles
- **Situational Splits**: Home/away, rest days, win/loss situations
- **Quarter Stats**: 4th quarter specialization and clutch performance
- **Milestone Tracking**: Progress toward records with projections
- **All-Time Rankings**: Where players rank in NBA history

### Additional Features
- **Player Headshots**: Basketball-reference.com player headshot URLs
- **Multiple Stat Types**: PER_GAME, TOTALS, PER_MINUTE, PER_POSS, ADVANCED
- **Historical Data**: Access to historical seasons and career progressions
- **23 Total Tools**: Comprehensive coverage of every conceivable player stat query

## Quick Start

### Install from PyPI

```bash
pip install nba-player-stats-mcp
```

### Install from Source

1. Clone the repository:
```bash
git clone https://github.com/ziyadmir/nba-player-stats-mcp
cd nba-player-stats-mcp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Server

```bash
# If installed from PyPI
nba-player-stats-server

# If running from source
python src/server.py
```

### Configure Claude Desktop
```json
{
  "mcpServers": {
    "nba-player-stats": {
      "command": "python",
      "args": ["path/to/basketball/src/server.py"],
      "cwd": "path/to/basketball"
    }
  }
}
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Install from PyPI

The easiest way to install the NBA Player Stats MCP Server:

```bash
pip install nba-player-stats-mcp
```

### Install from Source

For development or to get the latest changes:

1. **Clone the repository:**
```bash
git clone https://github.com/ziyadmir/nba-player-stats-mcp
cd nba-player-stats-mcp
```

2. **Create a virtual environment (recommended):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install in development mode:**
```bash
pip install -e .
# Or with development dependencies
pip install -e ".[dev]"
```

## Usage

### Starting the Server

```bash
# If installed from PyPI
nba-player-stats-server

# If running from source
python src/server.py
```

### Python Usage Examples

```python
# Import the fix first
import fix_basketball_reference
from basketball_reference_scraper.players import get_stats

# Get LeBron's career per-game stats
stats = get_stats('LeBron James', stat_type='PER_GAME', ask_matches=False)

# Get specific season
stats_2023 = stats[stats['SEASON'] == '2022-23']

# Get playoff stats
playoff_stats = get_stats('LeBron James', stat_type='PER_GAME', playoffs=True, ask_matches=False)
```

See `example_usage.py` for more comprehensive examples.

## Available Tools

### 1. `get_player_career_stats`
Get complete career statistics for an NBA player.

**Parameters:**
- `player_name` (string, required): The player's name (e.g., "LeBron James")
- `stat_type` (string, optional): Type of stats - "PER_GAME", "TOTALS", "PER_MINUTE", "PER_POSS", "ADVANCED"

### 2. `get_player_season_stats`
Get statistics for a specific season.

**Parameters:**
- `player_name` (string, required): The player's name
- `season` (integer, required): Season year (e.g., 2023 for 2022-23)
- `stat_type` (string, optional): Type of stats
- `include_playoffs` (boolean, optional): Include playoff stats if available

### 3. `get_player_advanced_stats`
Get advanced statistics (PER, TS%, WS, BPM, VORP, etc.).

**Parameters:**
- `player_name` (string, required): The player's name
- `season` (integer, optional): Specific season, or None for all seasons

### 4. `get_player_per36_stats`
Get per-36-minute statistics (pace-adjusted).

**Parameters:**
- `player_name` (string, required): The player's name
- `season` (integer, optional): Specific season, or None for all seasons

### 5. `compare_players`
Compare statistics between two NBA players.

**Parameters:**
- `player1_name` (string, required): First player's name
- `player2_name` (string, required): Second player's name
- `stat_type` (string, optional): Type of stats to compare
- `season` (integer, optional): Specific season, or None for career comparison

### 6. `get_player_shooting_splits`
Get detailed shooting statistics and splits.

**Parameters:**
- `player_name` (string, required): The player's name
- `season` (integer, optional): Specific season, or None for career stats

### 7. `get_player_totals`
Get total statistics (not averages).

**Parameters:**
- `player_name` (string, required): The player's name
- `season` (integer, optional): Specific season, or None for career totals

### 8. `get_player_playoff_stats`
Get playoff statistics with regular season comparison.

**Parameters:**
- `player_name` (string, required): The player's name
- `stat_type` (string, optional): Type of stats

### 9. `get_player_headshot_url`
Get the basketball-reference.com headshot URL.

**Parameters:**
- `player_name` (string, required): The player's name

### 10. `get_player_career_highlights`
Get career highlights and achievements.

**Parameters:**
- `player_name` (string, required): The player's name

## Layer 2: Deep Analytics Tools

### 11. `get_player_game_log`
Get game-by-game statistics for a specific season.

**Parameters:**
- `player_name` (string, required): The player's name
- `season` (integer, required): Season year (e.g., 2024)
- `playoffs` (boolean, optional): Whether to get playoff game logs
- `date_from` (string, optional): Start date in 'YYYY-MM-DD' format
- `date_to` (string, optional): End date in 'YYYY-MM-DD' format

### 12. `get_player_specific_stat`
Get a specific statistic for a player in a given season. Perfect for answering questions like "What was Steph's 3P% in 2018?"

**Parameters:**
- `player_name` (string, required): The player's name
- `stat_name` (string, required): The specific stat (e.g., "PTS", "3P%", "PER")
- `season` (integer, required): Season year

### 13. `get_player_vs_team_stats`
Get career statistics against a specific team.

**Parameters:**
- `player_name` (string, required): The player's name
- `team_abbreviation` (string, required): Team code (e.g., "GSW", "LAL")
- `stat_type` (string, optional): Type of stats

### 14. `get_player_awards_voting`
Get awards and voting history.

**Parameters:**
- `player_name` (string, required): The player's name
- `award_type` (string, optional): "MVP", "DPOY", "ROY", "SMOY", "MIP"

### 15. `get_player_monthly_splits`
Get statistics broken down by month.

**Parameters:**
- `player_name` (string, required): The player's name
- `season` (integer, required): Season year
- `month` (string, optional): Specific month or None for all

### 16. `get_player_clutch_stats`
Get performance in clutch situations.

**Parameters:**
- `player_name` (string, required): The player's name
- `season` (integer, optional): Specific season or None for career

### 17. `get_player_playoffs_by_year`
Get detailed playoff statistics for a specific year.

**Parameters:**
- `player_name` (string, required): The player's name
- `season` (integer, required): Season year

## Layer 3: Ultra-Deep Analytics Tools

### 18. `get_player_career_trends`
Analyze career trends and progression, including year-over-year changes and decline/improvement patterns.

**Parameters:**
- `player_name` (string, required): The player's name
- `stat_name` (string, optional): The stat to analyze trends for (default: "PTS")
- `window_size` (integer, optional): Years for moving average (default: 3)

### 19. `get_player_game_highs`
Get career high games and milestone performances (40+ point games, 50+ point games, triple-doubles).

**Parameters:**
- `player_name` (string, required): The player's name
- `threshold_points` (integer, optional): Point threshold for high-scoring games (default: 40)
- `include_triple_doubles` (boolean, optional): Whether to estimate triple-double games

### 20. `get_player_situational_splits`
Get situational performance splits including home/away, rest days, and win/loss situations.

**Parameters:**
- `player_name` (string, required): The player's name
- `season` (integer, optional): Specific season or None for career
- `split_type` (string, optional): "home_away", "rest_days", "monthly", "win_loss"

### 21. `get_player_quarter_stats`
Get quarter-by-quarter performance, especially 4th quarter and overtime stats.

**Parameters:**
- `player_name` (string, required): The player's name
- `season` (integer, optional): Specific season or None for career
- `quarter` (string, optional): "1st", "2nd", "3rd", "4th", "OT", or "all"

### 22. `get_player_milestone_tracker`
Track progress toward career milestones with projections for achievement.

**Parameters:**
- `player_name` (string, required): The player's name
- `milestone_type` (string, optional): "points", "assists", "rebounds", "3pm", "games"

### 23. `get_player_rankings`
Get all-time rankings for a player in various categories.

**Parameters:**
- `player_name` (string, required): The player's name
- `category` (string, optional): "points", "assists", "rebounds", "3pm", "steals", "blocks"

## Examples

Here are some example questions this MCP server can answer:

### Basic Queries (Layer 1)
1. **Career Overview**: "What are LeBron James' career statistics?"
2. **Season Comparison**: "How did Stephen Curry perform in the 2016 season?"
3. **Player Comparison**: "Compare Michael Jordan and LeBron James career stats"
4. **Shooting Analysis**: "What are Steph Curry's career shooting percentages?"
5. **Advanced Metrics**: "What was Nikola Jokić's PER in 2023?"
6. **Playoff Performance**: "How do Kawhi Leonard's playoff stats compare to regular season?"
7. **Career Milestones**: "What are Kareem Abdul-Jabbar's career highlights?"
8. **Per-36 Stats**: "What are Giannis Antetokounmpo's per-36 minute stats?"

### Deep Analytics Queries (Layer 2)
9. **Specific Stat**: "What was Steph Curry's 3-point percentage in 2018?"
10. **Points Query**: "How many points did Stephen Curry average in 2024?"
11. **Awards**: "Where did LeBron James finish in MVP voting in 2020?"
12. **Game Logs**: "Show me Damian Lillard's game log for the 2021 playoffs"
13. **Vs Team**: "What are Kevin Durant's career stats against the Lakers?"
14. **Monthly**: "How did Jayson Tatum perform in December 2023?"
15. **Clutch**: "What are Kyrie Irving's clutch stats for his career?"
16. **Playoff Year**: "How did Jimmy Butler perform in the 2020 playoffs?"

### Ultra-Deep Analytics Queries (Layer 3)
17. **Career Trends**: "Is LeBron James declining with age?"
18. **Milestone Games**: "How many 40-point games does Kevin Durant have?"
19. **Home/Away**: "How does Joel Embiid perform at home vs away?"
20. **4th Quarter**: "What's Luka Dončić's scoring average in 4th quarters?"
21. **Milestone Tracking**: "When will LeBron pass 40,000 points?"
22. **All-Time Rankings**: "Where does Steph Curry rank all-time in 3-pointers made?"
23. **Situational**: "How does Giannis perform on back-to-backs?"
24. **Quarter Breakdown**: "What percentage of Dame's points come in the 4th?"

### Stat Type Explanations

- **PER_GAME**: Traditional per-game averages (points, rebounds, assists, etc.)
- **TOTALS**: Total statistics for a season or career
- **PER_MINUTE**: Per-36-minute statistics (normalized for playing time)
- **PER_POSS**: Per-100-possessions statistics (normalized for pace)
- **ADVANCED**: Advanced metrics (PER, TS%, WS, BPM, VORP, etc.)

### Key Statistics Glossary
- **PER**: Player Efficiency Rating
- **TS%**: True Shooting Percentage
- **WS**: Win Shares
- **BPM**: Box Plus/Minus
- **VORP**: Value Over Replacement Player
- **eFG%**: Effective Field Goal Percentage
- **USG%**: Usage Rate
- **ORtg**: Offensive Rating (points per 100 possessions)
- **DRtg**: Defensive Rating (points allowed per 100 possessions)
- **3P%**: Three-Point Field Goal Percentage
- **FT%**: Free Throw Percentage
- **AST%**: Assist Percentage
- **REB%**: Rebound Percentage

## Basketball Reference Scraper Fixes

**Important**: The `basketball_reference_scraper` library has compatibility issues with the current basketball-reference.com website structure. This server includes automatic fixes for these issues.

### Issues Fixed

1. **Table ID Changes**: Basketball Reference updated their HTML table IDs
   - `per_game` → `per_game_stats`
   - `totals` → `totals_stats`
   - `per_minute` → `per_minute_stats`

2. **Pandas Compatibility**: Fixed deprecation warnings with `pd.read_html()`

3. **Error Handling**: Improved handling of missing data and edge cases

The fixes are automatically applied when the server starts via the `fix_basketball_reference.py` module.

### Complete Fix Details

The fix involves updating the `basketball_reference_scraper/players.py` file:

1. **Add StringIO import** (after BeautifulSoup import):
   ```python
   from io import StringIO
   ```

2. **Update table ID mapping** (in `get_stats` function):
   ```python
   # Map old table IDs to new ones
   table_id_map = {
       'per_game': 'per_game_stats',
       'totals': 'totals_stats',
       'per_minute': 'per_minute_stats',
       'per_poss': 'per_poss_stats',
       'advanced': 'advanced'
   }
   ```

3. **Fix pandas read_html deprecation**:
   ```python
   # Replace: df = pd.read_html(table)[0]
   df = pd.read_html(StringIO(table))[0]
   ```

4. **Handle missing Career row**:
   ```python
   career_rows = df[df['SEASON']=='Career'].index
   if len(career_rows) > 0:
       career_index = career_rows[0]
       # ... rest of logic
   ```

To contribute these fixes back to the original library, see the [Contributing](#contributing) section.

## Development Guide

### Setting Up Development Environment

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_integration.py -v
```

### Manual Testing

Test the fix module:
```bash
python example_usage.py
```

### Common Test Cases

1. **Player Name Variations**:
   - Exact match: "LeBron James" ✓
   - Case sensitivity: "lebron james" ✗
   - Partial names: "LeBron" ✗

2. **Edge Cases**:
   - Retired players
   - Players with no playoff experience
   - Historical players (pre-1973 for advanced stats)

### Code Style Guidelines

1. **Python Style**: Follow PEP 8
2. **Error Handling**: Always catch specific exceptions
3. **Data Processing**: Check for empty results before accessing

### Extending the Server

To add new tools:

1. Create function in `server.py`:
   ```python
   @mcp.tool()
   async def get_player_new_stat(
       player_name: str,
       **kwargs
   ) -> Dict[str, Any]:
       """Tool description"""
       try:
           # Implementation
           pass
       except Exception as e:
           logger.error(f"Error: {e}")
           return {"error": str(e)}
   ```

2. Test thoroughly with various players
3. Update this README with new tool documentation

## Known Issues

### Working Features ✅
- All player statistics tools function correctly with the fixes applied
- Player headshot URLs work reliably

### Limitations ⚠️

1. **Player Names**: Must match basketball-reference.com format exactly
   - ✓ "LeBron James" 
   - ✗ "Lebron" or "lebron james"

2. **Historical Data**: Some features may have limited data for older seasons
   - Advanced stats not available before 1973-74
   - Some shooting stats missing for early careers

3. **Library Limitations**: The underlying `basketball_reference_scraper` has:
   - No active maintenance
   - Inconsistent error handling
   - Limited documentation

### Troubleshooting

**"No tables found" Error**
- Cause: Website structure changed
- Fix: Applied automatically by fix_basketball_reference.py

**Player Not Found**
- Cause: Incorrect name format
- Solution: Use exact names from basketball-reference.com

**Empty Results**
- Cause: Player has no stats for requested type/season
- Solution: Check player's career span and stat availability

## Testing

Run the test suite:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Contributing Fixes to basketball_reference_scraper

To contribute our fixes back to the original library:

1. Fork: https://github.com/vishaalagartha/basketball_reference_scraper
2. Apply changes from `fix_basketball_reference.py`
3. Test thoroughly with various players
4. Submit PR: "Fix table parsing for updated basketball-reference.com structure"

## Changelog

### Version 0.3.0 (Latest)
- Added Layer 3 ultra-deep analytics tools (6 new tools)
- Career trend analysis with year-over-year progression
- Game highs and milestone tracking (40+ pt games, triple-doubles)
- Situational splits (home/away, rest days, wins/losses)
- Quarter-by-quarter performance analysis
- Milestone projections and all-time rankings
- Now includes 23 total tools across 3 layers

### Version 0.2.0
- Added Layer 2 deep analytics tools (7 new tools)
- Game logs and specific stat queries
- Awards and voting history support
- Team matchup statistics
- Monthly and temporal splits
- Clutch performance metrics
- Enhanced playoff year-by-year analysis

### Version 0.1.0
- Initial release with 10 core player statistics tools
- Basketball-reference.com compatibility fixes
- Career, season, and advanced statistics

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Data sourced from [basketball-reference.com](https://www.basketball-reference.com)
- Built using the [basketball_reference_scraper](https://github.com/vishaalagartha/basketball_reference_scraper) library
- Implements the [Model Context Protocol](https://modelcontextprotocol.io)
- Uses [FastMCP](https://github.com/jlowin/fastmcp) framework

## Support

For issues and feature requests, please use the [GitHub issue tracker](https://github.com/ziyadmir/nba-player-stats-mcp/issues).