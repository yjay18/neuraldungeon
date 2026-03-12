"""Damage calculation, collision detection."""
from neural_dungeon.entities.player import Player
from neural_dungeon.entities.enemies import Enemy
from neural_dungeon.entities.projectiles import Projectile, ProjectileManager
from neural_dungeon.utils import circles_collide, distance


def check_player_vs_enemy_bullets(
    player: Player,
    proj_mgr: ProjectileManager,
) -> int:
    """Returns total damage dealt to player this tick."""
    import random
    if player.invulnerable or not player.alive:
        return 0

    has_dropout = player.has_passive("dropout_layer")

    total_damage = 0
    for bullet in proj_mgr.get_enemy_bullets():
        if not bullet.alive:
            continue
        if circles_collide(
            player.x, player.y, player.hitbox_radius,
            bullet.x, bullet.y, bullet.hitbox_radius,
        ):
            # Dropout Layer: 10% chance enemy bullet misses
            if has_dropout and random.random() < 0.10:
                bullet.kill()
                continue
            dmg = player.take_damage(bullet.damage)
            total_damage += dmg
            bullet.kill()
    return total_damage


def check_player_bullets_vs_enemies(
    enemies: list[Enemy],
    proj_mgr: ProjectileManager,
) -> list[Enemy]:
    """Returns list of enemies killed this tick."""
    killed: list[Enemy] = []
    for bullet in proj_mgr.get_player_bullets():
        if not bullet.alive:
            continue
        for enemy in enemies:
            if not enemy.alive or enemy.intangible:
                continue
            if circles_collide(
                bullet.x, bullet.y, bullet.hitbox_radius,
                enemy.x, enemy.y, enemy.hitbox_radius,
            ):
                enemy.take_damage(bullet.damage)
                if not bullet.piercing:
                    bullet.kill()
                if not enemy.alive:
                    killed.append(enemy)
                break  # one hit per bullet per tick (unless piercing)
    return killed


def check_player_vs_enemy_contact(
    player: Player,
    enemies: list[Enemy],
) -> int:
    """Returns total contact damage dealt this tick."""
    if player.invulnerable or not player.alive:
        return 0

    total = 0
    for enemy in enemies:
        if not enemy.alive or enemy.contact_damage <= 0:
            continue
        if circles_collide(
            player.x, player.y, player.hitbox_radius,
            enemy.x, enemy.y, enemy.hitbox_radius,
        ):
            dmg = player.take_contact_damage(enemy.contact_damage)
            total += dmg
            if enemy.contact_damage > 0 and not enemy.is_boss:
                enemy.alive = False  # Token-type enemies die on contact
    return total
