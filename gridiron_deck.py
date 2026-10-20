#!/usr/bin/env python3
"""GRIDIRON DECK - backend: players, formations, plays, fatigue, weather,
kicking meter, lineup, packs.

Run the terminal version:   python3 gridiron_deck.py
The GUI (gridiron_gui.py) imports this module and uses the same rules.

NEW IN THIS BUILD
- WEATHER: clear / heavy rain / snow-cold / high wind. Rain raises fumble
  odds on runs and cuts deep-pass range; snow drains stamina faster and
  rewards fresh legs off the bench; bad weather tightens the kicking bar.
- KICKING METER: every field goal and every PAT is a timing bar. A marker
  sweeps the bar and you stop it - distance from centre decides accuracy.
  Longer kicks sweep faster; your kicker's kck sets the width of the good
  zone. Touchdowns are 6 points, then you kick the PAT (1) or go for 2.
- PLAY CHAINS: run the ball then call Play Action and the CPU's call sets
  your band, the chain can lift it, and a band-2 deep shot can go the
  distance. Chains add no flat yards - they raise the odds of a big play.
"""
# The number the GUI checks itself against. If the two files disagree the
# home screen says so, which catches the mixed-version problem before it
# turns into a crash mid-game. Keep this in step with gridiron_gui.py.
VERSION = "1.0.0"
VERSION_DATE = "2026-10-20"

import random

STATS = ["spd", "str", "pas", "hnd", "tak", "iq", "kck"]
OFF_POS = ["QB", "RB", "WR", "TE"]
DEF_POS = ["DL", "LB", "CB", "S"]
ST_POS = ["K"]

ALL_SLOTS = ["QB1", "QB2", "RB1", "RB2", "WR1", "WR2", "WR3", "TE1", "TE2",
             "DL1", "DL2", "LB1", "LB2", "CB1", "CB2", "S1", "S2", "K"]
MAX_PER_POS = {"QB": 2, "RB": 2, "WR": 3, "TE": 2, "DL": 2, "LB": 2, "CB": 2, "S": 2,
               "K": 1}

ALL_PLAYERS_REF = [[]]
_NEXT_UID = [1]

# the weather in force right now - fatigue reads this
_ACTIVE_WEATHER = ["clear"]


def new_uid():
    _NEXT_UID[0] += 1
    return _NEXT_UID[0]


def label(pos, n):
    return f"{pos}{n}"


def is_backup(slot):
    """True for "2"/"3" depth slots. A card with no slot yet counts as a
    starter, so a pack card can be priced before it is signed."""
    if not slot:
        return False
    return slot[-1] != "1"


def slot_pos(slot):
    """Position code for a slot name: "TE2" -> "TE", "TE3" -> "TE"."""
    if not slot:
        return ""
    out = []
    for ch in slot:
        if ch.isdigit():
            break
        if ch.isalpha():
            out.append(ch)
    return "".join(out)


def slot_num(slot):
    digits = "".join(c for c in slot if c.isdigit())
    return int(digits) if digits else 1


# ======================================================================
# WEATHER
# ======================================================================
# pass_range  - deep passes are capped to base * pass_range
# fumble      - added to the turnover roll, runs only
# kick        - percentage points taken off the kicking bar's good zone
# sweep       - multiplies how fast the meter marker travels
# stamina     - multiplies the fatigue penalty
# bench_bonus - snow rewards a rested backup (and penalises a worn starter)
WEATHER = {
    "clear": {
        "label": "CLEAR", "colour": "#38bdf8",
        "desc": "No effect. Ideal football weather.",
        "pass_range": 1.00, "fumble": 0.00, "kick": 0, "sweep": 1.00,
        "stamina": 1.00, "bench_bonus": 0,
    },
    "rain": {
        "label": "HEAVY RAIN", "colour": "#60a5fa",
        "desc": "Fumbles up on runs. Deep passes lose range. Kicking is harder.",
        "pass_range": 0.72, "fumble": 0.16, "kick": 9, "sweep": 1.18,
        "stamina": 1.10, "bench_bonus": 0,
    },
    "snow": {
        "label": "SNOW / COLD", "colour": "#e5edff",
        "desc": "Stamina drains fast. Fresh legs off the bench are rewarded.",
        "pass_range": 0.88, "fumble": 0.08, "kick": 7, "sweep": 1.10,
        "stamina": 1.75, "bench_bonus": 8,
    },
    "wind": {
        "label": "HIGH WIND", "colour": "#a3e635",
        "desc": "Kicking suffers badly. Deep balls float.",
        "pass_range": 0.78, "fumble": 0.02, "kick": 13, "sweep": 1.14,
        "stamina": 1.05, "bench_bonus": 0,
    },
}
WEATHER_ORDER = ["clear", "rain", "snow", "wind"]

# Base odds. Weather is rare early and gets commoner as the game wears on -
# see roll_weather(round_no=...). Round 1 is mostly clear.
WEATHER_ODDS = {"clear": 72, "rain": 15, "snow": 9}

# How hard the bad-weather share climbs per round past the first.
WEATHER_RAMP = 0.55


def _ramped(odds, round_no):
    """Shift weight out of "clear" and into the bad conditions as rounds pass."""
    base = dict(odds)
    steps = max(0, round_no - 1) * WEATHER_RAMP
    if steps:
        bad = [n for n in base if n != "clear" and base.get(n, 0) > 0]
        if bad:
            share = base.get("clear", 0) * min(0.85, steps / (steps + 1.0))
            base["clear"] = base.get("clear", 0) - share
            for n in bad:
                base[n] = base.get(n, 0) + share / len(bad)
    return base


def roll_weather(odds=None, round_no=1):
    """Pick a quarter's weather.

    Round 1 uses the base odds and is usually clear. Each round after that
    moves weight from clear into rain and snow, so late-round football is
    played in bad weather far more often. `round_no` is 1-based.
    """
    base = _ramped(odds or WEATHER_ODDS, round_no)
    names = [n for n in WEATHER_ORDER if base.get(n, 0) > 0] or ["clear"]
    weights = [base.get(n, 0) for n in names]
    return random.choices(names, weights=weights, k=1)[0]


def weather_table():
    """Chance of bad weather per round - used by the UI and for tuning."""
    out = []
    for r in range(1, 6):
        base = _ramped(WEATHER_ODDS, r)
        total = sum(base.values()) or 1
        out.append((r, 1.0 - base.get("clear", 0) / total))
    return out


def weather_of(key):
    return WEATHER.get(key, WEATHER["clear"])


def weather_line(key):
    w = weather_of(key)
    return f"{w['label']} - {w['desc']}"


def set_weather(key):
    """Set the weather the whole engine reads (fatigue included)."""
    _ACTIVE_WEATHER[0] = key if key in WEATHER else "clear"
    return _ACTIVE_WEATHER[0]


# ======================================================================
# KICKING METER
# ======================================================================
# The bar is a 0-100 scale with the sweet spot at 50. The marker sweeps it at
# a speed set by distance; you stop it, and how close you land to 50 decides
# the kick. `accuracy` is 0-100: 100 is a perfect strike, 0 is a shank.
KICK_ZONES = [
    # (max distance in yards, sweep speed, base half-width of the good zone)
    (25, 0.55, 13.0),     # PAT and chip shots - slow and forgiving
    (35, 0.85, 10.5),
    (45, 1.25, 8.0),
    (52, 1.70, 6.0),
    (999, 2.30, 4.5),     # 53+ is a prayer
]


def kick_zones_for(dist):
    """(sweep speed, good-zone half-width) for a kick of this distance."""
    for cap, speed, half in KICK_ZONES:
        if dist <= cap:
            return speed, half
    return KICK_ZONES[-1][1], KICK_ZONES[-1][2]


def kick_profile(kicker, dist, weather="clear"):
    """Everything the meter needs for one attempt.

    Returns a dict so the GUI can animate with the same numbers the terminal
    uses: `speed` for the marker, `half` for the green zone, `need` for the
    accuracy required to be good.
    """
    w = weather_of(weather)
    base_speed, base_half = kick_zones_for(dist)
    # a better kicker has a wider good zone to aim at
    skill = (kicker.st["kck"] - 60) / 40.0 if kicker else 0.0     # -1 .. +1
    half = base_half * (1 + skill * 0.30)
    half -= w["kick"] * 0.45                                      # weather bites
    half = max(1.6, half)
    speed = base_speed * w["sweep"]
    # the accuracy that counts as good enough, scaled by a pure kick skill
    need = 100.0 / (1 + (max(0.0, 62 - (kicker.st["kck"] if kicker else 60)) / 18.0))
    return {"speed": speed, "half": half, "need": need,
            "dist": dist, "weather": weather, "zone_label": f"+/-{half:.1f}"}


