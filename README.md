# Gridiron Deck

A football deck-builder you play in the terminal or in a window. Build a
roster, open packs, set your lineup, and call plays against the CPU in
whatever weather the game throws at you.

Version 1.0.0

## What it does

**Roster building.** 17 fixed depth slots plus a kicker. Starters are
always rated above their backups, and you can promote anyone into a
starting job — the man he replaces drops down the chart. Your library
holds unlimited cards and you can sell spares for coins.

**Packs with rarity.** Standard through Mythic, with the odds printed on
every pack. Four rarity tiers — common, rare, epic, legendary — and
rarity decides how good the card rolls. Player packs always deal three
distinct positions.

**Weather that matters.** Clear most of the time, but bad weather gets
commoner as the game wears on. Heavy rain raises fumble odds on runs,
shortens deep passes and tightens the kicking bar. Snow drains stamina
fast and rewards fresh legs off the bench. The field itself changes —
mud slicks in the rain, near-white turf with frozen patches in the snow.

**A kicking meter.** Every field goal and every PAT is a timing bar. A
marker sweeps and you stop it: how close you land to centre decides the
kick. Longer attempts sweep faster, your kicker's `kck` sets the width of
the good zone, and bad weather narrows it. Touchdowns are 6 points, then
you kick the PAT or go for two.

**Two-point tries that are real plays.** Not a dice roll. Pick a
goal-line formation, pick a run or a quick pass, pick who carries it, and
watch the CPU show its hand. Chemistry between your player and the play
sets the base odds, and the CPU's call moves them — a perfect-fit power
run into a stacked box converts about 74%, a poor-fit pass into coverage
sits near 35%.

**Play chains.** Run the ball, then call Play Action, and the defence
bites. Chains add no flat yards; they raise your odds of reaching a
breakaway band, and the CPU's call sets how high you can go. Play tiles
show the chain potential before you call it, and a banner fires across
the field when one lands.

## Running it

Both files must sit in the same folder.

    python3 gridiron_gui.py     # graphical version (tkinter)
    python3 gridiron_deck.py    # terminal version

Requires Python 3. tkinter ships with most installs; on Linux you may need
`sudo apt install python3-tk`.

## Files

- `gridiron_deck.py` — the engine. Players, plays, formations, weather,
  the kicking meter, play chains, packs and rarity.
- `gridiron_gui.py` — the tkinter front end. Home screen, game, lineup,
  card library, pro shop.

Both files carry a `VERSION` constant. Keep them in step.

## Status

v1.0.0 — complete and playable. Built and tested on Windows.

