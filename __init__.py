"""NBA Player Stats MCP Server

A Model Context Protocol server for NBA player statistics from basketball-reference.com.
"""

__version__ = "0.1.0"
__author__ = "Ziyad Mir"
__email__ = "ziyadmir@gmail.com"

# Import the fix automatically when the package is imported
try:
    import fix_basketball_reference
except ImportError:
    pass