"""premise.py — combinatorial premise composer for /dm:dnd prep.

Rolls one entry from each of four orthogonal axes (setting × conflict ×
antagonist × twist) from data/premise-seeds.yaml, colored by a tone drawn from
data/tones.yaml, and prints a labeled scaffold with an explicit reconcile
instruction. The axes are tone-agnostic on purpose: forcing independent random
choices is what stops 'grim' collapsing to one trope. The model turns the
scaffold into a coherent premise; discarding a clashing axis is expected.
"""
from __future__ import annotations

import pathlib
import random

import yaml

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"
AXES = ("setting", "conflict", "antagonist", "twist")

_INSTRUCTION = (
    "Reconcile into ONE coherent premise in the chosen tone. Discard any axis "
    "that fights the others — orthogonality is the point, coherence is your job. "
    "Do not default to the nearest cliché — especially avoid the frontier-town / "
    "sealed-mine / missing-people default that this tool exists to break."
)


def load_tones(path: pathlib.Path | None = None) -> list[dict]:
    p = path or DATA / "tones.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8"))["tones"]


def load_seeds(path: pathlib.Path | None = None) -> dict:
    p = path or DATA / "premise-seeds.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def tone_by_id(tone_id: str, tones: list[dict]) -> dict | None:
    for t in tones:
        if t["id"] == tone_id:
            return t
    return None


def roll_premise(tone_id, tones: list[dict], seeds: dict, rng: random.Random) -> dict:
    if tone_id is None:
        # surprise-me: roll the tone too, so prep has a concrete tone to author
        # the whole bible in. Roll tone BEFORE axes so a given seed is stable.
        tone = rng.choice(tones)
        tone_id = tone["id"]
    else:
        tone = tone_by_id(tone_id, tones)
        if tone is None:
            raise KeyError(f"unknown tone: {tone_id!r}")
    rolled = {axis: rng.choice(seeds["axes"][axis]) for axis in AXES}
    rolled.update(
        tone=tone_id,
        descriptor=tone["descriptor"],
        mood_note=tone["mood_note"],
        exemplars=seeds["exemplars"].get(tone_id, []),
    )
    return rolled


def format_scaffold(rolled: dict) -> str:
    lines = [
        f"PREMISE SCAFFOLD — tone: {rolled['tone']} ({rolled['descriptor']})",
        f"  mood: {rolled['mood_note']}",
        "",
        "Rolled axes (independent — reconcile, don't concatenate):",
        f"  setting    : {rolled['setting']}",
        f"  conflict   : {rolled['conflict']}",
        f"  antagonist : {rolled['antagonist']}",
        f"  twist      : {rolled['twist']}",
        "",
        "Exemplars for this tone (quality bar, not to be reused verbatim):",
    ]
    lines += [f"  - {ex}" for ex in rolled["exemplars"]]
    lines += ["", _INSTRUCTION]
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    import sys

    # Force UTF-8 output: the scaffold and seed content use em-dashes/× and the
    # Windows console default (cp1252) would emit them as bytes a UTF-8 reader
    # (the DM tool loop) sees as replacement chars.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description="Roll a combinatorial premise scaffold for prep.")
    ap.add_argument("--tone", default=None, help="tone id from data/tones.yaml (omit to roll one)")
    ap.add_argument("--seed", type=int, default=None, help="seed the roll (for reproducibility/tests)")
    args = ap.parse_args()

    tones = load_tones()
    seeds = load_seeds()
    rng = random.Random(args.seed)
    try:
        rolled = roll_premise(args.tone, tones, seeds, rng)
    except KeyError as e:
        valid = ", ".join(t["id"] for t in tones)
        # e.args[0] avoids KeyError.__str__ re-quoting the message.
        print(f"error: {e.args[0]}. valid tones: {valid}", file=sys.stderr)
        raise SystemExit(1)
    print(format_scaffold(rolled))
