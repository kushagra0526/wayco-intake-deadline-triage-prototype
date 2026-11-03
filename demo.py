"""Five intake calls, triaged for the deadline that runs first. Usage: python demo.py"""
from datetime import date

from deadlines.triage import flat_rule, triage

CALL = date(2026, 11, 3)
CALLS = [
    "Caller: The city bus ran the red and hit my car.\nCaller: It was the 4th of July.\nCaller: Over in Queens.",
    "Caller: A guy in a pickup rear-ended me.\nCaller: That was on 1/15/2025.\nCaller: Houston.",
    "Caller: I hit a pothole on a county road and broke my wrist.\nCaller: Five weeks ago.\nCaller: Atlanta, Georgia.",
    "Caller: A state trooper backed into me.\nCaller: It was 9/20/2026.\nCaller: Newark.",
    "Caller: I fell off scaffolding on the job site.\nCaller: Last Tuesday.\nCaller: Philadelphia.",
]

if __name__ == "__main__":
    for text in CALLS:
        t = triage(text, CALL)
        said = " / ".join(l.split(": ", 1)[1] for l in text.splitlines())
        print(f"> {said}")
        print(f"  {t.status:<10} state={t.state} government={t.government} incident={t.incident}"
              f"  (flat 2-year rule: {flat_rule(t.incident, CALL)})")
        if t.deadline:
            print(f"  first deadline {t.deadline:%d %b %Y} ({t.days_left} days) — {t.cite}")
        for r in t.reasons:
            print(f"  {r}")
        print()
