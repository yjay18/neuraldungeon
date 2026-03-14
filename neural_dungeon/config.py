"""Constants, tuning parameters, and difficulty settings."""

# -- Display (pixels) --------------------------------------------------------
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 720
FPS = 60
GAME_TITLE = "NEURAL DUNGEON"

# Game area in logical units
ROOM_WIDTH = 60
ROOM_HEIGHT = 25
HUD_HEIGHT = 3

# Pixel scaling
CELL_W = SCREEN_WIDTH // (ROOM_WIDTH + 2)
CELL_H = (SCREEN_HEIGHT - 80) // (ROOM_HEIGHT + 2)

# Play area pixel bounds
PLAY_AREA_X = (SCREEN_WIDTH - CELL_W * (ROOM_WIDTH + 2)) // 2
PLAY_AREA_Y = 80
PLAY_AREA_W = CELL_W * (ROOM_WIDTH + 2)
PLAY_AREA_H = CELL_H * (ROOM_HEIGHT + 2)

# -- Timing -------------------------------------------------------------------
TICK_RATE = 30
TICK_DURATION = 1.0 / TICK_RATE
RENDER_RATE = 60
INPUT_POLL_TIMEOUT = 0.005

# -- Player -------------------------------------------------------------------
PLAYER_CHAR = "@"
PLAYER_MAX_HP = 100
PLAYER_SPEED = 0.4
PLAYER_HITBOX_RADIUS = 0.4
PLAYER_IFRAMES = 9
DODGE_SPEED = 1.2
DODGE_DURATION = 6
DODGE_COOLDOWN = 18
PLAYER_SHOOT_COOLDOWN = 4
PLAYER_BULLET_SPEED = 1.0
PLAYER_BULLET_DAMAGE = 8
PLAYER_BULLET_RANGE = 40

# -- Enemies ------------------------------------------------------------------
PERCEPTRON_HP = 25
PERCEPTRON_SPEED = 0.15
PERCEPTRON_SHOOT_COOLDOWN = 45
PERCEPTRON_BULLET_SPEED = 0.5
PERCEPTRON_BULLET_DAMAGE = 10
PERCEPTRON_CHAR = "▲"

TOKEN_HP = 8
TOKEN_SPEED = 0.25
TOKEN_DAMAGE = 20
TOKEN_CHAR = "■"

BIT_SHIFTER_HP = 30
BIT_SHIFTER_SPEED = 0.1
BIT_SHIFTER_TELEPORT_CD = 60
BIT_SHIFTER_SHOOT_COOLDOWN = 20
BIT_SHIFTER_BULLET_SPEED = 0.7
BIT_SHIFTER_BULLET_DAMAGE = 12
BIT_SHIFTER_CHAR = "⬡"

CONVOLVER_HP = 40
CONVOLVER_SPEED = 0.08
CONVOLVER_SHOOT_COOLDOWN = 90
CONVOLVER_BULLET_SPEED = 0.4
CONVOLVER_BULLET_DAMAGE = 8
CONVOLVER_CHAR = "▣"

DROPOUT_HP = 20
DROPOUT_SPEED = 0.2
DROPOUT_SHOOT_COOLDOWN = 50
DROPOUT_BULLET_SPEED = 0.55
DROPOUT_BULLET_DAMAGE = 10
DROPOUT_CHAR = "◇"
DROPOUT_INTANGIBLE_CHANCE = 0.3

POOLER_HP = 50
POOLER_SPEED = 0.12
POOLER_ABSORB_RANGE = 3.0
POOLER_DAMAGE = 15
POOLER_CHAR = "◉"

ATTENTION_HP = 35
ATTENTION_SPEED = 0.1
ATTENTION_SHOOT_COOLDOWN = 60
ATTENTION_BULLET_SPEED = 0.35
ATTENTION_BULLET_DAMAGE = 12
ATTENTION_TURN_RATE = 0.05
ATTENTION_CHAR = "◎"

GRADIENT_GHOST_HP = 30
GRADIENT_GHOST_SPEED = 0.18
GRADIENT_GHOST_TRAIL_CD = 10
GRADIENT_GHOST_TRAIL_DAMAGE = 5
GRADIENT_GHOST_CHAR = "∇"

MIMIC_HP = 35
MIMIC_RECORD_TICKS = 90
MIMIC_SHOOT_COOLDOWN = 40
MIMIC_BULLET_SPEED = 0.6
MIMIC_BULLET_DAMAGE = 10
MIMIC_CHAR = "◆"

RELU_HP = 45
RELU_SPEED_ACTIVE = 0.25
RELU_SPEED_DORMANT = 0.05
RELU_SHOOT_CD_ACTIVE = 30
RELU_SHOOT_CD_DORMANT = 90
RELU_BULLET_SPEED = 0.55
RELU_BULLET_DAMAGE = 12
RELU_ACTIVATION_THRESHOLD = 0.5
RELU_CHAR = "▷"

