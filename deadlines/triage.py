"""Read an injury intake call and say which deadline runs first.

Facts come from the caller's own words: when it happened (casual dates
relative to the call), where (city/state), who is at fault (government
vehicle, road, building vs private), and anything that takes the case out
of the simple rules (work injury, minor, death, medical care). Output is a
status for the firm plus the deadline and its statute.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta

from .rules import NOTICE, SOL, STATES

MONTHS = {m: i + 1 for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                          "september", "october", "november", "december"])}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})
MONTHS["sept"] = 9
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
NUMS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve".split())}
NUMS.update({"a": 1, "an": 1, "a couple of": 2, "a couple": 2, "a few": 3, "couple": 2})
NUM = r"(\d+|a couple of|a couple|couple|a few|an?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"

CITY_STATE = {
    "new york": "NY", "nyc": "NY", "brooklyn": "NY", "queens": "NY", "the bronx": "NY", "bronx": "NY", "manhattan": "NY",
    "staten island": "NY", "buffalo": "NY", "rochester": "NY", "yonkers": "NY",
    "los angeles": "CA", "san diego": "CA", "san jose": "CA", "oakland": "CA", "fresno": "CA", "sacramento": "CA",
    "houston": "TX", "dallas": "TX", "austin": "TX", "san antonio": "TX", "el paso": "TX", "fort worth": "TX",
    "miami": "FL", "orlando": "FL", "tampa": "FL", "jacksonville": "FL",
    "chicago": "IL", "aurora": "IL", "naperville": "IL",
    "newark": "NJ", "jersey city": "NJ", "paterson": "NJ", "trenton": "NJ",
    "atlanta": "GA", "savannah": "GA", "macon": "GA",
    "philadelphia": "PA", "philly": "PA", "pittsburgh": "PA", "allentown": "PA",
}
STATE_NAMES = {"new york": "NY", "california": "CA", "texas": "TX", "florida": "FL", "illinois": "IL",
               "new jersey": "NJ", "georgia": "GA", "pennsylvania": "PA", "ohio": "OH", "arizona": "AZ"}

LOCAL = re.compile(r"\b((?:city|county|municipal|town) (?:bus|truck|vehicle|van|car|street|road|sidewalk|employee|"
                   r"worker|park|garbage truck|sanitation truck|sheriff)|county sheriff|mta|nyc transit|metro|cta|septa|marta|dart|muni|public school|"
                   r"school bus|police (?:car|cruiser|officer)|cop car|fire truck|sanitation truck|city garbage truck|"
                   r"pothole|city sidewalk|park district|transit authority|public bus|city bus)\b", re.I)
STATE_GOV = re.compile(r"\b(state trooper|state police|state highway|state road|dot truck|department of transportation|"
                       r"state university|state[- ]owned|turnpike authority|nj transit|caltrans|txdot|penndot|gdot)\b", re.I)
NOT_GOV = re.compile(r"\b(not|wasn't|was not|isn't|no,? it was|private|charter|uber|lyft|taxi|cab)\b", re.I)
WORK = re.compile(r"\b(at work|on the job|on shift|my (?:boss|employer|supervisor|manager)|clocked in|"
                  r"while working|work(?:ing)? site|job ?site|warehouse i work)\b", re.I)
MINOR = re.compile(r"\b(my (?:son|daughter|kid|child|boy|girl)|(?:he|she)'?s? (?:only )?(\d{1,2})|"
                   r"years? old)\b", re.I)
DEATH = re.compile(r"\b(passed away|died|killed|funeral|wrongful death)\b", re.I)
MEDMAL = re.compile(r"\b(surgery went wrong|misdiagnos\w*|malpractice|the surgeon|doctor (?:messed|missed)|"
                    r"wrong medication)\b", re.I)


@dataclass
class Triage:
    status: str                      # EXPIRED | URGENT | SOON | OK | ATTORNEY_REVIEW | ROUTE_WC | ASK
    incident: date | None = None
    state: str | None = None
    government: str | None = None    # local | state | None
    deadline: date | None = None
    cite: str = ""
    days_left: int | None = None
    reasons: list[str] = field(default_factory=list)


def _n(tok: str) -> int:
    tok = tok.lower()
    return int(tok) if tok.isdigit() else NUMS[tok]


def _thanksgiving(year: int) -> date:
    d = date(year, 11, 1)
    first_thu = d + timedelta(days=(3 - d.weekday()) % 7)
    return first_thu + timedelta(weeks=3)


def _back(d: date, months: int) -> date:
    y, m = d.year, d.month - months
    while m <= 0:
        m += 12
        y -= 1
    day = min(d.day, [31, 29 if y % 4 == 0 and (y % 100 or y % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
    return date(y, m, day)


def incident_date(text: str, call: date) -> tuple[date | None, str]:
    """Parse the caller's date relative to the call. Returns (date, why-not)."""
    t = text.lower()
    if re.search(r"\byesterday\b", t):
        return call - timedelta(days=1), ""
    if re.search(r"\b(today|this morning|earlier today|tonight)\b", t):
        return call, ""
    m = re.search(rf"\b{NUM}\s+(day|week|month|year)s?\s+ago\b", t)
    if m:
        n, unit = _n(m.group(1)), m.group(2)
        if unit == "day":
            return call - timedelta(days=n), ""
        if unit == "week":
            return call - timedelta(weeks=n), ""
        if unit == "month":
            return _back(call, n), ""
        return _back(call, 12 * n), ""
    m = re.search(r"\blast (" + "|".join(WEEKDAYS) + r")\b", t)
    if m:
        wd = WEEKDAYS.index(m.group(1))
        back = (call.weekday() - wd) % 7 or 7
        return call - timedelta(days=back), ""
    m = re.search(r"\b(?:the )?day after thanksgiving\b", t)
    if m or "black friday" in t:
        y = call.year if _thanksgiving(call.year) + timedelta(days=1) <= call else call.year - 1
        return _thanksgiving(y) + timedelta(days=1), ""
    if "christmas eve" in t or "new year's eve" in t or "fourth of july" in t or "july 4th" in t:
        md = (12, 24) if "christmas" in t else ((12, 31) if "new year" in t else (7, 4))
        d = date(call.year, *md)
        return (d if d <= call else date(call.year - 1, *md)), ""
    mon = "|".join(sorted(MONTHS, key=len, reverse=True))
    m = re.search(rf"\b({mon})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,?\s+(\d{{4}}))?\b", t) \
        or re.search(rf"\b(?:the )?(\d{{1,2}})(?:st|nd|rd|th)?\s+of\s+({mon})(?:,?\s+(\d{{4}}))?\b", t)
    if m:
        a, b, y = m.group(1), m.group(2), m.group(3)
        mo, dy = (MONTHS[a], int(b)) if a in MONTHS else (MONTHS[b], int(a))
        if y:
            return date(int(y), mo, dy), ""
        d = date(call.year, mo, dy)
        return (d if d <= call else date(call.year - 1, mo, dy)), ""
    m = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", t)
    if m:
        mo, dy = int(m.group(1)), int(m.group(2))
        if m.group(3):
            y = int(m.group(3))
            return date(y + 2000 if y < 100 else y, mo, dy), ""
        d = date(call.year, mo, dy)
        return (d if d <= call else date(call.year - 1, mo, dy)), ""
    m = re.search(rf"\b(?:back )?in ({mon})\b|\blast ({mon})\b", t)
    if m:
        return None, f"month only ('{m.group(0)}'): ask for the day"
    if re.search(r"\b(last (?:summer|winter|spring|fall|year)|a while (?:ago|back)|some time ago)\b", t):
        return None, "vague date: ask for the exact day"
    return None, "no date given: ask when it happened"