def kick_accuracy(marker, half, need):
    """Turn a stopped marker position into 0-100 accuracy.

    `marker` is where you stopped it on the 0-100 bar; 50 is dead centre.
    Landing inside the half-width is a clean strike, and it falls away
    sharply outside it.
    """
    off = abs(marker - 50.0)
    if off <= half:
        return 100.0
    over = off - half
    return max(0.0, 100.0 - over * (100.0 / max(1.0, 22.0)))


def kick_result(accuracy, need):
    """Did it go through? Plus how ugly it looked."""
    if accuracy >= need + 18:
        return True, "SPLIT THE UPRIGHTS"
    if accuracy >= need:
        return True, "GOOD"
    if accuracy >= need - 14:
        return False, "JUST WIDE"
    if accuracy >= need - 30:
        return False, "NO GOOD"
    return False, "SHANKED IT"


def kick_chance(kicker, dist, weather="clear"):
    """Expected make rate - used for the CPU's kicks and for previews."""
    prof = kick_profile(kicker, dist, weather)
    # integrate roughly: the marker lands uniformly, so the chance of being
    # inside the good zone is the zone width over the bar
    return min(0.97, max(0.03, (prof["half"] * 2) / 100.0 * 2.4))


def terminal_kick(kicker, dist, weather, prompt="Kick"):
    """Terminal version of the meter: press-and-stop.

    The game is menu-driven, so instead of animating we show the sweep band
    and let you stop it. Your reaction is the timing test: the marker has
    already travelled, and how far it has gone depends on the kick.
    """
    prof = kick_profile(kicker, dist, weather)
    name = kicker.name if kicker else "the kicker"
    print(f"\n  {prompt}: {name} from {dist} yards  "
          f"[{weather_of(weather)['label']}]  good zone +/-{prof['half']:.1f}")
    print("  Bar:  0 ....... 50 ....... 100      (50 is dead centre)")
    # the marker sweeps and you stop it; longer kicks have moved further
    sweep_pos = random.uniform(0, 100)
    print(f"  The marker is sweeping... {sweep_pos:5.1f}")
    while True:
        s = input("  Stop it (type a number 0-100 to set it, enter 'auto' to trust your leg): ").strip()
        if s.lower() in ("auto", ""):
            marker = sweep_pos
            break
        try:
            marker = float(s)
            if 0 <= marker <= 100:
                break
        except ValueError:
            pass
        print("  Enter a number from 0 to 100, or 'auto'.")
    acc = kick_accuracy(marker, prof["half"], prof["need"])
    good, label = kick_result(acc, prof["need"])
    print(f"  Stopped at {marker:.1f}  ->  accuracy {acc:.0f}  ->  {label}")
    return good, acc, label


# ======================================================================
# PLAYS
# ======================================================================
OFF_PLAYS = {
    "Inside Run":  ("run",   {"str": .45, "spd": .2, "iq": .35},  4, 3),
    "Power Dive":  ("run",   {"str": .55, "iq": .25, "spd": .2},  3, 2),
    "Sweep":       ("run",   {"spd": .6, "str": .15, "iq": .25},  5, 7),
    "Read Option": ("run",   {"spd": .45, "iq": .35, "str": .2},  6, 6),
    "Short Pass":  ("short", {"pas": .45, "hnd": .35, "iq": .2},  6, 6),
    "Screen":      ("short", {"hnd": .4, "spd": .3, "pas": .3},   5, 6),
    "Play Action": ("short", {"pas": .4, "iq": .3, "hnd": .3},    7, 8),
    "Deep Pass":   ("deep",  {"pas": .4, "hnd": .25, "spd": .35}, 10, 14),
}

# ---------------------------------------------------------------- chains
# A chain links two plays: run the first, and the next one cashes it in.
# The classic is hammering the run then hitting off play action, because
# the defence bites on the run and the pass goes over the top.
#
#   after      - the family you must have just run
#   play       - the play that cashes it in
#   yards      - flat yards added
#   boom       - added chance (0-1) of a big-play roll
#   boom_yards - what that roll is worth
#   note       - what the play-by-play prints
CHAINS = [
    {"after": "run",   "play": "Play Action", "chance": 0.34,
     "note": "PLAY ACTION OFF THE RUN"},
    {"after": "run",   "play": "Deep Pass",   "chance": 0.30,
     "note": "THE RUN SET UP THE DEEP SHOT"},
    {"after": "short", "play": "Deep Pass",   "chance": 0.26,
     "note": "DEEP SHOT OFF THE SHORT GAME"},
    {"after": "short", "play": "Play Action", "chance": 0.22,
     "note": "THE SHORT GAME SET THIS UP"},
    {"after": "deep",  "play": "Screen",      "chance": 0.24,
     "note": "SCREEN OFF THE DEEP BALL"},
    {"after": "run",   "play": "Read Option", "chance": 0.24,
     "note": "OPTION OFF THE RUN"},
    {"after": "run",   "play": "Short Pass",  "chance": 0.20,
     "note": "SHORT GAME OFF THE RUN"},
    {"after": "run",   "play": "Screen",      "chance": 0.20,
     "note": "SCREEN OFF THE RUN"},
]

# How far a chain can break. A play's own depth decides which band it rolls
# in, so a chained deep shot can go the distance while a chained screen only
# picks up a chunk.
CHAIN_BANDS = {
    "short": (1, 4, 9),      # (reach, min bonus, max bonus)
    "deep":  (2, 10, 22),
    "run":   (1, 3, 8),
}

# A completed chain skips this many bands. A short pass normally reaches
# band 1; chained, it reaches band 2 - which is where the big plays live.
CHAIN_BAND_SKIP = 1

# What the defence did to the play. Its matchup modifier says how badly it
# was beaten, and that sets the band the play would reach anyway. This is
# what makes the CPU's call matter to the size of the play.
DEF_BANDS = [
    (9, 2, "the defence was gashed"),      # badly beaten
    (4, 1, "the defence was stretched"),
    (999, 0, "the defence held its shape"),  # covered it well
]
CHAIN_BY_PLAY = {}
for _c in CHAINS:
    CHAIN_BY_PLAY.setdefault(_c["play"], []).append(_c)


def chain_for(last_family, play):
    """The chain that pays out when `play` follows `last_family`, if any."""
    if not last_family:
        return None
    for c in CHAIN_BY_PLAY.get(play, []):
        if c["after"] == last_family:
            return c
    return None


def defence_band(def_mod):
    """What the CPU's call did to this play.

    `def_mod` is the defence's matchup modifier for the play type: positive
    means the defence was beaten, negative means it covered it well. Returns
    (band, note). This is what stops a chain from being a free bonus - walk
    into a good call and even a chained play goes nowhere.
    """
    if def_mod >= 9:
        return 2, "the defence was gashed"
    if def_mod >= 4:
        return 1, "the defence was stretched"
    return 0, "the defence held its shape"


def band_bonus(band, ptype, roll=True):
    """Yards a play reaching this band gains. Band 0 is an ordinary play."""
    if band <= 0:
        return 0
    reach, lo, hi = CHAIN_BANDS.get(ptype, CHAIN_BANDS["short"])
    if band > reach:
        band = reach
    scaled_lo = lo * band / max(1, reach)
    scaled_hi = hi * band / max(1, reach)
    if not roll:
        return round((scaled_lo + scaled_hi) / 2)
    return random.randint(round(scaled_lo), round(scaled_hi))


def roll_breakaway(band, ptype):
    """Chance a play at this band breaks all the way.

    Only a deep shot reaching the top band can genuinely go to the house;
    shorter plays break for a chunk instead of a score.
    """
    if band <= 0:
        return None
    if ptype == "deep" and band >= 2:
        return 0.62
    if ptype == "deep" and band >= 1:
        return 0.30
    if ptype == "short" and band >= 2:
        return 0.34
    if ptype == "short" and band >= 1:
        return 0.18
    if ptype == "run" and band >= 2:
        return 0.26
    return 0.12


