"""Filing and notice deadlines by state and defendant type (simplified; cite-backed).

Every number carries its statute so a reviewer can check it. Anything this
table does not model (minors, wrongful death, med-mal, federal defendants,
discovery rule) is routed to an attorney instead of guessed.
"""

# state -> general personal-injury statute of limitations (years, cite)
SOL = {
    "NY": (3, "N.Y. CPLR 214(5)"),
    "CA": (2, "Cal. Civ. Proc. Code 335.1"),
    "TX": (2, "Tex. Civ. Prac. & Rem. Code 16.003"),
    "FL": (2, "Fla. Stat. 95.11(4)(a) (causes accruing after 3/24/2023)"),
    "IL": (2, "735 ILCS 5/13-202"),
    "NJ": (2, "N.J.S.A. 2A:14-2"),
    "GA": (2, "O.C.G.A. 9-3-33"),
    "PA": (2, "42 Pa.C.S. 5524"),
}

# (state, government level) -> notice-of-claim deadline in days, cite
NOTICE = {
    ("NY", "local"): (90, "N.Y. Gen. Mun. Law 50-e(1)(a)"),
    ("NY", "state"): (90, "N.Y. Court of Claims Act 10(3) (notice of intention)"),
    ("CA", "local"): (182, "Cal. Gov. Code 911.2 (six months)"),
    ("CA", "state"): (182, "Cal. Gov. Code 911.2 (six months)"),
    ("TX", "local"): (182, "Tex. Civ. Prac. & Rem. Code 101.101 (six months; city charters may be shorter)"),
    ("TX", "state"): (182, "Tex. Civ. Prac. & Rem. Code 101.101 (six months)"),
    ("FL", "local"): (1095, "Fla. Stat. 768.28(6) (three years)"),
    ("FL", "state"): (1095, "Fla. Stat. 768.28(6) (three years)"),
    ("IL", "local"): (365, "745 ILCS 10/8-101 (suit within one year)"),
    ("NJ", "local"): (90, "N.J.S.A. 59:8-8"),
    ("NJ", "state"): (90, "N.J.S.A. 59:8-8"),
    ("GA", "local"): (182, "O.C.G.A. 36-33-5 (municipality, six months)"),
    ("GA", "state"): (365, "O.C.G.A. 50-21-26 (twelve months)"),
    ("PA", "local"): (182, "42 Pa.C.S. 5522(a) (six months)"),
    ("PA", "state"): (182, "42 Pa.C.S. 5522(a) (six months)"),
}

# Government-level rows a state does not have here go to an attorney.
STATES = set(SOL)