def place(text: str) -> str | None:
    t = " " + text.lower() + " "
    for name, st in STATE_NAMES.items():
        if f" {name} " in t or f" {name}," in t or f" {name}." in t:
            if name == "new york" and re.search(r"new york city|in new york,? ny", t):
                return "NY"
            return st
    for city, st in sorted(CITY_STATE.items(), key=lambda kv: -len(kv[0])):
        if re.search(rf"(?<![a-z]){re.escape(city)}(?![a-z])", t):
            return st
    m = re.search(r",\s*([A-Z]{2})\b", text)
    return m.group(1) if m else None


def government(text: str) -> str | None:
    for sent in re.split(r"(?<=[.!?])\s+", text):
        hit_state, hit_local = STATE_GOV.search(sent), LOCAL.search(sent)
        if not (hit_state or hit_local):
            continue
        if NOT_GOV.search(sent):
            continue
        return "state" if hit_state else "local"
    return None


def triage(transcript: str, call: date) -> Triage:
    caller = " ".join(l.split(":", 1)[1] for l in transcript.splitlines() if l.lower().startswith("caller:")) or transcript
    out = Triage(status="OK")
    out.incident, why = incident_date(caller, call)
    out.state = place(caller)
    out.government = government(caller)
    routes = []
    if WORK.search(caller):
        routes.append(("ROUTE_WC", "injured at work: workers' comp is usually the exclusive remedy against the employer; check third parties"))
    if DEATH.search(caller):
        routes.append(("ATTORNEY_REVIEW", "a death: wrongful-death deadlines differ"))
    if MEDMAL.search(caller):
        routes.append(("ATTORNEY_REVIEW", "medical malpractice: different deadline and pre-suit rules"))
    if MINOR.search(caller) and re.search(r"\b(son|daughter|kid|child|boy|girl)\b", caller, re.I):
        routes.append(("ATTORNEY_REVIEW", "injured person is a minor: tolling rules differ by state"))
    if out.state and out.state not in STATES:
        routes.append(("ATTORNEY_REVIEW", f"{out.state} is not in this rules table"))
    if out.government and out.state and (out.state, out.government) not in NOTICE:
        routes.append(("ATTORNEY_REVIEW", f"{out.government} government claim in {out.state} not in this table"))
    if why:
        out.reasons.append(why)
    if not out.state:
        out.reasons.append("no state or city: ask where it happened")
    if out.incident is None or not out.state:
        out.status = "ASK"
    if routes:
        out.status = routes[0][0]
        out.reasons += [r for _, r in routes]
    if out.incident and out.state in SOL:
        cands = []
        years, cite = SOL[out.state]
        try:
            sol = out.incident.replace(year=out.incident.year + years)
        except ValueError:
            sol = out.incident + timedelta(days=365 * years)
        cands.append((sol, f"suit: {cite}"))
        if out.government and (out.state, out.government) in NOTICE:
            days, ncite = NOTICE[(out.state, out.government)]
            cands.append((out.incident + timedelta(days=days), f"notice of claim: {ncite}"))
        out.deadline, out.cite = min(cands)
        out.days_left = (out.deadline - call).days
        if out.status == "OK":
            out.status = ("EXPIRED" if out.days_left < 0 else "URGENT" if out.days_left <= 30
                          else "SOON" if out.days_left <= 90 else "OK")
        elif out.days_left < 0 or out.days_left <= 30:
            out.reasons.append(f"also: {out.cite} {'passed' if out.days_left < 0 else 'due'} {out.deadline:%d %b %Y}")
    return out


def flat_rule(incident: date | None, call: date) -> str:
    """Common intake shortcut: two years from the accident, everywhere."""
    if incident is None:
        return "ASK"
    left = (incident.replace(year=incident.year + 2) - call).days if not (incident.month == 2 and incident.day == 29) \
        else (incident + timedelta(days=730) - call).days
    return "EXPIRED" if left < 0 else "URGENT" if left <= 30 else "SOON" if left <= 90 else "OK"