def chain_hint(play):
    """One-line description of what sets this play up - for menus."""
    cs = CHAIN_BY_PLAY.get(play)
    if not cs:
        return ""
    return " or ".join(f"after a {c['after']}" for c in cs)


DEF_PLAYS = {
    "Run Stuff": ({"str": .4, "tak": .4, "iq": .2}, {"run": 10, "short": -5, "deep": -10}),
    "Coverage":  ({"spd": .35, "tak": .3, "iq": .35}, {"run": -6, "short": 8, "deep": 10}),
    "Blitz":     ({"spd": .35, "str": .3, "tak": .35}, {"run": 2, "short": 4, "deep": -6}),
    "Balanced":  ({"tak": .4, "iq": .3, "spd": .15, "str": .15}, {"run": 2, "short": 2, "deep": 2}),
}

PLAY_SLOTS = {
    "run":   ["RB1", "RB2", "QB1"],
    "short": ["WR1", "WR2", "WR3", "TE1", "TE2", "RB1"],
    "deep":  ["WR1", "WR2", "WR3", "TE1"],
}

POWERUPS = {
    "Turbo Boost": ("boost", 12, "+12 rating this play"),
    "Film Study":  ("boost", 8,  "+8 rating this play"),
    "Safe Hands":  ("safe", 0,   "no turnover / opp gain capped at 5"),
    "Big Play":    ("big", 6,    "+6 yards (off) / -6 yards allowed (def)"),
    "Adrenaline":  ("boost", 18, "+18 rating this play"),
    "Ice Water":   ("boost", 15, "+15 rating on a clutch down"),
}


def rate(player, weights):
    return sum(player.st[k] * w for k, w in weights.items())


# ======================================================================
# CARDS
# ======================================================================
class Player:
    def __init__(self, name, pos, slot, **st):
        self.name, self.pos, self.slot = name, pos, slot
        self.st = {s: st.get(s, 40) for s in STATS}
        self.unit = "OFF" if pos in OFF_POS else ("DEF" if pos in DEF_POS else "ST")
        self.uid = new_uid()
        self.streak = 0
        self.rest = 99
        self.rarity = "common"

    def tired(self):
        return fatigue_penalty(self) > 0

    def value(self):
        v = sum(self.st.values()) / 11
        v += {"common": 0, "rare": 4, "epic": 9, "legendary": 16}.get(self.rarity, 0)
        return max(10, round(v) + (0 if is_backup(self.slot) else 8))

    def show(self):
        a = " ".join(f"{k}:{v:<2}" for k, v in self.st.items())
        pen = fatigue_penalty(self)
        return f"{str(self.slot or self.pos):<4}{self.name:<14}| {a}" + (f"  TIRED -{pen}" if pen else "")


class PowerCard:
    def __init__(self, name):
        self.name = name
        self.uid = new_uid()

    @property
    def kind(self):
        return POWERUPS[self.name][0]

    @property
    def desc(self):
        return POWERUPS[self.name][2]

    def value(self):
        return POWERUPS[self.name][1] if POWERUPS[self.name][0] == "safe" else \
               max(12, POWERUPS[self.name][1])


# ======================================================================
# FATIGUE  (weather-aware)
# ======================================================================
REST_AFTER = 2


def fatigue_penalty(pl, heavy=False):
    if pl.rest >= REST_AFTER:
        return 0
    pen = min(20, 5 * max(pl.streak, 1) + 3 * (REST_AFTER - pl.rest))
    if pl.streak == 0:
        pen = min(pen, 5)
    pen += 4 if heavy else 0
    # snow and cold drain a player far faster
    return round(pen * weather_of(_ACTIVE_WEATHER[0])["stamina"])


def effective(pl, heavy=False):
    pen = fatigue_penalty(pl, heavy)
    if not pen:
        return dict(pl.st)
    return {k: max(1, v - pen) for k, v in pl.st.items()}


def eff_rate(pl, weights, heavy=False):
    est = effective(pl, heavy)
    return sum(est[k] * w for k, w in weights.items())


def tick_fatigue(played):
    played = list(played)
    for pl in ALL_PLAYERS_REF[0]:
        if pl in played:
            pl.streak += 1
            pl.rest = 0
        else:
            pl.rest = min(pl.rest + 1, 99)
            if pl.rest >= REST_AFTER:
                pl.streak = 0


def reset_fatigue(roster=None):
    for pl in (roster or ALL_PLAYERS_REF[0]):
        pl.streak, pl.rest = 0, 99


def bench_bonus(pl, weather_key):
    """Snow rewards fresh legs: a rested backup is worth extra, and a player
    on a long streak is worth less. This is what makes TE2/WR3/RB2 matter."""
    w = weather_of(weather_key)
    if not w["bench_bonus"]:
        return 0
    if pl.rest >= REST_AFTER and is_backup(pl.slot):
        return w["bench_bonus"]
    if pl.streak >= 3:
        return -w["bench_bonus"]
    return 0


# ======================================================================
# FORMATIONS
# ======================================================================
FORMATIONS = [
    {"name": "I-Form",         "slots": ["QB1", "RB1", "TE1", "WR1"],
     "pool": ["Inside Run", "Power Dive", "Play Action", "Short Pass", "Sweep"]},
    {"name": "Shotgun Spread", "slots": ["QB1", "WR1", "WR2", "WR3"],
     "pool": ["Short Pass", "Deep Pass", "Sweep", "Screen", "Play Action"]},
    {"name": "Singleback",     "slots": ["QB1", "RB1", "TE1", "WR1", "WR2"],
     "pool": ["Inside Run", "Play Action", "Short Pass", "Deep Pass", "Screen"]},
    {"name": "Pistol",         "slots": ["QB1", "RB1", "TE1", "WR2"],
     "pool": ["Inside Run", "Read Option", "Short Pass", "Deep Pass", "Screen"]},
    {"name": "Trips Right",    "slots": ["QB1", "WR1", "WR2", "WR3", "TE1"],
     "pool": ["Short Pass", "Deep Pass", "Screen", "Sweep", "Play Action"]},
    {"name": "Jumbo",          "slots": ["QB1", "RB1", "RB2", "TE1", "TE2"],
     "pool": ["Power Dive", "Inside Run", "Play Action", "Short Pass"]},
]

DEF_FORMATIONS = [
    {"name": "4-3 Base",    "slots": ["DL1", "DL2", "LB1", "LB2", "CB1", "CB2", "S1"],
     "pool": ["Run Stuff", "Coverage", "Balanced", "Blitz"], "bonus": 0},
    {"name": "Nickel",      "slots": ["DL1", "DL2", "LB1", "CB1", "CB2", "S1", "S2"],
     "pool": ["Coverage", "Blitz", "Balanced", "Run Stuff"], "bonus": 2},
    {"name": "Dime",        "slots": ["DL1", "DL2", "LB1", "CB1", "CB2", "S1", "S2"],
     "pool": ["Coverage", "Blitz", "Balanced"], "bonus": 3},
    {"name": "Goal Line D", "slots": ["DL1", "DL2", "LB1", "LB2", "CB1", "S1", "S2"],
     "pool": ["Run Stuff", "Blitz", "Balanced"], "bonus": 1},
]


def roll_formations(defense=False):
    bank = DEF_FORMATIONS if defense else FORMATIONS
    return random.sample(bank, random.randint(3, 4))


def roll_plays(formation):
    pool = list(formation["pool"])
    random.shuffle(pool)
    return pool[:random.randint(3, min(4, len(pool)))]


def on_field(roster, formation):
    return [p for p in roster if p.slot in formation["slots"]]


def eligible(roster, formation, play, unit="OFF"):
    guys = on_field(roster, formation)
    if unit == "DEF":
        return sorted(guys, key=lambda p: (is_backup(p.slot), -max(p.st["tak"], p.st["spd"])))
    fam = OFF_PLAYS[play][0]
    out = [p for p in guys if p.slot in PLAY_SLOTS[fam]]
    return out or guys


