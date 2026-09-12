#!/usr/bin/env python3
"""Nova Flip — original ElbowOS neon pinball arcade (Python 3 + pygame)."""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys
from pathlib import Path

W, H = 1080, 1920
FPS = 30
SECONDS = 15
FRAMES = FPS * SECONDS
TITLE = "NOVA FLIP"
OUT = Path("/home/workdir/artifacts/NOVA_FLIP_ElbowOS.mp4")

if "--play" not in sys.argv:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

TABLE_L, TABLE_R = 70, W - 70
TABLE_T, TABLE_B = 210, H - 160
GRAV = 0.55
FRIC = 0.994
BALL_R = 22
FLIP_LEN, FLIP_W = 168, 22


def lerp(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


class Bumper:
    def __init__(self, x, y, r, color, pts):
        self.x, self.y, self.r = x, y, r
        self.color, self.pts, self.flash = color, pts, 0


class Game:
    def __init__(self, seed=11):
        self.rng = random.Random(seed)
        self.score = 0
        self.balls = 3
        self.t = 0
        self.flash = 0
        self.sparks = []
        self.bumpers = [
            Bumper(320, 520, 58, (255, 80, 160), 80),
            Bumper(760, 520, 58, (80, 220, 255), 80),
            Bumper(540, 740, 72, (255, 210, 50), 140),
            Bumper(250, 980, 48, (180, 90, 255), 50),
            Bumper(830, 980, 48, (80, 255, 170), 50),
            Bumper(540, 1160, 42, (255, 120, 70), 60),
        ]
        self.la, self.ra = -0.55, math.pi + 0.55
        self.lt, self.rt = self.la, self.ra
        self.lp, self.rp = False, False
        self.spawn()

    def spawn(self):
        self.bx = TABLE_R - 90
        self.by = TABLE_B - 280
        self.vx = self.rng.uniform(-3.5, -1.2)
        self.vy = self.rng.uniform(-22.0, -16.5)
        self.alive = True

    def flip_base(self, side):
        if side == "L":
            return (TABLE_L + 210, TABLE_B - 36)
        return (TABLE_R - 210, TABLE_B - 36)

    def flip_tip(self, side, ang):
        x, y = self.flip_base(side)
        return (x + math.cos(ang) * FLIP_LEN, y + math.sin(ang) * FLIP_LEN)

    def set_flippers(self, left, right):
        self.lp, self.rp = left, right
        tgt_l = -1.15 if left else -0.55
        tgt_r = math.pi + 1.15 if right else math.pi + 0.55
        self.lt += (tgt_l - self.lt) * 0.45
        self.rt += (tgt_r - self.rt) * 0.45

    def autoplay(self):
        left = right = False
        if self.by > TABLE_B - 420 and self.vy > 0:
            if self.bx < W * 0.52:
                left = True
            if self.bx > W * 0.48:
                right = True
        elif self.by > TABLE_B - 620 and abs(self.vx) > 6:
            left = self.bx < 540
            right = self.bx >= 540
        elif self.t % 37 == 0:
            left = self.rng.random() < 0.35
            right = self.rng.random() < 0.35
        self.set_flippers(left, right)

    def bounce_circle(self, cx, cy, r, kick=0.0):
        dx, dy = self.bx - cx, self.by - cy
        dist = math.hypot(dx, dy) or 0.001
        if dist >= r + BALL_R:
            return False
        nx, ny = dx / dist, dy / dist
        overlap = r + BALL_R - dist
        self.bx += nx * overlap
        self.by += ny * overlap
        vn = self.vx * nx + self.vy * ny
        if vn < 0:
            self.vx -= 1.82 * vn * nx
            self.vy -= 1.82 * vn * ny
            self.vx += nx * kick
            self.vy += ny * kick
        return True

    def bounce_seg(self, ax, ay, bx, by, kick=0.0):
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1.0
        ux, uy = dx / L, dy / L
        t = max(0.0, min(1.0, ((self.bx - ax) * ux + (self.by - ay) * uy)))
        px, py = ax + ux * t, ay + uy * t
        return self.bounce_circle(px, py, FLIP_W * 0.55, kick)

    def drain(self):
        self.flash = 10
        self.balls = max(0, self.balls - 1)
        for _ in range(16):
            a = self.rng.random() * 6.28
            s = self.rng.uniform(2, 8)
            self.sparks.append([self.bx, self.by, math.cos(a) * s, math.sin(a) * s, 14, (255, 90, 140)])
        self.spawn()

    def tick(self, human=None):
        self.t += 1
        if self.flash:
            self.flash -= 1
        if human == "L":
            self.set_flippers(True, False)
        elif human == "R":
            self.set_flippers(False, True)
        elif human == "BOTH":
            self.set_flippers(True, True)
        else:
            self.autoplay()

        self.vy += GRAV
        self.vx *= FRIC
        self.vy *= FRIC
        self.bx += self.vx
        self.by += self.vy

        if self.bx < TABLE_L + BALL_R:
            self.bx = TABLE_L + BALL_R
            self.vx = abs(self.vx) * 0.88
        if self.bx > TABLE_R - BALL_R:
            self.bx = TABLE_R - BALL_R
            self.vx = -abs(self.vx) * 0.88
        if self.by < TABLE_T + BALL_R:
            self.by = TABLE_T + BALL_R
            self.vy = abs(self.vy) * 0.82

        if self.by < TABLE_T + 180:
            if self.bx < TABLE_L + 160:
                self.bounce_circle(TABLE_L + 40, TABLE_T + 40, 90, 1.2)
            if self.bx > TABLE_R - 160:
                self.bounce_circle(TABLE_R - 40, TABLE_T + 40, 90, 1.2)

        for b in self.bumpers:
            if b.flash:
                b.flash -= 1
            if self.bounce_circle(b.x, b.y, b.r, 7.5):
                b.flash = 8
                self.score += b.pts
                self.flash = 4
                for _ in range(8):
                    a = self.rng.random() * 6.28
                    s = self.rng.uniform(1.5, 6)
                    self.sparks.append([b.x, b.y, math.cos(a) * s, math.sin(a) * s, 12, b.color])

        kick_l = 11.0 if self.lp else 1.4
        kick_r = 11.0 if self.rp else 1.4
        lx, ly = self.flip_base("L")
        ltx, lty = self.flip_tip("L", self.lt)
        rx, ry = self.flip_base("R")
        rtx, rty = self.flip_tip("R", self.rt)
        self.bounce_seg(lx, ly, ltx, lty, kick_l)
        self.bounce_seg(rx, ry, rtx, rty, kick_r)

        if self.by > TABLE_B + 20:
            self.drain()

        spd = math.hypot(self.vx, self.vy)
        if spd > 28:
            self.vx *= 28 / spd
            self.vy *= 28 / spd

        keep = []
        for s in self.sparks:
            s[0] += s[2]
            s[1] += s[3]
            s[4] -= 1
            if s[4] > 0:
                keep.append(s)
        self.sparks = keep
        if self.t % 18 == 0:
            self.score += 1


def draw(surf, g, fonts):
    font_lg, font_md, font_sm = fonts
    t = g.t
    for y in range(0, H, 8):
        pygame.draw.rect(surf, lerp((18, 4, 28), (8, 6, 42), y / H), (0, y, W, 8))
    for i in range(12):
        yy = int((t * 5 + i * 170) % H)
        pygame.draw.line(surf, (48, 12, 70), (0, yy), (W, yy), 2)

    pygame.draw.rect(surf, (12, 8, 28), (TABLE_L, TABLE_T, TABLE_R - TABLE_L, TABLE_B - TABLE_T), border_radius=36)
    pygame.draw.rect(surf, (255, 70, 180), (TABLE_L, TABLE_T, TABLE_R - TABLE_L, TABLE_B - TABLE_T), 5, border_radius=36)
    pygame.draw.circle(surf, (40, 16, 60), (TABLE_L + 40, TABLE_T + 40), 92)
    pygame.draw.circle(surf, (40, 16, 60), (TABLE_R - 40, TABLE_T + 40), 92)

    for b in g.bumpers:
        glow = pygame.Surface((b.r * 4, b.r * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*b.color, 55 if not b.flash else 140), (b.r * 2, b.r * 2), b.r * 2)
        surf.blit(glow, (int(b.x - b.r * 2), int(b.y - b.r * 2)))
        pygame.draw.circle(surf, b.color, (int(b.x), int(b.y)), b.r)
        pygame.draw.circle(surf, (255, 255, 240), (int(b.x), int(b.y)), b.r, 3)
        pygame.draw.circle(surf, (20, 10, 30), (int(b.x), int(b.y)), max(10, b.r // 3))

    for side, ang, col in (("L", g.lt, (255, 90, 200)), ("R", g.rt, (80, 240, 255))):
        x, y = g.flip_base(side)
        tx, ty = g.flip_tip(side, ang)
        pygame.draw.line(surf, col, (x, y), (tx, ty), FLIP_W)
        pygame.draw.circle(surf, (255, 255, 230), (int(x), int(y)), 16)
        pygame.draw.circle(surf, col, (int(tx), int(ty)), 12)

    pygame.draw.circle(surf, (255, 240, 180), (int(g.bx), int(g.by)), BALL_R + 6)
    pygame.draw.circle(surf, (255, 255, 255), (int(g.bx), int(g.by)), BALL_R)
    pygame.draw.circle(surf, (255, 80, 160), (int(g.bx - 6), int(g.by - 7)), 6)

    for s in g.sparks:
        pygame.draw.circle(surf, s[5], (int(s[0]), int(s[1])), max(2, s[4] // 3))
    if g.flash:
        veil = pygame.Surface((W, H), pygame.SRCALPHA)
        veil.fill((255, 80, 180, 28))
        surf.blit(veil, (0, 0))

    bar = pygame.Surface((W, 160), pygame.SRCALPHA)
    bar.fill((10, 4, 22, 230))
    surf.blit(bar, (0, 0))
    surf.blit(font_lg.render(TITLE, True, (255, 90, 200)), (36, 16))
    surf.blit(font_sm.render("ElbowOS  ·  Python 3 neon pinball  ·  autoplay reel", True, (210, 180, 230)), (40, 100))
    sc = font_md.render(f"NOVA  {g.score:05d}", True, (255, 210, 70))
    surf.blit(sc, (W - sc.get_width() - 36, 26))
    lv = font_sm.render("\u25cf " * max(1, g.balls), True, (80, 240, 255))
    surf.blit(lv, (W - lv.get_width() - 36, 88))

    foot = pygame.Surface((W, 110), pygame.SRCALPHA)
    foot.fill((10, 4, 22, 230))
    surf.blit(foot, (0, H - 110))
    tag = font_sm.render("x.com/ElbowOS", True, (255, 90, 200))
    surf.blit(tag, (W - tag.get_width() - 36, H - 68))
    hint = font_sm.render("Z / LEFT  ·  /  X / RIGHT flip", True, (190, 160, 210))
    surf.blit(hint, (36, H - 68))


def fonts():
    try:
        return (
            pygame.font.SysFont("dejavusans", 68, bold=True),
            pygame.font.SysFont("dejavusans", 40, bold=True),
            pygame.font.SysFont("dejavusans", 28),
        )
    except Exception:
        return pygame.font.Font(None, 76), pygame.font.Font(None, 46), pygame.font.Font(None, 32)


def record(out: Path = OUT) -> Path:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.font.init()
    surf = pygame.Surface((W, H))
    g = Game()
    fnt = fonts()
    tmp = out.with_suffix(".tmp.mp4")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "20", "-preset", "veryfast", "-movflags", "+faststart", str(tmp),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    for _ in range(FRAMES):
        g.tick()
        draw(surf, g, fnt)
        proc.stdin.write(pygame.image.tostring(surf, "RGB"))
    proc.stdin.close()
    err = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
    rc = proc.wait()
    pygame.quit()
    if rc != 0 or not tmp.exists():
        raise RuntimeError(f"ffmpeg failed ({rc}): {err[-800:]}")
    tmp.replace(out)
    return out


def play():
    os.environ.pop("SDL_VIDEODRIVER", None)
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((W // 2, H // 2))
    pygame.display.set_caption("Nova Flip — ElbowOS")
    canvas = pygame.Surface((W, H))
    clock = pygame.time.Clock()
    g = Game()
    fnt = fonts()
    running = True
    while running:
        human = None
        keys = pygame.key.get_pressed()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif ev.key == pygame.K_r:
                    g = Game()
        left = keys[pygame.K_LEFT] or keys[pygame.K_z] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_x] or keys[pygame.K_d] or keys[pygame.K_SLASH]
        if left and right:
            human = "BOTH"
        elif left:
            human = "L"
        elif right:
            human = "R"
        g.tick(human)
        draw(canvas, g, fnt)
        pygame.transform.smoothscale(canvas, screen.get_size(), screen)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    if "--play" in sys.argv:
        play()
    else:
        path = record()
        print(path)
        print("bytes", path.stat().st_size)
        sys.exit(0)