# -- Door interaction ---------------------------------------------------------
DOOR_GAME_X = ROOM_WIDTH // 2
DOOR_GAME_Y = 0
DOOR_INTERACT_RANGE = 3.0

# -- Boss defaults ------------------------------------------------------------
CLASSIFIER_HP = 300
AUTOENCODER_HP = 400
GAN_HP = 250
TRANSFORMER_HP = 500
LOSS_FUNCTION_HP = 600

BOSS_FLOORS = {
    1: "classifier",
    3: "autoencoder",
    5: "gan",
    7: "transformer",
    9: "loss_function",
}

# -- Projectiles --------------------------------------------------------------
BULLET_CHARS = {
    "player": "·",
    "enemy": "•",
    "beam": "─",
    "spread": "∘",
}

# -- Room Layout --------------------------------------------------------------
COVER_HP = 30
PIT_DAMAGE_PER_SECOND = 5
SLOW_MULTIPLIER = 0.5

# -- Evolution (per-floor AI progression) -------------------------------------
EVOLUTION_STAT_SCALE = [
    1.0, 1.0, 1.0, 1.05, 1.05,
    1.10, 1.10, 1.15, 1.20, 1.25,
]
EVOLUTION_LEAD_ACCURACY = [
    0.0, 0.0, 0.0, 0.3, 0.5,
    0.5, 0.55, 0.6, 0.65, 0.7,
]
EVOLUTION_SPACING_DIST = [
    0.0, 0.0, 0.0, 0.0, 0.0,
    3.0, 3.0, 3.5, 3.5, 4.0,
]

# -- Rooms & Floors -----------------------------------------------------------
ROOMS_PER_FLOOR = 5
TOTAL_FLOORS = 10
ENEMIES_PER_ROOM_BASE = 3
ENEMIES_PER_ROOM_SCALE = 1.5

# -- Room types ---------------------------------------------------------------
ROOM_TYPE_COMBAT = "combat"
ROOM_TYPE_ELITE = "elite"
ROOM_TYPE_DEAD = "dead"
ROOM_TYPE_SHOP = "shop"
ROOM_TYPE_WEIGHT = "weight"
ROOM_TYPE_CHECKPOINT = "checkpoint"
ROOM_TYPE_BOSS = "boss"
ROOM_TYPE_START = "start"

# -- Difficulty ---------------------------------------------------------------
DIFFICULTY_EASY = "easy"
DIFFICULTY_NORMAL = "normal"
DIFFICULTY_HARD = "hard"
DIFFICULTY_NIGHTMARE = "nightmare"

ADAPTIVE_LEARNING_RATES = {
    DIFFICULTY_EASY: 0.01,
    DIFFICULTY_NORMAL: 0.05,
    DIFFICULTY_HARD: 0.1,
    DIFFICULTY_NIGHTMARE: 0.2,
}

WEIGHT_CLAMP = (-2.0, 2.0)
ADAPTIVE_UPDATE_INTERVAL = 2

# -- Neural Network -----------------------------------------------------------
NETWORK_LAYERS = [
    (32, 48),
    (48, 64),
    (64, 48),
    (48, 32),
    (32, 16),
]

ACTIVATION_DEAD = 0.05
ACTIVATION_LOW = 0.3
ACTIVATION_HIGH = 0.7
ACTIVATION_MAX = 1.0

# -- Colors (name strings kept for entity compatibility) ----------------------
COLOR_PLAYER = "green"
COLOR_PLAYER_BULLET = "cyan"
COLOR_ENEMY_BULLET = "red"
COLOR_WALL = "white"
COLOR_FLOOR_BG = "on_black"
COLOR_HUD_TEXT = "white"
COLOR_HUD_HP = "green"
COLOR_HUD_HP_LOW = "red"
COLOR_HUD_HP_MID = "yellow"
COLOR_ENEMY_DEFAULT = "red"
COLOR_DOOR_LOCKED = "red"
COLOR_DOOR_OPEN = "green"
COLOR_DODGE_TRAIL = "bright_cyan"

ACTIVATION_COLORS = {
    "dead": "bright_black",
    "low": "cyan",
    "mid": "magenta",
    "high": "bright_magenta",
    "max": "bright_white",
}

# -- Weapons ------------------------------------------------------------------
WEAPON_GRADIENT_BEAM = "gradient_beam"
WEAPON_SCATTER_SHOT = "scatter_shot"
WEAPON_PULSE_CANNON = "pulse_cannon"
WEAPON_RAPID_FIRE = "rapid_fire"
WEAPON_PIERCING_RAY = "piercing_ray"
WEAPON_HOMING_BURST = "homing_burst"
WEAPON_SNIPER = "sniper"
WEAPON_SHOTGUN_BLAST = "shotgun_blast"

