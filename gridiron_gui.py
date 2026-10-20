#!/usr/bin/env python3
"""GRIDIRON DECK - graphical front end (tkinter, no installs needed).

Keep this file in the same folder as gridiron_deck.py - it reuses the rules,
players, formations, power-ups, lineup, packs and library logic from there.
Run:  python3 gridiron_gui.py

Screens: Title | Game | Lineup | Card Library | Pro Shop
Game flow: Formation -> Play -> Player (offense)
           Formation -> Defensive play -> Defender (defense)
"""
# Bump this when the game changes, so a bug report says which build it came
# from. VERSION_DATE is the date that build was cut.
VERSION = "1.0.0"
VERSION_DATE = "2026-10-20"
VERSION_LINE = f"v{VERSION}  \u2022  build {VERSION_DATE}"

import random
import tkinter as tk
from collections import Counter

import gridiron_deck as gd

BG = "#0a0f1c"; PANEL = "#131b2e"; PANEL2 = "#1b2640"
ACC = "#22d3ee"; GOLD = "#fbbf24"; RED = "#f43f5e"; GRN = "#22c55e"
PINK = "#e879f9"; TXT = "#e5edff"; DIM = "#7d8aa8"; ORANGE = "#fb923c"
FONT = "Helvetica"; PIX = "Courier"


