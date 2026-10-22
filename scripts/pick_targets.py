"""Pick one validator per client class from the latest survey: the one with the most
leader slots left in the epoch, so its windows come often. Prints identities."""
import glob
import json
import sys

from itb.report import client_class

CLASSES = sys.argv[1:] or ["4.3.2 jito", "4.3.2 bam", "4.3.2 plain", "26.10.4 jito", "26.10.4 bam",
                           "4.3.0 jito", "26.10.3 jito", "4.5.0-alpha.2 jito", "4.5.0-alpha.2 plain"]
sv = json.load(open(sorted(glob.glob("data/survey_*.json"))[-1]))
for c in CLASSES:
    cands = [l for l in sv["leaders"] if l.get("version") and client_class(l) == c and len(l["slots_ahead"]) >= 32]
    if not cands:
        print(f"# no leader for {c}", file=sys.stderr)
        continue
    best = max(cands, key=lambda l: len(l["slots_ahead"]))
    print(best["identity"], f"# {c}, {len(best['slots_ahead'])} slots left", file=sys.stderr)
    print(best["identity"])
