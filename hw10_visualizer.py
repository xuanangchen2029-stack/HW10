"""
HW10 Visualizer — GRAVITY BALL
================================
The IMU ax/ay values become gravitational force on a bouncing ball.
Tilting the board rolls the ball; it bounces off walls with restitution.
Button triggers a neon explosion + colour cycle.

Protocol from Pico (unchanged):
    ax,ay,button\n        (CSV, ~33 Hz)

Usage:
    pip install pgzero pyserial
    Edit SERIAL_PORT below, then:
    python hw10_visualizer.py
"""

import math
import random
import pgzrun
import serial

# ── Window ───────────────────────────────────────────────────────────────────
WIDTH  = 900
HEIGHT = 700
TITLE  = "HW10 — GRAVITY BALL"

# ── Serial ────────────────────────────────────────────────────────────────────
SERIAL_PORT = "COM3"          # ← change to your Pico's port (e.g. /dev/ttyACM0)
BAUD        = 115200

# ── Physics constants ─────────────────────────────────────────────────────────
GRAVITY_SCALE = 600.0   # how strongly ax/ay accelerates the ball (px/s²/g)
RESTITUTION   = 0.72    # bounce energy kept (0=dead, 1=perfect elastic)
FRICTION      = 0.992   # per-frame velocity damping (air resistance)
BALL_RADIUS   = 22
DT            = 1 / 60  # physics timestep (seconds)

# ── Colour palettes ───────────────────────────────────────────────────────────
PALETTES = [
    {"ball": (0, 220, 255),   "glow": (0, 60, 120),   "trail": (0, 140, 200)},   # cyan
    {"ball": (255, 60, 120),  "glow": (110, 0, 55),   "trail": (200, 40, 100)},  # hot-pink
    {"ball": (80, 255, 140),  "glow": (0, 90, 40),    "trail": (50, 190, 100)},  # green
    {"ball": (255, 180, 0),   "glow": (110, 65, 0),   "trail": (210, 130, 0)},   # gold
    {"ball": (190, 90, 255),  "glow": (70, 0, 130),   "trail": (150, 70, 210)},  # violet
]
palette_idx = 0

