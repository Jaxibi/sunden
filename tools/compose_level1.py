"""Compose le niveau 1 (« La Crypte Gluante ») et l'écrit dans levels/niveau1.json.

La carte est dessinée en ASCII (1 case = 1 m) par tampons de rectangles, puis vérifiée :
tous les points importants doivent être atteignables depuis le départ. Le JSON produit reste
lisible et modifiable à la main (voir LEVEL_DESIGN.md pour l'intention de chaque salle).

Légende
  ' ' vide      '#' mur / roche   'T' forêt dense   '.' herbe   ',' terre   '_' dalles
  '^' piques    '=' herse         'P' pilier        'p' pilier brisé   't' torche   'r' rocher
  'L' stèle     '%' ossements     'o' jarre         'c' caisse    'B' brasero    'C' coffre
  'S' départ    's' slime         'k' squelette     'K' boss      '1'..'9' apparitions de la rencontre n

Usage :  python tools/compose_level1.py
"""
import json
from collections import deque
from pathlib import Path

W, H = 60, 64
OUT = Path(__file__).resolve().parent.parent / "levels" / "niveau1.json"
grid = [[" "] * W for _ in range(H)]
gates = {}


def rect(x0, z0, x1, z1, ch):
    for z in range(z0, z1 + 1):
        for x in range(x0, x1 + 1):
            grid[z][x] = ch


def put(x, z, ch):
    grid[z][x] = ch


def gate(gid, cells, open_):
    gates[gid] = {"cells": [list(c) for c in cells], "open": open_}
    for x, z in cells:
        grid[z][x] = "="


def row_cells(x0, x1, z):
    return [(x, z) for x in range(x0, x1 + 1)]


def col_cells(x, z0, z1):
    return [(x, z) for z in range(z0, z1 + 1)]


# =========================================================================== forêt (tutoriel)
rect(13, 32, 59, 63, "T")
rect(0, 42, 12, 63, "T")
# départ
rect(45, 53, 56, 60, ".")
rect(47, 55, 52, 58, ",")
put(52, 57, "S")
put(49, 55, "L")                      # stèle : premiers pas
for x, z in ((46, 54), (55, 54), (55, 59)):
    put(x, z, "r")
# chemin vers l'ouest, bordé de jarres (apprendre à frapper sans danger)
rect(38, 55, 46, 57, ",")
for x, z in ((44, 55), (43, 57), (41, 55), (40, 57)):
    put(x, z, "o")
put(42, 56, "c")
# clairière du slime solitaire
rect(34, 47, 42, 54, ".")
rect(36, 49, 40, 52, ",")
put(37, 49, "s")
put(34, 47, "r")
put(42, 50, "r")
put(35, 53, "o")
# passage en ruine piégé : apprendre la roulade (2 rangées de piques décalées)
rect(35, 41, 40, 46, "#")
rect(36, 41, 39, 46, ",")
rect(36, 43, 39, 44, "^")
put(36, 46, "t")
put(39, 46, "t")
# clairière fermée : 1re rencontre
rect(23, 33, 38, 40, ".")
rect(28, 35, 33, 39, "_")
for x, z in ((25, 35), (36, 35), (25, 39)):
    put(x, z, "P")
put(36, 39, "p")
for x, z in ((24, 34), (37, 34), (24, 40), (33, 37), (31, 34)):
    put(x, z, "1")
put(29, 34, "B")                      # brasero 1 : premier point de retour
put(26, 34, "t")
put(32, 34, "t")
for x, z in ((23, 37), (23, 33)):
    put(x, z, "o")
gate("e1_in", row_cells(36, 39, 41), True)
rect(27, 31, 28, 32, ",")
gate("e1_out", row_cells(27, 28, 32), False)

# =========================================================================== crypte
rect(0, 0, 59, 31, "#")
rect(0, 30, 12, 41, "#")
# hall (centre, carrefour)
rect(22, 18, 33, 29, "_")
for x, z in ((24, 20), (31, 20), (24, 27), (31, 27)):
    put(x, z, "P")