# ======================================================================
# RESOLUTION  (weather-aware)
# ======================================================================
def resolve(att_rating, def_rating, ptype, base, var, power, weather="clear",
            band=0, chain=False):
    """Return (yards, event).

    `band` is the breakaway tier the play reached, and `chain` says whether a
    play chain is what got it there. A chain does not add yards - it raises
    the odds of reaching a higher band, which is where the big plays are.
    """
    w = weather_of(weather)
    kind = power[0] if power else None
    if kind == "boost":
        att_rating += power[1]
    yards = round(base + (att_rating - def_rating) / 4 + random.randint(-var, var))
    event = ""
    if ptype in ("short", "deep") and yards <= 0:
        if ptype == "deep" and yards < -3 and kind != "safe" and random.random() < 0.55:
            return 0, "INT"
        yards, event = 0, "incomplete"
    if ptype == "deep":
        # rain and wind shorten how far a deep ball can travel
        cap = round(base * w["pass_range"])
        if yards > cap:
            yards = cap
            event = event or "held up"
    if yards < -3 and random.random() < (0.15 + (w["fumble"] if ptype == "run" else 0)) \
            and kind != "safe":
        return yards, "FUM"

    if band > 0:
        yards += band_bonus(band, ptype)
        brk = roll_breakaway(band, ptype)
        if brk and random.random() < brk:
            if ptype == "deep":
                yards += random.randint(14, 32)
                event = "HOUSE"
            elif ptype == "short":
                yards += random.randint(8, 20)
                event = "BREAKAWAY"
            else:
                yards += random.randint(6, 18)
                event = "BIG RUN"

    if kind == "safe":
        yards = max(yards, 0)
    if kind == "big":
        yards += power[1]
    return yards, event


def resolve_def(opp_rating, my_def_rating, ptype, base, var, power, weather="clear"):
    kind = power[0] if power else None
    my = my_def_rating + (power[1] if kind == "boost" else 0)
    yards = round(base + (opp_rating - my) / 4 + random.randint(-var, var))
    event = ""
    if ptype in ("short", "deep") and yards <= 0:
        if yards < -4 and random.random() < 0.5:
            return 0, "INT"
        yards, event = 0, "incomplete"
    if yards < -3 and random.random() < 0.2:
        return yards, "FUM"
    if kind == "safe":
        yards = min(yards, 5)
    if kind == "big":
        yards -= power[1]
    return yards, event


def off_rating(pl, play, heavy=False):
    return eff_rate(pl, OFF_PLAYS[play][1], heavy)


def def_rating(pl, scheme, ptype, form, heavy=False):
    return eff_rate(pl, DEF_PLAYS[scheme][0], heavy) + DEF_PLAYS[scheme][1][ptype] + form.get("bonus", 0)


# ======================================================================
# CHEMISTRY
# ======================================================================
# How well a player fits a play, 0-100. 50 is neutral.
#
# Set against the player's FULL attributes rather than his tired ones, so
# this measures the fit itself and not how worn down he is right now. A
# player lined up in a slot the play was drawn for scores a bonus, and the
# attributes the play leans on are weighted in. A man out of position, or
# short on the right skills, is penalised - which is what stops you from
# stacking stars and calling anything.
CHEM_ATTR_WEIGHT = 0.55
CHEM_SLOT_BONUS = 18
CHEM_WRONG_UNIT = -20


def chemistry(pl, play):
    """0-100 fit between a player and a play. 50 is neutral."""
    if pl is None or play not in OFF_PLAYS:
        return 50.0
    ptype, weights, base, var = OFF_PLAYS[play]
    c = 50.0
    # a play is drawn up for certain slots
    if pl.slot in PLAY_SLOTS.get(ptype, []):
        c += CHEM_SLOT_BONUS
    elif pl.unit != "OFF":
        c += CHEM_WRONG_UNIT
    # and leans on certain attributes - weight the two that matter most
    top = sorted(weights.items(), key=lambda kv: -kv[1])[:2]
    for attr, _w in top:
        c += (pl.st[attr] - 62) * CHEM_ATTR_WEIGHT
    c += {"common": 0, "rare": 2, "epic": 4, "legendary": 6}.get(getattr(pl, "rarity", "common"), 0)
    return max(0.0, min(100.0, c))


def chem_label(c):
    if c >= 80:
        return "PERFECT"
    if c >= 65:
        return "STRONG"
    if c >= 50:
        return "SOLID"
    if c >= 35:
        return "SHAKY"
    return "POOR"


def chem_bonus(c):
    """Chemistry is worth roughly +6 to -5 in the rating."""
    return (c - 50) / 50 * 5.5


# ======================================================================
# RARITY
# ======================================================================
RARITY = {
    "common":    {"label": "COMMON",    "colour": "#9aa7bd", "roll": 0},
    "rare":      {"label": "RARE",      "colour": "#38bdf8", "roll": 3},
    "epic":      {"label": "EPIC",      "colour": "#a855f7", "roll": 6},
    "legendary": {"label": "LEGENDARY", "colour": "#fbbf24", "roll": 10},
}
RARITY_ORDER = ["common", "rare", "epic", "legendary"]


def roll_rarity(odds):
    r = random.uniform(0, sum(odds.values()))
    acc = 0
    for name in RARITY_ORDER:
        acc += odds.get(name, 0)
        if r <= acc:
            return name
    return "common"


# ======================================================================
# ROSTER BUILDING
# ======================================================================
STARTERS = {
    "QB1": ("Dak Miller",   dict(pas=78, iq=74, spd=52, str=46, hnd=42, tak=20, kck=30)),
    "QB2": ("Cole Reed",    dict(pas=68, iq=66, spd=58, str=44, hnd=40, tak=20, kck=28)),
    "RB1": ("Jet Rivers",   dict(spd=80, str=64, pas=30, hnd=62, tak=30, iq=58, kck=20)),
    "RB2": ("Dre Vance",    dict(spd=71, str=58, pas=26, hnd=52, tak=28, iq=52, kck=18)),
    "WR1": ("Ace Cole",     dict(spd=84, str=40, pas=35, hnd=80, tak=30, iq=62, kck=20)),
    "WR2": ("Jax Poole",    dict(spd=78, str=38, pas=30, hnd=72, tak=28, iq=56, kck=18)),
    "WR3": ("Miles Fry",    dict(spd=74, str=36, pas=28, hnd=66, tak=26, iq=52, kck=18)),
    "TE1": ("Tank Boyd",    dict(spd=52, str=80, pas=22, hnd=68, tak=55, iq=60, kck=20)),
    "TE2": ("Hank Dole",    dict(spd=48, str=70, pas=20, hnd=58, tak=52, iq=54, kck=18)),
    "DL1": ("Rex Hunter",   dict(spd=62, str=78, tak=80, iq=62, hnd=30, pas=22, kck=20)),
    "DL2": ("Brock Neal",   dict(spd=58, str=70, tak=72, iq=56, hnd=28, pas=20, kck=18)),
    "LB1": ("Cruz Iglesias", dict(spd=68, str=72, tak=84, iq=70, hnd=38, pas=24, kck=20)),
    "LB2": ("Pete Okafor",  dict(spd=63, str=66, tak=75, iq=63, hnd=34, pas=22, kck=18)),
    "CB1": ("Sky Bishop",   dict(spd=82, str=46, tak=72, iq=70, hnd=58, pas=24, kck=20)),
    "CB2": ("Nino Hart",    dict(spd=76, str=42, tak=65, iq=62, hnd=52, pas=22, kck=18)),
    "S1":  ("Omar Blake",   dict(spd=74, str=54, tak=78, iq=72, hnd=50, pas=24, kck=20)),
    "S2":  ("Sim Rice",     dict(spd=68, str=50, tak=70, iq=64, hnd=44, pas=22, kck=18)),
}
KICKER = ("Leg Novak", dict(spd=40, str=40, pas=30, hnd=30, tak=30, iq=52, kck=80))
RECRUIT_NAMES = ["Zed Patton", "Max Cruz", "Bo Landry", "Kai Stone", "Ty Wolfe",
                 "Gus Ramos", "Cal Foster", "Nate Pike", "Ian Frost", "Roy Mack",
                 "Dex Nolan", "Wes Bright", "Abel Cross", "Moe Vance", "Luca Reyes",
                 "Trey Sloane", "Bram Adler", "Otis Fields", "Cole Vane", "Rue Marchal"]


def build_roster():
    roster = []
    for slot, (name, st) in STARTERS.items():
        pos, n = slot_pos(slot), slot_num(slot)
        if n > 1:
            cut = 5 + 4 * (n - 1) + random.randint(0, 4)
            st = {k: max(1, v - cut) for k, v in st.items()}
        roster.append(Player(name, pos, slot, **st))
    roster.append(Player(KICKER[0], "K", "K", **KICKER[1]))
    ALL_PLAYERS_REF[0] = roster
    return roster


