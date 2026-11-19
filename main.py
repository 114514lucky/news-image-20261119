# news-image-20261119: draws one 1024x1024 PNG that sums up the world news
# of Thursday 19 November 2026. Python 3.13, standard library only, no
# network, no clock, no randomness: two runs write identical bytes.
# The image is drawn at run time from the stories below, which were first
# reported on 19 November 2026 (Le Monde, Business Times, NDTV, Japan
# Times, AFP, Al Jazeera). Drawing and font code adapted from the sibling
# 18 November entry, written fresh here; all stories are 19 November.
import os, struct, zlib

W, H = 1024, 1024

# --- 5x7 bitmap font: one block per glyph, 7 rows of 5 chars, '#' = on ---
FONT_SRC = """
A
.###.
#...#
#...#
#####
#...#
#...#
#...#
B
####.
#...#
#...#
####.
#...#
#...#
####.
C
.####
#....
#....
#....
#....
#....
.####
D
####.
#...#
#...#
#...#
#...#
#...#
####.
E
#####
#....
#....
####.
#....
#....
#####
F
#####
#....
#....
####.
#....
#....
#....
G
.####
#....
#....
#.###
#...#
#...#
.###.
H
#...#
#...#
#...#
#####
#...#
#...#
#...#
I
.###.
..#..
..#..
..#..
..#..
..#..
.###.
J
..###
...#.
...#.
...#.
...#.
#..#.
.##..
K
#...#
#..#.
#.#..
##...
#.#..
#..#.
#...#
L
#....
#....
#....
#....
#....
#....
#####
M
#...#
##.##
#.#.#
#.#.#
#...#
#...#
#...#
N
#...#
##..#
##..#
#.#.#
#..##
#..##
#...#
O
.###.
#...#
#...#
#...#
#...#
#...#
.###.
P
####.
#...#
#...#
####.
#....
#....
#....
Q
.###.
#...#
#...#
#...#
#.#.#
#..#.
.##.#
R
####.
#...#
#...#
####.
#.#..
#..#.
#...#
S
.####
#....
#....
.###.
....#
....#
####.
T
#####
..#..
..#..
..#..
..#..
..#..
..#..
U
#...#
#...#
#...#
#...#
#...#
#...#
.###.
V
#...#
#...#
#...#
#...#
#...#
.#.#.
..#..
W
#...#
#...#
#...#
#.#.#
#.#.#
##.##
#...#
X
#...#
#...#
.#.#.
..#..
.#.#.
#...#
#...#
Y
#...#
#...#
.#.#.
..#..
..#..
..#..
..#..
Z
#####
....#
...#.
..#..
.#...
#....
#####
0
.###.
#..##
#.#.#
##..#
#...#
#...#
.###.
1
..#..
.##..
..#..
..#..
..#..
..#..
.###.
2
.###.
#...#
....#
...#.
..#..
.#...
#####
3
####.
....#
....#
.###.
....#
....#
####.
4
...#.
..##.
.#.#.
#..#.
#####
...#.
...#.
5
#####
#....
####.
....#
....#
#...#
.###.
6
.###.
#....
#....
####.
#...#
#...#
.###.
7
#####
....#
...#.
...#.
..#..
..#..
..#..
8
.###.
#...#
#...#
.###.
#...#
#...#
.###.
9
.###.
#...#
#...#
.####
....#
....#
.###.
.
.....
.....
.....
.....
.....
.....
.##..
,
.....
.....
.....
.....
.....
.##..
..#..
:
.....
.##..
.....
.....
.##..
.....
.....
;
.....
.##..
.....
.....
.##..
.....
..#..
'
..#..
..#..
.....
.....
.....
.....
.....
-
.....
.....
.....
#####
.....
.....
.....
/
....#
...#.
..#..
.#...
#....
.....
.....
(
...#.
..#..
.#...
.#...
.#...
..#..
...#.
)
.#...
..#..
...#.
...#.
...#.
..#..
.#...
&
.###.
#...#
#.#..
.#...
#.#.#
#..#.
.##.#
!
..#..
..#..
..#..
..#..
..#..
.....
..#..
?
.###.
#...#
....#
...#.
..#..
.....
..#..
%
##..#
##.#.
...#.
..#..
.#...
#.#.#
#..##
+
.....
..#..
..#..
#####
..#..
..#..
.....
=
.....
.....
#####
.....
#####
.....
.....
"
.#.#.
.#.#.
.....
.....
.....
.....
.....
"""