put(27, 27, "B")                      # brasero 2 : avant le boss
for x, z in ((22, 18), (33, 18), (22, 29), (33, 29)):
    put(x, z, "t")
for x, z in ((27, 20), (29, 23), (25, 24), (30, 26), (26, 22)):
    put(x, z, "2")
for x, z in ((23, 28), (32, 28), (32, 19)):
    put(x, z, "o")
rect(27, 30, 28, 31, "_")
gate("hall_s", row_cells(27, 28, 30), True)
# salle des piques (à l'ouest)
rect(3, 18, 16, 29, "_")
rect(5, 21, 14, 22, "^")
rect(5, 26, 14, 27, "^")
for x, z in ((4, 18), (15, 18), (4, 29), (15, 29)):
    put(x, z, "t")
for x, z in ((6, 19), (13, 24), (8, 24), (6, 28), (12, 19)):
    put(x, z, "3")
put(3, 24, "o")
put(16, 20, "o")
rect(17, 23, 21, 24, "_")
gate("spk", col_cells(17, 23, 24), True)
gate("hall_w", col_cells(21, 23, 24), True)
# alcôve du trésor (facultative, au sud de la salle des piques)
rect(6, 30, 7, 33, "_")
rect(6, 31, 7, 32, "^")
rect(3, 34, 10, 39, "_")
put(6, 38, "C")                       # Bottes de rafale
put(4, 36, "k")
put(9, 36, "k")
for x, z in ((3, 39), (10, 39), (3, 34), (10, 34)):
    put(x, z, "o")
put(4, 38, "c")
put(9, 38, "c")
put(6, 34, "t")
# ossuaire (au nord de la salle des piques)
rect(3, 3, 16, 14, "_")
for x, z in ((6, 6), (13, 6), (6, 11), (13, 11)):
    put(x, z, "p" if (x + z) % 2 else "P")
for x, z in ((4, 4), (9, 5), (15, 9), (11, 13), (4, 12), (8, 8)):
    put(x, z, "%")
for x, z in ((3, 3), (16, 3), (3, 14), (16, 14)):
    put(x, z, "t")
for x, z in ((5, 8), (10, 4), (14, 12), (9, 10), (12, 8), (5, 13)):
    put(x, z, "4")
rect(9, 15, 10, 17, "_")
gate("oss", row_cells(9, 10, 16), True)
# raccourci : ossuaire -> hall (ne s'ouvre qu'une fois l'ossuaire vaincu)
rect(17, 8, 25, 9, "_")
rect(24, 10, 25, 17, "_")
gate("oss_e", col_cells(17, 8, 9), True)
gate("short", row_cells(24, 25, 17), False)
put(20, 9, "%")
# vers le boss : porte scellée à l'est du hall
rect(34, 23, 39, 24, "_")
gate("boss", col_cells(34, 23, 24), False)
gate("arena", col_cells(39, 23, 24), True)
# arène du Roi Gluant
rect(40, 6, 56, 25, "_")
for x, z in ((43, 9), (53, 9), (43, 22), (53, 22)):
    put(x, z, "P")
for x, z in ((40, 6), (56, 6), (40, 25), (56, 25), (48, 6)):
    put(x, z, "t")
put(48, 14, "K")
for x, z in ((41, 7), (55, 24)):
    put(x, z, "%")
# salle du trésor finale
rect(47, 4, 48, 5, "_")
gate("exit", row_cells(47, 48, 5), False)
rect(44, 1, 51, 3, "_")
put(47, 2, "C")
put(44, 1, "t")
put(51, 1, "t")

