r"""Génère tout l'audio de Sunden avec MiniMax Music 3 (ComfyUI, workflow `sound_and_music`).

Aucune synthèse par le code : chaque son est un enregistrement généré par le modèle à partir d'une
description d'instruments acoustiques, puis découpé, fondu et normalisé (voir AUDIO_THEME.md).

Usage (ComfyUI doit tourner sur http://127.0.0.1:8188) :
    "C:\Users\cleme\AppData\Local\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI\.venv\Scripts\python.exe" ^
        tools/generate_audio.py                 # génère ce qui manque
        tools/generate_audio.py sword_hit       # seulement ces sons (régénère)
        tools/generate_audio.py --list          # liste des sons
"""
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, r"C:\Users\cleme\.claude\skills\game-sound-designer\scripts")
import comfy_audio_gen as gen  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SFX = ROOT / "assets" / "audio" / "sfx"
MUSIC = ROOT / "assets" / "audio" / "music"

SPACE = "short open-air stone ruin reverb in a forest clearing"
SHORT = "[intro]\n[outro]"
LONG = "[intro]\n[bridge]\n[outro]"


def caption(style, mood, tempo, lead, arrangement):
    return (f"Global Metadata\nStyle: {style}\nMood: {mood}\nTempo: {tempo}\n\n"
            f"Vocal Details\nInstrumental track - No vocals. The lead role is carried by {lead}.\n\n"
            f"Arrangement\n{arrangement}")


