"""Tests for power-up behaviors."""

import pytest
import random

from gh_space_shooter.game.game_state import GameState
from gh_space_shooter.game.drawables import Enemy, Boss, PowerUp, RapidFirePowerUp, Bullet
from gh_space_shooter.github_client import ContributionData
from gh_space_shooter.constants import (
    DEFAULT_FPS,
    POWER_UP_DROP_CHANCE_ENEMY,
    RAPID_FIRE_DURATION,
    SHIP_SHOOT_COOLDOWN,
    SHIP_POSITION_Y,
)

TEST_DELTA_TIME = 1.0 / DEFAULT_FPS


class TestPowerUps:
    """Tests for Power-up spawning, movement, collection, and effects."""

    @pytest.fixture
    def empty_contribution_data(self) -> ContributionData:
        """Fixture for empty contribution data."""
        return {"total_contributions": 0, "weeks": []}

    @pytest.fixture
    def game_state_with_ship(self, empty_contribution_data: ContributionData) -> GameState:
        """Fixture for game state with a ship."""
        return GameState(empty_contribution_data)

    def test_power_up_spawning_enemy(self, game_state_with_ship: GameState) -> None:
        """Test that power-ups are spawned by enemies with a given chance."""
        # Temporarily set drop chance to 100% for testing
        original_chance = POWER_UP_DROP_CHANCE_ENEMY
        # Mock random.random to always return a value that triggers drop
        random.seed(0) # Seed for reproducibility
        # This part requires mocking a global constant, which is tricky.
        # A better approach would be to pass the drop chance as an argument
        # or use a mock. For now, we will rely on a high number of attempts.

        num_enemies = 100
        destroyed_power_ups = 0
        
        # We can't easily mock a constant, so we will test the probability over many trials
        # This test aims to ensure that power-ups *can* drop.
        # A more robust test would involve mocking random.random()

        for _ in range(num_enemies):
            enemy = Enemy(x=0, y=0, health=1, game_state=game_state_with_ship)
            game_state_with_ship.enemies.append(enemy)
            bullet = Bullet(x=enemy.x, game_state=game_state_with_ship)
            bullet.y = enemy.y + 1
            game_state_with_ship.bullets.append(bullet)

            while bullet in game_state_with_ship.bullets:
                bullet.animate(TEST_DELTA_TIME)
            
            if len(game_state_with_ship.power_ups) > destroyed_power_ups:
                destroyed_power_ups += 1
                power_up = game_state_with_ship.power_ups[-1]
                assert isinstance(power_up, RapidFirePowerUp)
                assert power_up.x == enemy.x
                assert power_up.y == enemy.y

        # Assert that at least some power-ups dropped, given enough enemies
        assert destroyed_power_ups > 0

        # Clean up power-ups for next tests
        game_state_with_ship.power_ups.clear()


    def test_power_up_spawning_boss(self, game_state_with_ship: GameState) -> None:
        """Test that the boss always spawns a RapidFirePowerUp."""
        boss = Boss(x=0, y=0, health=1, game_state=game_state_with_ship)
        game_state_with_ship.enemies.append(boss)

        boss.take_damage() # Should destroy boss and spawn power-up

        assert len(game_state_with_ship.power_ups) == 1
        power_up = game_state_with_ship.power_ups[0]
        assert isinstance(power_up, RapidFirePowerUp)
        assert power_up.x == boss.x
        assert power_up.y == boss.y

    def test_power_up_movement_and_off_screen_removal(self, game_state_with_ship: GameState) -> None:
        """Test that power-ups move downwards and are removed when off-screen."""
        power_up = RapidFirePowerUp(x=0, y=0, game_state=game_state_with_ship)
        game_state_with_ship.power_ups.append(power_up)

        initial_y = power_up.y
        # Animate until it's removed off-screen
        while power_up in game_state_with_ship.power_ups:
            power_up.animate(TEST_DELTA_TIME)
        
        assert power_up.y > SHIP_POSITION_Y + 5 # Should have gone past off-screen y
        assert power_up not in game_state_with_ship.power_ups

    def test_power_up_collection_by_ship(self, game_state_with_ship: GameState) -> None:
        """Test that the ship collects a power-up on collision."""
        ship = game_state_with_ship.ship
        power_up = RapidFirePowerUp(x=ship.x, y=SHIP_POSITION_Y, game_state=game_state_with_ship)
        game_state_with_ship.power_ups.append(power_up)

        # Before animating ship, power-up should be in list
        assert power_up in game_state_with_ship.power_ups

        # Animate ship (which checks for collisions)
        ship.animate(TEST_DELTA_TIME)

        # Power-up should be collected and removed
        assert power_up not in game_state_with_ship.power_ups
        assert ship.is_rapid_fire_active == True
        assert ship.rapid_fire_duration_remaining == pytest.approx(RAPID_FIRE_DURATION)


    def test_rapid_fire_effect(self, game_state_with_ship: GameState) -> None:
        """Test that rapid fire enables continuous shooting and deactivates after duration."""
        ship = game_state_with_ship.ship
        ship.shoot_cooldown = SHIP_SHOOT_COOLDOWN # Set cooldown to ensure it can't shoot normally

        # Activate rapid fire
        ship.is_rapid_fire_active = True
        ship.rapid_fire_duration_remaining = RAPID_FIRE_DURATION

        # Should be able to shoot even with cooldown
        assert ship.can_shoot() == True

        # Animate until duration runs out
        remaining_duration = RAPID_FIRE_DURATION
        while remaining_duration > 0:
            ship.animate(TEST_DELTA_TIME)
            remaining_duration -= TEST_DELTA_TIME
        
        # Rapid fire should be deactivated
        assert ship.is_rapid_fire_active == False
        assert ship.rapid_fire_duration_remaining <= 0
        
        # Set cooldown to a positive value and check if can_shoot is False
        ship.shoot_cooldown = SHIP_SHOOT_COOLDOWN # Ensure cooldown is active
        assert ship.can_shoot() == False # Should now respect cooldown again