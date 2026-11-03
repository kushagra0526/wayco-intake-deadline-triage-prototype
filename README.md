# Intake deadline triage for injury calls (Wayco-style)

**Unofficial prototype by Kushagra Pratap Singh. Not affiliated with Wayco.**

## The problem
Wayco's AI agent takes injury intakes 24/7 in all 50 states and matches callers to partner firms ([wayco.ai](https://wayco.ai)). The costly intake miss is the deadline: a city bus or pothole claim often needs a notice of claim in 90 days to 6 months, long before the 2–3 year statute of limitations.

## What I built
Reads the caller's words (casual dates relative to the call: "yesterday", "three weeks ago", "last Friday", "the 4th of July", "1/15/2025"; city or state; who is at fault: city bus, pothole, state trooper vs private driver, with negation like "it wasn't a city bus") and returns **EXPIRED / URGENT (≤30 d) / SOON (≤90 d) / OK**, or **ROUTE_WC** (work injury), **ATTORNEY_REVIEW** (minor, death, med-mal, state not in table), **ASK** (no exact date or place), with the first deadline and its statute (8 states: NY, CA, TX, FL, IL, NJ, GA, PA; `deadlines/rules.py`).

## Demo (`python demo.py`)
```
> The city bus ran the red and hit my car. / It was the 4th of July. / Over in Queens.
  EXPIRED  (flat 2-year rule: OK)  first deadline 02 Oct 2026 — notice of claim: N.Y. Gen. Mun. Law 50-e(1)(a)
> A state trooper backed into me. / It was 9/20/2026. / Newark.
  SOON     (flat 2-year rule: OK)  first deadline 19 Dec 2026 — N.J.S.A. 59:8-8
```

## Results (synthetic calls, known truth)
| | dev (1,200 calls) | held-out (2,400 calls, first run) |
|---|---|---|
| right status | 1,200 / 1,200 | **2,400 / 2,400** |
| urgent/expired cases missed | 0 / 206 | **0 / 448** |
| … by a flat "2 years from the accident" rule | 132 / 206 | 294 / 448 |

Dev fixes before these numbers: the word "city" alone counted as government ("Jersey City" became a city claim) — narrowed to "city bus/truck/street…"; the generator produced year-less dates for incidents over a year old (ambiguous even to a person) — fixed in the generator.

**Untuned probe** (`results/probe.txt`, written after the held-out run): 3 of 10 phrasings were unsafe — a USPS truck (federal FTCA claim), an "NYPD cruiser" and an "Access-A-Ride van" all came back OK instead of a short government deadline. Date phrasings it can't read ("the Friday before last", "around Labor Day") safely go to ASK. The fix is an explicit "whose vehicle was it?" question rather than a longer word list.

## Honest limits
- Near-circular: I wrote the generator, both phrase banks and the parser; held-out phrasings knew the parser.
- Rules simplified: no minors' tolling, discovery rule, federal defendants, county-vs-city splits (e.g. Georgia counties have 12 months under O.C.G.A. 36-11-1; the table uses the municipal 6-month rule), city charters shorter than state law. Not legal advice; every number carries its cite for an attorney to check.

## Run it (Python 3.10+, stdlib only)
```
python demo.py
python -m unittest discover -s tests -t .
python -m deadlines.evaluate heldout
```