# nom, dossier, max_duration, découpe finale, peak dB, variantes, mono, fondu de sortie, caption
SOUNDS = [
    # ------------------------------------------------------------------ héros
    ("sword_swing", SFX, 1.5, 0.32, -6.0, 4, True, 0.08, caption(
        "Acoustic Percussion Earcon / Quick Brushed Swipe Accent",
        "Swift, airy, agile, heroic fairy-tale knight",
        "140 BPM in D Dorian",
        "wire brushes swept fast across a bodhran frame drum skin and a bowed crotale",
        "Opens at time zero with one very fast wire-brush sweep across a tight frame drum skin, "
        f"rising into a tiny bright bowed crotale shimmer on A5, cut short and dry, {SPACE}, "
        "gone into silence within a third of a second.")),
    ("sword_hit", SFX, 1.5, 0.5, -3.0, 4, True, 0.1, caption(
        "Orchestral Percussion Single Impact / Tuned Metal Strike",
        "Punchy, satisfying, decisive, heroic",
        "120 BPM in D Dorian",
        "a tuned iron anvil, a muted orchestral timpani and crotales",
        "Opens immediately at time zero with one sharp forceful strike on a tuned iron anvil in D5 "
        "layered with a dry muted timpani hit in D2 and a bright crotale ping on A5, "
        f"{SPACE}, decaying quickly into silence.")),
    ("spin_attack", SFX, 2.0, 0.9, -3.0, 2, True, 0.2, caption(
        "Orchestral Percussion Accent / Swirling Metal Flourish",
        "Powerful, sweeping, triumphant finishing blow",
        "132 BPM in D Dorian",
        "a suspended cymbal played with mallets, a tuned iron anvil and orchestral timpani",
        "Opens at time zero with a fast rolling suspended cymbal swell circling upward, landing on a "
        "forceful tuned anvil strike in D5 with a big orchestral timpani hit on D2 and a ringing "
        f"open fifth on crotales, {SPACE}, ringing out briefly into silence.")),
    ("dodge_roll", SFX, 1.5, 0.42, -8.0, 3, True, 0.1, caption(
        "Acoustic Percussion Earcon / Soft Rolling Frame Drum Gesture",
        "Light, nimble, quick, tumbling",
        "150 BPM in D Dorian",
        "a frame drum played with soft brushes and a wooden shaker",
        "Opens at time zero with a quick soft brushed roll on a bodhran frame drum tumbling downward "
        f"with a short wooden shaker rattle, ending on one muted low tap, {SPACE}, then silence.")),
    ("footstep", SFX, 1.5, 0.16, -18.0, 4, True, 0.06, caption(
        "Minimalist Acoustic Percussion / Single Soft Tap",
        "Discreet, light, grounded, walking on old stone and earth",
        "100 BPM in D Dorian",
        "a single soft felt mallet tap on a low frame drum",
        "Opens at time zero with one single soft muted felt mallet tap on a low frame drum, "
        "very short and dry, decaying immediately into complete silence with no further notes.")),
    ("hero_hurt", SFX, 1.5, 0.6, -4.0, 3, True, 0.12, caption(
        "Orchestral Percussion & Strings Stab / Dissonant Accent",
        "Painful, sudden, alarming setback",
        "110 BPM in D Dorian",
        "a low pizzicato double bass, a cello stab and a muted timpani",
        "Opens at time zero with a hard dry muted timpani hit and a harsh low pizzicato double bass "
        "on D2 clashing with a short accented cello stab on G sharp 2, a tense tritone, "
        f"{SPACE}, decaying quickly into silence.")),
    ("hero_death", SFX, 6.0, 4.0, -2.0, 1, False, 1.2, caption(
        "Orchestral Defeat Stinger / Descending Lament",
        "Somber, defeated, tender, fairy-tale ending",
        "Slow (64 BPM) in D Dorian",
        "a solo cello, a wooden flute, a concert harp and soft timpani",
        "Opens at time zero with a soft timpani roll and a solo cello playing a slow descending line "
        "A3, F3, E3, D3 answered by a fragile wooden flute, closing on a quiet open D minor chord on "
        f"concert harp, {SPACE}, fading gently into silence.")),
    # ------------------------------------------------------------------ slime
    ("slime_windup", SFX, 1.5, 0.55, -6.0, 2, True, 0.1, caption(
        "Acoustic Earcon / Rising Wobbly Glissando",
        "Comic, gooey, building tension, cartoon warning",
        "100 BPM in D Dorian",
        "a cello glissando played sul ponticello and a low rosewood marimba",
        "Opens at time zero with a low rosewood marimba tremolo on D2 under a wobbling cello "
        f"glissando sliding upward from D2 to A2 with a quick vibrato, {SPACE}, stopping abruptly.")),
    ("slime_jump", SFX, 1.5, 0.45, -6.0, 2, True, 0.1, caption(
        "Acoustic Earcon / Bouncy Upward Slide",
        "Playful, springy, comic, cartoon bounce",
        "120 BPM in D Dorian",
        "a pizzicato double bass slide and a low rosewood marimba",
        "Opens at time zero with a single bouncy pizzicato double bass note on A1 bending quickly "
        f"upward an octave, doubled by a soft low marimba note, {SPACE}, then silence.")),
    ("slime_hit", SFX, 1.5, 0.4, -4.0, 3, True, 0.08, caption(
        "Acoustic Percussion Earcon / Muted Soft Slap",
        "Squishy, comic, satisfying, cartoon",
        "120 BPM in D Dorian",
        "a muted low rosewood marimba dead stroke and a soft concert bass drum",
        "Opens at time zero with one damped dead-stroke on a low rosewood marimba bar on F2 with a "
        f"soft padded concert bass drum thump underneath, {SPACE}, very short, decaying into silence.")),
    ("slime_death", SFX, 2.0, 0.85, -3.0, 2, True, 0.2, caption(
        "Mallet Percussion Earcon / Bright Descending Cascade",
        "Rewarding, bubbly, comic, popping victory",
        "132 BPM in D Dorian",
        "a rosewood marimba and an orchestral glockenspiel",
        "Opens at time zero with a bright popping glockenspiel and marimba strike on D5 cascading "
        f"quickly downward A4, F4, D4 in a bubbly run, {SPACE}, ending into silence.")),
    # ------------------------------------------------------------------ squelette
    ("skeleton_windup", SFX, 1.5, 0.6, -6.0, 2, True, 0.1, caption(
        "Folk Percussion Earcon / Dry Rattling Tremolo",
        "Creepy but playful, rattling, warning, bony",
        "120 BPM in D Dorian",
        "folk bones percussion and a dry wooden xylophone",
        "Opens at time zero with a fast dry rattling tremolo of folk bones percussion and a wooden "
        f"xylophone trill on E5 and F5 crescendoing upward, {SPACE}, stopping abruptly.")),
    ("skeleton_attack", SFX, 1.5, 0.6, -4.0, 2, True, 0.12, caption(
        "Orchestral Percussion Single Impact / Heavy Downward Chop",
        "Brutal, heavy, threatening",
        "100 BPM in D Dorian",
        "orchestral timpani, a low brass stab and a rusty iron anvil",
        "Opens at time zero with one heavy downward strike of orchestral timpani on D2 with a short "
        f"low muted horn stab on F2 and a dull rusty anvil clank, {SPACE}, decaying into silence.")),
    ("skeleton_hit", SFX, 1.5, 0.4, -4.0, 3, True, 0.08, caption(
        "Folk Percussion Earcon / Dry Wooden Clack",
        "Bony, crisp, satisfying",
        "120 BPM in D Dorian",
        "a dry wooden xylophone and folk bones percussion",
        "Opens at time zero with one crisp dry wooden xylophone clack on A4 and a sharp click of folk "
        f"bones percussion, played col legno, {SPACE}, very short, decaying into silence.")),
    ("skeleton_death", SFX, 2.0, 1.0, -3.0, 2, True, 0.25, caption(
        "Folk Percussion Earcon / Tumbling Clattering Cascade",
        "Comic collapse, rattling, rewarding",
        "140 BPM in D Dorian",
        "a dry wooden xylophone, folk bones percussion and a woodblock",
        "Opens at time zero with a clattering cascade of dry wooden xylophone notes tumbling down "
        "D5, A4, F4, D4 with rattling folk bones percussion and a last hollow woodblock knock, "
        f"{SPACE}, ending into silence.")),
    ("skeleton_spawn", SFX, 2.0, 0.9, -6.0, 1, True, 0.2, caption(
        "Orchestral Percussion Swell / Rising Earthy Crescendo",
        "Ominous, rising from the earth, suspense",
        "90 BPM in D Dorian",
        "a low timpani roll and strings played col legno",
        "Opens at time zero with a low soft timpani roll on D2 crescendoing quickly with dry col legno "
        f"string taps and a single bony click at the peak, {SPACE}, stopping into silence.")),
    # ------------------------------------------------------------------ jeu
    ("wave_start", SFX, 5.0, 3.0, -2.0, 1, False, 0.8, caption(
        "Orchestral Fanfare Stinger / Heroic Call to Arms",
        "Heroic, rousing, adventurous, fairy-tale battle call",
        "120 BPM in D Dorian",
        "warm French horns, bodhran frame drums and orchestral timpani",
        "Opens at time zero with two bodhran hits and a bold French horn call rising D4, A4, D5, "
        f"answered by a timpani roll and a bright open fifth, {SPACE}, resolving and ringing out.")),
    # ------------------------------------------------------------------ niveau 1 : objets et décor
    ("pot_break", SFX, 1.5, 0.45, -5.0, 3, True, 0.12, caption(
        "Acoustic Percussion Earcon / Bright Clay Pot Strike",
        "Crisp, satisfying, small reward, playful",
        "130 BPM in D Dorian",
        "a clay udu drum and a rosewood marimba",
        "Opens at time zero with one sharp bright slap on a clay udu drum followed by a tiny "
        f"descending rosewood marimba flurry A4, F4, D4, {SPACE}, decaying into silence.")),
    ("crate_break", SFX, 1.5, 0.45, -5.0, 2, True, 0.12, caption(
        "Acoustic Percussion Earcon / Dry Wooden Crack",
        "Crunchy, satisfying, small reward",
        "120 BPM in D Dorian",
        "a wooden slit log drum, woodblocks and a frame drum",
        "Opens at time zero with one loud dry crack on a wooden slit log drum and two quick "
        f"tumbling woodblock knocks, {SPACE}, decaying into silence.")),
    ("heart_pickup", SFX, 1.5, 0.6, -6.0, 2, True, 0.2, caption(
        "Mallet Percussion Earcon / Rising Healing Chime",
        "Warm, comforting, restorative, gentle reward",
        "110 BPM in D Dorian",
        "a crystal celesta and concert harp harmonics",
        "Opens at time zero with a soft celesta note on D5 rising to A5 with a shimmering concert "
        f"harp harmonic, {SPACE}, ringing out softly into silence.")),
    ("gate_move", SFX, 2.0, 1.0, -6.0, 1, True, 0.25, caption(
        "Orchestral Percussion Earcon / Heavy Iron Rumble",
        "Heavy, mechanical, ancient, decisive",
        "90 BPM in D Dorian",
        "a low timpani roll, tubular bells and a muted iron anvil",
        "Opens at time zero with a short low rumbling timpani roll on D2 and a heavy clank of a "
        f"muted iron anvil with a low tubular bell, {SPACE}, settling into silence.")),
    ("spike_trap", SFX, 1.5, 0.32, -9.0, 2, True, 0.08, caption(
        "Metal Percussion Earcon / Sharp Scrape and Tap",
        "Sharp, dangerous, warning",
        "140 BPM in D Dorian",
        "crotales played with a scraping bow and a small anvil",
        "Opens at time zero with a very short sharp scrape of a bowed crotale on E6 and a dry small "
        f"anvil tap, {SPACE}, very short, decaying into silence.")),
    ("brazier_light", SFX, 3.0, 1.6, -4.0, 1, False, 0.5, caption(
        "Chamber Earcon / Warm Rising Bloom",
        "Hopeful, safe, warm, comforting rest",
        "80 BPM in D Dorian",
        "a concert harp, tubular bells and a solo cello",
        "Opens at time zero with an upward concert harp glissando into a warm low tubular bell on D3 "
        f"and a soft sustained cello open fifth, {SPACE}, blooming and fading gently into silence.")),
    ("chest_open", SFX, 4.0, 2.0, -3.0, 1, False, 0.5, caption(
        "Mallet Percussion Stinger / Treasure Discovery Arpeggio",
        "Wondrous, rewarding, magical discovery",
        "120 BPM in D Dorian",
        "a celesta, an orchestral glockenspiel and a concert harp",
        "Opens at time zero with a celesta and glockenspiel arpeggio rising D5, F5, A5, C6, D6 over "
        f"a sweeping concert harp glissando, landing on a bright open fifth, {SPACE}, ringing out.")),
    # ------------------------------------------------------------------ niveau 1 : boss
    ("boss_roar", SFX, 3.0, 1.4, -2.0, 2, False, 0.3, caption(
        "Orchestral Brass Swell / Monstrous Low Growl",
        "Menacing, enormous, furious, gelatinous monster king",
        "70 BPM in D Dorian",
        "a tuba, a contrabassoon, low trombones and a timpani roll",
        "Opens at time zero with a huge low brass growl from tuba, contrabassoon and trombones "
        "fluttering on D1 and G sharp 1 over a rolling timpani crescendo, "
        f"{SPACE}, cutting off into silence.")),
    ("boss_slam", SFX, 1.5, 0.9, -2.0, 2, True, 0.2, caption(
        "Orchestral Percussion Single Impact / Massive Ground Strike",
        "Crushing, enormous, earth-shaking",
        "80 BPM in D Dorian",
        "a concert bass drum, orchestral timpani and a low piano string cluster",
        "Opens at time zero with one massive strike on a concert bass drum and timpani on D1 "
        f"together with a low piano string cluster, {SPACE}, rumbling out into silence.")),
    ("victory", SFX, 6.0, 4.5, -2.0, 1, False, 1.2, caption(
        "Orchestral Victory Stinger / Triumphant Fanfare",
        "Triumphant, joyful, heroic relief, fairy-tale victory",
        "126 BPM in D Dorian",
        "warm French horns, trumpets, bodhran frame drums and a concert harp",
        "Opens at time zero with bodhran hits and a bright French horn and trumpet fanfare rising "
        "D4, A4, D5, F5, A5, landing on a radiant sustained D major chord with a harp glissando, "
        f"{SPACE}, ringing out.")),
    ("boss_theme", MUSIC, 120.0, None, -10.0, 1, False, 3.0, caption(
        "Folk-Medieval Orchestral Boss Battle Soundtrack",
        "Intense, dramatic, heroic, a giant crowned slime king in a torch-lit crypt",
        "148 BPM (4/4 Time) in D Dorian",
        "low brass, orchestral timpani, spiccato strings, a hurdy-gurdy and bodhran frame drums",
        "Relentless and driving across the full duration. Opens with pounding timpani and bodhran "
        "ostinato and low brass stabs, then spiccato strings and a gritty hurdy-gurdy play an urgent "
        "D Dorian theme. The middle bridge raises the tension with French horn calls and tremolo "
        "strings over a heavier drum pattern, keeping the mid range clear. The outro returns to the "
        "main ostinato and ends on a sustained open D chord for seamless looping, in a large stone "
        "crypt acoustic.")),
    # ------------------------------------------------------------------ musique
    ("combat_theme", MUSIC, 120.0, None, -10.0, 1, False, 3.0, caption(
        "Folk-Medieval Orchestral Battle Soundtrack",
        "Energetic, heroic, adventurous, fairy-tale skirmish in forest ruins",
        "136 BPM (4/4 Time) in D Dorian",
        "a hurdy-gurdy, a wooden flute, spiccato strings, bodhran frame drums and warm French horns",
        "Driving and steady across the full duration. Opens with a bodhran and frame drum ostinato "
        "and spiccato strings, then a hurdy-gurdy drone and a wooden flute play a lively D Dorian "
        "melody. The middle bridge brings fingerpicked lute, pizzicato double basses and French horn "
        "counter-melodies over orchestral timpani, keeping the mid range open and uncluttered. "
        "The outro returns to the drum ostinato and ends on a sustained open D chord for seamless "
        "looping, in a warm open-air stone ruin acoustic.")),
    ("forest_ambience", MUSIC, 90.0, None, -12.0, 1, False, 4.0, caption(
        "Sparse Ambient Acoustic Soundscape",
        "Calm, mysterious, ancient, quiet forest ruins at dusk with flickering torches",
        "Very slow (56 BPM) in D Dorian",
        "a bowed glass harmonica, a low cello drone and a distant wooden flute",
        "Extremely sparse and static across the full duration. A soft low cello drone on D2 and a "
        "rubbed glass harmonica hold long quiet tones, with rare distant wooden flute phrases and "
        "faint concert harp harmonics, leaving lots of space. Ends on the same sustained D drone "
        "for seamless looping, in a wide open-air forest acoustic.")),
]


