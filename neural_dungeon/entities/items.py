"""Item definitions — passive items, active items, weapon shop pool."""
from __future__ import annotations

import random
from neural_dungeon.config import (
    WEAPON_SCATTER_SHOT, WEAPON_PULSE_CANNON, WEAPON_RAPID_FIRE,
    WEAPON_PIERCING_RAY, WEAPON_HOMING_BURST, WEAPON_SNIPER,
    WEAPON_SHOTGUN_BLAST,
    WEAPON_COST, PASSIVE_COST, ACTIVE_COST,
)

PASSIVE_ITEMS = {
    "overclocked_core": {
        "name": "Overclocked Core",
        "desc": "+15% damage",
        "cost": PASSIVE_COST,
    },
    "heat_sink": {
        "name": "Heat Sink",
        "desc": "-20% fire rate CD",
        "cost": PASSIVE_COST,
    },
    "ram_upgrade": {
        "name": "RAM Upgrade",
        "desc": "+25 max HP",
        "cost": PASSIVE_COST,
    },
    "error_correction": {
        "name": "Error Correction",
        "desc": "Heal 5 on clear",
        "cost": PASSIVE_COST,
    },
    "batch_norm": {
        "name": "Batch Norm",
        "desc": "+15% move speed",
        "cost": PASSIVE_COST,
    },
    "kernel_expansion": {
        "name": "Kernel Expansion",
        "desc": "+25% bullet range",
        "cost": PASSIVE_COST,
    },
    "bias_shift": {
        "name": "Bias Shift",
        "desc": "-3 contact damage",
        "cost": PASSIVE_COST,
    },
    "gradient_boost": {
        "name": "Gradient Boost",
        "desc": "+25% dodge speed",
        "cost": PASSIVE_COST,
    },
    "dropout_layer": {
        "name": "Dropout Layer",
        "desc": "10% bullets miss",
        "cost": PASSIVE_COST,
    },
    "skip_connection": {
        "name": "Skip Connection",
        "desc": "+3 iframes on dodge",
        "cost": PASSIVE_COST,
    },
}

ACTIVE_ITEMS = {
    "memory_dump": {
        "name": "Memory Dump",
        "desc": "Clear enemy bullets",
        "cooldown": 120,
        "cost": ACTIVE_COST,
    },
    "fork_bomb": {
        "name": "Fork Bomb",
        "desc": "8 bullets outward",
        "cooldown": 150,
        "cost": ACTIVE_COST,
    },
    "firewall": {
        "name": "Firewall",
        "desc": "3s invulnerability",
        "cooldown": 240,
        "cost": ACTIVE_COST,
    },
    "heap_overflow": {
        "name": "Heap Overflow",
        "desc": "20 dmg all enemies",
        "cooldown": 180,
        "cost": ACTIVE_COST,
    },
    "stack_trace": {
        "name": "Stack Trace",
        "desc": "Teleport randomly",
        "cooldown": 90,
        "cost": ACTIVE_COST,
    },
    "debugger": {
        "name": "Debugger",
        "desc": "Freeze enemies 2s",
        "cooldown": 180,
        "cost": ACTIVE_COST,
    },
}

SHOP_WEAPONS = [
    WEAPON_SCATTER_SHOT, WEAPON_PULSE_CANNON, WEAPON_RAPID_FIRE,
    WEAPON_PIERCING_RAY, WEAPON_HOMING_BURST, WEAPON_SNIPER,
    WEAPON_SHOTGUN_BLAST,
]


def generate_shop_items(player_weapon, player_passives, player_active):
    """Generate up to 3 shop items: 1 weapon, 1 passive, 1 active."""
    items = []

    available_weapons = [w for w in SHOP_WEAPONS if w != player_weapon]
    if available_weapons:
        wkey = random.choice(available_weapons)
        from neural_dungeon.config import WEAPONS
        winfo = WEAPONS[wkey]
        items.append({
            "type": "weapon", "id": wkey,
            "name": winfo["name"],
            "desc": f"DMG:{winfo['damage']} SPD:{winfo['bullet_speed']}",
            "cost": WEAPON_COST,
        })

    available_passives = [k for k in PASSIVE_ITEMS if k not in player_passives]
    if available_passives:
        pkey = random.choice(available_passives)
        pinfo = PASSIVE_ITEMS[pkey]
        items.append({
            "type": "passive", "id": pkey,
            "name": pinfo["name"], "desc": pinfo["desc"],
            "cost": pinfo["cost"],
        })

    available_actives = [k for k in ACTIVE_ITEMS if k != player_active]
    if available_actives:
        akey = random.choice(available_actives)
        ainfo = ACTIVE_ITEMS[akey]
        items.append({
            "type": "active", "id": akey,
            "name": ainfo["name"], "desc": ainfo["desc"],
            "cost": ainfo["cost"],
        })

    return items


def roll_item_drop(room_type, player_weapon, player_passives, player_active):
    """Roll for item drop on room clear. Returns item dict or None."""
    if room_type == "combat":
        if random.random() > 0.20:
            return None
        available = [k for k in PASSIVE_ITEMS if k not in player_passives]
        if not available:
            return None
        key = random.choice(available)
        return {"type": "passive", "id": key,
                "name": PASSIVE_ITEMS[key]["name"]}

    elif room_type == "elite":
        if random.random() > 0.40:
            return None
        # Passives or actives only — weapons are shop-exclusive
        if random.random() < 0.6:
            available = [k for k in PASSIVE_ITEMS if k not in player_passives]
            if available:
                key = random.choice(available)
                return {"type": "passive", "id": key,
                        "name": PASSIVE_ITEMS[key]["name"]}
        available_a = [k for k in ACTIVE_ITEMS if k != player_active]
        if available_a:
            akey = random.choice(available_a)
            return {"type": "active", "id": akey,
                    "name": ACTIVE_ITEMS[akey]["name"]}
        return None

    elif room_type == "boss":
        # Boss guaranteed drop — weapons, passives, or actives
        roll = random.random()
        if roll < 0.35:
            available_w = [w for w in SHOP_WEAPONS if w != player_weapon]
            if available_w:
                wkey = random.choice(available_w)
                from neural_dungeon.config import WEAPONS
                return {"type": "weapon", "id": wkey,
                        "name": WEAPONS[wkey]["name"]}
        if roll < 0.65:
            available = [k for k in PASSIVE_ITEMS if k not in player_passives]
            if available:
                key = random.choice(available)
                return {"type": "passive", "id": key,
                        "name": PASSIVE_ITEMS[key]["name"]}
        available_a = [k for k in ACTIVE_ITEMS if k != player_active]
        if available_a:
            akey = random.choice(available_a)
            return {"type": "active", "id": akey,
                    "name": ACTIVE_ITEMS[akey]["name"]}
        return None

    return None
