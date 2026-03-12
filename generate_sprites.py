"""Generate 16x16 pixel art sprites for Neural Dungeon."""
from PIL import Image, ImageDraw

# Color palette — cyberpunk neon
C = {
    "black": (0, 0, 0, 0),         # transparent
    "dark": (15, 15, 25, 255),
    "green": (0, 200, 80, 255),
    "bright_green": (0, 255, 120, 255),
    "dark_green": (0, 100, 40, 255),
    "red": (200, 40, 40, 255),
    "bright_red": (255, 60, 60, 255),
    "dark_red": (120, 20, 20, 255),
    "cyan": (0, 200, 220, 255),
    "bright_cyan": (0, 255, 255, 255),
    "dark_cyan": (0, 100, 120, 255),
    "magenta": (200, 50, 200, 255),
    "bright_magenta": (255, 80, 255, 255),
    "dark_magenta": (100, 25, 100, 255),
    "yellow": (220, 200, 40, 255),
    "bright_yellow": (255, 255, 80, 255),
    "dark_yellow": (120, 100, 20, 255),
    "orange": (230, 130, 30, 255),
    "dark_orange": (140, 70, 15, 255),
    "blue": (50, 80, 220, 255),
    "bright_blue": (80, 120, 255, 255),
    "dark_blue": (25, 40, 120, 255),
    "white": (230, 230, 240, 255),
    "bright_white": (255, 255, 255, 255),
    "gray": (100, 100, 120, 255),
    "dark_gray": (50, 50, 65, 255),
    "purple": (140, 50, 200, 255),
    "dark_purple": (70, 25, 100, 255),
}

T = C["black"]  # transparent shorthand