def score_of(pl):
    return round(sum(sorted(pl.st.values(), reverse=True)[:4]) / 4)


def make_player(tier=1, slot="WR2", name=None, rarity="common"):
    pos, n = slot_pos(slot), slot_num(slot)
    bonus = RARITY[rarity]["roll"]
    base = (46 if n > 1 else 58) + 5 * tier + bonus
    nm = name or random.choice(RECRUIT_NAMES)
    st = {s: random.randint(base - 12, base + 14) for s in STATS}
    st["kck"] = random.randint(20, 40)
    pl = Player(nm, pos, slot, **st)
    pl.rarity = rarity
    return pl


def free_slots(prof, pos):
    used = {p.slot for p in prof.roster}
    order = {"QB": ["QB1", "QB2"], "RB": ["RB1", "RB2"],
             "WR": ["WR1", "WR2", "WR3"], "TE": ["TE1", "TE2"],
             "K": ["K"]}.get(
                 pos, [f"{pos}1", f"{pos}2"])
    return [s for s in order if s not in used]


def open_slot(prof, pos):
    fs = free_slots(prof, pos)
    return fs[0] if fs else None


def slot_base(pos):
    return MAX_PER_POS.get(pos, 1)


def spare_slot_name(pos, n):
    """Spare slots are numbered on from the real ones: TE3, WR4, CB3."""
    return f"{pos}{slot_base(pos) + n}"


def nice_slot(slot):
    if not slot:
        return "-"
    pos, num = slot_pos(slot), slot_num(slot)
    if pos and num > slot_base(pos):
        return f"{pos}{num} (spare)"
    return slot


# ======================================================================
# PACKS
# ======================================================================
ODDS = {
    "standard":  {"common": 70, "rare": 22, "epic": 7,  "legendary": 1},
    "premium":   {"common": 42, "rare": 33, "epic": 19, "legendary": 6},
    "elite":     {"common": 16, "rare": 31, "epic": 34, "legendary": 19},
    "mythic":    {"common": 0,  "rare": 18, "epic": 42, "legendary": 40},
}
UPGRADE_SIZE = {"common": 3, "rare": 4, "epic": 5, "legendary": 7}
POWER_TIER = {
    "Film Study": "common", "Big Play": "common",
    "Turbo Boost": "rare", "Ice Water": "rare",
    "Safe Hands": "epic", "Adrenaline": "legendary",
}


def _unique_power_names(k):
    names = list(POWERUPS)
    random.shuffle(names)
    return names[:k]


def make_pack(name, cost, kind, odds_key, blurb):
    return {"name": name, "cost": cost, "kind": kind, "odds": odds_key, "blurb": blurb}


PACKS = [
    make_pack("Standard Player Pack",  80,  "player",  "standard", "3 players, keep 1"),
    make_pack("Premium Player Pack",  200,  "player",  "premium",  "3 players, better odds"),
    make_pack("Elite Player Pack",    450,  "player",  "elite",    "3 players, high odds"),
    make_pack("Mythic Player Pack",   900,  "player",  "mythic",   "3 players, no commons"),
    make_pack("Standard Power Pack",   40,  "power",   "standard", "3 power-ups, keep 1"),
    make_pack("Elite Power Pack",     160,  "power",   "elite",    "3 power-ups, better odds"),
    make_pack("Standard Upgrade Pack", 60,  "upgrade", "standard", "3 upgrades, keep 1"),
    make_pack("Elite Upgrade Pack",   220,  "upgrade", "elite",    "3 upgrades, bigger boosts"),
]
PACK_BY_NAME = {p["name"]: p for p in PACKS}
PACK_POWER = PACK_BY_NAME["Standard Power Pack"]
PACK_PLAYER = PACK_BY_NAME["Standard Player Pack"]
PACK_UPGRADE = PACK_BY_NAME["Standard Upgrade Pack"]


def open_pack(prof, kind, odds_key="standard"):
    """Exactly three offers, drawn with the pack's rarity odds."""
    odds = ODDS.get(odds_key, ODDS["standard"])
    offers = []

    if kind == "power":
        for name in _unique_power_names(3):
            offers.append({"title": name, "sub": POWERUPS[name][2],
                           "rarity": POWER_TIER.get(name, "common"), "power": name})

    elif kind == "player":
        # kickers are a real position now, so they show up in player packs too
        positions = list(OFF_POS + DEF_POS)
        random.shuffle(positions)
        picks = (positions * 2)[:2] + (["K"] if random.random() < 0.45 else positions[:1])
        random.shuffle(picks)
        picks = picks[:3]
        taken = {p.name for p in prof.roster}
        for pos in picks:
            rarity = roll_rarity(odds)
            pool = [n for n in RECRUIT_NAMES if n not in taken] or RECRUIT_NAMES
            pl = make_player(prof.level, label(pos, 1), random.choice(pool), rarity)
            pl.slot = None
            taken.add(pl.name)
            offers.append({"title": f"{pl.name}  ({pl.pos})",
                           "sub": f"overall {score_of(pl)}",
                           "rarity": rarity, "player": pl})
        while len(offers) < 3:
            pos = picks[len(offers)]
            offers.append({"title": f"Scout Report ({pos})", "sub": "bonus coins instead",
                           "rarity": "rare", "coins": 60})

    else:  # upgrade
        for _ in range(3):
            rarity = roll_rarity(odds)
            size = UPGRADE_SIZE[rarity]
            pl = random.choice(prof.roster)
            st = random.choice(STATS)
            offers.append({"title": f"{pl.name}  {st.upper()} +{size}",
                           "sub": f"{nice_slot(pl.slot)}: {pl.st[st]} \u2192 {min(99, pl.st[st] + size)}",
                           "rarity": rarity, "upgrade": (pl, st, size)})
    return offers


def apply_offer(prof, offer):
    if "player" in offer:
        pl = offer["player"]
        pl.slot = prof.next_free_slot(pl.pos)
        pl.pos = slot_pos(pl.slot)
        ok, msg, _ = prof.add(pl, free_slot=False)
        return msg
    if "power" in offer:
        prof.add_power(offer["power"])
        return f"Added {offer['power']} to your deck."
    if "coins" in offer:
        prof.coins += offer["coins"]
        return f"Bonus of {offer['coins']} coins instead."
    pl, st, size = offer["upgrade"]
    pl.st[st] = min(99, pl.st[st] + size)
    return f"{pl.name} {st.upper()} is now {pl.st[st]}."


# ======================================================================
# LINEUP
# ======================================================================
class Lineup:
    def __init__(self, prof):
        self.prof = prof
        self.players = {p.uid for p in prof.roster}
        self.powers = {c.uid for c in prof.powerups}

    def sync(self):
        self.players &= {p.uid for p in self.prof.roster}
        self.powers &= {c.uid for c in self.prof.powerups}

    def player_pool(self):
        return [p for p in self.prof.roster if p.uid in self.players]

    def power_pool(self):
        return [c for c in self.prof.powerups if c.uid in self.powers]

    def toggle_player(self, pl):
        self.players.discard(pl.uid) if pl.uid in self.players else self.players.add(pl.uid)

    def toggle_power(self, card):
        self.powers.discard(card.uid) if card.uid in self.powers else self.powers.add(card.uid)

    def autofill(self):
        self.players = {p.uid for p in self.prof.roster}
        self.powers = {c.uid for c in self.prof.powerups}

    def clear(self):
        self.players.clear()
        self.powers.clear()

    def set_player(self, pl, on):
        self.players.add(pl.uid) if on else self.players.discard(pl.uid)

    def off(self):
        return [p for p in self.player_pool() if p.unit == "OFF"]

    def deff(self):
        return [p for p in self.player_pool() if p.unit == "DEF"]


# ======================================================================
# HELPERS
# ======================================================================
def yl_text(pos):
    return "own %d" % pos if pos < 50 else ("midfield" if pos == 50 else "opp %d" % (100 - pos))


def pick(options, prompt, labels=None):
    for i, o in enumerate(options, 1):
        print(f"  {i}) {labels[i-1] if labels else o}")
    while True:
        s = input(prompt + " > ").strip()
        if s.isdigit() and 1 <= int(s) <= len(options):
            return options[int(s) - 1]
        print("  Enter a number from the list.")


