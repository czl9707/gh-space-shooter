"""Tests for boss behavior."""

import pytest

from gh_space_shooter.game.game_state import GameState
from gh_space_shooter.game.drawables import Boss, BossBullet, Ship
from gh_space_shooter.constants import DEFAULT_FPS, BOSS_MOVE_SPEED, BOSS_SHOOT_INTERVAL, GAME_GRID_WIDTH, SHIP_MAX_HEALTH, SHIP_POSITION_Y

# Delta time for tests (1/fps seconds per frame)
TEST_DELTA_TIME = 1.0 / DEFAULT_FPS


class TestBossBehavior:
    """Tests for Boss movement, shooting, and interaction with the ship."""

    def test_boss_movement_side_to_side(self, default_game_state: GameState) -> None:
        """Test that the boss moves horizontally and reverses direction at boundaries."""
        boss_initial_x = 10.0
        boss = Boss(x=boss_initial_x, y=1, health=5, game_state=default_game_state)
        default_game_state.enemies.append(boss) # Add to enemies list if needed for general collision

        # Test moving right
        boss.direction = 1
        initial_direction = boss.direction
        while boss.direction == initial_direction:
            boss.animate(TEST_DELTA_TIME)
            assert boss.x <= GAME_GRID_WIDTH - boss.width_cells # Ensure it doesn't go past the right boundary
        
        assert pytest.approx(boss.x) == GAME_GRID_WIDTH - boss.width_cells # Should be at the right edge
        assert boss.direction == -1 # Should have reversed direction

        # Test moving left
        initial_direction = boss.direction
        while boss.direction == initial_direction:
            boss.animate(TEST_DELTA_TIME)
            assert boss.x >= 0 # Ensure it doesn't go past the left boundary

        assert pytest.approx(boss.x) == 0 # Should be at the left edge
        assert boss.direction == 1 # Should have reversed direction

    def test_boss_shooting_spread(self, default_game_state: GameState) -> None:
        """Test that the boss shoots a spread of BossBullets."""
        boss = Boss(x=GAME_GRID_WIDTH // 2, y=1, health=5, game_state=default_game_state)
        default_game_state.enemies.append(boss)
        default_game_state.bullets.clear() # Clear any existing bullets

        # Advance time to trigger shooting
        boss.shoot_cooldown = 0 # Ensure it shoots immediately
        boss.animate(TEST_DELTA_TIME) # Should trigger a shot

        assert len(default_game_state.bullets) == 3
        for bullet in default_game_state.bullets:
            assert isinstance(bullet, BossBullet)
            assert bullet.y == boss.y + boss.height_cells - 1 # Should be at boss's bottom y
        
        # Test bullet positions relative to boss x
        bullet_x_positions = sorted([b.x for b in default_game_state.bullets])
        assert pytest.approx(bullet_x_positions[0]) == boss.x + 0.5
        assert pytest.approx(bullet_x_positions[1]) == boss.x + 1.0
        assert pytest.approx(bullet_x_positions[2]) == boss.x + 1.5

        # Ensure cooldown is reset
        assert boss.shoot_cooldown == BOSS_SHOOT_INTERVAL

    def test_boss_health_and_destruction(self, default_game_state: GameState) -> None:
        """Test that the boss takes damage and is destroyed after health reaches zero."""
        boss_health = 10
        boss = Boss(x=10, y=1, health=boss_health, game_state=default_game_state)
        default_game_state.enemies.append(boss)

        for _ in range(boss_health - 1):
            boss.take_damage()
            assert boss.health == boss_health - (_ + 1)
            assert boss in default_game_state.enemies # Boss should still be present

        boss.take_damage() # Final hit
        assert boss.health == 0
        assert boss not in default_game_state.enemies # Boss should be removed

    def test_ship_takes_damage_from_boss_bullet(self, default_game_state: GameState) -> None:
        """Test that the ship takes damage when hit by a BossBullet."""
        ship = default_game_state.ship
        ship.health = SHIP_MAX_HEALTH # Reset ship health for test

        boss_bullet = BossBullet(x=ship.x, y=SHIP_POSITION_Y - 1.0, game_state=default_game_state)
        default_game_state.bullets.append(boss_bullet)

        initial_ship_health = ship.health
        
        # Animate bullet until it's removed (either collides or goes off-screen)
        while boss_bullet in default_game_state.bullets:
            boss_bullet.animate(TEST_DELTA_TIME)

        assert ship.health == initial_ship_health - 1
        assert boss_bullet not in default_game_state.bullets # Bullet should be removed
        assert len(default_game_state.explosions) == 1 # Explosion should be created
    
    def test_ship_destroyed_by_boss_bullet(self, default_game_state: GameState) -> None:
        """Test that the ship is destroyed when its health reaches zero from boss bullets."""
        ship = default_game_state.ship
        ship.health = 1 # Set health to 1 for quick destruction

        boss_bullet = BossBullet(x=ship.x, y=SHIP_POSITION_Y - 1.0, game_state=default_game_state)
        default_game_state.bullets.append(boss_bullet)

        # Animate bullet until it's removed (either collides or goes off-screen)
        while boss_bullet in default_game_state.bullets:
            boss_bullet.animate(TEST_DELTA_TIME)

        assert ship.health == 0
        assert ship.is_destroyed == True
        assert len(default_game_state.explosions) == 2 # Small explosion from bullet, large from ship