def make(pixels, filename):
    """Create a 16x16 RGBA image from pixel data and save."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(pixels):
        for x, color in enumerate(row):
            if color != T:
                img.putpixel((x, y), color)
    img.save(f"assets/sprites/{filename}")
    print(f"  Created {filename}")


def make_32(pixels, filename):
    """Create a 32x32 RGBA image from pixel data and save."""
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    for y, row in enumerate(pixels):
        for x, color in enumerate(row):
            if color != T:
                img.putpixel((x, y), color)
    img.save(f"assets/sprites/{filename}")
    print(f"  Created {filename} (32x32)")


# ============================================================
# PLAYER — cyberpunk figure with visor
# ============================================================
def gen_player():
    g = C["green"]
    bg = C["bright_green"]
    dg = C["dark_green"]
    c = C["bright_cyan"]
    d = C["dark"]
    pixels = [
        [T,T,T,T,T,T, bg,bg,bg,bg, T,T,T,T,T,T],
        [T,T,T,T,T, bg,bg,bg,bg,bg,bg, T,T,T,T,T],
        [T,T,T,T, bg,bg,bg,bg,bg,bg,bg,bg, T,T,T,T],
        [T,T,T,T, bg,bg,bg,bg,bg,bg,bg,bg, T,T,T,T],
        [T,T,T,T, bg, c, c, c, c, c, c,bg, T,T,T,T],
        [T,T,T,T, bg, c,bg, c, c,bg, c,bg, T,T,T,T],
        [T,T,T,T, bg,bg,bg,bg,bg,bg,bg,bg, T,T,T,T],
        [T,T,T,T,T, bg,dg,dg,dg,dg,bg, T,T,T,T,T],
        [T,T,T,T,T,T, g, g, g, g, T,T,T,T,T,T],
        [T,T,T, g, g, g, g, g, g, g, g, g, g, T,T,T],
        [T,T, g, g, g, g, g, g, g, g, g, g, g, g, T,T],
        [T,T,bg, g, T, g, g, g, g, g, g, T, g,bg, T,T],
        [T,T, T, T, T, g, g, g, g, g, g, T, T, T, T,T],
        [T,T, T, T, T, g,dg,dg,dg,dg, g, T, T, T, T,T],
        [T,T, T, T, T, g, g, T, T, g, g, T, T, T, T,T],
        [T,T, T, T,dg,dg, T, T, T, T,dg,dg, T, T, T,T],
    ]
    make(pixels, "player.png")


# ============================================================
# PERCEPTRON — triangle with glowing eye
# ============================================================
def gen_perceptron():
    r = C["red"]
    br = C["bright_red"]
    dr = C["dark_red"]
    y = C["bright_yellow"]
    pixels = [
        [T,T,T,T,T,T,T, br,br, T,T,T,T,T,T,T],
        [T,T,T,T,T,T, br,br,br,br, T,T,T,T,T,T],
        [T,T,T,T,T,T, br, r, r,br, T,T,T,T,T,T],
        [T,T,T,T,T, br, r, r, r, r,br, T,T,T,T,T],
        [T,T,T,T,T, br, r, r, r, r,br, T,T,T,T,T],
        [T,T,T,T, br, r, r, y, y, r, r,br, T,T,T,T],
        [T,T,T,T, br, r, y,br,br, y, r,br, T,T,T,T],
        [T,T,T, br, r, r, r, y, y, r, r, r,br, T,T,T],
        [T,T,T, br, r, r, r, r, r, r, r, r,br, T,T,T],
        [T,T, br, r, r, r, r, r, r, r, r, r, r,br, T,T],
        [T,T, br, r, r, r, r, r, r, r, r, r, r,br, T,T],
        [T, br, r, r, r, r, r, r, r, r, r, r, r, r,br, T],
        [T, br, r, r, r, r, r, r, r, r, r, r, r, r,br, T],
        [br, r, r, r, r, r, r, r, r, r, r, r, r, r, r,br],
        [br,br,br,br,br,br,br,br,br,br,br,br,br,br,br,br],
        [T,dr,dr,dr,dr,dr,dr,dr,dr,dr,dr,dr,dr,dr,dr, T],
    ]
    make(pixels, "perceptron.png")


# ============================================================
# TOKEN — small aggressive square with teeth
# ============================================================
def gen_token():
    r = C["red"]
    br = C["bright_red"]
    w = C["white"]
    d = C["dark"]
    pixels = [
        [T,T,T,T,T,T,T,T,T,T,T,T,T,T,T,T],
        [T,T,T,T,T,T,T,T,T,T,T,T,T,T,T,T],
        [T,T,T, r, r, T, r, r, r, r, T, r, r, T,T,T],
        [T,T, r,br,br, r,br,br,br,br, r,br,br, r, T,T],
        [T,T, r,br,br,br,br,br,br,br,br,br,br, r, T,T],
        [T,T, r,br,br,br,br,br,br,br,br,br,br, r, T,T],
        [T,T, r,br, w, w,br,br,br, w, w,br,br, r, T,T],
        [T,T, r,br, w, d,br,br,br, w, d,br,br, r, T,T],
        [T,T, r,br,br,br,br,br,br,br,br,br,br, r, T,T],
        [T,T, r,br, w,br, w,br, w,br, w,br,br, r, T,T],
        [T,T, r,br,br, w,br, w,br, w,br,br,br, r, T,T],
        [T,T, r,br,br,br,br,br,br,br,br,br,br, r, T,T],
        [T,T, r, r,br,br,br,br,br,br,br,br, r, r, T,T],
        [T,T,T, r, r, r, r, r, r, r, r, r, r, T,T,T],
        [T,T,T,T,T,T,T,T,T,T,T,T,T,T,T,T],
        [T,T,T,T,T,T,T,T,T,T,T,T,T,T,T,T],
    ]
    make(pixels, "token.png")


# ============================================================
# BIT_SHIFTER — hexagonal shape, cyan, teleport vibe
# ============================================================
def gen_bit_shifter():
    c = C["cyan"]
    bc = C["bright_cyan"]
    dc = C["dark_cyan"]
    pixels = [
        [T,T,T,T,T, bc,bc,bc,bc,bc,bc, T,T,T,T,T],
        [T,T,T,T, bc, c, c, c, c, c, c,bc, T,T,T,T],
        [T,T,T, bc, c, c, c, c, c, c, c, c,bc, T,T,T],
        [T,T, bc, c, c,dc,dc, c, c,dc,dc, c, c,bc, T,T],
        [T, bc, c, c,dc,bc,dc, c, c,dc,bc,dc, c, c,bc, T],
        [T, bc, c, c,dc,dc,dc, c, c,dc,dc,dc, c, c,bc, T],
        [bc, c, c, c, c, c, c, c, c, c, c, c, c, c, c,bc],
        [bc, c, c, c, c, c,dc,dc,dc,dc, c, c, c, c, c,bc],
        [bc, c, c, c, c, c,dc,bc,bc,dc, c, c, c, c, c,bc],
        [bc, c, c, c, c, c,dc,dc,dc,dc, c, c, c, c, c,bc],
        [T, bc, c, c, c, c, c, c, c, c, c, c, c, c,bc, T],
        [T, bc, c, c, c, c, c, c, c, c, c, c, c, c,bc, T],
        [T,T, bc, c, c, c, c, c, c, c, c, c, c,bc, T,T],
        [T,T,T, bc, c, c, c, c, c, c, c, c,bc, T,T,T],
        [T,T,T,T, bc,dc,dc,dc,dc,dc,dc,bc, T,T,T,T],
        [T,T,T,T,T, bc,bc,bc,bc,bc,bc, T,T,T,T,T],
    ]
    make(pixels, "bit_shifter.png")


# ============================================================
# CONVOLVER — grid/kernel pattern, yellow
# ============================================================
def gen_convolver():
    y = C["yellow"]
    by = C["bright_yellow"]
    dy = C["dark_yellow"]
    d = C["dark"]
    pixels = [
        [T,T,T, by,by,by,by,by,by,by,by,by,by, T,T,T],
        [T,T, by, y, y, y, y, y, y, y, y, y, y,by, T,T],
        [T, by, y,dy,dy, y,dy,dy, y,dy,dy, y,dy, y,by, T],
        [by, y,dy, d, d,dy, d, d,dy, d, d,dy, d,dy, y,by],
        [by, y,dy, d,by,dy, d,by,dy, d,by,dy, d,dy, y,by],
        [by, y, y,dy,dy, y,dy,dy, y,dy,dy, y,dy, y, y,by],
        [by, y,dy, d, d,dy, d, d,dy, d, d,dy, d,dy, y,by],
        [by, y,dy, d,by,dy, d,by,dy, d,by,dy, d,dy, y,by],
        [by, y, y,dy,dy, y,dy,dy, y,dy,dy, y,dy, y, y,by],
        [by, y,dy, d, d,dy, d, d,dy, d, d,dy, d,dy, y,by],
        [by, y,dy, d,by,dy, d,by,dy, d,by,dy, d,dy, y,by],
        [by, y, y,dy,dy, y,dy,dy, y,dy,dy, y, y, y, y,by],
        [T, by, y,dy, y, y,dy, y, y,dy, y, y,dy, y,by, T],
        [T,T, by, y, y, y, y, y, y, y, y, y, y,by, T,T],
        [T,T,T, by,by,by,by,by,by,by,by,by,by, T,T,T],
        [T,T,T,T,T,T,T,T,T,T,T,T,T,T,T,T],
    ]
    make(pixels, "convolver.png")


# ============================================================
# DROPOUT — ghost-like, semi-transparent feel, magenta
# ============================================================
def gen_dropout():
    m = C["magenta"]
    bm = C["bright_magenta"]
    dm = C["dark_magenta"]
    w = C["white"]
    pixels = [
        [T,T,T,T,T, bm,bm,bm,bm,bm,bm, T,T,T,T,T],
        [T,T,T, bm,bm, m, m, m, m, m, m,bm,bm, T,T,T],
        [T,T, bm, m, m, m, m, m, m, m, m, m, m,bm, T,T],
        [T, bm, m, m, m, m, m, m, m, m, m, m, m, m,bm, T],
        [T, bm, m, m, w, w, m, m, m, w, w, m, m, m,bm, T],
        [bm, m, m, m, w,bm, m, m, m, w,bm, m, m, m, m,bm],
        [bm, m, m, m, m, m, m, m, m, m, m, m, m, m, m,bm],
        [bm, m, m, m, m, m,dm, m, m,dm, m, m, m, m, m,bm],
        [bm, m, m, m, m, m, m,dm,dm, m, m, m, m, m, m,bm],
        [bm, m, m, m, m, m, m, m, m, m, m, m, m, m, m,bm],
        [bm, m, m, m, m, m, m, m, m, m, m, m, m, m, m,bm],
        [T, bm, m, m, m, m, m, m, m, m, m, m, m, m,bm, T],
        [T, bm, m, m, T, m, m, m, m, m, m, T, m, m,bm, T],
        [T,T, bm, m, T, T, m, m, m, m, T, T, m,bm, T,T],
        [T,T, bm, T, T, T, bm, T, T,bm, T, T, T,bm, T,T],
        [T,T,T, T, T, T, T, T, T, T, T, T, T, T, T,T],
    ]
    make(pixels, "dropout.png")


# ============================================================
# POOLER — big circle with absorption ring, orange
# ============================================================
def gen_pooler():
    o = C["orange"]
    do = C["dark_orange"]
    br = C["bright_red"]
    d = C["dark"]
    pixels = [
        [T,T,T,T,T, do,do,do,do,do,do, T,T,T,T,T],
        [T,T,T, do,do, o, o, o, o, o, o,do,do, T,T,T],
        [T,T, do, o, o, o, o, o, o, o, o, o, o,do, T,T],
        [T, do, o, o, o,do,do,do,do,do,do, o, o, o,do, T],
        [T, do, o, o,do, d, d, d, d, d, d,do, o, o,do, T],
        [do, o, o,do, d, d, d, d, d, d, d, d,do, o, o,do],
        [do, o, o,do, d, d,br,br,br,br, d, d,do, o, o,do],
        [do, o, o,do, d,br,br, o, o,br,br, d,do, o, o,do],
        [do, o, o,do, d,br, o, o, o, o,br, d,do, o, o,do],
        [do, o, o,do, d,br,br, o, o,br,br, d,do, o, o,do],
        [do, o, o,do, d, d,br,br,br,br, d, d,do, o, o,do],
        [T, do, o, o,do, d, d, d, d, d, d,do, o, o,do, T],
        [T, do, o, o, o,do,do,do,do,do,do, o, o, o,do, T],
        [T,T, do, o, o, o, o, o, o, o, o, o, o,do, T,T],
        [T,T,T, do,do, o, o, o, o, o, o,do,do, T,T,T],
        [T,T,T,T,T, do,do,do,do,do,do, T,T,T,T,T],
    ]
    make(pixels, "pooler.png")


# ============================================================
# ATTENTION HEAD — bullseye/target, cyan
# ============================================================
def gen_attention():
    c = C["cyan"]
    bc = C["bright_cyan"]
    dc = C["dark_cyan"]
    w = C["bright_white"]
    pixels = [
        [T,T,T,T,T, dc,dc,dc,dc,dc,dc, T,T,T,T,T],
        [T,T,T, dc,dc, c, c, c, c, c, c,dc,dc, T,T,T],
        [T,T, dc, c, c, c, c, c, c, c, c, c, c,dc, T,T],
        [T, dc, c, c, c, c,dc,dc,dc,dc, c, c, c, c,dc, T],
        [T, dc, c, c,dc,dc, c, c, c, c,dc,dc, c, c,dc, T],
        [dc, c, c,dc, c, c, c, c, c, c, c, c,dc, c, c,dc],
        [dc, c, c,dc, c, c,bc,bc,bc,bc, c, c,dc, c, c,dc],
        [dc, c, c, c, c,bc,bc, w, w,bc,bc, c, c, c, c,dc],
        [dc, c, c, c, c,bc, w, w, w, w,bc, c, c, c, c,dc],
        [dc, c, c,dc, c, c,bc,bc,bc,bc, c, c,dc, c, c,dc],
        [dc, c, c,dc, c, c, c, c, c, c, c, c,dc, c, c,dc],
        [T, dc, c, c,dc,dc, c, c, c, c,dc,dc, c, c,dc, T],
        [T, dc, c, c, c, c,dc,dc,dc,dc, c, c, c, c,dc, T],
        [T,T, dc, c, c, c, c, c, c, c, c, c, c,dc, T,T],
        [T,T,T, dc,dc, c, c, c, c, c, c,dc,dc, T,T,T],
        [T,T,T,T,T, dc,dc,dc,dc,dc,dc, T,T,T,T,T],
    ]
    make(pixels, "attention_head.png")


# ============================================================
# GRADIENT GHOST — spooky nabla shape, green trails
# ============================================================
def gen_gradient_ghost():
    g = C["green"]
    bg = C["bright_green"]
    dg = C["dark_green"]
    w = C["white"]
    pixels = [
        [T,T,T,T,T,T,T, bg, bg, T,T,T,T,T,T,T],
        [T,T,T,T,T,T, bg, g, g,bg, T,T,T,T,T,T],
        [T,T,T,T,T, bg, g, g, g, g,bg, T,T,T,T,T],
        [T,T,T,T, bg, g, g, g, g, g, g,bg, T,T,T,T],
        [T,T,T, bg, g, w, w, g, g, w, w, g,bg, T,T,T],
        [T,T, bg, g, g, w,bg, g, g, w,bg, g, g,bg, T,T],
        [T,T, bg, g, g, g, g, g, g, g, g, g, g,bg, T,T],
        [T, bg, g, g, g, g,dg, g, g,dg, g, g, g, g,bg, T],
        [T, bg, g, g, g, g, g,dg,dg, g, g, g, g, g,bg, T],
        [bg, g, g, g, g, g, g, g, g, g, g, g, g, g, g,bg],
        [bg, g, g, g, g, g, g, g, g, g, g, g, g, g, g,bg],
        [bg, g, g, g, T, g, g, g, g, g, g, T, g, g, g,bg],
        [T, bg, g, T, T, T, g, g, g, g, T, T, T, g,bg, T],
        [T, T, T, T, T, T,bg, g, g,bg, T, T, T, T, T, T],
        [T, T, T, T, T, T, T,dg,dg, T, T, T, T, T, T, T],
        [T, T, T, T, T, T, T,dg,dg, T, T, T, T, T, T, T],
    ]
    make(pixels, "gradient_ghost.png")


# ============================================================
# MIMIC — diamond shape that mimics, blue
# ============================================================
def gen_mimic():
    b = C["blue"]
    bb = C["bright_blue"]
    db = C["dark_blue"]
    w = C["white"]
    r = C["bright_red"]
    pixels = [
        [T,T,T,T,T,T,T, bb,bb, T,T,T,T,T,T,T],
        [T,T,T,T,T,T, bb, b, b,bb, T,T,T,T,T,T],
        [T,T,T,T,T, bb, b, b, b, b,bb, T,T,T,T,T],
        [T,T,T,T, bb, b, b, b, b, b, b,bb, T,T,T,T],
        [T,T,T, bb, b, b, b, b, b, b, b, b,bb, T,T,T],
        [T,T, bb, b, b, r, r, b, b, r, r, b, b,bb, T,T],
        [T, bb, b, b, b, r, w, b, b, r, w, b, b, b,bb, T],
        [bb, b, b, b, b, b, b, b, b, b, b, b, b, b, b,bb],
        [bb, b, b, b, b, b, b,db,db, b, b, b, b, b, b,bb],
        [T, bb, b, b, b, b, b, b, b, b, b, b, b, b,bb, T],
        [T,T, bb, b, b, b, b, b, b, b, b, b, b,bb, T,T],
        [T,T,T, bb, b, b, b, b, b, b, b, b,bb, T,T,T],
        [T,T,T,T, bb, b, b, b, b, b, b,bb, T,T,T,T],
        [T,T,T,T,T, bb, b, b, b, b,bb, T,T,T,T,T],
        [T,T,T,T,T,T, bb,db,db,bb, T,T,T,T,T,T],
        [T,T,T,T,T,T,T, bb,bb, T,T,T,T,T,T,T],
    ]
    make(pixels, "mimic.png")


# ============================================================
# RELU GUARDIAN — arrow/chevron, yellow, active/dormant
# ============================================================
def gen_relu():
    y = C["yellow"]
    by = C["bright_yellow"]
    dy = C["dark_yellow"]
    w = C["white"]
    pixels = [
        [T,T,T,T,T,T, by,by,by,by, T,T,T,T,T,T],
        [T,T,T,T,T, by, y, y, y, y,by, T,T,T,T,T],
        [T,T,T,T, by, y, y, y, y, y, y,by, T,T,T,T],
        [T,T,T,T, by, y, y, y, y, y, y,by, T,T,T,T],
        [T,T,T, by, y, w, w, y, y, y, y, y,by, T,T,T],
        [T,T, by, y, w, w, y, y, y, y, y, y, y,by, T,T],
        [T, by, y, w, w, y, y, y, y, y, y, y, y, y,by, T],
        [by, y, w, w, y, y, y, y, y, y, y, y, y, y, y,by],
        [by, y, w, w, y, y, y, y, y, y, y, y, y, y, y,by],
        [T, by, y, w, w, y, y, y, y, y, y, y, y, y,by, T],
        [T,T, by, y, w, w, y, y, y, y, y, y, y,by, T,T],
        [T,T,T, by, y, w, w, y, y, y, y, y,by, T,T,T],
        [T,T,T,T, by, y, y, y, y, y, y,by, T,T,T,T],
        [T,T,T,T, by, y, y, y, y, y, y,by, T,T,T,T],
        [T,T,T,T,T, by,dy,dy,dy,dy,by, T,T,T,T,T],
        [T,T,T,T,T,T, by,by,by,by, T,T,T,T,T,T],
    ]
    make(pixels, "relu_guardian.png")


# ============================================================
# BOSSES — 32x32 sprites
# ============================================================

def gen_boss_classifier():
    """The Classifier — large red diamond with decision line."""
    r = C["red"]
    br = C["bright_red"]
    dr = C["dark_red"]
    w = C["white"]
    y = C["bright_yellow"]
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Diamond body
    diamond = [(16, 2), (30, 16), (16, 30), (2, 16)]
    draw.polygon(diamond, fill=r, outline=br)
    # Inner diamond
    inner = [(16, 6), (26, 16), (16, 26), (6, 16)]
    draw.polygon(inner, fill=dr, outline=r)
    # Decision boundary line
    draw.line([(4, 16), (28, 16)], fill=y, width=2)
    draw.line([(16, 4), (16, 28)], fill=y, width=2)
    # Eye
    draw.ellipse([(13, 13), (19, 19)], fill=w, outline=br)
    draw.ellipse([(14, 14), (18, 18)], fill=y)
    img.save("assets/sprites/boss_classifier.png")
    print("  Created boss_classifier.png (32x32)")


def gen_boss_autoencoder():
    """The Autoencoder — hourglass/compression shape."""
    m = C["magenta"]
    bm = C["bright_magenta"]
    dm = C["dark_magenta"]
    w = C["white"]
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Wide top
    draw.rectangle([(4, 3), (27, 8)], fill=m, outline=bm)
    # Narrow middle (compressed)
    draw.rectangle([(11, 9), (20, 14)], fill=dm, outline=m)
    draw.rectangle([(13, 13), (18, 18)], fill=bm, outline=w)
    # Narrow middle lower
    draw.rectangle([(11, 17), (20, 22)], fill=dm, outline=m)
    # Wide bottom
    draw.rectangle([(4, 23), (27, 28)], fill=m, outline=bm)
    # Connecting lines
    draw.line([(4, 8), (11, 13)], fill=bm, width=1)
    draw.line([(27, 8), (20, 13)], fill=bm, width=1)
    draw.line([(11, 18), (4, 23)], fill=bm, width=1)
    draw.line([(20, 18), (27, 23)], fill=bm, width=1)
    # Eye in center
    draw.ellipse([(14, 14), (18, 18)], fill=w)
    img.save("assets/sprites/boss_autoencoder.png")
    print("  Created boss_autoencoder.png (32x32)")


def gen_boss_gan_gen():
    """GAN Generator — G shape, green."""
    g = C["green"]
    bg = C["bright_green"]
    dg = C["dark_green"]
    w = C["white"]
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Circular body
    draw.ellipse([(3, 3), (28, 28)], fill=g, outline=bg)
    draw.ellipse([(7, 7), (24, 24)], fill=dg, outline=g)
    # G letter shape
    draw.arc([(10, 10), (22, 22)], 0, 360, fill=bg, width=2)
    draw.rectangle([(15, 14), (21, 17)], fill=bg)
    # Spawn indicators (small circles)
    for pos in [(6, 6), (25, 6), (6, 25), (25, 25)]:
        draw.ellipse([(pos[0]-2, pos[1]-2), (pos[0]+2, pos[1]+2)], fill=w)
    img.save("assets/sprites/boss_gan_gen.png")
    print("  Created boss_gan_gen.png (32x32)")


def gen_boss_gan_disc():
    """GAN Discriminator — D shape, red."""
    r = C["red"]
    br = C["bright_red"]
    dr = C["dark_red"]
    w = C["white"]
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Circular body
    draw.ellipse([(3, 3), (28, 28)], fill=r, outline=br)
    draw.ellipse([(7, 7), (24, 24)], fill=dr, outline=r)
    # D letter
    draw.rectangle([(11, 10), (14, 22)], fill=br)
    draw.arc([(12, 10), (22, 22)], -90, 90, fill=br, width=3)
    # Crosshair
    draw.line([(8, 16), (24, 16)], fill=w, width=1)
    draw.line([(16, 8), (16, 24)], fill=w, width=1)
    img.save("assets/sprites/boss_gan_disc.png")
    print("  Created boss_gan_disc.png (32x32)")


def gen_boss_transformer():
    """The Transformer — star with orbiting dots."""
    y = C["yellow"]
    by = C["bright_yellow"]
    dy = C["dark_yellow"]
    c = C["bright_cyan"]
    w = C["white"]
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Star body (overlapping diamonds)
    star1 = [(16, 4), (26, 16), (16, 28), (6, 16)]
    draw.polygon(star1, fill=y, outline=by)
    star2 = [(4, 10), (16, 6), (28, 10), (16, 26)]
    draw.polygon(star2, fill=dy, outline=y)
    # Inner core
    draw.ellipse([(11, 11), (21, 21)], fill=by, outline=w)
    draw.ellipse([(13, 13), (19, 19)], fill=w)
    # 4 orbiting heads (cyan dots)
    for pos in [(16, 2), (30, 16), (16, 30), (2, 16)]:
        draw.ellipse([(pos[0]-3, pos[1]-3), (pos[0]+3, pos[1]+3)], fill=c, outline=w)
    img.save("assets/sprites/boss_transformer.png")
    print("  Created boss_transformer.png (32x32)")


def gen_boss_loss_function():
    """The Loss Function — sigma symbol, white/menacing."""
    w = C["white"]
    bw = C["bright_white"]
    g = C["gray"]
    dg = C["dark_gray"]
    r = C["bright_red"]
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Outer ring
    draw.ellipse([(2, 2), (29, 29)], fill=dg, outline=w)
    draw.ellipse([(5, 5), (26, 26)], fill=(20, 20, 30, 255), outline=g)
    # Sigma shape (∑)
    sigma = [
        (10, 8), (22, 8), (22, 11), (14, 11),
        (16, 16), (14, 21), (22, 21), (22, 24),
        (10, 24), (14, 16),
    ]
    draw.polygon(sigma, fill=w, outline=bw)
    # Glowing eyes
    draw.ellipse([(9, 12), (13, 16)], fill=r)
    draw.ellipse([(19, 12), (23, 16)], fill=r)
    # Outer glow dots
    import math
    for i in range(8):
        angle = i * math.pi / 4
        x = 16 + int(14 * math.cos(angle))
        y = 16 + int(14 * math.sin(angle))
        draw.ellipse([(x-1, y-1), (x+1, y+1)], fill=r)
    img.save("assets/sprites/boss_loss_function.png")
    print("  Created boss_loss_function.png (32x32)")


# ============================================================
# PROJECTILE SPRITES — 8x8
# ============================================================
def gen_projectiles():
    """Generate small projectile sprites."""
    # Player bullet — cyan dot
    img = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([(1, 1), (6, 6)], fill=C["cyan"], outline=C["bright_cyan"])
    img.save("assets/sprites/bullet_player.png")

    # Enemy bullet — red dot
    img = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([(1, 1), (6, 6)], fill=C["red"], outline=C["bright_red"])
    img.save("assets/sprites/bullet_enemy.png")
    print("  Created bullet sprites (8x8)")


# ============================================================
if __name__ == "__main__":
    print("Generating Neural Dungeon sprites...")
    print("\n[Enemies]")
    gen_perceptron()
    gen_token()
    gen_bit_shifter()
    gen_convolver()
    gen_dropout()
    gen_pooler()
    gen_attention()
    gen_gradient_ghost()
    gen_mimic()
    gen_relu()

    print("\n[Player]")
    gen_player()

    print("\n[Bosses]")
    gen_boss_classifier()
    gen_boss_autoencoder()
    gen_boss_gan_gen()
    gen_boss_gan_disc()
    gen_boss_transformer()
    gen_boss_loss_function()

    print("\n[Projectiles]")
    gen_projectiles()

    print("\nDone! All sprites saved to assets/sprites/")