# ======================================================================
# PROFILE
# ======================================================================
class Profile:
    ROUNDS = 3

    def __init__(self):
        self.roster = build_roster()
        self.powerups = [PowerCard(n) for n in
                         ("Turbo Boost", "Film Study", "Safe Hands", "Big Play")]
        self.coins = 120
        self.level = 1
        self.lineup = Lineup(self)
        self.repair()   # heal a roster written by an older version

    def repair(self):
        seen = {}
        for pl in list(self.roster):
            code = slot_pos(pl.slot) if pl.slot else pl.pos
            if code and code.endswith("S") and code[:-1] in OFF_POS + DEF_POS:
                code = code[:-1]
            if code in OFF_POS + DEF_POS:
                pl.pos = code
            if pl.slot and pl.slot not in seen:
                seen[pl.slot] = pl
            else:
                pl.slot = self.next_free_slot(pl.pos)
                seen[pl.slot] = pl
        ALL_PLAYERS_REF[0] = list(self.roster)

    def next_free_slot(self, pos):
        order = {"QB": ["QB1", "QB2"], "RB": ["RB1", "RB2"],
                 "WR": ["WR1", "WR2", "WR3"], "TE": ["TE1", "TE2"]}.get(
                     pos, [f"{pos}1", f"{pos}2"])
        used = {p.slot for p in self.roster}
        for s in order:
            if s not in used:
                return s
        n = 1
        cand = spare_slot_name(pos, n)
        while cand in used:
            n += 1
            cand = spare_slot_name(pos, n)
        return cand

    def add(self, pl, free_slot=True):
        pos = pl.pos
        if pl in self.roster or self.by_uid(pl.uid) is not None:
            return False, f"{pl.name} is already in your roster.", pl.slot
        if free_slot or not pl.slot or self.at_slot(pl.slot):
            pl.slot = self.next_free_slot(pos)
        self.roster.append(pl)
        if pl not in ALL_PLAYERS_REF[0]:
            ALL_PLAYERS_REF[0].append(pl)
        self.lineup.players.add(pl.uid)
        pl.pos = slot_pos(pl.slot) or pos
        self.dedupe_slots(keep=[pl])
        return True, f"Added {pl.name} ({pl.slot}).", pl.slot

    def remove_player(self, pl_or_uid):
        pl = pl_or_uid if isinstance(pl_or_uid, Player) else self.by_uid(pl_or_uid)
        if pl is None:
            return False, "Card not found."
        if pl in self.roster:
            self.roster.remove(pl)
        if pl in ALL_PLAYERS_REF[0]:
            ALL_PLAYERS_REF[0].remove(pl)
        self.lineup.players.discard(pl.uid)
        self.compact_slots(pl.pos)
        return True, f"Removed {pl.name}."

    def add_power(self, name):
        c = name if isinstance(name, PowerCard) else PowerCard(name)
        self.powerups.append(c)
        self.lineup.powers.add(c.uid)
        return c

    def sell_player(self, pl_or_uid):
        pl = pl_or_uid if isinstance(pl_or_uid, Player) else self.by_uid(pl_or_uid)
        if pl is None:
            return False, "Card not found."
        if pl.pos == "QB" and len([p for p in self.roster if p.pos == "QB"]) <= 1:
            return False, "You need at least one quarterback to play."
        coins = pl.value()
        self.remove_player(pl)
        self.coins += coins
        return True, f"Sold {pl.name} for {coins} coins."

    def sell_power(self, card_or_uid):
        card = card_or_uid if isinstance(card_or_uid, PowerCard) else \
            next((c for c in self.powerups if c.uid == card_or_uid), None)
        if card is None or card not in self.powerups:
            return False, "Card not found."
        self.powerups.remove(card)
        self.lineup.powers.discard(card.uid)
        self.coins += card.value()
        return True, f"Sold {card.name} for {card.value()} coins."

    def compact_slots(self, pos):
        guys = [p for p in self.roster
                if (slot_pos(p.slot) or p.pos) == pos and p.slot]
        if len(guys) < 2:
            return []
        guys.sort(key=lambda p: -rate(p, {s: 1 for s in STATS}))
        base = slot_base(pos)
        moves = []
        for i, p in enumerate(guys):
            want = f"{pos}{i + 1}" if i < base else spare_slot_name(pos, i + 1 - base)
            if p.slot != want:
                moves.append((p, p.slot, want))
                p.slot = want
                p.pos = pos
        return moves

    def promote(self, pl, to_slot):
        want = slot_pos(to_slot)
        here = slot_pos(pl.slot) or pl.pos
        if want != here:
            return False, f"{pl.name} is a {here}, not a {want}."
        if pl.slot == to_slot:
            return False, f"{pl.name} is already at {to_slot}."
        pl.pos = here
        holders = [p for p in self.roster if p.slot == to_slot and p is not pl]
        other = holders[0] if holders else None
        old = pl.slot
        if other is not None:
            other.slot = old
        pl.slot = to_slot
        self.dedupe_slots(keep=[pl, other] if other else [pl])
        if other is not None:
            return True, f"Promoted {pl.name} to {to_slot}; {other.name} moves to {old}."
        return True, f"Promoted {pl.name} to {to_slot}."

    def dedupe_slots(self, keep=None):
        keep = list(keep or [])
        seen = {}
        for pl in keep:
            if pl is not None:
                seen[pl.slot] = pl
        for pl in list(self.roster):
            if pl in keep:
                continue
            if pl.slot in seen:
                pl.slot = self.next_free_slot(pl.pos)
            seen[pl.slot] = pl
        return True

    # ---- access
    def off_roster(self):
        return [p for p in self.roster if p.unit == "OFF"]

    def def_roster(self):
        return [p for p in self.roster if p.unit == "DEF"]

    def kicker(self):
        return next((p for p in self.roster if p.pos == "K"), None)

    def by_uid(self, uid):
        return next((p for p in self.roster if p.uid == uid), None)

    def at_slot(self, slot):
        return next((p for p in self.roster if p.slot == slot), None)

    def depth_chart(self, unit=None):
        colour = {"OFF": 0, "DEF": 1, "ST": 2}
        pos_order = {p: i for i, p in enumerate(OFF_POS + DEF_POS + ["K"])}
        guys = self.roster if unit is None else [p for p in self.roster if p.unit == unit]

        def key(p):
            pos = slot_pos(p.slot) or p.pos
            return (colour[p.unit], pos_order.get(pos, 90), slot_num(p.slot), p.name)
        return sorted(guys, key=key)

    def can_play(self):
        return any(p.pos == "QB" for p in self.roster)