# =========================================================================== données
data = {
    "name": "La Crypte Gluante",
    "map": ["".join(r) for r in grid],
    "gates": gates,
    "encounters": [
        {"id": "e1", "name": "La Clairière", "marker": "1", "rect": [24, 34, 37, 40],
         "gates": ["e1_in", "e1_out"], "open_on_clear": [],
         "hint": "Enchaîne 3 coups : le 3e tournoie autour de toi",
         "waves": [{"slime": 2}, {"slime": 3}]},
        {"id": "e2", "name": "Le Vestibule", "marker": "2", "rect": [23, 19, 32, 28],
         "gates": ["hall_s", "hall_w"], "open_on_clear": [],
         "hint": "Le squelette lève son épée avant de frapper : roule sous le coup",
         "waves": [{"skeleton": 1}, {"skeleton": 1, "slime": 2}]},
        {"id": "e3", "name": "La Salle des Piques", "marker": "3", "rect": [4, 19, 15, 28],
         "gates": ["spk"], "open_on_clear": [],
         "hint": "Les piques blessent aussi les monstres",
         "waves": [{"slime": 3}, {"skeleton": 2, "slime": 1}]},
        {"id": "e4", "name": "L'Ossuaire", "marker": "4", "rect": [4, 4, 15, 13],
         "gates": ["oss", "oss_e"], "open_on_clear": ["short", "boss"],
         "clear_message": "Un sceau se brise dans le hall...",
         "waves": [{"skeleton": 2, "slime": 2}, {"skeleton": 2, "slime": 3}]},
    ],
    "boss": {"rect": [41, 7, 55, 24], "gates": ["arena"], "open_on_victory": ["arena", "exit"],
             "name": "Le Roi Gluant"},
    "zones": [
        {"name": "Crypte d'Émeraude", "rect": [0, 30, 12, 41], "sun": 0.55, "music": "dungeon"},
        {"name": "Forêt de Sunden", "rect": [13, 32, 59, 63], "sun": 1.0, "music": "forest"},
        {"name": "Trône du Roi Gluant", "rect": [40, 0, 59, 25], "sun": 0.42, "music": "dungeon"},
        {"name": "Crypte d'Émeraude", "rect": [0, 0, 39, 31], "sun": 0.55, "music": "dungeon"},
    ],
    "hints": [
        {"rect": [45, 53, 56, 60], "text": "ZQSD / stick gauche : se déplacer"},
        {"rect": [38, 54, 46, 58], "text": "J / clic gauche : frapper (les jarres cachent des cœurs)"},
        {"rect": [34, 47, 42, 54], "text": "Un slime ! Il se tasse avant de bondir : écarte-toi puis frappe"},
        {"rect": [36, 45, 39, 46], "text": "Espace / clic droit : roulade, invulnérable un instant"},
        {"rect": [6, 30, 7, 33], "text": "Les piques ont un rythme... ou une roulade"},
    ],
    "chests": {"6,38": "bottes", "47,2": "fin"},
}

# =========================================================================== vérifications
BLOCK = set("#TPptrL ")
start = next((x, z) for z in range(H) for x in range(W) if grid[z][x] == "S")
seen = {start}
todo = deque([start])
while todo:
    x, z = todo.popleft()
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, nz = x + dx, z + dz
        if 0 <= nx < W and 0 <= nz < H and (nx, nz) not in seen and grid[nz][nx] not in BLOCK:
            seen.add((nx, nz))
            todo.append((nx, nz))
must = [(x, z, grid[z][x]) for z in range(H) for x in range(W) if grid[z][x] in "BCKsk123456789o=c^"]
unreached = [m for m in must if (m[0], m[1]) not in seen]
for e in data["encounters"]:
    n = sum(1 for z in range(H) for x in range(W) if grid[z][x] == e["marker"])
    assert n >= 3, f"rencontre {e['id']} : seulement {n} points d'apparition"
for gid, g in gates.items():
    for x, z in g["cells"]:
        assert grid[z][x] == "=", f"herse {gid} écrasée en {x},{z}"
assert not unreached, f"cases inaccessibles : {unreached}"

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
counts = {c: sum(r.count(c) for r in data["map"]) for c in "^=oPtBCsk"}
print(f"OK {OUT.name} : {W}x{H}, {len(seen)} cases accessibles, {len(gates)} herses, {counts}")
for r in data["map"]:
    print(r)