def lighten(c, f=0.2):
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    r, g, b = (int(v + (255 - v) * f) for v in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def ovr(pl):
    return round(sum(sorted(pl.st.values(), reverse=True)[:4]) / 4)


def tier_color(o):
    return GOLD if o >= 78 else ("#cbd5e1" if o >= 68 else "#c2813b")


def mkbtn(parent, text, cmd, bg=ACC, fg="#041018", size=12, padx=18, pady=9):
    b = tk.Label(parent, text=text, bg=bg, fg=fg, font=(FONT, size, "bold"),
                 padx=padx, pady=pady, cursor="hand2")
    b.bind("<Button-1>", lambda e: cmd())
    b.bind("<Enter>", lambda e: b.config(bg=lighten(bg)))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def vscroll(parent, height):
    """Vertical scroller: returns (outer, inner)."""
    outer = tk.Frame(parent, bg=BG)
    cv = tk.Canvas(outer, height=height, bg=BG, highlightthickness=0)
    sb = tk.Scrollbar(outer, orient="vertical", command=cv.yview)
    cv.configure(yscrollcommand=sb.set)
    inner = tk.Frame(cv, bg=BG)
    cv.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
    cv.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    # mouse wheel while hovering
    def wheel(ev):
        cv.yview_scroll(-1 * (ev.delta // 120), "units")
    cv.bind("<Enter>", lambda e: cv.bind_all("<MouseWheel>", wheel))
    cv.bind("<Leave>", lambda e: cv.unbind_all("<MouseWheel>"))
    # expose the canvas as an attribute so callers can reset the view
    outer.canvas = cv
    outer.reset_view = lambda: cv.yview_moveto(0)
    return outer, inner


# ---------------------------------------------------------------- pixel art
def px(canvas, art, ox, oy, size, palette):
    """Draw 8-bit art. `art` is rows of chars, `.` = transparent."""
    for r, row in enumerate(art):
        for c, ch in enumerate(row):
            col = palette.get(ch)
            if col:
                canvas.create_rectangle(ox + c * size, oy + r * size,
                                        ox + (c + 1) * size, oy + (r + 1) * size,
                                        fill=col, outline="")


PAL = {
    "k": "#0b1220",   # outline
    "s": "#f2b98a",   # skin
    "j": "#22d3ee",   # offense jersey
    "d": "#f43f5e",   # defense jersey
    "w": "#e5edff",   # white / helmet stripe
    "b": "#111827",   # helmet shell
    "g": "#fbbf24",   # gold trim
    "p": "#3b2a1a",   # ball
    "n": "#7c3a00",   # ball laces
}

# generic standee, colored by unit
BALLER = [
    "....kkkk....",
    "...kbbbbk...",
    "..kbbwwbbk..",
    "..kbswwsbk..",
    "...kssssk...",
    "...kkkkkk...",
    "..kjjjjjjk..",
    ".kjjwjjwjjk.",
    ".kjjjjjjjjk.",
    "..kjjjjjjk..",
    "..kjj..jjk..",
    "..kkk..kkk..",
    "...kk..kk...",
    "...kk..kk...",
    "..kkk..kkk..",
]

QB_ART = [
    "....kkkk....",
    "...kbbbbk...",
    "..kbbwwbbk..",
    "..kbswwsbk..",
    "...kssssk...",
    "...kkkkkk...",
    "..kjjjjjjk..",
    ".kjjwjjwjjk.",
    ".kjjjjjjjjk.",
    "..kjjjjpjk..",
    "..kjjpppjk..",
    "..kkkppkkk..",
    "...kknnkk...",
    "...kk..kk...",
    "..kkk..kkk..",
]

RB_ART = [
    "....kkkk....",
    "...kbbbbk...",
    "..kbbwwbbk..",
    "..kbswwsbk..",
    "...kssssk...",
    "...kkkkkk...",
    "..kjjjjjjk..",
    ".kjjwjjwjjk.",
    "..kjjjjpjk..",
    "..kjjpppk...",
    "..kjjjnjk...",
    "..kkkppkk...",
    "...kk.kk....",
    "...kkmmkk...",
    "..kkk..kkk..",
]

WR_ART = [
    "....kkkk....",
    "...kbbbbk...",
    "..kbbwwbbk..",
    "..kbswwsbk..",
    "...kssssk...",
    "...kkkkkk...",
    ".kjjjjjjjjk.",
    "kjjwjjjwjjk.",
    ".kjjjjjjjjk.",
    "..kjjjjjjk..",
    "..kjj..jjk..",
    "..kkk..kkk..",
    "...k....k...",
    "...kk..kk...",
    "..kkk..kkk..",
]

DL_ART = [
    "....kkkk....",
    "...kbbbbk...",
    "..kbbwwbbk..",
    "..kbswwsbk..",
    "...kssssk...",
    "..kdddddk...",
    ".kddwddwdk..",
    "kdddddddddk.",
    ".kdddddddk..",
    ".kdddddddk..",
    "..kddddddk..",
    "..kkddddkk..",
    "..kk.kk.kk..",
    "..kk.kk.kk..",
    ".kkk.kk.kkk.",
]

LB_ART = [
    "....kkkk....",
    "...kbbbbk...",
    "..kbbwwbbk..",
    "..kbswwsbk..",
    "...kssssk...",
    "..kdddddk...",
    ".kddwddwdk..",
    ".kdddddddk..",
    "..kdddddk...",
    "..kddddddk..",
    "...kdddk....",
    "...kkddkk...",
    "...kk..kk...",
    "..kkk..kkk..",
    "..kkk..kkk..",
]

CB_ART = [
    "....kkkk....",
    "...kbbbbk...",
    "..kbbwwbbk..",
    "..kbswwsbk..",
    "...kssssk...",
    "...kkkkkk...",
    ".kddddddddk.",
    "kddwddddwdk.",
    ".kddddddddk.",
    "..kddddddk..",
    "..kdd..ddk..",
    "..kkk..kkk..",
    "...k....k...",
    "...kk..kk...",
    "..kkk..kkk..",
]

S_ART = [
    "....kkkk....",
    "...kbbbbk...",
    "..kbbwwbbk..",
    "..kbswwsbk..",
    "...kssssk...",
    "...kkkkkk...",
    "..kddddddk..",
    ".kddwddwdk..",
    ".kddddddddk.",
    "..kddddddk..",
    "..kdd.ddk...",
    "..kkk.kkk...",
    "...kk..kk...",
    "...kk..kk...",
    "..kkk..kkk..",
]

K_ART = [
    "....kkkk....",
    "...kbbbbk...",
    "..kbbwwbbk..",
    "..kbswwsbk..",
    "...kssssk...",
    "...kkkkkk...",
    "..kgggggk...",
    ".kggwggwgk..",
    "..kgggggk...",
    "..kgg.ggk...",
    "..kkk..kkk..",
    "...k....k...",
    "...kk..kk...",
    "..kkk..kkk..",
    "..kkk..kkk..",
]

POS_ART = {"QB": QB_ART, "RB": RB_ART, "WR": WR_ART, "TE": WR_ART,
           "DL": DL_ART, "LB": LB_ART, "CB": CB_ART, "S": S_ART, "K": K_ART}

# 8-bit power-up icons (14 wide)
IC_BOOST = [
    "..............",
    ".....y........",
    "....yyy.......",
    "...yyyyy......",
    "..yyyyyyy.....",
    ".yyyyoyyyy....",
    "yyyyooyyyyyy..",
    ".yyyooyyyyy...",
    "..yyooooyy....",
    "...yyooyy.....",
    "....yooy......",
    ".....oo.......",
    ".....o........",
    "..............",
]
IC_SAFE = [
    "..............",
    "...gggggg.....",
    "..gggggggg....",
    ".gggwwwwggg...",
    ".ggwwwwwwgg...",
    ".ggwwwwwwgg...",
    ".gggwwwwggg...",
    "..gggwwggg....",
    "...ggggggg....",
    "....ggggg.....",
    ".....ggg......",
    "......g.......",
    "..............",
    "..............",
]
IC_BIG = [
    "..............",
    "......gg......",
    ".....gggg.....",
    "....gggggg....",
    "...ggoooo gg..",
    "..ggoo..oogg..",
    ".ggoo....oogg.",
    "ggoo......oogg",
    "ggo........ogg",
    "ggoo......oogg",
    ".ggooooooogg..",
    "..ggggggggg...",
    "...ggggggg....",
    "..............",
]

ICONS = {"boost": IC_BOOST, "safe": IC_SAFE, "big": IC_BIG}
ICON_PAL = {"y": "#fbbf24", "o": "#fb923c", "g": "#e5edff", "w": "#22d3ee",
            "k": "#0b1220"}


# ---------------------------------------------------------------- cards
class PlayerCard(tk.Canvas):
    """Pixel-art portrait, attribute bars, fatigue strip and a status badge."""
    W, H = 152, 268

    def __init__(self, parent, pl, weights=None, fit=None, cmd=None,
                 badge=None, badge_col=None, dim=False, art_size=5):
        col = tier_color(ovr(pl))
        bgc = "#0d1425" if dim else PANEL
        super().__init__(parent, width=self.W, height=self.H, bg=bgc,
                         highlightthickness=3,
                         highlightbackground=("#334155" if dim else col),
                         cursor="hand2" if cmd else "")
        self.col = col
        unitcol = ACC if pl.unit == "OFF" else (RED if pl.unit == "DEF" else GRN)

        # header
        self.create_rectangle(0, 0, self.W, 42, fill=PANEL2, outline="")
        self.create_text(7, 13, text=pl.name, anchor="w",
                         fill=TXT if not dim else DIM, font=(PIX, 9, "bold"))
        slot_label = pl.pos if not pl.slot else gd.nice_slot(pl.slot)
        self.create_text(7, 29, text=slot_label, anchor="w", fill=unitcol,
                         font=(PIX, 11, "bold"))
        self.create_text(self.W - 7, 26, text=str(ovr(pl)), anchor="e", fill=col,
                         font=(PIX, 20, "bold"))

        # pixel portrait on a little pitch
        art = POS_ART.get(pl.pos, BALLER)
        aw, ah = len(art[0]) * art_size, len(art) * art_size
        ox = (self.W - aw) // 2
        oy = 48
        self.create_rectangle(6, oy - 4, self.W - 6, oy + ah + 6,
                              fill="#123a1f" if pl.unit == "OFF" else "#3a1220", outline="")
        for i in range(0, self.W - 12, 12):
            self.create_line(6 + i, oy - 4, 6 + i, oy + ah + 6,
                             fill="#17502b" if pl.unit == "OFF" else "#521a2c")
        px(self, art, ox, oy, art_size, PAL)

        # attributes
        y = oy + ah + 12
        for s in gd.STATS:
            v = pl.st[s]
            hot = bool(weights) and s in weights
            self.create_text(8, y + 5, text=s.upper(), anchor="w",
                             fill=GOLD if hot else DIM, font=(PIX, 8, "bold"))
            self.create_rectangle(38, y + 1, 112, y + 10, fill=BG, outline="")
            self.create_rectangle(38, y + 1, 38 + 74 * v / 99, y + 10,
                                  fill=GOLD if hot else unitcol, outline="")
            self.create_text(146, y + 5, text=str(v), anchor="e", fill=TXT, font=(PIX, 8, "bold"))
            y += 13

        # fatigue
        pen = gd.fatigue_penalty(pl)
        self.create_rectangle(8, y + 2, self.W - 8, y + 24,
                              fill=ORANGE if pen else "#25314f", outline="")
        self.create_text(self.W / 2, y + 13,
                         text=(f"TIRED -{pen}" if pen else "RESTED"),
                         fill="#2b1200" if pen else DIM, font=(PIX, 9, "bold"))
        y += 30

        if fit is not None:
            self.create_rectangle(8, y, self.W - 8, y + 26, fill=GOLD, outline="")
            self.create_text(self.W / 2, y + 13, text=f"FIT {fit:.0f}",
                             fill="#1a1200", font=(PIX, 13, "bold"))
        if badge:
            bc = badge_col or ACC
            self.create_rectangle(8, y, self.W - 8, y + 26, fill=bc, outline="")
            self.create_text(self.W / 2, y + 13, text=badge, fill="#041018",
                             font=(PIX, 11, "bold"))
        if cmd:
            self.bind("<Button-1>", lambda e: cmd(pl))
            self.bind("<Enter>", lambda e: self.config(highlightbackground="#ffffff"))
            self.bind("<Leave>", lambda e: self.config(highlightbackground=self.col))


class PowerTile(tk.Canvas):
    """Power-up card with an 8-bit icon."""
    W, H = 168, 132
    COL = {"boost": ACC, "safe": GRN, "big": PINK}

    def __init__(self, parent, card, cmd=None, badge=None, armed=False, dim=False):
        col = self.COL[card.kind]
        bgc = "#0d1425" if dim else PANEL2
        super().__init__(parent, width=self.W, height=self.H, bg=bgc,
                         highlightthickness=3,
                         highlightbackground=GOLD if armed else ("#334155" if dim else col),
                         cursor="hand2" if cmd else "")
        self.create_rectangle(0, 0, self.W, 22, fill=col, outline="")
        self.create_text(7, 11, text=("\u2605 " if armed else "") + card.name.upper(),
                         anchor="w", fill="#041018", font=(PIX, 9, "bold"))
        art = ICONS[card.kind]
        px(self, art, 6, 28, 4, ICON_PAL)
        self.create_text(70, 34, text=card.desc, anchor="nw", width=92,
                         fill=TXT if not dim else DIM, font=(PIX, 8))
        if badge:
            self.create_text(70, 108, text=badge, anchor="w", fill=GOLD, font=(PIX, 10, "bold"))
        if cmd:
            self.bind("<Button-1>", lambda e: cmd(card))
            self.bind("<Enter>", lambda e: self.config(highlightbackground="#ffffff"))
            self.bind("<Leave>", lambda e: self.config(highlightbackground=col))


def choice_tile(parent, name, lines, cmd, col=ACC):
    t = tk.Frame(parent, bg=PANEL2, cursor="hand2", padx=16, pady=10,
                 highlightthickness=2, highlightbackground=col)
    t.pack(side="left", padx=6, pady=4)
    tk.Label(t, text=name.upper(), bg=PANEL2, fg=col, font=(FONT, 12, "bold")).pack()
    for ln, c in lines:
        tk.Label(t, text=ln, bg=PANEL2, fg=c, font=(FONT, 9, "bold")).pack()
    for wd in [t] + t.winfo_children():
        wd.bind("<Button-1>", lambda e: cmd())
        wd.bind("<Enter>", lambda e: t.config(highlightbackground="#ffffff"))
        wd.bind("<Leave>", lambda e: t.config(highlightbackground=col))
    return t


def nav_bar(app, active=None):
    """Kept for callers lower down; delegates to the app's own home_nav."""
    app.active = active
    return app.home_nav()


# ---------------------------------------------------------------- game screen
class GameScreen:
    PPY, EZ = 9, 50

    def __init__(self, app, prof):
        self.app, self.prof, self.root = app, prof, app.root
        self.dead = False
        self.me = self.cpu = self.earned = 0
        self.round, self.side = 1, "me"
        self.game = gd.Game(prof)
        self.deck = self.game.deck
        self.hand, self.armed = [], None
        self.pos, self.down, self.togo, self.shown = 25, 1, 10, 25
        self.form = self.play = self.player = self.cpu_play = None
        # weather lives on the Game, so fatigue and the meter read the same value
        self.weather = self.game.weather
        f = app.main

        sb = tk.Frame(f, bg=PANEL)
        sb.pack(fill="x", padx=14, pady=(0, 6))
        self.l_me = tk.Label(sb, bg=PANEL, fg=ACC, font=(FONT, 28, "bold"), width=8)
        self.l_me.pack(side="left", padx=(10, 4))
        self.l_cpu = tk.Label(sb, bg=PANEL, fg=RED, font=(FONT, 28, "bold"), width=8)
        self.l_cpu.pack(side="right", padx=(4, 10))
        mid = tk.Frame(sb, bg=PANEL)
        mid.pack(expand=True, pady=6)
        self.l_info = tk.Label(mid, bg=PANEL, fg=TXT, font=(FONT, 14, "bold"))
        self.l_info.pack()
        self.l_sub = tk.Label(mid, bg=PANEL, fg=DIM, font=(FONT, 10))
        self.l_sub.pack()
        # in-game quit
        mkbtn(sb, "QUIT", self.confirm_quit, bg=RED, fg="#fff", size=11,
              padx=16, pady=8).place(relx=1.0, x=-8, y=6, anchor="ne")

        self.field = tk.Canvas(f, width=1000, height=140, bg=BG, highlightthickness=0)
        self.field.pack(padx=14)
        self.log = tk.Text(f, height=4, bg=PANEL, fg=TXT, bd=0, font=("Courier", 10),
                           state="disabled", padx=10, pady=6)
        self.log.pack(fill="x", padx=14, pady=6)
        self.panel = tk.Frame(f, bg=BG)
        self.panel.pack(fill="both", expand=True, padx=14)
        self.handbar = tk.Frame(f, bg=BG)
        self.handbar.pack(fill="x", padx=14, pady=(4, 10))

        self.start_possession()

    # ---- infrastructure
    def later(self, ms, fn):
        self.root.after(ms, lambda: None if self.dead else fn())

    def confirm_quit(self):
        self.clear_panel()
        self.title("Quit the game?", RED)
        tk.Label(self.panel, text=f"You'd forfeit, leaving the score {self.me}\u2013{self.cpu}.\n"
                                  "Coins earned so far are banked when you leave.",
                 bg=BG, fg=TXT, font=(FONT, 12)).pack(anchor="w")
        row = tk.Frame(self.panel, bg=BG)
        row.pack(anchor="w", pady=10)
        mkbtn(row, "FORFEIT & LEAVE", self.quit, bg=RED, fg="#fff").pack(side="left", padx=4)
        mkbtn(row, "KEEP PLAYING", self.resume, bg=ACC).pack(side="left", padx=4)

    def resume(self):
        if self.side == "me":
            self.form_menu()
        else:
            self.cpu_snap()

    def quit(self):
        self.dead = True
        self.prof.coins += self.earned
        self.app.show_menu()

    def say(self, txt):
        self.log.config(state="normal")
        self.log.insert("end", txt + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def clear_panel(self):
        for w in self.panel.winfo_children():
            w.destroy()

    def title(self, text, color=TXT):
        tk.Label(self.panel, text=text, bg=BG, fg=color,
                 font=(FONT, 13, "bold")).pack(anchor="w", pady=(4, 6))

    def flash(self, text, color=GOLD):
        self.field.delete("flash")
        self.field.create_text(503, 73, text=text, fill="#000",
                               font=(FONT, 32, "bold"), tags="flash")
        self.field.create_text(500, 70, text=text, fill=color,
                               font=(FONT, 32, "bold"), tags="flash")

        def clr():
            try:
                self.field.delete("flash")
            except tk.TclError:
                pass
        self.later(1500, clr)

    def chain_popup(self, note, band, broke=False):
        """A banner across the top of the field when a chain actually fires.

        `note` is the chain description from the backend, `band` is the
        breakaway tier it reached, and `broke` says whether the breakaway
        roll then paid off. It sits above the yard lines and fades after a
        couple of seconds, so it reads clearly without stopping play.
        """
        c = self.field
        c.delete("chain")
        # solid banner so it stands out over any weather surface
        c.create_rectangle(120, 4, 880, 46, fill="#1c1206", outline=ORANGE,
                           width=3, tags="chain")
        c.create_text(500, 17, text="CHAIN FIRED", fill=ORANGE,
                      font=(FONT, 15, "bold"), tags="chain")
        c.create_text(500, 34, text=f"{note}   \u2022   BAND {band}", fill=TXT,
                      font=(FONT, 10, "bold"), tags="chain")
        if broke:
            c.create_text(860, 26, text="BREAKAWAY!", anchor="e", fill=GOLD,
                          font=(FONT, 12, "bold"), tags="chain")

        def clr():
            try:
                c.delete("chain")
            except tk.TclError:
                pass
        self.later(2200, clr)

    def x_of(self, p):
        p = max(0, min(100, p))
        return self.EZ + p * self.PPY if self.side == "me" else 1000 - self.EZ - p * self.PPY

    # weather -> turf palette. Each condition gets its own grass tones, line
    # colour and surface marks, so the field itself reads as the weather.
    SURFACES = {
        "clear": {
            "grass": ("#15803d", "#166534"), "line": "#86efac",
            "thin": "#22633a", "num": "#bbf7d0",
            "mud": [], "mud_col": None, "speck": None,
        },
        "rain": {
            "grass": ("#14532d", "#0f3f22"), "line": "#4ade80",
            "thin": "#1b4d2a", "num": "#86efac",
            "mud": [(0.16, 0.30, 92, 40), (0.40, 0.64, 132, 50),
                    (0.63, 0.26, 104, 44), (0.85, 0.68, 150, 56),
                    (0.28, 0.82, 88, 34), (0.74, 0.46, 70, 28),
                    (0.52, 0.12, 76, 26)],
            "mud_col": "#3f2a12", "speck": "#4b5563",
        },
        "snow": {
            "grass": ("#eef3f8", "#dde6ef"), "line": "#9aa8bb",
            "thin": "#c8d4e2", "num": "#3f4c5f",
            "mud": [(0.22, 0.56, 104, 36), (0.56, 0.34, 126, 40),
                    (0.80, 0.64, 88, 30), (0.36, 0.18, 72, 24)],
            "mud_col": "#b9c6d6", "speck": "#ffffff",
        },
        "wind": {
            "grass": ("#15803d", "#14532d"), "line": "#a3e635",
            "thin": "#22633a", "num": "#d9f99d",
            "mud": [], "mud_col": None, "speck": None,
        },
    }

    def surface(self):
        return self.SURFACES.get(self.weather, self.SURFACES["clear"])

    def redraw(self):
        c = self.field
        c.delete("f")
        s = self.surface()
        grass_a, grass_b = s["grass"]
        c.create_rectangle(0, 0, self.EZ, 140, fill="#0e7490", outline="", tags="f")
        c.create_rectangle(1000 - self.EZ, 0, 1000, 140, fill="#9f1239", outline="", tags="f")
        c.create_text(self.EZ / 2, 70, text="YOU", angle=90, fill="#fff",
                      font=(FONT, 13, "bold"), tags="f")
        c.create_text(1000 - self.EZ / 2, 70, text="CPU", angle=270, fill="#fff",
                      font=(FONT, 13, "bold"), tags="f")

        # turf in mown stripes, tinted by the weather
        for i in range(10):
            c.create_rectangle(self.EZ + i * 90, 0, self.EZ + (i + 1) * 90, 140,
                               fill=grass_a if i % 2 == 0 else grass_b,
                               outline="", tags="f")

        # surface marks: mud slicks for rain, frozen patches for snow
        if s["mud"]:
            field_w = 1000 - 2 * self.EZ
            for fx, fy, rw, rh in s["mud"]:
                x = self.EZ + field_w * fx
                y = 140 * fy
                c.create_oval(x - rw / 2, y - rh / 2, x + rw / 2, y + rh / 2,
                              fill=s["mud_col"], outline="", tags="f")

        for yd in range(0, 101, 5):
            x = self.EZ + yd * self.PPY
            c.create_line(x, 0, x, 140,
                          fill=s["line"] if yd % 10 == 0 else s["thin"], tags="f")
            if yd % 10 == 0 and 0 < yd < 100:
                c.create_text(x, 130, text=str(min(yd, 100 - yd)), fill=s["num"],
                              font=(FONT, 9, "bold"), tags="f")

        # a scatter of flakes on snow, grit specks in the rain
        if s["speck"]:
            seed = 7 if self.weather == "snow" else 11
            for i in range(0, 1000, 23):
                for j in range(6, 140, 26):
                    k = (i * 31 + j * seed) % 97
                    if k > 62:
                        r = 2 if self.weather == "snow" else 1
                        c.create_oval(i + (k % 9), j + (k % 7),
                                      i + (k % 9) + r, j + (k % 7) + r,
                                      fill=s["speck"], outline="", tags="f")
        los, fd = self.x_of(self.pos), self.x_of(self.pos + self.togo)
        c.create_line(fd, 0, fd, 140, fill=GOLD, width=3, tags="f")
        c.create_line(los, 0, los, 140, fill="#38bdf8", width=3, tags="f")
        # the chain banner and the big-play flash must sit above the surface
        c.tag_raise("chain")
        c.tag_raise("flash")
        bx = self.x_of(self.shown)
        c.create_oval(bx - 12, 58, bx + 12, 82, fill="#7c2d12", outline="#fff", width=2, tags="f")
        c.create_line(bx - 6, 70, bx + 6, 70, fill="#fff", width=2, tags="f")
        c.tag_raise("flash")

    def move_to(self, target, cb):
        start, steps = self.shown, 14

        def step(i):
            self.shown = start + (target - start) * i / steps
            self.redraw()
            if i < steps:
                self.later(28, lambda: step(i + 1))
            else:
                cb()
        step(1)

    def hud(self):
        self.l_me.config(text=f"YOU {self.me}")
        self.l_cpu.config(text=f"CPU {self.cpu}")
        who = "YOUR BALL" if self.side == "me" else "CPU BALL"
        self.l_info.config(text=f"{who}  \u2022  {self.down} & {self.togo}  \u2022  {gd.yl_text(self.pos)}",
                           fg=ACC if self.side == "me" else RED)
        w = gd.weather_of(self.weather)
        self.l_sub.config(text=f"Round {self.round}/{self.prof.ROUNDS}   \u2022   Level {self.prof.level}"
                               f"   \u2022   {w['label']}   \u2022   Deck {len(self.deck)}"
                               f"   \u2022   Earned {self.earned}",
                           fg=w["colour"])

    def refill(self):
        while len(self.hand) < 3 and self.deck:
            self.hand.append(self.deck.pop())

    def draw_hand(self):
        for w in self.handbar.winfo_children():
            w.destroy()
        tk.Label(self.handbar, text=f"POWER-UP HAND\n(click to arm)\nDeck: {len(self.deck)}",
                 bg=BG, fg=GOLD, font=(FONT, 9, "bold"), justify="left").pack(side="left", padx=(0, 12))
        if not self.hand:
            tk.Label(self.handbar, text="empty", bg=BG, fg=DIM).pack(side="left")
        for card in self.hand:
            PowerTile(self.handbar, card, self.toggle,
                      armed=card.uid == self.armed).pack(side="left", padx=5)

    def toggle(self, card):
        self.armed = None if self.armed == card.uid else card.uid
        self.draw_hand()

    def take_power(self):
        card = next((c for c in self.hand if c.uid == self.armed), None)
        if card:
            self.hand.remove(card)
            self.armed = None
            self.draw_hand()
            return gd.POWERUPS[card.name][:2], card.name
        return None, None

    def start_possession(self):
        if self.round > self.prof.ROUNDS:
            return self.finish()
        self.pos, self.down, self.togo, self.shown = 25, 1, 10, 25
        self.refill()
        self.draw_hand()
        self.hud()
        self.redraw()
        if self.side == "me":
            self.say(f"\u2500\u2500 Round {self.round}: your possession \u2500\u2500")
            self.form_menu()
        else:
            self.say(f"\u2500\u2500 Round {self.round}: you defend \u2500\u2500")
            self.cpu_snap()

    def end_possession(self):
        self.clear_panel()
        self.hud()

        def nxt():
            if self.side == "me":
                self.side = "cpu"
            else:
                self.side, self.round = "me", self.round + 1
            self.start_possession()
        self.later(1700, nxt)

    def form_menu(self):
        self.hud()
        self.clear_panel()
        pool = self.prof.lineup.player_pool()
        forms = gd.roll_formations()
        self.title(f"Formation  \u2013  {len(forms)} available this snap", ACC)
        row = tk.Frame(self.panel, bg=BG)
        row.pack(fill="x")
        for fm in forms:
            have = [s for s in fm["slots"] if any(p.slot == s for p in pool)]
            gone = [s for s in fm["slots"] if s not in have]
            lines = [(f"on field: {', '.join(have) if have else '-'}", DIM),
                     (f"missing: {', '.join(gone)}" if gone else f"{len(fm['pool'])} plays in the book",
                      ORANGE if gone else GOLD)]
            choice_tile(row, fm["name"], lines, lambda fm=fm: self.play_menu(fm),
                        ACC if not gone else "#64748b")

    def pick_player(self, roster, weights, title, on_pick, back, heavy=False):
        self.clear_panel()
        top = tk.Frame(self.panel, bg=BG)
        top.pack(fill="x")
        tk.Label(top, text=title, bg=BG, fg=TXT, font=(FONT, 13, "bold")).pack(side="left", pady=4)
        mkbtn(top, "\u25c0 Back", back, bg=PANEL2, fg=TXT, size=10, pady=4).pack(side="right")
        outer, inner = vscroll(self.panel, 290)
        outer.pack(fill="x")
        strip = tk.Frame(inner, bg=BG)
        strip.pack(anchor="w")
        if not roster:
            tk.Label(strip, text="Nobody available - check your LINEUP tab.",
                     bg=BG, fg=RED, font=(FONT, 12, "bold")).pack(padx=10, pady=20)
            return
        for pl in sorted(roster, key=lambda x: -gd.eff_rate(x, weights, heavy)):
            PlayerCard(strip, pl, weights, gd.eff_rate(pl, weights, heavy),
                       on_pick, art_size=4).pack(side="left", padx=4, pady=2)

    # ---- offense
    def play_menu(self, form):
        self.form = form
        self.clear_panel()
        self.title(f"{form['name']}  \u2013  call your play", GOLD)
        row = tk.Frame(self.panel, bg=BG)
        row.pack(fill="x")
        for name in gd.roll_plays(form):
            ptype, w, base, var = gd.OFF_PLAYS[name]
            chance, note = self.game.chain_preview(name)
            lines = [(f"[{ptype}] " + " \u2022 ".join(k.upper() for k in w), GOLD),
                     (f"avg ~{base} yds  \u2022  risk {var}", DIM)]
            if note:
                # this play cashes in the last one - show the reach and the odds
                lines.append((f"CHAIN: {note}", ORANGE))
                lines.append((f"{chance:.0%} to open it up", ORANGE))
            else:
                setup = gd.chain_hint(name)
                if setup:
                    lines.append((f"sets up: {setup}", ACC))
                elif ptype == "run":
                    lines.append(("sets up the next play", DIM))
            choice_tile(row, name, lines, lambda n=name: self.off_pick(n),
                        ORANGE if note else GOLD)
        extra = tk.Frame(self.panel, bg=BG)
        extra.pack(fill="x", pady=8)
        mkbtn(extra, "\u25c0 Formation", self.form_menu, bg=PANEL2, fg=TXT, size=10).pack(side="left")
        if self.pos >= 55 and self.down >= 3:
            mkbtn(extra, "FIELD GOAL", self.field_goal, bg=GRN).pack(side="left", padx=8)
        if self.down == 4:
            mkbtn(extra, "PUNT", self.punt, bg="#64748b", fg="#fff").pack(side="left", padx=8)

    def off_pick(self, play):
        self.play = play
        w = gd.OFF_PLAYS[play][1]
        pool = gd.eligible(self.prof.lineup.player_pool(), self.form, play, "OFF")
        self.pick_player(pool, w, f"{play} \u2013 who gets the ball?",
                         lambda pl: self.run_offense(play, pl), self.play_menu,
                         heavy=self.down == 4)

    def punt(self):
        self.say("You punt. Possession ends.")
        self.flash("PUNT", DIM)
        self.end_possession()

    # ---- kicking meter -------------------------------------------------
    def kick_meter(self, kicker, dist, label, on_done):
        """Animated timing bar. A marker sweeps 0-100; click STOP to nail it.

        Longer kicks sweep faster and the good zone narrows, so a 50-yarder
        is a genuine test. The kicker's kck sets the zone width and the
        weather tightens it further - all from gd.kick_profile.
        """
        prof = gd.kick_profile(kicker, dist, self.weather)
        self.clear_panel()
        w = gd.weather_of(self.weather)
        self.title(f"{label} \u2013 {kicker.name} from {dist} yards", GOLD)
        tk.Label(self.panel,
                 text=f"{w['label']}   \u2022   accuracy zone +/-{prof['half']:.1f}"
                      f"   \u2022   sweep speed x{prof['speed']:.2f}",
                 bg=BG, fg=DIM, font=(FONT, 10, "bold")).pack(anchor="w")

        cv = tk.Canvas(self.panel, width=760, height=110, bg=BG, highlightthickness=0)
        cv.pack(pady=10)
        cv.create_rectangle(20, 40, 740, 78, fill=PANEL2, outline="#334155", width=2)
        left = 20 + 720 * (50 - prof["half"]) / 100.0
        right = 20 + 720 * (50 + prof["half"]) / 100.0
        cv.create_rectangle(left, 40, right, 78, fill="#15803d", outline="")
        cv.create_line(380, 32, 380, 86, fill=GOLD, width=3)
        cv.create_text(380, 96, text="dead centre", fill=GOLD, font=(FONT, 9, "bold"))

        state = {"pos": 0.0, "dir": 1, "live": True}
        marker = cv.create_rectangle(0, 30, 0, 88, fill="#fff", outline="")

        def tick():
            if not state["live"]:
                return
            state["pos"] += state["dir"] * prof["speed"] * 2.6
            if state["pos"] >= 100:
                state["pos"], state["dir"] = 100, -1
            elif state["pos"] <= 0:
                state["pos"], state["dir"] = 0, 1
            x = 20 + 720 * state["pos"] / 100.0
            cv.coords(marker, x - 3, 30, x + 3, 88)
            self.later(16, tick)

        def stop():
            if not state["live"]:
                return
            state["live"] = False
            marker_pos = state["pos"]
            acc = gd.kick_accuracy(marker_pos, prof["half"], prof["need"])
            good, res = gd.kick_result(acc, prof["need"])
            x = 20 + 720 * marker_pos / 100.0
            cv.itemconfig(marker, fill=GRN if good else RED)
            self.say(f"{label}: stopped at {marker_pos:.1f} -> accuracy {acc:.0f} -> {res}")
            self.flash(res, GRN if good else RED)
            mkbtn(self.panel, "\u25b6 CONTINUE", lambda: on_done(good, res),
                  bg=ACC, size=12, padx=30, pady=8).pack(pady=8)

        mkbtn(self.panel, "STOP  \u25a0", stop, bg=GRN, fg="#04180c",
              size=16, padx=60, pady=14).pack(pady=8)
        tick()

    def field_goal(self):
        k = self.prof.kicker()
        if not k:
            self.say("No kicker signed!")
            return self.end_possession()
        dist = max(18, 117 - self.pos)

        def done(good, res):
            if good:
                self.me += 3
                self.earned += 8
            self.end_possession()
        self.kick_meter(k, dist, "FIELD GOAL", done)

    def pat(self, two_point):
        """Extra point after a touchdown: kick it on the meter, or go for two."""
        if two_point:
            return self.two_point_form()
        k = self.prof.kicker()
        if not k:
            self.say("No kicker signed - the PAT is no good.")
            return self.end_possession()

        def done(good, res):
            if good:
                self.me += 1
            self.end_possession()
        self.kick_meter(k, 20, "PAT", done)

    # ---- two-point try: a real play, not a dice roll -------------------
    def two_point_form(self):
        """Step 1 of the two-point try: pick a goal-line formation."""
        self.clear_panel()
        self.title("TWO-POINT TRY \u2013 you need two yards", ORANGE)
        tk.Label(self.panel, text="Chemistry sets your odds, and the CPU's call moves them.",
                 bg=BG, fg=DIM, font=(FONT, 10)).pack(anchor="w", pady=(0, 6))
        row = tk.Frame(self.panel, bg=BG)
        row.pack(fill="x")
        forms = self.game.two_point_formations()
        for fm in forms:
            have = [s for s in fm["slots"]
                    if any(p.slot == s for p in self.prof.lineup.player_pool())]
            gone = [s for s in fm["slots"] if s not in have]
            power = "HEAVY (best odds)" if fm["name"] == "Jumbo" else "balanced look"
            lines = [(f"on field: {', '.join(have) if have else '-'}", DIM),
                     (f"{power}", GRN),
                     (f"missing: {', '.join(gone)}" if gone else "everyone available",
                      ORANGE if gone else DIM)]
            choice_tile(row, fm["name"], lines,
                        lambda f=fm: self.two_point_play(f),
                        ORANGE if fm["name"] == "Jumbo" else GOLD)

    def two_point_play(self, form):
        """Step 2: pick the play. Only short-yardage calls are on the card."""
        self.form = form
        self.clear_panel()
        self.title(f"{form['name']} \u2013 call the two-point play", ORANGE)
        row = tk.Frame(self.panel, bg=BG)
        row.pack(fill="x")
        plays = [n for n in gd.roll_plays(form)
                 if gd.OFF_PLAYS[n][0] in ("run", "short")] or \
                ["Power Dive", "Quick Slant"]
        for name in plays:
            ptype, w, base, var = gd.OFF_PLAYS[name]
            fam = {"run": "power run", "short": "quick pass"}.get(ptype, ptype)
            choice_tile(row, name,
                        [(f"[{ptype}] {fam}", GOLD),
                         (" \u2022 ".join(k.upper() for k in w), DIM)],
                        lambda n=name: self.two_point_pick(n), ORANGE)
        mkbtn(self.panel, "\u25c0 Formation", self.two_point_form, bg=PANEL2, fg=TXT,
              size=10, pady=4).pack(anchor="w", pady=6)

    def two_point_pick(self, play):
        """Step 3: pick the player. The fit shown includes chemistry."""
        self.play = play
        ptype, w, base, var = gd.OFF_PLAYS[play]
        pool = gd.eligible(self.prof.lineup.player_pool(), self.form, play, "OFF")
        self.pick_player(pool, w, f"{play} \u2013 who carries the two-point try?",
                         lambda pl: self.two_point_go(play, pl), self.two_point_play)

    def two_point_go(self, play, pl):
        """Step 4: the CPU shows its hand, then the try resolves."""
        self.clear_panel()
        ptype, w, base, var = gd.OFF_PLAYS[play]
        scheme = random.choice(list(gd.DEF_PLAYS))
        chance = self.game.two_point_chance(pl, play, scheme, self.form)
        chem = gd.chemistry(pl, play)
        self.say(f"TWO-POINT TRY: {pl.slot} {pl.name} on the {play} "
                 f"from the {self.form['name']}. CPU shows {scheme}.")
        self.say(f"  chemistry {chem:.0f} {gd.chem_label(chem)} "
                 f"\u2022 conversion chance {chance:.0%}")
        tk.Label(self.panel, text=f"{self.form['name']}  \u2022  {play}", bg=BG,
                 fg=ORANGE, font=(FONT, 14, "bold")).pack(anchor="w", pady=(4, 0))
        tk.Label(self.panel, text=f"{pl.name}   chemistry {gd.chem_label(chem)}"
                                  f"   \u2022   CPU shows {scheme}",
                 bg=BG, fg=TXT, font=(FONT, 12)).pack(anchor="w", pady=2)
        tk.Label(self.panel, text=f"CONVERSION CHANCE  {chance:.0%}", bg=BG,
                 fg=GOLD, font=(FONT, 20, "bold")).pack(anchor="w", pady=(8, 2))
        # draw the bar before anyone gets to click it
        bar = tk.Canvas(self.panel, width=560, height=22, bg=PANEL2,
                        highlightthickness=0)
        bar.pack(anchor="w", pady=4)
        bar.create_rectangle(0, 0, 560 * chance, 22, fill=GRN if chance >= 0.5 else RED,
                             outline="")
        mkbtn(self.panel, "SNAP IT", lambda: self.two_point_resolve(pl, play, scheme, chance),
              bg=ORANGE, fg="#1a0c00", size=15, padx=44, pady=12).pack(pady=12)

    def two_point_resolve(self, pl, play, scheme, chance):
        ok = random.random() < chance
        gd.tick_fatigue([pl])
        if ok:
            self.me += 2
            self.say(f"  CONVERTED! {pl.name} gets in. Two points.")
            self.flash("2 POINTS!", GRN)
        else:
            self.say(f"  STOPPED short by {scheme}. No points.")
            self.flash("NO GOOD", RED)
        self.later(1600, self.end_possession)

    def choose_extra_point(self):
        self.clear_panel()
        self.title("TOUCHDOWN! Six points \u2013 how do you want the extra?", GOLD)
        row = tk.Frame(self.panel, bg=BG)
        row.pack(anchor="w", pady=6)
        mkbtn(row, "KICK THE PAT  (+1)", lambda: self.pat(False),
              bg=GRN, fg="#04180c", size=13, padx=24, pady=10).pack(side="left", padx=6)
        mkbtn(row, "GO FOR TWO  (+2)", lambda: self.pat(True),
              bg=ORANGE, fg="#1a0c00", size=13, padx=24, pady=10).pack(side="left", padx=6)
        tk.Label(self.panel, text="The PAT uses the kicking meter from 20 yards.\n"
                                  "The two-point try is a real snap: formation, play, then "
                                  "chemistry against the CPU's call.",
                 bg=BG, fg=DIM, font=(FONT, 10)).pack(anchor="w", pady=6)

    def run_offense(self, play, pl):
        self.clear_panel()
        ptype, w, base, var = gd.OFF_PLAYS[play]
        heavy = self.down == 4
        power, pname = self.take_power()
        scheme = random.choice(list(gd.DEF_PLAYS))
        def_mod = gd.DEF_PLAYS[scheme][1][ptype]
        drat = self.game.cpu_def + def_mod + random.randint(-8, 8)
        self.say(f"{self.form['name']}: {pl.slot} {pl.name} on the {play}. CPU shows {scheme}."
                 + (f"   You used {pname}." if pname else ""))
        # the CPU's call sets the base band; a completed chain can lift it
        band, band_note = self.game.chain_band(play, def_mod)
        chain_hit = band > gd.defence_band(def_mod)[0]
        yards, ev = gd.resolve(gd.eff_rate(pl, w, heavy), drat, ptype, base, var,
                               power, self.game.weather, band=band, chain=chain_hit)
        gd.tick_fatigue([pl])

        if ev == "INT":
            self.say("INTERCEPTED! Possession lost.")
            self.flash("INTERCEPTED!", RED)
            return self.end_possession()
        if ev == "FUM":
            self.say(f"{pl.name} FUMBLES! Turnover.")
            self.flash("FUMBLE!", RED)
            return self.end_possession()
        # show the chain on the field and in the log, so it is never missed
        broke = ev in ("HOUSE", "BREAKAWAY", "BIG RUN")
        if chain_hit:
            self.say(f"  CHAIN FIRED: {band_note}  (band {band})")
            self.chain_popup(band_note, band, broke)
        elif band > 0:
            self.say(f"  {band_note}  (band {band})")
        if broke:
            self.say(f"  {ev}! The defence was punished.")
        self.say(f"{pl.name} \u2013 {play}: " + ("incomplete" if ev else f"{yards:+d} yds"))
        self.earned += max(0, yards) // 3
        self.pos += yards
        if self.pos >= 100:
            self.pos = 100
            self.me += 6
            self.earned += 20
            return self.move_to(100, lambda: (self.say("TOUCHDOWN! Six points."),
                                              self.flash("TOUCHDOWN!", GOLD),
                                              self.choose_extra_point()))
        if self.pos <= 0:
            self.pos = 0
            self.cpu += 2
            return self.move_to(0, lambda: (self.say("SAFETY... CPU +2"),
                                            self.flash("SAFETY", RED), self.end_possession()))
        self.togo -= yards
        fd = False
        if self.togo <= 0:
            self.down, self.togo, fd = 1, min(10, 100 - self.pos), True
        else:
            self.down += 1
            if self.down > 4:
                return self.move_to(self.pos, lambda: (self.say("Turnover on downs."),
                                                       self.flash("TURNOVER ON DOWNS", RED),
                                                       self.end_possession()))

        def done():
            if fd:
                self.say("FIRST DOWN!")
                self.flash("FIRST DOWN!", GOLD)
            self.form_menu()
        self.move_to(self.pos, done)

    # ---- defense
    def cpu_snap(self):
        self.hud()
        self.clear_panel()
        if self.down == 4 and self.pos >= 62 and random.random() < 0.8:
            if random.random() < 0.6:
                self.say("CPU kicks a field goal. Good. CPU +3")
                self.cpu += 3
                self.flash("CPU FIELD GOAL", RED)
            else:
                self.say("CPU field goal missed!")
                self.flash("NO GOOD!", GRN)
            return self.end_possession()
        if self.down == 4 and self.pos < 62 and random.random() < 0.7:
            self.say("CPU punts.")
            self.flash("CPU PUNT", DIM)
            return self.end_possession()
        self.cpu_play = random.choice(list(gd.OFF_PLAYS))
        ptype = gd.OFF_PLAYS[self.cpu_play][0]
        self.say(f"CPU runs {self.cpu_play} ({ptype}). Call your formation.")
        self.title(f"CPU shows {self.cpu_play.upper()} ({ptype}) \u2013 pick a formation", RED)
        row = tk.Frame(self.panel, bg=BG)
        row.pack(fill="x")
        for fm in gd.roll_formations(defense=True):
            choice_tile(row, fm["name"],
                        [(f"on field: {', '.join(fm['slots'])}", DIM),
                         (f"scheme bonus +{fm.get('bonus', 0)}", GRN)],
                        lambda fm=fm: self.def_play_menu(fm), RED)

    def def_play_menu(self, form):
        self.form = form
        self.clear_panel()
        ptype = gd.OFF_PLAYS[self.cpu_play][0]
        self.title(f"{form['name']} \u2013 defensive play vs {self.cpu_play}", RED)
        row = tk.Frame(self.panel, bg=BG)
        row.pack(fill="x")
        for name in gd.roll_plays(form):
            dw, mods = gd.DEF_PLAYS[name]
            m = mods[ptype]
            choice_tile(row, name,
                        [(" \u2022 ".join(k.upper() for k in dw), GOLD),
                         (f"vs this play: {m:+d}", GRN if m > 0 else (RED if m < 0 else DIM))],
                        lambda n=name: self.def_pick(n), RED)
        mkbtn(self.panel, "\u25c0 Formations", self.cpu_snap, bg=PANEL2, fg=TXT,
              size=10, pady=4).pack(anchor="w", pady=6)

    def def_pick(self, scheme):
        self.play = scheme
        dw = gd.DEF_PLAYS[scheme][0]
        pool = gd.eligible(self.prof.lineup.player_pool(), self.form, None, "DEF")
        self.pick_player(pool, dw, f"{scheme} \u2013 who anchors the defense?",
                         lambda pl: self.run_defense(scheme, pl),
                         lambda: self.def_play_menu(self.form), heavy=self.down == 4)

    def run_defense(self, scheme, pl):
        self.clear_panel()
        play = self.cpu_play
        ptype, w, base, var = gd.OFF_PLAYS[play]
        heavy = self.down == 4
        power, pname = self.take_power()
        my_def = gd.def_rating(pl, scheme, ptype, self.form, heavy)
        orat = self.game.cpu_off + random.randint(-8, 8)
        yards, ev = gd.resolve_def(orat, my_def, ptype, base, var, power)
        gd.tick_fatigue([pl])
        if pname:
            self.say(f"You used {pname}.")
        if ev == "INT":
            self.say(f"{pl.name} INTERCEPTS! Big stop.")
            self.earned += 10
            self.flash("INTERCEPTION!", GRN)
            return self.end_possession()
        if ev == "FUM":
            self.say(f"{pl.name} forces a FUMBLE!")
            self.earned += 10
            self.flash("FORCED FUMBLE!", GRN)
            return self.end_possession()
        self.say(f"{pl.name} defends: " + ("incomplete" if ev else f"{yards:+d} yds allowed"))
        if yards <= 1:
            self.earned += 3
        self.pos += yards
        if self.pos >= 100:
            self.pos = 100
            self.cpu += 7
            return self.move_to(100, lambda: (self.say("CPU touchdown. Touchdown and the "
                                                       "extra point: CPU +7"),
                                              self.flash("CPU TOUCHDOWN", RED),
                                              self.end_possession()))
        if self.pos <= 0:
            self.pos = 0
            self.me += 2
            return self.move_to(0, lambda: (self.say("SAFETY! You score 2."),
                                            self.flash("SAFETY! +2", GRN), self.end_possession()))
        self.togo -= yards
        fd = False
        if self.togo <= 0:
            self.down, self.togo, fd = 1, min(10, 100 - self.pos), True
        else:
            self.down += 1
            if self.down > 4:
                return self.move_to(self.pos, lambda: (self.say("Turnover on downs! Great stand."),
                                                       self.flash("STOPPED ON DOWNS!", GRN),
                                                       self.end_possession()))

        def done():
            if fd:
                self.say("CPU first down.")
            self.cpu_snap()
        self.move_to(self.pos, done)

    def finish(self):
        self.hud()
        self.clear_panel()
        for w in self.handbar.winfo_children():
            w.destroy()
        if self.me > self.cpu:
            head, col, extra = "VICTORY!", GOLD, "The next opponent gets tougher."
            self.earned += 60
            self.prof.level += 1
        elif self.me < self.cpu:
            head, col, extra = "DEFEAT", RED, "Upgrade your deck and run it back."
        else:
            head, col, extra = "TIE GAME", ACC, "Nobody blinked."
            self.earned += 20
        self.prof.coins += self.earned
        self.hud()
        self.flash(head, col)
        tk.Label(self.panel, text=f"{head}   {self.me} \u2013 {self.cpu}", bg=BG, fg=col,
                 font=(FONT, 28, "bold")).pack(pady=(14, 2))
        tk.Label(self.panel, text=f"Earned {self.earned} coins  \u2022  Total {self.prof.coins}\n{extra}",
                 bg=BG, fg=TXT, font=(FONT, 13)).pack()
        row = tk.Frame(self.panel, bg=BG)
        row.pack(pady=14)
        mkbtn(row, "CARD LIBRARY", self.app.show_library, bg=PINK, fg="#1a0418").pack(side="left", padx=6)
        mkbtn(row, "VISIT THE SHOP", self.app.show_shop, bg=GOLD, fg="#1a1200").pack(side="left", padx=6)
        mkbtn(row, "PLAY AGAIN", self.app.show_game, bg=ACC).pack(side="left", padx=6)
        mkbtn(row, "MENU", self.app.show_menu, bg=PANEL2, fg=TXT).pack(side="left", padx=6)


# ---------------------------------------------------------------- lineup screen
class LineupScreen:
    def __init__(self, app):
        self.app, self.prof = app, app.prof
        self.lu = app.prof.lineup
        self.lu.sync()
        nav_bar(app, "lineup")
        f = app.main

        head = tk.Frame(f, bg=BG)
        head.pack(fill="x", padx=16, pady=(4, 2))
        tk.Label(head, text="LINEUP", bg=BG, fg=ACC, font=(FONT, 24, "bold")).pack(side="left")
        self.count = tk.Label(head, text="", bg=BG, fg=TXT, font=(FONT, 12, "bold"))
        self.count.pack(side="left", padx=16)
        mkbtn(head, "SELECT ALL", self.all_on, bg=GRN, size=10, pady=5).pack(side="right", padx=4)
        mkbtn(head, "CLEAR", self.all_off, bg=PANEL2, fg=TXT, size=10, pady=5).pack(side="right", padx=4)
        tk.Label(f, text="Click a card to add or remove it. Only what you select here is used in a game.",
                 bg=BG, fg=DIM, font=(FONT, 10)).pack(anchor="w", padx=16)
        self.warn = tk.Label(f, text="", bg=BG, fg=ORANGE, font=(FONT, 10, "bold"))
        self.warn.pack(anchor="w", padx=16)

        outer, self.body = vscroll(f, 620)
        outer.pack(fill="both", expand=True, padx=14, pady=4)
        mkbtn(f, "\u25b6  PLAY WITH THIS LINEUP", self.play, size=14, padx=50, pady=10).pack(pady=8)
        self.render()

    def render(self):
        for w in self.body.winfo_children():
            w.destroy()
        self.prof.dedupe_slots()      # never draw the same card twice
        for unit, col, label in (("OFF", ACC, "OFFENSE"), ("DEF", RED, "DEFENSE"),
                                 ("ST", ORANGE, "SPECIAL TEAMS")):
            owned = [p for p in self.prof.roster if p.unit == unit]
            tk.Label(self.body, text=f"{label}   ({len(owned)} owned)", bg=BG,
                     fg=col, font=(FONT, 12, "bold")).pack(anchor="w", pady=(8, 2))
            if not owned:
                tk.Label(self.body, text="  no cards", bg=BG, fg=DIM,
                         font=(FONT, 10)).pack(anchor="w")
            for pl in self.prof.depth_chart(unit):
                self.row_for(pl)

        tk.Label(self.body, text=f"POWER-UP DECK   ({len(self.prof.powerups)} cards)", bg=BG,
                 fg=PINK, font=(FONT, 12, "bold")).pack(anchor="w", pady=(12, 2))
        if not self.prof.powerups:
            tk.Label(self.body, text="  no power-ups yet - open a pack in the shop",
                     bg=BG, fg=DIM, font=(FONT, 10)).pack(anchor="w")
        grid = tk.Frame(self.body, bg=BG)
        grid.pack(anchor="w", fill="x")
        for i, card in enumerate(self.prof.powerups):
            if i and i % 5 == 0:
                grid = tk.Frame(self.body, bg=BG)
                grid.pack(anchor="w", fill="x")
            on = card.uid in self.lu.powers
            PowerTile(grid, card, cmd=self.toggle_power,
                      badge="IN DECK" if on else "SIDELINED",
                      dim=not on).pack(side="left", padx=4, pady=4)
        self.update_counts()

    def row_for(self, pl):
        """One player per row: portrait, stats, and a big on/off switch."""
        on = pl.uid in self.lu.players
        col = tier_color(ovr(pl))
        unitcol = ACC if pl.unit == "OFF" else (RED if pl.unit == "DEF" else GRN)
        row = tk.Frame(self.body, bg=PANEL if on else "#0d1425",
                       highlightthickness=2,
                       highlightbackground=col if on else "#334155")
        row.pack(fill="x", pady=3)

        # on/off switch on the far left
        sw = tk.Frame(row, bg=GRN if on else "#334155", padx=12, pady=18, cursor="hand2")
        sw.pack(side="left", fill="y")
        tk.Label(sw, text="IN" if on else "OUT", bg=GRN if on else "#334155",
                 fg="#041018" if on else DIM, font=(FONT, 12, "bold")).pack()
        tk.Label(sw, text="\u2714" if on else "\u2718", bg=GRN if on else "#334155",
                 fg="#041018" if on else DIM, font=(FONT, 15, "bold")).pack()

        # pixel portrait
        art = POS_ART.get(pl.pos, BALLER)
        cv = tk.Canvas(row, width=64, height=76, bg=row["bg"], highlightthickness=0)
        cv.pack(side="left", padx=(8, 4))
        cv.create_rectangle(0, 0, 64, 76, fill="#123a1f" if pl.unit == "OFF" else "#3a1220",
                            outline="")
        px(cv, art, 4, 4, 4, PAL)

        # name block
        name = tk.Frame(row, bg=row["bg"], width=170)
        name.pack(side="left", padx=4)
        tk.Label(name, text=pl.name, bg=row["bg"], fg=TXT if on else DIM,
                 font=(FONT, 12, "bold")).pack(anchor="w")
        tk.Label(name, text=f"{pl.slot}   overall {ovr(pl)}", bg=row["bg"], fg=unitcol,
                 font=(FONT, 10, "bold")).pack(anchor="w")
        pen = gd.fatigue_penalty(pl)
        tk.Label(name, text=(f"TIRED -{pen}" if pen else "RESTED"), bg=row["bg"],
                 fg=ORANGE if pen else DIM, font=(FONT, 9, "bold")).pack(anchor="w")

        # attribute bars
        bars = tk.Frame(row, bg=row["bg"])
        bars.pack(side="left", padx=6)
        for s in gd.STATS:
            v = pl.st[s]
            cell = tk.Frame(bars, bg=row["bg"])
            cell.pack(anchor="w")
            tk.Label(cell, text=s.upper(), bg=row["bg"], fg=DIM, width=4,
                     font=(PIX, 8, "bold")).pack(side="left")
            bar = tk.Canvas(cell, width=150, height=9, bg=BG, highlightthickness=0)
            bar.pack(side="left", padx=3)
            bar.create_rectangle(0, 0, 150 * v / 99, 9, fill=unitcol, outline="")
            tk.Label(cell, text=str(v), bg=row["bg"], fg=TXT, width=3,
                     font=(PIX, 8, "bold")).pack(side="left")

        # status badge
        tk.Label(row, text="IN LINEUP" if on else "BENCHED", bg=GRN if on else "#475569",
                 fg="#041018" if on else TXT, font=(FONT, 11, "bold"),
                 padx=14, pady=10).pack(side="right", padx=10)

        for wd in [row, sw, name, bars]:
            wd.bind("<Button-1>", lambda e, p=pl: self.toggle_player(p))

    def update_counts(self):
        self.count.config(text=f"{len(self.lu.player_pool())} players in  \u2022  "
                               f"{len(self.lu.power_pool())} power-ups in")
        missing = []
        for fm in gd.FORMATIONS:
            for s in fm["slots"]:
                if not any(p.slot == s and p.uid in self.lu.players for p in self.prof.roster):
                    missing.append(s)
        uniq = sorted(set(missing))
        self.warn.config(text=("No player selected for: " + ", ".join(uniq)
                               + "  \u2013 those formations will have gaps.") if uniq else "")

    def toggle_player(self, pl):
        self.lu.toggle_player(pl)
        self.render()

    def toggle_power(self, card):
        self.lu.toggle_power(card)
        self.render()

    def all_on(self):
        self.lu.autofill()
        self.render()

    def all_off(self):
        self.lu.clear()
        self.render()

    def play(self):
        if not self.lu.player_pool():
            self.warn.config(text="Select at least one player before playing.")
            return
        self.app.show_game()


# ---------------------------------------------------------------- library screen
class LibraryScreen:
    def __init__(self, app):
        self.app, self.prof = app, app.prof
        self.prof.lineup.sync()
        nav_bar(app, "library")
        f = app.main
        self.sel_player, self.sel_power, self.msg = None, None, ""
        self.promote_target = None

        head = tk.Frame(f, bg=BG)
        head.pack(fill="x", padx=16, pady=(4, 2))
        tk.Label(head, text="CARD LIBRARY", bg=BG, fg=PINK, font=(FONT, 24, "bold")).pack(side="left")
        self.stat = tk.Label(head, text="", bg=BG, fg=TXT, font=(FONT, 12, "bold"))
        self.stat.pack(side="left", padx=16)
        self.coinsl = tk.Label(head, text="", bg=BG, fg=GOLD, font=(FONT, 14, "bold"))
        self.coinsl.pack(side="right")
        self.msgbar = tk.Label(f, text="", bg=BG, fg=TXT, font=(FONT, 11, "bold"))
        self.msgbar.pack(anchor="w", padx=16, pady=(2, 0))

        outer, self.body = vscroll(f, 600)
        self.scroller = outer
        outer.pack(fill="both", expand=True, padx=14, pady=4)
        mkbtn(f, "\u25c0 BACK TO MENU", app.show_menu, bg=PANEL2, fg=TXT,
              size=11).pack(side="bottom", pady=12)
        self.render()

    def render(self):
        for w in self.body.winfo_children():
            w.destroy()
        p = self.prof
        p.dedupe_slots()      # never draw the same card twice
        self.stat.config(text=f"{len(p.roster)} player cards  \u2022  {len(p.powerups)} power-up cards")
        self.coinsl.config(text=f"\u25cf {p.coins} coins")
        self.msgbar.config(text=self.msg)
        # the same message inside the scroll area, so it's visible wherever you are
        if self.msg:
            tk.Label(self.body, text=self.msg, bg=PANEL2, fg=GOLD, font=(FONT, 11, "bold"),
                     padx=12, pady=8, anchor="w").pack(fill="x", pady=(0, 6))
        tk.Label(self.body, text="Click a card to sell it or promote it. Promotions move a player "
                                 "into a starter slot, and the man he replaces takes his old slot.",
                 bg=BG, fg=DIM, font=(FONT, 9)).pack(anchor="w", pady=(0, 4))

        for unit, col, label in (("OFF", ACC, "OFFENSE"), ("DEF", RED, "DEFENSE"),
                                 ("ST", ORANGE, "SPECIAL TEAMS")):
            tk.Label(self.body, text=f"{label}   ({len(p.depth_chart(unit))} cards)", bg=BG,
                     fg=col, font=(FONT, 11, "bold")).pack(anchor="w", pady=(8, 0))
            grid = tk.Frame(self.body, bg=BG)
            grid.pack(anchor="w")
            per_row = 6
            dealing = getattr(self, "slot_target", None)
            for i, pl in enumerate(p.depth_chart(unit)):
                if i and i % per_row == 0:
                    grid = tk.Frame(self.body, bg=BG)
                    grid.pack(anchor="w")
                # the selected card's place is taken over by its action panel
                if dealing is pl:
                    self.action_panel(grid, pl)
                    continue
                PlayerCard(grid, pl, cmd=lambda x: self.select_player(x),
                           badge=f"SELL {pl.value()}c", badge_col=GOLD,
                           art_size=4).pack(side="left", padx=4, pady=3)

        tk.Label(self.body, text=f"POWER-UP CARDS   ({len(p.powerups)} owned)",
                 bg=BG, fg=PINK, font=(FONT, 11, "bold")).pack(anchor="w", pady=(12, 0))
        grid = tk.Frame(self.body, bg=BG)
        grid.pack(anchor="w")
        dealing_power = getattr(self, "slot_power_target", None)
        for i, card in enumerate(sorted(p.powerups, key=lambda c: c.name)):
            if i and i % 5 == 0:
                grid = tk.Frame(self.body, bg=BG)
                grid.pack(anchor="w")
            if dealing_power is not None and dealing_power is card:
                self.action_panel(grid, None, card)
                continue
            PowerTile(grid, card, lambda c=card: self.select_power(c),
                      badge=f"sell {card.value()}c").pack(side="left", padx=4, pady=4)

    def action_panel(self, parent, pl=None, card=None):
        """The sell / promote panel, drawn in place of the card you clicked."""
        if pl is not None:
            col = tier_color(ovr(pl))
            bgc = PANEL
            head = f"{pl.name}"
            sub = f"{pl.slot}  \u2022  overall {ovr(pl)}"
            price = pl.value()
        else:
            col = PowerTile.COL[card.kind]
            bgc = PANEL2
            head = card.name
            sub = card.desc
            price = card.value()

        panel = tk.Frame(parent, bg=bgc, highlightthickness=3, highlightbackground=GOLD)
        panel.pack(side="left", padx=4, pady=3)

        head_box = tk.Frame(panel, bg=bgc, padx=8, pady=6)
        head_box.pack(fill="x")
        tk.Label(head_box, text=head, bg=bgc, fg=TXT, font=(FONT, 11, "bold"),
                 wraplength=180, justify="left").pack(anchor="w")
        tk.Label(head_box, text=sub, bg=bgc, fg=col, font=(FONT, 9, "bold"),
                 wraplength=180, justify="left").pack(anchor="w")

        btns = tk.Frame(panel, bg=bgc)
        btns.pack(fill="x", padx=6, pady=(0, 6))
        mkbtn(btns, f"SELL  {price}c", lambda: self.confirm_sale(pl, card),
              bg=RED, fg="#fff", size=10, padx=12, pady=7).pack(fill="x", pady=2)

        if pl is not None:
            mine = gd.slot_pos(pl.slot) or pl.pos
            starters = [s for s in gd.ALL_SLOTS
                        if gd.slot_pos(s) == mine and not gd.is_backup(s)]
            if starters:
                mkbtn(btns, "PROMOTE", lambda: self.toggle_promote(starters),
                      bg=GRN, fg="#04180c", size=10, padx=12, pady=7).pack(fill="x", pady=2)
            if getattr(self, "promote_open", False):
                self.promote_picker(panel)

        mkbtn(btns, "CANCEL", self.cancel, bg=PANEL2, fg=TXT, size=10,
              padx=12, pady=6).pack(fill="x", pady=2)

    def promote_picker(self, panel):
        """Inline starter-slot choices, shown under the promote button."""
        pl = self.slot_target
        mine = gd.slot_pos(pl.slot) or pl.pos
        starters = [s for s in gd.ALL_SLOTS
                    if gd.slot_pos(s) == mine and not gd.is_backup(s)]
        box = tk.Frame(panel, bg=PANEL2, padx=6, pady=6,
                       highlightthickness=2, highlightbackground=GRN)
        box.pack(fill="x", padx=6, pady=(0, 6))
        tk.Label(box, text="Promote into:", bg=PANEL2, fg=GRN,
                 font=(FONT, 9, "bold")).pack(anchor="w")
        for s in starters:
            here = self.prof.at_slot(s)
            mkbtn(box, f"{s}  ({here.name if here else 'empty'})",
                  lambda s=s: self.do_promote_inline(s),
                  bg=GRN, fg="#04180c", size=9, padx=8, pady=5).pack(fill="x", pady=2)

    def toggle_promote(self, starters):
        self.promote_open = not getattr(self, "promote_open", False)
        self.render()

    def do_promote_inline(self, slot):
        ok, msg = self.prof.promote(self.slot_target, slot)
        self.msg = msg
        self.clear_selection()
        self.render()

    def clear_selection(self):
        self.sel_player, self.sel_power = None, None
        self.slot_target, self.slot_power_target = None, None
        self.promote_open = False

    def confirm_sale(self, pl, card):
        if pl is not None:
            ok, msg = self.prof.sell_player(pl)
        else:
            ok, msg = self.prof.sell_power(card)
        self.msg = msg
        self.clear_selection()
        self.render()
        try:
            self.scroller.reset_view()
        except Exception:
            pass

    def promote_menu(self, starters):
        pl = self.sel_player
        win = tk.Toplevel(self.app.root)
        win.title("Promote to starter")
        win.configure(bg=BG)
        tk.Label(win, text=f"Promote {pl.name} ({pl.slot}) into which starter slot?",
                 bg=BG, fg=TXT, font=(FONT, 12, "bold"), padx=16, pady=12).pack()
        row = tk.Frame(win, bg=BG)
        row.pack(padx=16, pady=(0, 14))
        for s in starters:
            here = self.prof.at_slot(s)
            mkbtn(row, f"{s}\n{here.name if here else 'empty'}",
                  lambda s=s: self.do_promote(s, win),
                  bg=GRN, fg="#04180c", size=10, padx=12, pady=8).pack(side="left", padx=5)
        mkbtn(row, "CANCEL", win.destroy, bg=PANEL2, fg=TXT, size=10, padx=12, pady=8).pack(side="left", padx=5)

    def do_promote(self, slot, win):
        ok, msg = self.prof.promote(self.sel_player, slot)
        self.msg = msg
        self.sel_player, self.sel_power = None, None
        win.destroy()
        self.render()

    def select_player(self, pl):
        """Swap the clicked card for its action panel, right where it sat."""
        was = getattr(self, "slot_target", None)
        self.clear_selection()
        if was is not pl:
            self.slot_target = pl
        self.render()

    def select_power(self, card):
        was = getattr(self, "slot_power_target", None)
        self.clear_selection()
        if was is not card:
            self.slot_power_target = card
        self.render()

    def cancel(self):
        self.clear_selection()
        self.render()


# ---------------------------------------------------------------- app
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GRIDIRON DECK")
        self.root.geometry("1120x940")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self.prof = gd.Profile()
        self.main = tk.Frame(self.root, bg=BG)
        self.main.pack(fill="both", expand=True)
        self.pack_offers, self.pack_kind, self.pack_cost = None, None, 0
        self.shop_msg = ""
        self.show_menu()

    def reset(self):
        for w in self.main.winfo_children():
            w.destroy()

    def run(self):
        self.root.mainloop()

    # ---- home / menu
    def home_nav(self):
        """Tab strip for every screen except the game, HOME included."""
        bar = tk.Frame(self.main, bg=PANEL)
        bar.pack(fill="x", padx=14, pady=(12, 6))
        for name, key, fn in (("HOME", "home", self.show_menu),
                              ("LINEUP", "lineup", self.show_lineup),
                              ("CARD LIBRARY", "library", self.show_library),
                              ("PRO SHOP", "shop", self.show_shop),
                              ("PLAY", "game", self.show_game)):
            on = key == getattr(self, "active", None)
            mkbtn(bar, name, fn, bg=ACC if on else PANEL2,
                  fg="#041018" if on else TXT, size=11, pady=7).pack(side="left", padx=4)
        tk.Label(bar, text=f"\u25cf {self.prof.coins} coins", bg=PANEL, fg=GOLD,
                 font=(FONT, 13, "bold")).pack(side="right", padx=10)
        mkbtn(bar, "QUIT", self.root.destroy, bg=RED, fg="#fff", size=11,
              padx=14, pady=7).pack(side="right", padx=8)
        return bar

    def show_menu(self):
        self.reset()
        self.active = "home"
        self.home_nav()
        cv = tk.Canvas(self.main, width=1120, height=290, bg=BG, highlightthickness=0)
        cv.pack()
        for i in range(0, 1120, 80):
            cv.create_polygon(i, 290, i + 40, 0, i + 80, 0, i + 40, 290,
                              fill="#0f1a30" if (i // 80) % 2 else "#0c1426", outline="")
        cv.create_rectangle(0, 234, 1120, 240, fill=GOLD, outline="")
        cv.create_text(563, 113, text="GRIDIRON DECK", fill="#000", font=(FONT, 54, "bold"))
        cv.create_text(560, 110, text="GRIDIRON DECK", fill=ACC, font=(FONT, 54, "bold"))
        cv.create_text(560, 172, text="BUILD YOUR DECK  \u2022  SET YOUR LINEUP  \u2022  TRADE CARDS",
                       fill=GOLD, font=(FONT, 13, "bold"))
        px(cv, QB_ART, 500, 190, 5, PAL)
        # build stamp, bottom-right of the banner
        cv.create_text(1108, 276, text=VERSION_LINE, anchor="e",
                       fill=DIM, font=(PIX, 10, "bold"))
        p = self.prof
        tk.Label(self.main, text=f"Level {p.level} opponent   \u2022   {p.coins} coins   \u2022   "
                                 f"{len(p.off_roster())} offensive / {len(p.def_roster())} defensive"
                                 f"   \u2022   {len(p.powerups)} power-ups",
                 bg=BG, fg=TXT, font=(FONT, 12, "bold")).pack(pady=(10, 8))
        mkbtn(self.main, "\u25b6  PLAY GAME", self.show_game, size=17, padx=58, pady=11).pack(pady=4)
        row = tk.Frame(self.main, bg=BG)
        row.pack(pady=4)
        mkbtn(row, "LINEUP", self.show_lineup, bg=GRN, fg="#04180c", size=13,
              padx=40, pady=9).pack(side="left", padx=5)
        mkbtn(row, "CARD LIBRARY", self.show_library, bg=PINK, fg="#1a0418", size=13,
              padx=34, pady=9).pack(side="left", padx=5)
        mkbtn(row, "PRO SHOP", self.show_shop, bg=GOLD, fg="#1a1200", size=13,
              padx=44, pady=9).pack(side="left", padx=5)
        mkbtn(self.main, "QUIT", self.root.destroy, bg=PANEL2, fg=TXT,
              size=11, padx=70, pady=6).pack(pady=8)

    def show_game(self):
        self.reset()
        self.active = "game"
        GameScreen(self, self.prof)

    def show_lineup(self):
        self.reset()
        self.active = "lineup"
        LineupScreen(self)

    def show_library(self):
        self.reset()
        self.active = "library"
        LibraryScreen(self)

    # ---- shop with packs
    def show_shop(self):
        self.reset()
        nav_bar(self, "shop")
        p, f = self.prof, self.main
        head = tk.Frame(f, bg=BG)
        head.pack(fill="x", padx=16, pady=(4, 2))
        tk.Label(head, text="PRO SHOP", bg=BG, fg=GOLD, font=(FONT, 24, "bold")).pack(side="left")
        tk.Label(head, text="  every pack shows 3 cards \u2014 you keep one",
                 bg=BG, fg=DIM, font=(FONT, 11)).pack(side="left", padx=8)

        if self.pack_offers:
            self.render_pack()
            return

        # three columns of packs, by card type
        for kind, col, label in (("player", ACC, "PLAYER PACKS"),
                                 ("power", PINK, "POWER PACKS"),
                                 ("upgrade", GRN, "UPGRADE PACKS")):
            colframe = tk.Frame(f, bg=BG)
            colframe.pack(side="left", fill="y", padx=10, anchor="n")
            tk.Label(colframe, text=label, bg=BG, fg=col,
                     font=(FONT, 13, "bold")).pack(anchor="w", pady=(4, 4))
            for pack in [x for x in gd.PACKS if x["kind"] == kind]:
                odds = gd.ODDS[pack["odds"]]
                t = tk.Frame(colframe, bg=PANEL2, cursor="hand2", padx=16, pady=10,
                             highlightthickness=3, highlightbackground=col)
                t.pack(fill="x", pady=5)
                tk.Label(t, text=pack["name"].upper(), bg=PANEL2, fg=col,
                         font=(FONT, 12, "bold")).pack(anchor="w")
                tk.Label(t, text=pack["blurb"], bg=PANEL2, fg=TXT,
                         font=(FONT, 9)).pack(anchor="w")
                od = tk.Frame(t, bg=PANEL2)
                od.pack(anchor="w", pady=3)
                for r in gd.RARITY_ORDER:
                    tk.Label(od, text=f"{gd.RARITY[r]['label'][:4]} {odds.get(r, 0)}%",
                             bg=PANEL2, fg=gd.RARITY[r]["colour"],
                             font=(PIX, 8, "bold"), padx=3).pack(side="left")
                tk.Label(t, text=f"{pack['cost']} coins", bg=PANEL2,
                         fg=GOLD if p.coins >= pack["cost"] else RED,
                         font=(FONT, 12, "bold")).pack(anchor="w", pady=(2, 0))
                for wd in [t] + t.winfo_children() + od.winfo_children():
                    wd.bind("<Button-1>", lambda e, pk=pack: self.buy_pack(pk))
        tk.Label(f, text=self.shop_msg, bg=BG, fg=GOLD,
                 font=(FONT, 12, "bold")).pack(side="bottom", pady=6)
        mkbtn(f, "\u25c0 BACK TO MENU", self.show_menu, bg=PANEL2, fg=TXT,
              size=11).pack(side="bottom", pady=8)

    def buy_pack(self, pack):
        if self.prof.coins < pack["cost"]:
            self.shop_msg = "Not enough coins."
            self.show_shop()
            return
        offers = gd.open_pack(self.prof, pack["kind"], pack["odds"])
        if not offers:
            self.shop_msg = "No room - every slot is full."
            self.show_shop()
            return
        self.prof.coins -= pack["cost"]
        self.pack_offers, self.pack_kind, self.pack_cost = offers, pack["kind"], pack["cost"]
        self.pack_name = pack["name"]
        self.show_shop()

    def render_pack(self):
        f = self.main
        tk.Label(f, text=f"{self.pack_name.upper()} \u2013 pick ONE of the three",
                 bg=BG, fg=GOLD, font=(FONT, 20, "bold")).pack(pady=(14, 6))
        tk.Label(f, text="Rarity colours:  C common  \u2022  R rare  \u2022  E epic  \u2022  L legendary",
                 bg=BG, fg=DIM, font=(FONT, 10)).pack()
        row = tk.Frame(f, bg=BG)
        row.pack(pady=10)
        for offer in self.pack_offers:
            rar = gd.RARITY[offer["rarity"]]
            col = rar["colour"]
            card = tk.Frame(row, bg=PANEL2, padx=16, pady=12, highlightthickness=4,
                            highlightbackground=col, cursor="hand2")
            card.pack(side="left", padx=10)
            tk.Label(card, text=rar["label"], bg=col, fg="#041018",
                     font=(PIX, 10, "bold"), padx=10, pady=2).pack(fill="x")
            if self.pack_kind == "player":
                pl = offer["player"]
                cv = tk.Canvas(card, width=96, height=84, bg=PANEL2, highlightthickness=0)
                cv.pack(pady=4)
                cv.create_rectangle(4, 2, 92, 82,
                                    fill="#123a1f" if pl.unit == "OFF" else "#3a1220", outline="")
                px(cv, POS_ART.get(pl.pos, BALLER), 16, 4, 4, PAL)
                tk.Label(card, text=offer["title"], bg=PANEL2, fg=col,
                         font=(FONT, 12, "bold")).pack()
                tk.Label(card, text=offer["sub"], bg=PANEL2, fg=TXT,
                         font=(FONT, 10)).pack()
                tk.Label(card, text=f"sell value {pl.value()}c", bg=PANEL2, fg=GOLD,
                         font=(FONT, 9)).pack()
            elif self.pack_kind == "power":
                cv = tk.Canvas(card, width=70, height=64, bg=PANEL2, highlightthickness=0)
                cv.pack(pady=4)
                px(cv, ICONS[gd.POWERUPS[offer["power"]][0]], 2, 2, 4, ICON_PAL)
                tk.Label(card, text=offer["title"], bg=PANEL2, fg=col,
                         font=(FONT, 12, "bold")).pack()
                tk.Label(card, text=offer["sub"], bg=PANEL2, fg=TXT,
                         font=(FONT, 10)).pack()
            else:
                tk.Label(card, text=offer["title"], bg=PANEL2, fg=col,
                         font=(FONT, 13, "bold")).pack(pady=(8, 0))
                tk.Label(card, text=offer["sub"], bg=PANEL2, fg=TXT,
                         font=(FONT, 11)).pack(pady=6)
            for wd in [card] + card.winfo_children():
                wd.bind("<Button-1>", lambda e, o=offer: self.take_offer(o))
        mkbtn(f, "SKIP THIS PACK", self.close_pack, bg=PANEL2, fg=TXT, size=11).pack(pady=16)

    def take_offer(self, offer):
        self.shop_msg = gd.apply_offer(self.prof, offer)
        self.pack_offers = None
        self.show_shop()

    def close_pack(self):
        self.shop_msg = "Pack skipped."
        self.pack_offers = None
        self.show_shop()


if __name__ == "__main__":
    App().run()