# ======================================================================
# GAME
# ======================================================================
class Game:
    def __init__(self, prof, weather=None, weather_changes=True):
        self.p = prof
        self.lineup = prof.lineup
        self.lineup.sync()
        reset_fatigue(prof.roster)
        self.me = self.cpu = self.earned = 0
        self.round = 1
        self.deck = list(self.lineup.power_pool())
        random.shuffle(self.deck)
        self.hand = []
        self.cpu_off = 52 + prof.level * 5
        self.cpu_def = 52 + prof.level * 5
        # weather: rolled at kickoff, and it can turn between rounds
        self.weather = set_weather(weather or roll_weather())
        self.weather_changes = weather_changes
        self.weather_log = [(1, self.weather)]
        # play chains: what family went last, cleared at the start of a drive
        self.last_family = None
        self.chain_log = []

    def reset_chain(self):
        """Chains only carry within a single drive."""
        self.last_family = None

    def chain_preview(self, play):
        """(chance, note) a chain would give this play right now.

        The chain does not add yards. It raises the odds of the play reaching
        a higher breakaway band, which is where the big plays live.
        """
        c = chain_for(self.last_family, play)
        if not c:
            return 0.0, ""
        return c["chance"], c["note"]

    def chain_band(self, play, def_mod):
        """(band, note) for this play.

        The CPU's call sets the base band - beat it badly and you are already
        at band 2. A completed chain then raises the odds of going one band
        higher still, so running the ball to set up play action genuinely
        improves your chance of a big play.
        """
        base_band, def_note = defence_band(def_mod)
        chance, chain_note = self.chain_preview(play)
        band = base_band
        if chance and random.random() < chance:
            band = min(2, base_band + CHAIN_BAND_SKIP)
            return band, f"{chain_note}  ({def_note})"
        return band, def_note

    def roster(self):
        return self.lineup.player_pool()

    def refill(self):
        while len(self.hand) < 3 and self.deck:
            self.hand.append(self.deck.pop())

    def choose_power(self):
        if not self.hand:
            return None, None
        opts = [None] + self.hand
        labels = ["No power-up"] + [f"{c.name} - {c.desc}" for c in self.hand]
        c = pick(opts, "Play a power-up?", labels)
        if c:
            self.hand.remove(c)
            return POWERUPS[c.name][:2], c.name
        return None, None

    def turn_weather(self):
        """Weather can change between possessions.

        The change is judged against the same ramped odds as the kickoff
        roll, so late rounds turn nasty far more often than early ones.
        """
        if not self.weather_changes:
            return None
        r = self.round
        if self.weather != "clear" and random.random() < 0.55:
            old = self.weather
            self.weather = set_weather("clear")
            self.weather_log.append((r, self.weather))
            return f"The weather clears up. ({weather_of(old)['label']} \u2192 CLEAR)"
        ramp = _ramped({"clear": 72, "rain": 15, "snow": 9}, r)
        total = sum(ramp.values()) or 1
        bad_chance = 1.0 - ramp.get("clear", 0) / total
        if self.weather == "clear" and random.random() < bad_chance * 0.7:
            self.weather = set_weather(roll_weather(round_no=r))
            self.weather_log.append((r, self.weather))
            return f"The weather turns: {weather_of(self.weather)['label']}."
        return None

    def banner(self):
        w = weather_of(self.weather)
        print(f"\n=== YOU {self.me} - {self.cpu} CPU | Round {self.round}/{self.p.ROUNDS} "
              f"| Level {self.p.level} | {w['label']} ===")

    # ---- kicking
    def kicker(self):
        return self.p.kicker()

    def try_field_goal(self, pos, label="FIELD GOAL"):
        """Run the kicking meter for one attempt. Returns True if it went."""
        k = self.kicker()
        if not k:
            print("  No kicker on the roster!")
            return False
        dist = max(18, 117 - pos)
        good, acc, res = terminal_kick(k, dist, self.weather, label)
        print(f"  {k.name}: {res} from {dist} yards!")
        return good

    def two_point_formations(self):
        """Goal-line looks only - a two-yard try is a short-yardage snap."""
        return [f for f in roll_formations() if "Jumbo" in f["name"] or "I-Form" in f["name"]] \
               or [f for f in FORMATIONS if f["name"] in ("Jumbo", "I-Form")]

    def two_point_chance(self, pl, play, scheme, form):
        """Conversion odds for a two-point try.

        Chemistry sets the base - a well-drawn play with the right personnel
        is far more likely to convert than a square peg in a round hole. The
        CPU's call then moves it, so walking into a goal-line stack is
        punished the same way it is on any other down.
        """
        chem = chemistry(pl, play)
        ptype = OFF_PLAYS[play][0]
        fam_bonus = {"run": 6, "short": 2, "deep": -10}.get(ptype, 0)
        power_bonus = 10 if form["name"] == "Jumbo" else 0
        base = 22 + chem * 0.55 + fam_bonus + power_bonus
        # the defence's matchup modifier for this play type
        base -= DEF_PLAYS[scheme][1].get(ptype, 0) * 1.6
        return max(0.08, min(0.88, base / 100.0))

    def try_two_point(self):
        """Run a real two-point play: formation, play, player, then resolve."""
        print("\n  TWO-POINT TRY - you need two yards.")
        form = pick(self.two_point_formations(), "Formation",
                    [f"{f['name']:<14} on field: {', '.join(f['slots'])}"
                     for f in self.two_point_formations()])
        plays = [n for n in roll_plays(form) if OFF_PLAYS[n][0] in ("run", "short")]
        if not plays:
            plays = ["Power Dive", "Quick Slant"]
        play = pick(plays, "Play",
                    [f"{n:<14} [{OFF_PLAYS[n][0]}]  chem sets your odds" for n in plays])
        ptype, wts, base, var = OFF_PLAYS[play]
        pool = sorted(eligible(self.roster(), form, play, "OFF"),
                      key=lambda x: -(eff_rate(x, wts) + chem_bonus(chemistry(x, play))))
        if not pool:
            print("  Nobody available - the try is stuffed.")
            return 0
        pl = pick(pool, "Player",
                  [f"{x.show()}  -> fit {eff_rate(x, wts):.0f}"
                   f"  CHEM {chemistry(x, play):.0f} {chem_label(chemistry(x, play))}"
                   for x in pool])
        scheme = random.choice(list(DEF_PLAYS))
        chance = self.two_point_chance(pl, play, scheme, form)
        print(f"  CPU shows: {scheme}")
        print(f"  {pl.name} on the {play} - chemistry {chem_label(chemistry(pl, play))}, "
              f"conversion chance {chance:.0%}")
        ok = random.random() < chance
        if ok:
            print("  CONVERTED! Two points.")
        else:
            print(f"  STOPPED short by {scheme}. No points.")
        return 2 if ok else 0

    def try_pat(self, two_point=False):
        """After a touchdown: kick the PAT (1) or go for two."""
        if two_point:
            return self.try_two_point()
        good = self.try_field_goal(20, label="PAT")
        return 1 if good else 0

    # ---- offense
    def my_possession(self):
        pos, down, togo = 25, 1, 10
        print(f"\n--- ROUND {self.round}: YOUR POSSESSION ---")
        w = weather_of(self.weather)
        print(f"Weather: {w['label']} - {w['desc']}")
        self.refill()
        while True:
            self.banner()
            forms = roll_formations()
            form = pick(forms, "Formation",
                        [f"{f['name']:<14} on field: {', '.join(f['slots'])}" for f in forms])
            plays = roll_plays(form)
            labels = []
            for n in plays:
                t, wts, b, v = OFF_PLAYS[n]
                cchance, cnote = self.chain_preview(n)
                tag = f"  *** {cnote} ({cchance:.0%} big play)" if cnote else ""
                if not cnote and t == "run":
                    tag = "  (sets up the next play)"
                labels.append(f"{n:<12} [{t}] uses {', '.join(k.upper() for k in wts)}"
                              f"  ~{b} yds{tag}")
            play = pick(plays, "Play", labels)
            ptype, wts, base, var = OFF_PLAYS[play]
            heavy = down == 4
            pool = sorted(eligible(self.roster(), form, play, "OFF"),
                          key=lambda x: -eff_rate(x, wts, heavy))
            if not pool:
                print("Nobody available in your lineup for that play. Pick another.")
                continue
            print("Choose the player:")
            labels = []
            for x in pool:
                pen = fatigue_penalty(x, heavy)
                bb = bench_bonus(x, self.weather)
                labels.append(f"{x.show()}  -> fit {eff_rate(x, wts, heavy):.0f}"
                              + (f"  TIRED -{pen}" if pen else "")
                              + (f"  FRESH +{bb}" if bb > 0 else (f"  WORN {bb}" if bb < 0 else "")))
            pl = pick(pool, "Player", labels)
            power, pname = self.choose_power()
            scheme = random.choice(list(DEF_PLAYS))
            drat = self.cpu_def + DEF_PLAYS[scheme][1][ptype] + random.randint(-8, 8)
            print(f"CPU shows: {scheme}" + (f"   (you played {pname})" if pname else ""))
            # the CPU's call sets the base band; a completed chain can lift it
            def_mod = DEF_PLAYS[scheme][1][ptype]
            band, band_note = self.chain_band(play, def_mod)
            chain_hit = band > defence_band(def_mod)[0]
            yards, ev = resolve(eff_rate(pl, wts, heavy), drat, ptype, base, var,
                                power, self.weather, band=band, chain=chain_hit)
            tick_fatigue([pl])
            if ev == "INT":
                print("INTERCEPTED! Possession over.")
                return
            if ev == "FUM":
                print(f"{pl.name} FUMBLES! Turnover.")
                return
            if ev == "held up":
                print(f"  Deep ball held up in the {w['label'].lower()} - capped at {yards}.")
            if chain_hit:
                print(f"  CHAIN FIRED: {band_note}")
                self.chain_log.append((self.round, play, band_note, band))
            elif band > 0:
                print(f"  {band_note}")
            if ev in ("HOUSE", "BREAKAWAY", "BIG RUN"):
                print(f"  {ev}! It broke open.")
                self.earned += 5
            print(f"{pl.name} - {play}: " + ("incomplete" if ev == "incomplete" else f"{yards:+d} yds"))
            self.last_family = ptype
            pos += yards
            self.earned += max(0, yards) // 3
            if pos >= 100:
                print("TOUCHDOWN! 6 points.")
                self.me += 6
                self.earned += 20
                # you must kick the PAT, or gamble on two
                pick_two = pick(["Kick the PAT", "Go for two"], "Extra point")
                pts = self.try_pat(two_point=pick_two.startswith("Go"))
                self.me += pts
                print(f"  Total on the drive: {6 + pts} points.")
                return
            if pos <= 0:
                print("SAFETY... CPU +2")
                self.cpu += 2
                return
            togo -= yards
            if togo <= 0:
                down, togo = 1, min(10, 100 - pos)
                print("FIRST DOWN!")
            else:
                down += 1
                if down > 4:
                    print("Turnover on downs.")
                    return

    # ---- defense
    def cpu_possession(self):
        pos, down, togo = 25, 1, 10
        print(f"\n--- ROUND {self.round}: YOU DEFEND ---")
        self.refill()
        while True:
            self.banner()
            if down == 4 and pos >= 62 and random.random() < 0.8:
                k = self.kicker()
                dist = 117 - pos
                if k:
                    chance = kick_chance(k, dist, self.weather)
                    print(f"  CPU kick preview: {chance:.0%} in {weather_of(self.weather)['label']}")
                good = random.random() < 0.6
                print("CPU field goal... " + ("good. CPU +3" if good else "missed!"))
                if good:
                    self.cpu += 3
                return
            if down == 4 and pos < 62 and random.random() < 0.7:
                print("CPU punts.")
                return
            play = random.choice(list(OFF_PLAYS))
            ptype, base, var = OFF_PLAYS[play][0], OFF_PLAYS[play][2], OFF_PLAYS[play][3]
            heavy = down == 4
            forms = roll_formations(defense=True)
            form = pick(forms, f"CPU runs {play} ({ptype}) - call your formation",
                        [f"{f['name']:<14} on field: {', '.join(f['slots'])}" for f in forms])
            plays = roll_plays(form)
            labels = []
            for d in plays:
                dw, mods = DEF_PLAYS[d]
                labels.append(f"{d:<11} ({', '.join(k.upper() for k in dw)})  vs {ptype}: {mods[ptype]:+d}")
            scheme = pick(plays, "Defensive play", labels)
            dw, mods = DEF_PLAYS[scheme]
            pool = sorted(eligible(self.roster(), form, None, "DEF"),
                          key=lambda x: -eff_rate(x, dw, heavy))
            if not pool:
                print("Nobody available in your lineup for that formation.")
                continue
            print("Choose your defender:")
            labels = []
            for x in pool:
                pen = fatigue_penalty(x, heavy)
                labels.append(f"{x.show()}  -> fit {eff_rate(x, dw, heavy):.0f}"
                              + (f"  TIRED -{pen}" if pen else ""))
            pl = pick(pool, "Defender", labels)
            power, pname = self.choose_power()
            if pname:
                print(f"You played {pname}.")
            my_def = def_rating(pl, scheme, ptype, form, heavy)
            orat = self.cpu_off + random.randint(-8, 8)
            yards, ev = resolve_def(orat, my_def, ptype, base, var, power, self.weather)
            tick_fatigue([pl])
            if ev == "INT":
                print(f"{pl.name} INTERCEPTS!")
                self.earned += 10
                return
            if ev == "FUM":
                print(f"{pl.name} forces a FUMBLE!")
                self.earned += 10
                return
            print(f"{pl.name} defends: " + ("incomplete" if ev == "incomplete" else f"{yards:+d} yds allowed"))
            if yards <= 1:
                self.earned += 3
            pos += yards
            if pos >= 100:
                print("CPU touchdown. CPU +6, and the PAT is good. CPU +7 total.")
                self.cpu += 7
                return
            if pos <= 0:
                print("SAFETY! You score 2.")
                self.me += 2
                return
            togo -= yards
            if togo <= 0:
                down, togo = 1, min(10, 100 - pos)
                print("CPU first down.")
            else:
                down += 1
                if down > 4:
                    print("Turnover on downs! Great stand.")
                    return

    # ---- game
    def play(self):
        for r in range(1, self.p.ROUNDS + 1):
            self.round = r
            if r > 1:
                msg = self.turn_weather()
                if msg:
                    print(f"\n>>> {msg}")
            self.my_possession()
            self.cpu_possession()
        self.banner()
        if self.me > self.cpu:
            print("YOU WIN!"); self.earned += 60; res = "W"
        elif self.me < self.cpu:
            print("You lose."); res = "L"
        else:
            print("Tie game."); self.earned += 20; res = "T"
        self.p.coins += self.earned
        print(f"Earned {self.earned} coins. Total: {self.p.coins}")
        return res


