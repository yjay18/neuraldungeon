"""Lightweight particle system for visual effects."""
import math
import random
import pygame


class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'color', 'life', 'max_life', 'size', 'glow')

    def __init__(self, x, y, vx, vy, color, life, size=2, glow=False):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size
        self.glow = glow


class ParticleSystem:
    MAX_PARTICLES = 600

    def __init__(self):
        self.particles: list[Particle] = []

    def emit_explosion(self, gx, gy, color, count=14):
        """Burst of particles on enemy death."""
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(0.5, 2.5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.randint(15, 35)
            size = random.randint(1, 3)
            # Vary the color slightly
            c = (
                min(255, max(0, color[0] + random.randint(-30, 30))),
                min(255, max(0, color[1] + random.randint(-30, 30))),
                min(255, max(0, color[2] + random.randint(-30, 30))),
            )
            self.particles.append(Particle(gx, gy, vx, vy, c, life, size, glow=True))

    def emit_hit(self, gx, gy, color, count=6):
        """Small spark on bullet hit."""
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(0.3, 1.5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.randint(6, 14)
            self.particles.append(Particle(gx, gy, vx, vy, color, life, 1))

    def emit_trail(self, gx, gy, color):
        """Single trail particle behind a bullet."""
        vx = random.uniform(-0.15, 0.15)
        vy = random.uniform(-0.15, 0.15)
        life = random.randint(4, 9)
        c = (color[0] // 2, color[1] // 2, color[2] // 2)
        self.particles.append(Particle(gx, gy, vx, vy, c, life, 1))

    def emit_dodge_trail(self, gx, gy):
        """Afterimage particles during dodge roll."""
        for _ in range(3):
            vx = random.uniform(-0.3, 0.3)
            vy = random.uniform(-0.3, 0.3)
            life = random.randint(8, 16)
            c = (0, random.randint(180, 255), random.randint(200, 255))
            self.particles.append(Particle(gx, gy, vx, vy, c, life, 2))

    def emit_ambient(self, room_w, room_h):
        """Spawn a floating data-bit particle in the room."""
        gx = random.uniform(1, room_w - 1)
        gy = random.uniform(1, room_h - 1)
        vx = random.uniform(-0.03, 0.03)
        vy = random.uniform(-0.08, -0.01)
        color = random.choice([
            (0, 80, 100), (0, 60, 80), (30, 0, 60),
            (0, 50, 50), (20, 20, 50),
        ])
        life = random.randint(80, 160)
        self.particles.append(Particle(gx, gy, vx, vy, color, life, 1))

    def emit_player_damage(self, gx, gy, count=10):
        """Red sparks when player takes damage."""
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(0.5, 2.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.randint(10, 20)
            c = (255, random.randint(30, 80), random.randint(20, 50))
            self.particles.append(Particle(gx, gy, vx, vy, c, life, 2))

    def emit_room_clear(self, room_w, room_h, count=40):
        """Celebration burst when room is cleared."""
        cx, cy = room_w / 2, room_h / 2
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(1.0, 4.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.randint(20, 50)
            c = random.choice([
                (0, 255, 120), (0, 255, 255), (100, 255, 255),
                (255, 255, 100), (0, 200, 100),
            ])
            self.particles.append(Particle(cx, cy, vx, vy, c, life, 2))

    def update(self):
        alive = []
        for p in self.particles:
            p.x += p.vx * 0.12
            p.y += p.vy * 0.12
            p.vx *= 0.96  # friction
            p.vy *= 0.96
            p.life -= 1
            if p.life > 0:
                alive.append(p)
        # Cap particle count
        if len(alive) > self.MAX_PARTICLES:
            alive = alive[-self.MAX_PARTICLES:]
        self.particles = alive

    def draw(self, screen, game_to_screen_fn):
        for p in self.particles:
            px, py = game_to_screen_fn(p.x, p.y)
            ratio = p.life / p.max_life
            color = (
                int(p.color[0] * ratio),
                int(p.color[1] * ratio),
                int(p.color[2] * ratio),
            )
            if p.glow and p.size > 1:
                # Outer glow halo for explosion particles
                glow_r = p.size + 3
                glow_c = (
                    max(0, color[0] // 3),
                    max(0, color[1] // 3),
                    max(0, color[2] // 3),
                )
                pygame.draw.circle(screen, glow_c, (px, py), glow_r)
                # Bright core
                pygame.draw.circle(screen, color, (px, py), p.size)
                bright = (
                    min(255, color[0] + 80),
                    min(255, color[1] + 80),
                    min(255, color[2] + 80),
                )
                pygame.draw.circle(screen, bright, (px, py), max(1, p.size // 2))
            elif p.size <= 1:
                if 0 <= px < screen.get_width() and 0 <= py < screen.get_height():
                    screen.set_at((px, py), color)
            else:
                pygame.draw.circle(screen, color, (px, py), p.size)
