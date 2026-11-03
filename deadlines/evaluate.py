"""Score intake triage. Usage: python -m deadlines.evaluate dev|heldout"""
from __future__ import annotations

import json
import sys
from collections import Counter

from .gen import calls
from .triage import flat_rule, triage

SEEDS = {"dev": range(0, 20), "heldout": range(500, 540)}
DANGER = {"EXPIRED", "URGENT"}


def run(split):
    right = total = 0
    confusion = Counter()
    danger = danger_missed = danger_missed_flat = 0
    false_urgent = 0
    examples = []
    for seed in SEEDS[split]:
        for c in calls(seed, split):
            t = triage(c["transcript"], c["call"])
            total += 1
            right += t.status == c["truth"]
            if t.status != c["truth"]:
                confusion[f"{c['truth']}->{t.status}"] += 1
                if len(examples) < 10:
                    examples.append({"truth": c["truth"], "got": t.status, "kind": c["kind"], "reasons": t.reasons,
                                     "transcript": c["transcript"].splitlines()[1::2]})
            if c["truth"] in DANGER:
                danger += 1
                danger_missed += t.status not in DANGER
                danger_missed_flat += flat_rule(c["incident"], c["call"]) not in DANGER
            elif t.status in DANGER:
                false_urgent += 1
    return {"split": split, "status_right": f"{right}/{total}",
            "urgent_or_expired_cases": danger, "missed_by_triage": danger_missed,
            "missed_by_flat_2yr_rule": danger_missed_flat, "false_urgent": false_urgent,
            "confusion": dict(confusion), "examples": examples}


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1] if len(sys.argv) > 1 else "dev"), indent=1, default=str))