def _parse_font(src):
    # Blank-line independent: a 1-char line starts a glyph, the next
    # 7 lines (5 chars each) are its rows. Empty lines are skipped.
    font = {}
    lines = [l for l in src.split("\n") if l.strip()]
    i = 0
    while i + 7 < len(lines) + 1 and i < len(lines):
        ch = lines[i]
        rows = lines[i + 1:i + 8]
        if len(ch) == 1 and len(rows) == 7 and all(len(r) == 5 for r in rows):
            font[ch] = rows
            i += 8
        else:
            i += 1
    font[" "] = ["....."] * 7
    return font

FONT = _parse_font(FONT_SRC)

# --- pixel buffer ---
buf = bytearray(W * H * 3)

def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i:i + 3] = bytes(c)

def rect(x, y, w, h, c):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            buf[base + (xx - x0) * 3: base + (xx - x0) * 3 + 3] = bytes(c)

def hline(x, y, w, c):
    rect(x, y, w, 1, c)

def vline(x, y, h, c):
    rect(x, y, 1, h, c)

def circle(cx, cy, r, c, fill=True):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            d2 = (xx - cx) ** 2 + (yy - cy) ** 2
            if fill:
                if d2 <= r * r:
                    px(xx, yy, c)
            else:
                if r * r - 2 * r <= d2 <= r * r:
                    px(xx, yy, c)

def tri(x1, y1, x2, y2, x3, y3, c):
    # filled triangle by scanlines
    ys = sorted([(x1, y1), (x2, y2), (x3, y3)], key=lambda p: p[1])
    (ax, ay), (bx, by), (cx, cy) = ys
    def edge(xa, ya, xb, yb, y):
        if yb == ya:
            return xa
        return xa + (xb - xa) * (y - ya) / (yb - ya)
    for y in range(ay, cy + 1):
        if y < by:
            xa = edge(ax, ay, bx, by, y)
            xb = edge(ax, ay, cx, cy, y)
        else:
            xa = edge(bx, by, cx, cy, y)
            xb = edge(ax, ay, cx, cy, y)
        x0, x1 = int(min(xa, xb)), int(max(xa, xb))
        hline(x0, y, x1 - x0 + 1, c)

def text(s, x, y, scale, c):
    cx = x
    for ch in s.upper():
        rows = FONT.get(ch)
        if rows is None:
            cx += 6 * scale
            continue
        for r, row in enumerate(rows):
            for col, bit in enumerate(row):
                if bit == "#":
                    rect(cx + col * scale, y + r * scale, scale, scale, c)
        cx += 6 * scale
    return cx

def text_w(s, scale):
    return len(s) * 6 * scale - scale

def wrap(s, scale, width):
    lines, cur = [], ""
    for word in s.split(" "):
        t = word if not cur else cur + " " + word
        if text_w(t, scale) <= width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines

def para(s, x, y, scale, width, c, lh=None):
    lh = lh or (7 * scale + 6)
    for line in wrap(s, scale, width):
        text(line, x, y, scale, c)
        y += lh
    return y