# ── Ball state ────────────────────────────────────────────────────────────────
ball_x  = float(WIDTH  // 2)
ball_y  = float(HEIGHT // 2)
ball_vx = 0.0
ball_vy = 0.0

# ── Trail ─────────────────────────────────────────────────────────────────────
TRAIL_LEN = 30
trail = []   # list of (x, y) positions

# ── Particles ─────────────────────────────────────────────────────────────────
particles = []  # each: dict with x,y,vx,vy,life,maxlife,r,color

# ── Serial state ──────────────────────────────────────────────────────────────
ser          = None
_serial_buf  = ""
ax_val       = 0.0
ay_val       = 0.0
button_state = 0
prev_button  = 0
status_text  = "Waiting for Pico..."

# ── Background elements ───────────────────────────────────────────────────────
random.seed(42)
STARS = [
    (random.randint(0, WIDTH), random.randint(0, HEIGHT), random.random())
    for _ in range(180)
]
SCAN_LINES = list(range(0, HEIGHT, 8))

frame_count = 0


# ─────────────────────────────────────────────────────────────────────────────
# Serial
# ─────────────────────────────────────────────────────────────────────────────

def try_open_serial():
    global status_text, _serial_buf
    try:
        s = serial.Serial(SERIAL_PORT, BAUD, timeout=0)
        s.reset_input_buffer()
        _serial_buf = ""
        status_text = "Connected: " + SERIAL_PORT
        return s
    except Exception as e:
        status_text = "No serial: " + str(e)[:40]
        return None


ser = try_open_serial()


def read_serial():
    global ser, _serial_buf, status_text
    if ser is None:
        ser = try_open_serial()
        return None
    try:
        waiting = ser.in_waiting
        if waiting:
            _serial_buf += ser.read(waiting).decode("utf-8", errors="ignore")
        lines       = _serial_buf.split("\n")
        _serial_buf = lines[-1]
        complete    = [l.strip() for l in lines[:-1] if l.strip()]
        for line in reversed(complete):
            parts = line.split(",")
            if len(parts) == 3:
                try:
                    return float(parts[0]), float(parts[1]), int(parts[2])
                except ValueError:
                    continue
        return None
    except Exception as e:
        status_text = "Serial error: " + str(e)[:40]
        try:
            ser.close()
        except Exception:
            pass
        ser         = None
        _serial_buf = ""
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Particles
# ─────────────────────────────────────────────────────────────────────────────

def spawn_explosion(x, y, color):
    for _ in range(60):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(80, 440)
        life  = random.uniform(0.4, 1.2)
        particles.append({
            "x": x, "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": life, "maxlife": life,
            "r": random.randint(3, 9),
            "color": color,
        })


def update_particles(dt):
    dead = []
    for p in particles:
        p["x"]    += p["vx"] * dt
        p["y"]    += p["vy"] * dt
        p["vy"]   += 220 * dt   # gravity on sparks
        p["vx"]   *= 0.97
        p["life"] -= dt
        if p["life"] <= 0:
            dead.append(p)
    for p in dead:
        particles.remove(p)


# ─────────────────────────────────────────────────────────────────────────────
# Colour helpers
# ─────────────────────────────────────────────────────────────────────────────

def dim(color, factor):
    return tuple(max(0, min(255, int(c * factor))) for c in color)


def blend(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


# ─────────────────────────────────────────────────────────────────────────────
# Draw
# ─────────────────────────────────────────────────────────────────────────────

def draw_glow_ball(cx, cy, radius, color, glow_color):
    # outer glow rings
    for i in range(6, 0, -1):
        r_off = i * 6
        factor = 0.12 * (7 - i) / 6
        g = dim(glow_color, factor * 3)
        screen.draw.filled_circle((int(cx), int(cy)), radius + r_off, g)
    # main body
    screen.draw.filled_circle((int(cx), int(cy)), radius, color)
    # bright specular core
    screen.draw.filled_circle((int(cx), int(cy)), max(4, radius // 3),
                               blend(color, (255, 255, 255), 0.75))


def draw_trail_segments():
    pal = PALETTES[palette_idx]
    n = len(trail)
    for i, (tx, ty) in enumerate(trail):
        frac = (i + 1) / max(n, 1)
        r    = max(2, int(BALL_RADIUS * 0.55 * frac))
        col  = dim(pal["trail"], frac * 0.75)
        screen.draw.filled_circle((int(tx), int(ty)), r, col)


def draw_particles_all():
    for p in particles:
        frac = max(0.0, p["life"] / p["maxlife"])
        col  = dim(p["color"], frac)
        if col[0] > 5 or col[1] > 5 or col[2] > 5:
            screen.draw.filled_circle((int(p["x"]), int(p["y"])), p["r"], col)


def draw_hud():
    pal = PALETTES[palette_idx]
    bc  = pal["ball"]
    gc  = pal["glow"]

    # ── outer border frame ──
    screen.draw.rect(Rect(3, 3, WIDTH - 6, HEIGHT - 6), bc)
    screen.draw.rect(Rect(7, 7, WIDTH - 14, HEIGHT - 14), gc)

    # ── mini tilt indicator (top-right) ──
    hx, hy, hr = WIDTH - 82, 82, 58
    screen.draw.circle((hx, hy), hr, (40, 40, 65))
    screen.draw.circle((hx, hy), hr - 1, (20, 20, 40))
    # crosshair inside indicator
    screen.draw.line((hx - hr + 6, hy), (hx + hr - 6, hy), (50, 50, 75))
    screen.draw.line((hx, hy - hr + 6), (hx, hy + hr - 6), (50, 50, 75))
    # dot position (clamped to circle)
    raw_dx = ax_val * (hr - 10)
    raw_dy = -ay_val * (hr - 10)
    dist   = math.sqrt(raw_dx ** 2 + raw_dy ** 2)
    max_d  = hr - 10
    if dist > max_d:
        scale = max_d / dist
        raw_dx *= scale
        raw_dy *= scale
    dot_x = int(hx + raw_dx)
    dot_y = int(hy + raw_dy)
    screen.draw.filled_circle((dot_x, dot_y), 8, bc)
    screen.draw.circle((dot_x, dot_y), 10, dim(bc, 0.4))

    screen.draw.text("TILT", (hx - 16, hy + hr + 5), color=(80, 80, 110), fontsize=17)

    # ── readout text ──
    screen.draw.text(f"ax  {ax_val:+.3f} g", (18, 18),  color=bc, fontsize=22)
    screen.draw.text(f"ay  {ay_val:+.3f} g", (18, 44),  color=bc, fontsize=22)
    btn_label = "BTN [PRESSED]" if button_state else "BTN [       ]"
    btn_color = (255, 80, 80) if button_state else (60, 60, 90)
    screen.draw.text(btn_label, (18, 70), color=btn_color, fontsize=22)

    vspeed = math.sqrt(ball_vx ** 2 + ball_vy ** 2)
    screen.draw.text(f"speed {vspeed:.0f} px/s", (18, 96), color=(80, 100, 130), fontsize=20)

    screen.draw.text("GRAVITY BALL", (WIDTH // 2 - 95, 14), color=bc, fontsize=28)
    screen.draw.text("tilt to roll  |  button = color", (WIDTH // 2 - 135, 46),
                     color=dim(bc, 0.5), fontsize=18)

    screen.draw.text(status_text, (18, HEIGHT - 32), color=(80, 80, 120), fontsize=18)
    # palette swatch dots
    for i, p in enumerate(PALETTES):
        cx = WIDTH - 18 - (len(PALETTES) - 1 - i) * 22
        cy = HEIGHT - 18
        screen.draw.filled_circle((cx, cy), 7, p["ball"])
        if i == palette_idx:
            screen.draw.circle((cx, cy), 10, p["ball"])


def draw():
    # background
    screen.fill((5, 5, 16))

    # stars
    for sx, sy, br in STARS:
        twinkle = int(br * (150 + 50 * math.sin(frame_count * 0.035 + sx * 0.1)))
        c = (twinkle, twinkle, int(twinkle * 1.1))
        screen.draw.filled_circle((sx, sy), 1, c)

    # scanlines
    for y in SCAN_LINES:
        screen.draw.line((0, y), (WIDTH, y), (0, 0, 0))

    draw_trail_segments()
    draw_particles_all()

    pal = PALETTES[palette_idx]
    draw_glow_ball(ball_x, ball_y, BALL_RADIUS, pal["ball"], pal["glow"])

    draw_hud()


# ─────────────────────────────────────────────────────────────────────────────
# Update
# ─────────────────────────────────────────────────────────────────────────────

def update():
    global ball_x, ball_y, ball_vx, ball_vy
    global ax_val, ay_val, button_state, prev_button
    global palette_idx, frame_count

    frame_count += 1

    # serial
    result = read_serial()
    if result is not None:
        ax_val, ay_val, button_state = result

    # button edge: explosion + next palette
    if button_state == 1 and prev_button == 0:
        palette_idx = (palette_idx + 1) % len(PALETTES)
        spawn_explosion(ball_x, ball_y, PALETTES[palette_idx]["ball"])
    prev_button = button_state

    # ── wall boundaries ──
    lw = BALL_RADIUS + 12
    rw = WIDTH  - BALL_RADIUS - 12
    tw = BALL_RADIUS + 12
    bw = HEIGHT - BALL_RADIUS - 12

    # ── physics ──
    # ax > 0  → board right  → ball right (+x)
    # ay > 0  → board nose-down → ball up (-y in screen coords)
    accel_x =  ax_val * GRAVITY_SCALE
    accel_y = -ay_val * GRAVITY_SCALE

    # KEY FIX: if the ball is pressed against a wall and the IMU is still
    # pushing it into that wall, suppress the wall-ward acceleration component.
    # This prevents the "pinned forever" situation where IMU force exactly
    # cancels or overwhelms any bounce velocity every frame.
    if ball_x <= lw and accel_x < 0:
        accel_x = 0.0
    if ball_x >= rw and accel_x > 0:
        accel_x = 0.0
    if ball_y <= tw and accel_y < 0:
        accel_y = 0.0
    if ball_y >= bw and accel_y > 0:
        accel_y = 0.0

    ball_vx += accel_x * DT
    ball_vy += accel_y * DT

    ball_vx *= FRICTION
    ball_vy *= FRICTION

    ball_x += ball_vx * DT
    ball_y += ball_vy * DT

    # ── wall bounce ──
    if ball_x < lw:
        ball_x  = lw
        ball_vx = abs(ball_vx) * RESTITUTION
    elif ball_x > rw:
        ball_x  = rw
        ball_vx = -abs(ball_vx) * RESTITUTION

    if ball_y < tw:
        ball_y  = tw
        ball_vy = abs(ball_vy) * RESTITUTION
    elif ball_y > bw:
        ball_y  = bw
        ball_vy = -abs(ball_vy) * RESTITUTION

    # trail
    trail.append((ball_x, ball_y))
    if len(trail) > TRAIL_LEN:
        trail.pop(0)

    update_particles(DT)


pgzrun.go()