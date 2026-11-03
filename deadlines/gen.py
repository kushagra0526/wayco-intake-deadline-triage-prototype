"""Synthetic intake calls with known facts and the expected triage status."""
from __future__ import annotations

import random
from datetime import date, timedelta

from .rules import NOTICE, SOL

CITIES = {"NY": ["Brooklyn", "Queens", "the Bronx", "Buffalo", "Manhattan"], "CA": ["Los Angeles", "San Diego", "Fresno"],
          "TX": ["Houston", "Dallas", "San Antonio"], "FL": ["Miami", "Orlando", "Tampa"], "IL": ["Chicago", "Naperville"],
          "NJ": ["Newark", "Jersey City"], "GA": ["Atlanta", "Savannah"], "PA": ["Philadelphia", "Pittsburgh"]}
STATE_WORD = {"NY": "New York", "CA": "California", "TX": "Texas", "FL": "Florida", "IL": "Illinois", "NJ": "New Jersey",
              "GA": "Georgia", "PA": "Pennsylvania"}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]

BANKS = {
    "dev": {
        "where": ["It happened in {city}.", "I live in {city}, that's where it was.", "This was in {state}."],
        "local": ["A city bus hit my car.", "I tripped in a pothole on a city street.", "A police car rear-ended me.",
                  "The MTA bus ran a red light." ],
        "state": ["A state trooper hit me on the highway.", "A DOT truck backed into my car."],
        "private": ["Another driver ran the light.", "I slipped on a wet floor at a grocery store.",
                    "An Uber driver hit me.", "It wasn't a city bus, it was a private charter bus."],
        "work": ["I fell off a ladder at work."],
        "minor": ["My son got hurt, he's 9."],
        "medmal": ["The surgery went wrong and they left something in."],
    },
    "heldout": {
        "where": ["We were over in {city} when it happened.", "{city}, near downtown.", "This was down in {state}."],
        "local": ["A county sheriff's car? No, sorry, a city sanitation truck clipped me.",
                  "I hit a huge pothole and went over the handlebars.", "A public school bus sideswiped us.",
                  "The transit authority bus pulled out without looking."],
        "state": ["It was a Department of Transportation truck doing roadwork.",
                  "One of those state police cruisers, a state trooper, hit my bumper."],
        "private": ["Some guy in a pickup rear-ended me.", "A Lyft driver T-boned us.",
                    "I slipped at a restaurant, private place, not the city."],
        "work": ["My supervisor told me to move boxes and the shelf fell on me while working."],
        "minor": ["It's my daughter, she's only 12."],
        "medmal": ["I think it's malpractice, they misdiagnosed my fracture."],
    },
}


def date_phrase(rng, incident: date, call: date, split: str) -> tuple[str, bool]:
    """Spoken date for the incident. Returns (phrase, precise)."""
    days = (call - incident).days
    opts = []
    if days == 1:
        opts.append("yesterday")
    if 2 <= days <= 6:
        opts.append(f"last {WEEKDAYS[incident.weekday()]}" if split == "dev" else f"{WORDS[days] if days < 13 else days} days ago")
    if days % 7 == 0 and 7 <= days <= 70:
        w = days // 7
        opts.append(f"{w} weeks ago" if split == "dev" else f"{WORDS[w] if w < 13 else w} weeks ago")
    if split == "dev":
        opts.append(f"on {incident.month}/{incident.day}/{incident.year}")
        if days < 300:
            opts.append(f"on {incident:%B} {incident.day}")
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(incident.day % 10 if incident.day not in (11, 12, 13) else 0, "th")
        opts += [f"on the {incident.day}{suf} of {incident:%B}, {incident.year}", f"{incident:%b}. {incident.day}, {incident.year}"]
    return rng.choice(opts), True


def expected(incident, state, gov, flags, call):
    if flags:
        return flags[0]
    years, _ = SOL[state]
    sol = incident.replace(year=incident.year + years) if not (incident.month == 2 and incident.day == 29) \
        else incident + timedelta(days=365 * years)
    cands = [sol]
    if gov:
        cands.append(incident + timedelta(days=NOTICE[(state, gov)][0]))
    left = (min(cands) - call).days
    return "EXPIRED" if left < 0 else "URGENT" if left <= 30 else "SOON" if left <= 90 else "OK"


def calls(seed: int, split: str = "dev", n: int = 60):
    rng = random.Random(seed)
    bank = BANKS[split]
    out = []
    for i in range(n):
        call = date(2026, 11, 3) - timedelta(days=rng.randint(0, 200))
        state = rng.choice(sorted(SOL))
        kind = rng.choices(["private", "local", "state", "work", "minor", "medmal", "nodate", "noplace"],
                           [40, 25, 10, 6, 5, 4, 6, 4])[0]
        if kind == "state" and (state, "state") not in NOTICE:
            kind = "local"
        days = rng.choice([rng.randint(1, 60), rng.randint(60, 200), rng.randint(200, 900)])
        incident = call - timedelta(days=days)
        phrase, _ = date_phrase(rng, incident, call, split)
        story = rng.choice(bank["private" if kind in ("nodate", "noplace") else kind])
        where = rng.choice(bank["where"]).format(city=rng.choice(CITIES[state]), state=STATE_WORD[state])
        lines = [f"Agent: Thanks for calling, what happened?", f"Caller: {story}",
                 f"Agent: When was this?", f"Caller: It was {phrase}." if kind != "nodate" else
                 f"Caller: {rng.choice(['A while back.', 'Last summer I think.', 'Back in ' + incident.strftime('%B') + '.'])}",
                 f"Agent: And where?", f"Caller: {where}" if kind != "noplace" else "Caller: Just on the road near my place."]
        gov = kind if kind in ("local", "state") else None
        flags = {"work": ["ROUTE_WC"], "minor": ["ATTORNEY_REVIEW"], "medmal": ["ATTORNEY_REVIEW"],
                 "nodate": ["ASK"], "noplace": ["ASK"]}.get(kind, [])
        truth = expected(incident, state, gov, flags, call)
        out.append({"id": f"{split}-{seed}-{i}", "call": call, "transcript": "\n".join(lines), "truth": truth,
                    "incident": incident if kind != "nodate" else None, "state": state, "gov": gov, "kind": kind})
    return out