# --- the day's news: six stories, first reported on 19 November 2026 ---
# (kicker, headline, one-line summary, accent colour)
STORIES = [
    ("US-CHINA-RUSSIA SUMMIT",
     "TRUMP, XI AND PUTIN MEET IN SHENZHEN",
     "First-ever trilateral summit in Shenzhen; nuclear arms and two wars on the table.",
     (18, 58, 124)),
    ("CULTURE - VIDEO GAMES",
     "GTA VI LAUNCHES WORLDWIDE",
     "Midnight rollout after 13 years; first reviews score 99 out of 100.",
     (14, 120, 110)),
    ("BUSINESS - AI IPO",
     "ANTHROPIC'S RECORD 107.3BN IPO DEBUTS",
     "Largest listing ever tops SpaceX; shares trade on Nasdaq as ANT.",
     (178, 34, 34)),
    ("MIDDLE EAST - HORMUZ",
     "IRAN SAYS 3 TANKERS HIT MINES",
     "Tehran claims three ships caught fire off Hormuz; claim unverified.",
     (204, 102, 0)),
    ("AFRICA - HORN OF AFRICA",
     "ETHIOPIA-ERITREA WAR FEARS GROW",
     "Monitors warn of full-scale war after border clashes at Badme.",
     (102, 45, 145)),
    ("AMERICAS - VENEZUELA",
     "HEGSETH SIGNS US-VENEZUELA PACT",
     "Surprise Caracas trip restores training and intelligence sharing.",
     (34, 120, 60)),
]

TICKER = ("ALSO TODAY - WORLD COURT RULES ON MYANMAR ROHINGYA CASE. "
          "VAN GOGH SELLS FOR A RECORD 190.4M. "
          "VOYAGER 1 REACHES ONE LIGHT-DAY. "
          "COPPER PLUNGES 5% ON AI WORRIES. "
          "JEFFRIES SET TO BE FIRST BLACK US HOUSE SPEAKER. "
          "5.7 QUAKE SHAKES KUMAMOTO.")

PAPER = (246, 241, 231)
NAVY = (19, 41, 75)
GOLD = (232, 184, 75)
INK = (24, 24, 24)
GREY = (90, 90, 90)
WHITE = (255, 255, 255)

def centre(s, y, scale, c):
    text(s, (W - text_w(s, scale)) // 2, y, scale, c)

def draw():
    rect(0, 0, W, H, PAPER)
    # header
    rect(0, 0, W, 170, NAVY)
    rect(0, 170, W, 4, GOLD)
    centre("THE WORLD IN ONE DAY", 16, 2, GOLD)
    centre("WORLD NEWS", 44, 7, WHITE)
    centre("THURSDAY 19 NOVEMBER 2026", 112, 3, GOLD)
    # subhead
    centre("SIX STORIES THAT DEFINED THE DAY", 184, 2, NAVY)
    # story cards: 2 columns x 3 rows
    cw, ch, gx, gy = 472, 208, 16, 16
    for i, (kick, head, sub, col) in enumerate(STORIES):
        x = 32 + (i % 2) * (cw + gx)
        y = 214 + (i // 2) * (ch + gy)
        rect(x, y, cw, ch, WHITE)
        rect(x, y, cw, 10, col)
        # border
        hline(x, y + ch - 1, cw, (216, 208, 188))
        vline(x, y, ch, (216, 208, 188))
        vline(x + cw - 1, y, ch, (216, 208, 188))
        # story number in a filled circle, top right
        circle(x + cw - 34, y + 36, 17, col)
        text(str(i + 1), x + cw - 34 - 3 * 3, y + 36 - 10, 3, WHITE)
        text(kick, x + 20, y + 26, 2, col)
        para(head, x + 20, y + 52, 3, cw - 40, INK)
        para(sub, x + 20, y + 118, 2, cw - 40, GREY)
    # ticker band
    rect(0, 886, W, 82, NAVY)
    para(TICKER, 32, 898, 2, W - 64, WHITE)
    # footer
    centre("ALL STORIES FIRST REPORTED ON 19 NOVEMBER 2026", 980, 2, NAVY)

def png_bytes():
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += buf[y * W * 3:(y + 1) * W * 3]
    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    out = b"\x89PNG\r\n\x1a\n"
    out += chunk(b"IHDR", ihdr)
    out += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    out += chunk(b"IEND", b"")
    return out

def main():
    draw()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(png_bytes())

if __name__ == "__main__":
    main()
