"""Phrasings written after the held-out run, never tuned for. Shows what the triage does with them."""
from datetime import date

from deadlines.triage import triage

CALL = date(2026, 11, 3)
PROBES = [
    ("A USPS mail truck hit me.", "yesterday", "In Dallas."),             # federal: FTCA, should go to an attorney
    ("An NYPD cruiser hit me.", "two weeks ago", "Brooklyn."),             # city police, cue not in list
    ("It was the Friday before last.", "", "Queens."),
    ("A month and a half ago.", "", "Houston."),
    ("Around Labor Day.", "", "Chicago."),
    ("On the 3rd.", "", "Miami."),
    ("Got hit in LA.", "yesterday", ""),
    ("Access-A-Ride van rear-ended me.", "three weeks ago", "the Bronx."),  # MTA paratransit
    ("A FedEx truck hit me.", "yesterday", "Atlanta."),                     # private, should stay private
    ("My mom fell at the nursing home and passed away.", "last Tuesday", "Philadelphia."),
]
for p in PROBES:
    t = triage("\n".join(f"Caller: {x}" for x in p if x), CALL)
    print(f"{t.status:<16} gov={t.government} state={t.state} date={t.incident} | {' / '.join(x for x in p if x)}")
