#!/usr/bin/env python3
"""Draw a one-page newspaper image summing up the world's news of
Thursday 26 November 2026.

Pure Python standard library: the rasteriser, the 5x7 bitmap font and
the PNG encoder are all written here, so the program runs with no
network and no installed packages. Two runs write byte-identical output.

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
Writes out/entry.png (1024x1024).
"""

import os
import struct
import zlib

W, H = 1024, 1024

# Palette: newsprint on cream paper.
PAPER = (246, 241, 229)
CARD = (255, 253, 246)
INK = (20, 20, 20)
GREY = (90, 86, 76)
RED = (166, 28, 28)
BLUE = (30, 77, 140)
TEAL = (14, 107, 107)
GOLD = (176, 124, 0)
GREEN = (46, 110, 58)
SKY = (24, 48, 96)
LIGHT_BLUE = (214, 228, 244)
LIGHT_GREY = (226, 222, 210)
ORANGE = (214, 98, 20)
FLAME = (232, 126, 24)

# ---------------------------------------------------------------- font
# 5x7 bitmap glyphs, one row per string, "#" = ink.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
}


def text_width(text, scale):
    """Pixel width of text at the given scale (6 px per glyph cell)."""
    return len(text) * 6 * scale


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def rect_border(self, x, y, w, h, color, t=3):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color, t=2):
        self.fill_rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=2):
        self.fill_rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=2):
        """Bresenham line with square brush of thickness t."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.fill_rect(x - t // 2, y - t // 2, t, t, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, color, t=3):
        for yy in range(cy - r - t, cy + r + t + 1):
            for xx in range(cx - r - t, cx + r + t + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 <= d2 <= (r + t) ** 2:
                    self.set(xx, yy, color)

    def ellipse(self, cx, cy, rx, ry, color, t=2):
        import math
        steps = 360
        prev = None
        for k in range(steps + 1):
            a = 2 * math.pi * k / steps
            px = int(cx + rx * math.cos(a))
            py = int(cy + ry * math.sin(a))
            if prev is not None:
                self.line(prev[0], prev[1], px, py, color, t)
            prev = (px, py)

    def triangle(self, pts, color):
        """Filled triangle via scanline fill."""
        (x0, y0), (x1, y1), (x2, y2) = pts
        ymin = min(y0, y1, y2)
        ymax = max(y0, y1, y2)
        for yy in range(ymin, ymax + 1):
            xs = []
            for (ax, ay), (bx, by) in (((x0, y0), (x1, y1)),
                                       ((x1, y1), (x2, y2)),
                                       ((x2, y2), (x0, y0))):
                if ay == by:
                    continue
                if min(ay, by) <= yy < max(ay, by):
                    xs.append(ax + (yy - ay) * (bx - ax) / (by - ay))
            if len(xs) >= 2:
                xa, xb = int(min(xs)), int(max(xs))
                self.fill_rect(xa, yy, xb - xa + 1, 1, color)

    def draw_text(self, x, y, text, scale, color):
        cx = x
        for ch in text:
            glyph = FONT.get(ch.upper(), FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, color)
            cx += 6 * scale
        return cx

    def draw_text_centered(self, x, y, w, text, scale, color):
        tw = text_width(text, scale)
        self.draw_text(x + max(0, (w - tw) // 2), y, text, scale, color)


# ---------------------------------------------------------------- icons
def icon_rocket(cv, x, y, w, h):
    """Rocket climbing past a ringed planet, on a night-sky panel."""
    cv.fill_rect(x, y, w, h, SKY)
    for sx, sy in ((18, 22), (52, 60), (150, 30), (196, 74), (30, 130),
                   (170, 140), (90, 18), (220, 44), (120, 96)):
        cv.fill_rect(x + sx, y + sy, 4, 4, CARD)
    # ringed planet, lower left
    cv.circle(x + 52, y + h - 52, 30, TEAL)
    cv.ellipse(x + 52, y + h - 52, 46, 12, GOLD, 3)
    # rocket body
    bx = x + w // 2 - 14
    by = y + 34
    cv.fill_rect(bx, by + 26, 28, 62, CARD)
    cv.triangle([(bx, by + 26), (bx + 14, by), (bx + 28, by + 26)], RED)
    cv.circle(bx + 14, by + 48, 7, LIGHT_BLUE)
    cv.ring(bx + 14, by + 48, 7, INK, 2)
    cv.triangle([(bx - 2, by + 62), (bx + 6, by + 88), (bx + 8, by + 62)], RED)
    cv.triangle([(bx + 20, by + 62), (bx + 22, by + 88), (bx + 30, by + 62)], RED)
    # flame
    cv.triangle([(bx + 6, by + 88), (bx + 14, by + 128), (bx + 22, by + 88)], FLAME)
    cv.triangle([(bx + 10, by + 88), (bx + 14, by + 112), (bx + 18, by + 88)], GOLD)


def icon_bars(cv, x, y, w, h):
    """Three falling bars: losses approaching half a million."""
    cv.fill_rect(x, y, w, h, LIGHT_GREY)
    base = y + h - 26
    heights = (96, 66, 38)
    bw = 26
    gap = 14
    x0 = x + (w - (3 * bw + 2 * gap)) // 2
    for i, hh in enumerate(heights):
        cv.fill_rect(x0 + i * (bw + gap), base - hh, bw, hh, RED)
    cv.hline(x + 8, base, w - 16, INK, 3)
    cv.draw_text(x + 8, y + 8, "500K", 3, RED)


def icon_shield(cv, x, y, w, h):
    """Shield with a check mark: a rescue that ended safely."""
    cv.fill_rect(x, y, w, h, LIGHT_BLUE)
    cx = x + w // 2
    top = y + 14
    cv.fill_rect(cx - 34, top, 68, 62, BLUE)
    cv.triangle([(cx - 34, top + 62), (cx, top + 96), (cx + 34, top + 62)], BLUE)
    cv.fill_rect(cx - 30, top + 4, 60, 54, CARD)
    cv.triangle([(cx - 30, top + 58), (cx, top + 88), (cx + 30, top + 58)], CARD)
    cv.line(cx - 18, top + 34, cx - 4, top + 50, GREEN, 6)
    cv.line(cx - 4, top + 50, cx + 22, top + 18, GREEN, 6)


def icon_planet(cv, x, y, w, h):
    """Mercury with its orbit and a small probe."""
    cv.fill_rect(x, y, w, h, (232, 226, 214))
    cx, cy = x + w // 2, y + h // 2 + 6
    cv.ellipse(cx, cy, 58, 20, GREY, 2)
    cv.circle(cx, cy, 30, (150, 138, 122))
    cv.circle(cx - 10, cy - 8, 6, (120, 110, 96))
    cv.circle(cx + 8, cy + 10, 4, (120, 110, 96))
    cv.circle(cx + 12, cy - 12, 3, (120, 110, 96))
    # probe on the orbit, upper right
    px, py = cx + 44, cy - 16
    cv.fill_rect(px - 14, py - 4, 10, 8, GOLD)
    cv.fill_rect(px + 4, py - 4, 10, 8, GOLD)
    cv.fill_rect(px - 4, py - 6, 8, 12, INK)
    cv.line(px + 4, py, px + 14, py - 8, INK, 2)


def icon_fire(cv, x, y, w, h):
    """Flame over a road: a tanker blaze."""
    cv.fill_rect(x, y, w, h, (250, 226, 200))
    cx = x + w // 2
    base = y + h - 22
    cv.fill_rect(x + 10, base, w - 20, 8, INK)
    cv.circle(cx, base - 34, 30, FLAME)
    cv.triangle([(cx - 30, base - 20), (cx, base - 78), (cx + 30, base - 20)], FLAME)
    cv.circle(cx, base - 22, 16, GOLD)
    cv.triangle([(cx - 16, base - 12), (cx, base - 48), (cx + 16, base - 12)], GOLD)
    cv.circle(cx - 26, base - 56, 5, GREY)
    cv.circle(cx + 24, base - 64, 6, GREY)
    cv.circle(cx + 6, base - 80, 4, GREY)


def icon_chess(cv, x, y, size):
    """8x8 board with two kings facing off."""
    sq = size // 8
    for r in range(8):
        for c in range(8):
            col = CARD if (r + c) % 2 == 0 else INK
            cv.fill_rect(x + c * sq, y + r * sq, sq, sq, col)
    cv.rect_border(x, y, size, size, INK, 2)
    cv.circle(x + 2 * sq + sq // 2, y + 1 * sq + sq // 2, sq // 2 - 1, CARD)
    cv.ring(x + 2 * sq + sq // 2, y + 1 * sq + sq // 2, sq // 2 - 1, INK, 2)
    cv.circle(x + 5 * sq + sq // 2, y + 6 * sq + sq // 2, sq // 2 - 1, INK)
    cv.ring(x + 5 * sq + sq // 2, y + 6 * sq + sq // 2, sq // 2 - 1, CARD, 2)


# ---------------------------------------------------------------- layout
def kicker_band(cv, x, y, w, label, color):
    cv.fill_rect(x, y, w, 26, color)
    cv.draw_text(x + 10, y + 5, label, 2, CARD)


def story_panel(cv, x, y, w, h, kicker, color, icon, headline, deck):
    cv.fill_rect(x, y, w, h, CARD)
    cv.rect_border(x, y, w, h, INK, 3)
    kicker_band(cv, x + 3, y + 3, w - 6, kicker, color)
    icon_x = x + 14
    icon_y = y + 42
    icon_w = 132
    icon_h = h - 56
    icon(cv, icon_x, icon_y, icon_w, icon_h)
    tx = icon_x + icon_w + 14
    tw = x + w - 14 - tx
    lines = wrap_text(headline, 3, tw)
    ly = y + 44
    for ln in lines:
        cv.draw_text(tx, ly, ln, 3, INK)
        ly += 24
    ly += 6
    cv.hline(tx, ly, tw, LIGHT_GREY, 2)
    ly += 10
    for ln in wrap_text(deck, 2, tw):
        cv.draw_text(tx, ly, ln, 2, GREY)
        ly += 17


def draw_page():
    cv = Canvas(W, H, PAPER)
    cv.rect_border(8, 8, W - 16, H - 16, INK, 4)

    # ---- masthead
    cv.fill_rect(16, 16, W - 32, 112, INK)
    cv.draw_text_centered(16, 32, W - 32, "THE WORLD IN ONE PAGE", 7, CARD)
    cv.fill_rect(36, 96, W - 72, 2, GOLD)
    cv.draw_text_centered(16, 104, W - 32,
                           "THURSDAY 26 NOVEMBER 2026", 2, GOLD)

    # ---- lead story: Pakistan's first astronaut
    lx, ly, lw, lh = 16, 140, W - 32, 252
    cv.fill_rect(lx, ly, lw, lh, CARD)
    cv.rect_border(lx, ly, lw, lh, INK, 3)
    kicker_band(cv, lx + 3, ly + 3, lw - 6, "SPACE  -  LEAD STORY", RED)
    icon_rocket(cv, lx + 14, ly + 42, 250, lh - 56)
    tx = lx + 278
    tw = lx + lw - 14 - tx
    cv.draw_text(tx, ly + 44, "PAKISTAN'S FIRST", 4, INK)
    cv.draw_text(tx, ly + 76, "ASTRONAUT FLIES TO", 4, INK)
    cv.draw_text(tx, ly + 108, "CHINA'S SPACE STATION", 4, RED)
    cv.hline(tx, ly + 152, tw, LIGHT_GREY, 2)
    deck = ("Muhammad Zeeshan Ali joins the Shenzhou-24 crew bound for "
            "Tiangong, the first foreign astronaut to visit the station.")
    dy = ly + 164
    for ln in wrap_text(deck, 2, tw):
        cv.draw_text(tx, dy, ln, 2, GREY)
        dy += 17
    dy += 8
    cv.draw_text(tx, dy, "SHENZHOU-24  -  TIANGONG  -  A FIRST FOR PAKISTAN",
                 2, BLUE)

    # ---- grid: four more stories
    gx0, gx1 = 16, 520
    gw = 488
    gy0, gy1 = 404, 652
    gh = 236
    story_panel(cv, gx0, gy0, gw, gh, "WAR IN UKRAINE", RED, icon_bars,
                "RUSSIA'S OWN FIGURES PUT WAR DEAD NEAR 500,000",
                "Moscow's data shows losses approaching half a million "
                "since the invasion began.")
    story_panel(cv, gx1, gy0, gw, gh, "COLOMBIA", BLUE, icon_shield,
                "POLICE FREE 20 HOSTAGES AFTER 17-HOUR SIEGE",
                "Officers storm a supermarket and free 20 people held "
                "hostage for 17 hours.")
    story_panel(cv, gx0, gy1, gw, gh, "SCIENCE", TEAL, icon_planet,
                "BEPICOLOMBO REACHES MERCURY AFTER 8-YEAR TRIP",
                "The European-Japanese probe settles into orbit around "
                "the Solar System's smallest planet.")
    story_panel(cv, gx1, gy1, gw, gh, "EGYPT", ORANGE, icon_fire,
                "CAIRO TANKER FIRE KILLS AT LEAST 30",
                "A fuel tanker crash ignites a huge blaze on a highway "
                "ringing the capital.")

    # ---- bottom strip: chess
    sx, sy, sw, sh = 16, 900, W - 32, 84
    cv.fill_rect(sx, sy, sw, sh, CARD)
    cv.rect_border(sx, sy, sw, sh, INK, 3)
    icon_chess(cv, sx + 12, sy + 10, 64)
    tx = sx + 92
    cv.draw_text(tx, sy + 12, "CHESS", 2, GREEN)
    cv.draw_text(tx + 78, sy + 12, "GUKESH DRAWS GAME 2 IN 20 MOVES", 3, INK)
    cv.draw_text(tx, sy + 46,
                 "The world champion and Sindarov split the point in Geneva.",
                 2, GREY)

    # ---- footer
    cv.draw_text_centered(16, 994, W - 32,
        "SIX STORIES, ONE DAY  -  AS REPORTED ON 26 NOVEMBER 2026", 1, GREY)
    return cv


# ---------------------------------------------------------------- PNG
def png_bytes(cv):
    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = cv.w * 3
    for yy in range(cv.h):
        raw.append(0)
        raw += cv.px[yy * stride:(yy + 1) * stride]
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(draw_page())
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