# ======================================================================
# TERMINAL SHOP / LIBRARY / MAIN
# ======================================================================
def shop(prof):
    while True:
        print(f"\n=== SHOP === Coins: {prof.coins}")
        opts = [f"{p['name']} - {p['cost']} coins  ({p['blurb']})" for p in PACKS]
        opts += ["Card library (sell cards)", "View lineup", "Leave shop"]
        c = pick(opts, "Buy")
        if c in PACK_BY_NAME:
            pack = PACK_BY_NAME[c]
            if prof.coins < pack["cost"]:
                print("Not enough coins.")
                continue
            offers = open_pack(prof, pack["kind"], pack["odds"])
            if not offers:
                print("No room for that pack right now.")
                continue
            prof.coins -= pack["cost"]
            print("Choose ONE:")
            o = pick(offers, "Keep",
                     [f"[{RARITY[x['rarity']]['label']:<9}] {x['title']}  -  {x['sub']}"
                      for x in offers])
            print(apply_offer(prof, o))
        elif c.startswith("Card library"):
            library(prof)
        elif c.startswith("View"):
            for p in prof.lineup.player_pool():
                print(" ", p.show())
            for c2 in prof.lineup.power_pool():
                print(f"  {c2.name} - {c2.desc}")
        else:
            return


def library(prof):
    while True:
        print(f"\n=== CARD LIBRARY === Coins: {prof.coins}")
        print(f"Players: {len(prof.roster)}   Power-up cards: {len(prof.powerups)}")
        c = pick(["Browse / sell / promote players", "Browse / sell power-ups", "Back"],
                 "Choose")
        if c == "Back":
            return
        if c.startswith("Browse / sell"):
            pl = pick(prof.depth_chart(), "Which player", [x.show() for x in prof.depth_chart()])
            act = pick([f"Sell for {pl.value()} coins", "Promote to starter", "Cancel"], "Action")
            if act.startswith("Sell"):
                print(prof.sell_player(pl)[1])
            elif act.startswith("Promote"):
                starters = [s for s in ALL_SLOTS
                            if slot_pos(s) == (slot_pos(pl.slot) or pl.pos)
                            and not is_backup(s)]
                if not starters:
                    print("No starter slot available for that position.")
                else:
                    tgt = pick(starters, "Into which starter slot")
                    print(prof.promote(pl, tgt)[1])
        else:
            if not prof.powerups:
                print("No power-up cards.")
                continue
            names = sorted({x.name for x in prof.powerups})
            n = pick(names, "Which to sell",
                     [f"{nm} x{sum(1 for x in prof.powerups if x.name == nm)}" for nm in names])
            card = next(x for x in prof.powerups if x.name == n)
            print(prof.sell_power(card)[1])


def main():
    print("=== GRIDIRON DECK ===")
    print("Kicking meter and weather are live. Build your deck.")
    prof = Profile()
    prof.add_power("Adrenaline")
    while True:
        print(f"\nMenu  (Level {prof.level}, coins {prof.coins})")
        c = pick(["Play game", "Shop", "Card library", "Lineup", "Quit"], "Choose")
        if c == "Quit":
            break
        if c == "Shop":
            shop(prof); continue
        if c == "Card library":
            library(prof); continue
        if c == "Lineup":
            prof.lineup.autofill()
            print(f"Lineup: {len(prof.lineup.player_pool())} players, "
                  f"{len(prof.lineup.power_pool())} power-ups (autofilled)")
            continue
        if not prof.can_play():
            print("You need a quarterback before you can play.")
            continue
        Game(prof).play()
        shop(prof)


if __name__ == "__main__":
    main()