WEAPONS = {
    WEAPON_GRADIENT_BEAM: {
        "name": "Gradient Beam",
        "damage": 8,
        "fire_rate": 4,
        "bullet_speed": 1.0,
        "bullet_char": "·",
        "bullet_color": "cyan",
        "spread": 0.0,
        "projectiles": 1,
        "range": 40,
        "piercing": False,
        "homing": False,
        "turn_rate": 0.0,
    },
    WEAPON_SCATTER_SHOT: {
        "name": "Scatter Shot",
        "damage": 5,
        "fire_rate": 5,
        "bullet_speed": 0.9,
        "bullet_char": "∘",
        "bullet_color": "bright_yellow",
        "spread": 15.0,
        "projectiles": 3,
        "range": 35,
        "piercing": False,
        "homing": False,
        "turn_rate": 0.0,
    },
    WEAPON_PULSE_CANNON: {
        "name": "Pulse Cannon",
        "damage": 20,
        "fire_rate": 10,
        "bullet_speed": 0.7,
        "bullet_char": "●",
        "bullet_color": "bright_magenta",
        "spread": 0.0,
        "projectiles": 1,
        "range": 30,
        "piercing": False,
        "homing": False,
        "turn_rate": 0.0,
    },
    WEAPON_RAPID_FIRE: {
        "name": "Rapid Fire",
        "damage": 4,
        "fire_rate": 2,
        "bullet_speed": 1.2,
        "bullet_char": "·",
        "bullet_color": "bright_green",
        "spread": 0.0,
        "projectiles": 1,
        "range": 35,
        "piercing": False,
        "homing": False,
        "turn_rate": 0.0,
    },
    WEAPON_PIERCING_RAY: {
        "name": "Piercing Ray",
        "damage": 6,
        "fire_rate": 5,
        "bullet_speed": 1.0,
        "bullet_char": "─",
        "bullet_color": "bright_white",
        "spread": 0.0,
        "projectiles": 1,
        "range": 45,
        "piercing": True,
        "homing": False,
        "turn_rate": 0.0,
    },
    WEAPON_HOMING_BURST: {
        "name": "Homing Burst",
        "damage": 5,
        "fire_rate": 8,
        "bullet_speed": 0.5,
        "bullet_char": "◦",
        "bullet_color": "bright_cyan",
        "spread": 0.0,
        "projectiles": 1,
        "range": 50,
        "piercing": False,
        "homing": True,
        "turn_rate": 0.04,
    },
    WEAPON_SNIPER: {
        "name": "Sniper",
        "damage": 15,
        "fire_rate": 12,
        "bullet_speed": 1.5,
        "bullet_char": "—",
        "bullet_color": "white",
        "spread": 0.0,
        "projectiles": 1,
        "range": 60,
        "piercing": False,
        "homing": False,
        "turn_rate": 0.0,
    },
    WEAPON_SHOTGUN_BLAST: {
        "name": "Shotgun Blast",
        "damage": 4,
        "fire_rate": 7,
        "bullet_speed": 0.8,
        "bullet_char": "∘",
        "bullet_color": "bright_red",
        "spread": 30.0,
        "projectiles": 5,
        "range": 15,
        "piercing": False,
        "homing": False,
        "turn_rate": 0.0,
    },
}

# -- Item costs ---------------------------------------------------------------
WEAPON_COST = 50
PASSIVE_COST = 30
ACTIVE_COST = 40

# -- Data Fragments -----------------------------------------------------------
FRAGMENTS_PER_ENEMY = 5
FRAGMENTS_PER_ELITE = 15
FRAGMENTS_PER_BOSS = 50

# -- Directions ---------------------------------------------------------------
DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)
DIR_UP_LEFT = (-0.707, -0.707)
DIR_UP_RIGHT = (0.707, -0.707)
DIR_DOWN_LEFT = (-0.707, 0.707)
DIR_DOWN_RIGHT = (0.707, 0.707)
DIR_NONE = (0, 0)

# -- Game states --------------------------------------------------------------
STATE_TITLE = "title"
STATE_PLAYING = "playing"
STATE_MAP = "map"
STATE_PAUSED = "paused"
STATE_GAME_OVER = "game_over"
STATE_VICTORY = "victory"
STATE_ROOM_CLEAR = "room_clear"
STATE_FLOOR_TRANSITION = "floor_transition"

# -- Flashlight / Dark rooms --------------------------------------------------
DARK_ROOM_CHANCE = 35  # percent of combat/elite rooms that are dark
FLASHLIGHT_RANGE = 18.0  # game units
FLASHLIGHT_HALF_ANGLE_DEG = 30.0
ENEMY_FOV_RANGE = 15.0
ENEMY_FOV_HALF_ANGLE_DEG = 45.0
ENEMY_AWARE_DURATION = 90  # ticks (3 seconds at 30 TPS)
ENEMY_SENSE_RANGE = 4.0  # close range — can sense without line of sight
