# CSS Selectors
# Updated for OdiLeague structure

# General
POPUP_CLOSE_BUTTON = "div.roadblock-close button"
ROUND_TIMER = ".virtual-timer .ss.active"
LIVE_BADGE = ".live"  # Based on <li class="live">

# Navigation
LEAGUE_LOGO = ".virtual-logos .logo"
# Note: There isn't a traditional dropdown anymore, selection is via logos.
# We'll keep LEAGUE_DROPDOWN as a placeholder or deprecate it in logic.
LEAGUE_CONTAINER = ".virtual-logos" 
LEAGUE_CONTAINER = ".virtual-logos" 
LEAGUE_NAME_TEXT = ".text-xs" # Text inside the logo container
LEAGUE_DROPDOWN = LEAGUE_CONTAINER # Alias for backward compatibility
LEAGUE_OPTION_TEMPLATE = "div.logo:has(.text-xs:contains('{}'))" # Placeholder for league selection

# Match Items
MATCH_CONTAINER = ".game"
TEAM_NAMES = ".info .t .t-l"
ODDS_BUTTON = ".odds .o button"

# Markets
MARKET_CONTAINER = ".market_container_placeholder" # Update with actual selector if known
MARKET_DROPDOWN = MARKET_CONTAINER # Alias
MARKET_OPTION_TEMPLATE = "div.market:contains('{}')" # Placeholder

# Results & Stats
RESULTS_CONTAINER = ".rs"
RESULT_ROW = ".rs-g"
STANDINGS_TABLE = ".virtual-standings table"
GOAL_EVENT = ".goal-alert" # Placeholder, update if found in dynamic interactions