RAW = ROOT / "audio_raw"          # enregistrements bruts du modèle (pour redécouper sans régénérer)
PASSAGE = 10.0                    # durée générée pour les SFX : en dessous, le modèle n'a pas le temps de jouer
MIN_PEAK_DB = -30.0               # un passage plus faible est rejeté (sinon on normaliserait du souffle)
GOOD_SCORE = 12.0                 # coupe nette : attaque franche, pas de 2e frappe, vraie décroissance
# Le modèle joue de la musique continue : on lui demande de répéter lentement le geste avec des
# silences, puis on récolte les meilleures répétitions.
SPARSE = ("A sparse slow solo passage that plays the following short gesture, then rests in complete "
          "silence for two full beats, then repeats it with small natural variations, many times. ")


def env_db(x, sr, hop_s=0.01):
    hop = max(1, int(hop_s * sr))
    env = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, len(x) - hop, hop)])
    return 20 * np.log10(env + 1e-9), hop


def harvest(wave, sr, length):
    """Repère dans un passage les attaques franches et note chaque coupe de `length` secondes :
    force de l'attaque, contraste avec ce qui précède, et netteté de la décroissance.
    Renvoie [(score, début en échantillons), ...]."""
    x = wave.mean(axis=0)
    db, hop = env_db(x, sr)
    skip = 15                                   # les 150 premières ms contiennent souvent un clic
    if len(db) <= skip + 10:
        return []
    top = db[skip:].max()
    if 20 * np.log10(np.abs(x[skip * hop:]).max() + 1e-9) < MIN_PEAK_DB:
        return []
    n = max(4, int(length * sr / hop))
    q = max(1, n // 4)
    out = []
    for i in range(skip + 5, len(db) - 1):
        pre = db[i - 5:i].min()
        if db[i] < top - 10.0 or db[i] - pre < 8.0 or db[i] < db[i - 1] or db[i] < db[i + 1] - 3.0:
            continue
        j = i
        while j > skip and db[j - 1] < db[j] - 1.0 and i - j < 5:     # pied de la montée
            j -= 1
        seg = db[j:j + n]
        if len(seg) < n * 0.9:
            continue
        decay = seg[:q].mean() - seg[-q:].mean()                     # dB perdus sur la coupe
        score = (db[i] - top) + 0.5 * (db[i] - pre) + 0.8 * decay
        if seg[q:].max() > seg[:q].max() - 2.0:                      # une 2e frappe dans la coupe
            score -= 12.0
        if decay < 6.0:                                              # son qui tient au lieu de s'éteindre
            score -= 8.0
        out.append((score, j * hop))
    return out


def slices_from(entry, passages, sr):
    """Choisit les meilleures coupes dans tous les passages, sans chevauchement."""
    name, folder, max_dur, trim, peak, variants, mono, fade_out, cap = entry
    cands = []
    for k, wave in enumerate(passages):
        cands += [(score, k, start) for score, start in harvest(wave, sr, trim)]
    cands.sort(reverse=True)
    picked = []
    for score, k, start in cands:
        if all(k != pk or abs(start - ps) > trim * sr for _, pk, ps in picked):
            picked.append((score, k, start))
        if len(picked) == variants:
            break
    pre = int(0.002 * sr)
    return [(score, passages[k][:, max(0, start - pre):start + int(trim * sr)]) for score, k, start in picked]


def finish(entry, wave, sr, target, score=None):
    name, folder, max_dur, trim, peak, variants, mono, fade_out, cap = entry
    if mono and wave.shape[0] > 1:
        wave = wave.mean(axis=0, keepdims=True)
    wave = gen.post_process_audio(wave, sr, mono=False, trim_silence=trim is None, trim_duration=trim,
                                  fade_in=0.002 if folder == SFX else 0.5,
                                  fade_out=fade_out, target_db=peak)
    if target.suffix == ".mp3":
        save_mp3(wave, sr, target)
    else:
        gen.save_audio_file(wave, sr, target)
    extra = f"  score {score:5.1f}" if score is not None else ""
    print(f"+ {target.relative_to(ROOT)}  {wave.shape[1] / sr:.2f}s{extra}", flush=True)


def targets_of(entry):
    name, folder = entry[0], entry[1]
    ext = ".mp3" if folder == MUSIC else ".wav"
    if entry[5] == 1:
        return [folder / f"{name}{ext}"]
    return [folder / f"{name}_{i + 1}{ext}" for i in range(entry[5])]


def run_model(cap, max_dur, seed, prefix):
    lyrics = SHORT if max_dur <= 10.0 else LONG
    cap, lyrics = gen.sanitize_instrumental(cap, lyrics, max_dur)
    prompt = gen.build_sound_and_music_api_prompt(
        caption=cap, lyrics=lyrics, max_duration=max_dur, seed=seed,
        tiled_decode=max_dur > 15.0, filename_prefix=f"audio/sunden_{prefix}")
    pid = gen.queue_prompt(gen.DEFAULT_COMFY_URL, prompt)
    hist = gen.wait_for_completion(gen.DEFAULT_COMFY_URL, pid, timeout=1800)
    return gen.decode_audio_bytes(gen.fetch_audio_bytes(gen.DEFAULT_COMFY_URL, hist))


def raw_passages(name):
    out = []
    for f in sorted(RAW.glob(f"{name}_p*.flac")):
        w, sr = gen.decode_audio_bytes(f.read_bytes())
        out.append(w)
    return out, (sr if out else 44100)


MIN_KEEP = 8.0                    # en dessous, une variante est jugée trop molle et n'est pas gardée


def cut_and_save(entry, passages, sr):
    picked = slices_from(entry, passages, sr)
    kept = [p for p in picked if p[0] >= MIN_KEEP] or picked[:1]
    targets = targets_of(entry)
    for target in targets:
        target.unlink(missing_ok=True)
    if len(targets) > 1:                         # variantes renumérotées 1..n
        targets = [targets[0].with_name(f"{entry[0]}_{i + 1}{targets[0].suffix}") for i in range(len(kept))]
    for target, (score, wave) in zip(targets, kept):
        finish(entry, wave, sr, target, score)
    return len(kept)


def generate(entry, force=False):
    name, folder, max_dur, trim, peak, variants, mono, fade_out, cap = entry
    targets = targets_of(entry)
    if not force and all(t.exists() for t in targets):
        print(f"= {name} (déjà généré)")
        return
    RAW.mkdir(exist_ok=True)
    (RAW / ".gdignore").touch()
    base_seed = random.randint(100_000, 999_999_999)

    if trim is None:                                            # musique : on garde tout le morceau
        for old in RAW.glob(f"{name}_p*.flac"):
            old.unlink()
        wave, sr = run_model(cap, max_dur, base_seed, name)
        gen.save_audio_file(wave, sr, RAW / f"{name}_p1.flac")
        finish(entry, wave, sr, targets[0])
        return

    # SFX : plusieurs passages de 10 s, puis on récolte les meilleures attaques
    passages, sr = raw_passages(name)           # on complète les passages déjà enregistrés
    first = len(passages)
    sparse = cap.replace("Arrangement\n", "Arrangement\n" + SPARSE, 1)
    for k in range(first, first + 6):
        good = sum(1 for p in passages for score, _ in harvest(p, sr, trim) if score >= GOOD_SCORE)
        if k - first >= 2 and good >= variants + 1:
            break
        wave, sr = run_model(sparse, PASSAGE, base_seed + k * 10007, f"{name}_p{k + 1}")
        gen.save_audio_file(wave, sr, RAW / f"{name}_p{k + 1:02d}.flac")
        passages.append(wave)
    got = cut_and_save(entry, passages, sr)
    if got < variants:
        print(f"! {name} : {got}/{variants} variantes seulement")


def retrim(entry):
    passages, sr = raw_passages(entry[0])
    if not passages:
        return
    if entry[3] is None:
        finish(entry, passages[0], sr, targets_of(entry)[0])
    else:
        cut_and_save(entry, passages, sr)


def save_mp3(wave, sr, path):
    """MP3 192 kbit/s, lu en boucle par Godot (AudioStreamMP3) : le PyAV de ComfyUI n'a pas libvorbis."""
    import av
    path.parent.mkdir(parents=True, exist_ok=True)
    layout = "mono" if wave.shape[0] == 1 else "stereo"
    with av.open(str(path), mode="w") as container:
        stream = container.add_stream("libmp3lame", rate=sr, layout=layout)
        stream.bit_rate = 192_000
        pts = 0
        for start in range(0, wave.shape[1], 4096):
            chunk = np.ascontiguousarray(wave[:, start:start + 4096].astype(np.float32))
            frame = av.AudioFrame.from_ndarray(chunk, format="fltp", layout=layout)
            frame.sample_rate = sr
            frame.pts = pts
            pts += chunk.shape[1]
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode(None):
            container.mux(packet)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--list" in sys.argv:
        for e in SOUNDS:
            print(e[0])
        return
    chosen = [e for e in SOUNDS if not args or e[0] in args]
    for e in chosen:
        if "--retrim" in sys.argv:
            retrim(e)
        else:
            generate(e, force=bool(args))
    print("TERMINE")


if __name__ == "__main__":
    main()
