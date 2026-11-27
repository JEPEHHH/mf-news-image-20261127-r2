"""Deterministic 1024x1024 news poster for Friday 27 November 2026.

Standard library only: no Pillow, no font files, no network.  The PNG is
assembled by hand (IHDR/IDAT/IEND, RGB8) from a bytearray canvas and a
built-in 5x7 bitmap font defined below.
"""

import hashlib
import os
import struct
import zlib

W = H = 1024

IVORY = (248, 245, 239)
INK = (17, 17, 17)
CRIMSON = (165, 31, 43)
GRAY = (119, 115, 110)
NAVY = (27, 42, 74)
WHITE = (255, 255, 255)

# 5x7 glyphs, one row of five bits per string character.  '1' = ink.
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10011", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    " ": ["00000"] * 7,
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "01100", "01100", "01000"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    ";": ["00000", "01100", "01100", "00000", "01100", "01100", "01000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "&": ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    "'": ["01100", "01100", "01000", "00000", "00000", "00000", "00000"],
    "%": ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "?": ["01110", "10001", "00001", "00010", "00100", "00000", "00100"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "*": ["00000", "10101", "01110", "11111", "01110", "10101", "00000"],
    "#": ["01010", "01010", "11111", "01010", "11111", "01010", "01010"],
}


class Canvas:
    def __init__(self, width, height, paper):
        self.w = width
        self.h = height
        self.buf = bytearray(paper * (width * height))

    def pixel(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def frame(self, x, y, w, h, color):
        self.rect(x, y, w, 1, color)
        self.rect(x, y + h - 1, w, 1, color)
        self.rect(x, y, 1, h, color)
        self.rect(x + w - 1, y, 1, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.rect(x0, y0, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def ellipse(self, cx, cy, rx, ry, color):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1:
                    self.pixel(xx, yy, color)

    def glyph(self, ch, x, y, scale, color):
        rows = FONT.get(ch.upper(), FONT[" "])
        for ry, bits in enumerate(rows):
            for rx, bit in enumerate(bits):
                if bit == "1":
                    self.rect(x + rx * scale, y + ry * scale, scale, scale, color)

    def text(self, s, x, y, scale=2, color=INK, tracking=0, max_x=None):
        cursor = x
        for ch in s:
            width = 5 * scale
            if max_x is not None and cursor + width > max_x:
                break
            self.glyph(ch, cursor, y, scale, color)
            cursor += width + tracking
        return cursor - x

    def wrap(self, s, x, y, scale, color, width, line_h, max_lines):
        words = s.split()
        lines = []
        current = ""
        cap = width // (6 * scale)
        for word in words:
            trial = word if not current else current + " " + word
            if len(trial) <= cap or not current:
                current = trial
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        for index, line in enumerate(lines[:max_lines]):
            self.text(line, x, y + index * line_h, scale, color, max_x=x + width)


def png_bytes(canvas):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw.extend(canvas.buf[y * stride:(y + 1) * stride])
    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload +
                struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))
    header = struct.pack(">2I5B", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) +
            chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


EDITION = {
    "date": "FRIDAY, 27 NOVEMBER 2026",
    "tagline": "GLOBAL EDITION  ·  ELEVEN STORIES IN ONE PAGE",
    "sources": "Sources: Reuters, AP, BBC, AFP, Financial Times, Bloomberg, ONS",
}

HERO = {
    "head": "New 25% Tariff Plan Roils Global Markets",
    "body": (
        "Washington proposed import duties on major partners, rattling equities "
        "and drawing warnings of retaliation from Ottawa, Mexico City and Beijing."
    ),
    "value": "25%",
    "pill": "+21.6 PTS VS 2024 AVG",
}

GRID = [
    ("MIDDLE EAST / SECURITY", "Drone Strike Rattles Kuwait Oil Corridor",
     "Air defenses intercepted drones near energy facilities, lifting crude futures as patrols tightened.", "drone"),
    ("ASIA-PACIFIC / ENERGY", "Fire Halts Bangkok Refinery",
     "Crews contained a blaze at a processing unit near the Chao Phraya as regulators opened a safety probe.", "refinery"),
    ("DIPLOMACY / GAZA", "Hague Court Presses on Gaza Aid",
     "Judges reviewed urgent filings on winter relief crossings while mediators pushed a ceasefire pause.", "court"),
    ("AMERICAS / WEATHER", "Storm Soaks Macy Parade Route",
     "Driving rain and 45 mph gusts forced crews to lower balloons across Manhattan and snarled holiday travel.", "storm"),
    ("SPACE / TECHNOLOGY", "SpaceX Sets Starship Turnaround Record",
     "Another booster catch in Texas signaled a faster cadence ahead of 2027 orbital cargo missions.", "rocket"),
    ("SPORT / CHESS", "World Chess Title Match Deadlocked",
     "A five-hour endgame ended in another draw, keeping both grandmasters level into the weekend rounds.", "chess"),
]

BRIEFS = [
    ("UK / MIGRATION", "UK Net Migration Drops 22%",
     "Annual net arrivals eased to 428,000 as tighter student and work visa rules took hold."),
    ("EUROPE / ECONOMY", "Eurozone Inflation Edges Higher",
     "Flash figures showed prices ticking up on winter energy bills ahead of December ECB talks."),
    ("AFRICA / RELIEF", "Sudan Aid Routes Under Strain",
     "UN agencies warned damaged bridges and fighting continue to slow food convoys into Darfur."),
    ("CLIMATE / POLICY", "Post-COP Climate Finance Stalls",
     "Developing nations pressed wealthy states for clearer grant timelines after tense global talks."),
]


def icon_drone(c, ox, oy):
    c.line(ox + 8, oy + 40, ox + 68, oy + 40, NAVY, 2)
    c.line(ox + 38, oy + 12, ox + 38, oy + 62, NAVY, 2)
    c.line(ox + 20, oy + 30, ox + 56, oy + 30, NAVY, 2)
    c.ellipse(ox + 38, oy + 30, 8, 5, NAVY)
    c.ellipse(ox + 38, oy + 30, 3, 2, CRIMSON)


def icon_refinery(c, ox, oy):
    c.rect(ox + 18, oy + 16, 18, 52, NAVY)
    c.rect(ox + 44, oy + 28, 22, 40, NAVY)
    c.line(ox + 27, oy + 16, ox + 27, oy + 8, GRAY, 2)
    c.ellipse(ox + 55, oy + 22, 4, 6, CRIMSON)
    c.line(ox + 14, oy + 68, ox + 70, oy + 68, GRAY, 2)


def icon_court(c, ox, oy):
    c.line(ox + 38, oy + 8, ox + 38, oy + 62, NAVY, 3)
    c.rect(ox + 12, oy + 22, 52, 4, NAVY)
    c.line(ox + 12, oy + 22, ox + 4, oy + 40, NAVY, 2)
    c.line(ox + 64, oy + 22, ox + 72, oy + 40, NAVY, 2)
    c.rect(ox + 2, oy + 40, 20, 4, GRAY)
    c.rect(ox + 54, oy + 40, 20, 4, GRAY)
    c.rect(ox + 28, oy + 62, 20, 4, CRIMSON)


def icon_storm(c, ox, oy):
    c.ellipse(ox + 26, oy + 26, 18, 10, NAVY)
    c.ellipse(ox + 44, oy + 24, 16, 12, NAVY)
    for dx in (18, 38, 58):
        c.line(ox + dx, oy + 38, ox + dx - 4, oy + 58, GRAY, 2)
    c.line(ox + 38, oy + 36, ox + 30, oy + 52, CRIMSON, 2)
    c.line(ox + 30, oy + 52, ox + 40, oy + 52, CRIMSON, 2)


def icon_rocket(c, ox, oy):
    c.line(ox + 38, oy + 60, ox + 38, oy + 18, NAVY, 3)
    c.line(ox + 38, oy + 18, ox + 30, oy + 8, NAVY, 2)
    c.line(ox + 38, oy + 18, ox + 46, oy + 8, NAVY, 2)
    c.line(ox + 20, oy + 26, ox + 8, oy + 16, CRIMSON, 2)
    c.line(ox + 20, oy + 26, ox + 8, oy + 36, CRIMSON, 2)
    c.line(ox + 30, oy + 62, ox + 34, oy + 70, GRAY, 2)
    c.line(ox + 46, oy + 62, ox + 42, oy + 70, GRAY, 2)


def icon_chess(c, ox, oy):
    c.line(ox + 26, oy + 60, ox + 22, oy + 40, NAVY, 3)
    c.line(ox + 22, oy + 40, ox + 34, oy + 30, NAVY, 3)
    c.line(ox + 34, oy + 30, ox + 44, oy + 42, NAVY, 3)
    c.line(ox + 44, oy + 42, ox + 52, oy + 60, NAVY, 3)
    c.rect(ox + 10, oy + 60, 56, 6, GRAY)
    c.rect(ox + 38, oy + 24, 8, 4, CRIMSON)


ICONS = {"drone": icon_drone, "refinery": icon_refinery, "court": icon_court,
         "storm": icon_storm, "rocket": icon_rocket, "chess": icon_chess}


def hero_card(c, x, y):
    c.rect(x, y, 316, 194, CRIMSON)
    c.text("PROPOSED U.S. IMPORT DUTY", x + 16, y + 14, 2, WHITE)
    c.text(HERO["value"], x + 16, y + 38, 10, WHITE, tracking=2)
    c.text("Blanket rate on key imports;", x + 16, y + 100, 2, WHITE)
    c.text("$1.4T annual trade exposed", x + 16, y + 118, 2, WHITE)
    bars = [("23", 4), ("24", 6), ("25", 14), ("26", 34)]
    for i, (label, height) in enumerate(bars):
        bx = x + 18 + i * 72
        c.rect(bx, y + 158 - height, 20, height, WHITE if i == 3 else GRAY)
        c.text(label, bx + 2, y + 164, 1, WHITE)
    c.rect(x + 16, y + 176, 284, 14, IVORY)
    c.text(HERO["pill"], x + 22, y + 179, 2, CRIMSON)


def draw_page(c):
    c.rect(0, 0, W, H, IVORY)
    c.frame(14, 14, 996, 996, GRAY)
    c.rect(40, 36, 944, 3, INK)
    c.text("WORLD DISPATCH", 40, 52, 12, INK, tracking=1)
    c.rect(40, 132, 944, 2, INK)
    c.text(EDITION["date"], 40, 142, 3, CRIMSON, tracking=1)
    c.text(EDITION["tagline"], 452, 144, 2, GRAY)
    c.rect(40, 168, 944, 1, GRAY)

    c.text("LEAD STORY / GLOBAL TRADE", 40, 176, 2, CRIMSON)
    c.wrap(HERO["head"], 40, 200, 8, INK, 600, 76, 2)
    c.wrap(HERO["body"], 40, 276, 3, GRAY, 600, 20, 3)
    hero_card(c, 668, 160)

    c.rect(40, 374, 944, 2, INK)
    tops = [394, 518, 642]
    for idx, (kicker, head, body, key) in enumerate(GRID):
        col, row = idx % 2, idx // 2
        ox = 40 + col * 476
        oy = tops[row]
        c.text(kicker, ox, oy, 2, CRIMSON)
        c.wrap(head, ox, oy + 24, 4, INK, 376, 24, 2)
        ICONS[key](c, ox + 388, oy + 22)
        c.wrap(body, ox, oy + 76, 2, GRAY, 456, 18, 3)
        if row < 2:
            c.rect(ox, oy + 116, 456, 1, GRAY)

    c.rect(40, 774, 944, 2, INK)
    c.text("ALSO TODAY", 40, 788, 3, NAVY)
    for i, (kicker, head, body) in enumerate(BRIEFS):
        bx = 40 + i * 236
        c.text(kicker, bx, 820, 2, NAVY)
        c.wrap(head, bx, 842, 3, INK, 220, 18, 2)
        c.wrap(body, bx, 886, 2, GRAY, 220, 16, 4)

    c.rect(40, 958, 944, 1, GRAY)
    c.text(EDITION["sources"], 40, 966, 2, GRAY)
    c.text("27 NOVEMBER 2026 / WORLD SUMMARY", 660, 966, 2, NAVY)
    c.rect(660, 962, 324, 1, GRAY)


def render(output_dir):
    target = os.path.join(output_dir, "entry.png")
    c = Canvas(W, H, IVORY)
    draw_page(c)
    data = png_bytes(c)
    with open(target, "wb") as fh:
        fh.write(data)
    return target, data


def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    target, data = render(out)
    print("wrote %s (%d bytes, sha256 %s)" %
          (target, len(data), hashlib.sha256(data).hexdigest()))


if __name__ == "__main__":
    main()
