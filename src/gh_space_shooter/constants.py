"""Global constants for the application."""

# Animation settings
DEFAULT_FPS = 40  # Default frames per second for animation

# GitHub contribution graph dimensions
NUM_WEEKS = 52  # Number of weeks in contribution graph
NUM_DAYS = 7  # Number of days in a week (Sun-Sat)
GAME_GRID_WIDTH = NUM_WEEKS # Width of the game grid in cells
SHIP_POSITION_Y = NUM_DAYS + 3  # Ship is positioned just below the grid

# Speeds in cells per second (frame-rate independent)
SHIP_SPEED = 12.5  # Cells per second the ship moves
BULLET_SPEED = 7.5  # Cells per second the bullet moves
BOSS_MOVE_SPEED = 0.5 # Cells per second the boss moves
POWER_UP_SPEED = 1.0 # Cells per second power-ups move downwards
BULLET_TRAILING_LENGTH = 3  # Number of trailing segments for bullets
BULLET_TRAIL_SPACING = 0.15  # Spacing between trail segments in cells

# Durations in seconds (frame-rate independent)
SHIP_SHOOT_COOLDOWN = 0.2  # Seconds between ship shots
BOSS_SHOOT_INTERVAL = 1.5 # Seconds between boss shots
SHIP_MAX_HEALTH = 3 # Maximum health for the player's ship
RAPID_FIRE_DURATION = 5.0 # Seconds rapid fire power-up lasts

# Power-up settings
POWER_UP_COLORS = {
    "rapid_fire": (0, 255, 0), # Green for rapid fire
}
POWER_UP_DROP_CHANCE_ENEMY = 0.1 # 10% chance for enemies to drop a power-up

# Explosion settings
EXPLOSION_PARTICLE_COUNT_LARGE = 8  # Number of particles in a large explosion
EXPLOSION_PARTICLE_COUNT_SMALL = 4  # Number of particles in a small explosion
EXPLOSION_MAX_RADIUS_LARGE = 20  # Max radius for large explosions
EXPLOSION_MAX_RADIUS_SMALL = 10  # Max radius for small explosions
EXPLOSION_DURATION_LARGE = 0.4  # Seconds for large explosion animation
EXPLOSION_DURATION_SMALL = 0.12  # Seconds for small explosion animation

# Starfield settings (speeds in cells per second)
STAR_SPEED_MIN = 1.0  # Minimum star speed (dimmer/farther stars)
STAR_SPEED_MAX = 2.5  # Maximum star speed (brighter/closer stars)

# Colors
BOSS_BULLET_COLOR = (255, 0, 0) # Red color for boss bullets
