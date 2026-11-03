import unittest
from datetime import date

from deadlines.triage import flat_rule, government, incident_date, place, triage

CALL = date(2026, 11, 3)


def run(*caller):
    return triage("\n".join(f"Caller: {c}" for c in caller), CALL)


class Parsing(unittest.TestCase):
    def test_casual_dates(self):
        self.assertEqual(incident_date("it was yesterday", CALL)[0], date(2026, 11, 2))
        self.assertEqual(incident_date("three weeks ago", CALL)[0], date(2026, 10, 13))
        self.assertEqual(incident_date("last Friday", CALL)[0], date(2026, 10, 30))
        self.assertEqual(incident_date("the 4th of July", CALL)[0], date(2026, 7, 4))
        self.assertEqual(incident_date("the day after Thanksgiving", CALL)[0], date(2025, 11, 28))
        self.assertIsNone(incident_date("back in March", CALL)[0])

    def test_place_and_government(self):
        self.assertEqual(place("I live in Jersey City"), "NJ")
        self.assertIsNone(government("I live in Jersey City and a guy rear-ended me."))
        self.assertEqual(government("A city bus hit me."), "local")
        self.assertIsNone(government("It wasn't a city bus, it was a private charter."))
        self.assertEqual(government("A state trooper hit me."), "state")


class Deadlines(unittest.TestCase):
    def test_city_bus_notice_beats_three_year_rule(self):
        t = run("A city bus hit my car.", "It was 14 weeks ago.", "In Brooklyn.")
        self.assertEqual(t.status, "EXPIRED")
        self.assertIn("50-e", t.cite)
        self.assertEqual(flat_rule(t.incident, CALL), "OK")

    def test_private_crash_in_new_york_uses_three_years(self):
        t = run("Another driver ran the light.", "It was on 1/15/2024.", "In Queens.")
        self.assertEqual((t.status, t.deadline), ("SOON", date(2027, 1, 15)))

    def test_routes(self):
        self.assertEqual(run("I fell off a ladder at work.", "yesterday", "Houston").status, "ROUTE_WC")
        self.assertEqual(run("My son got hurt, he's 9.", "yesterday", "Miami").status, "ATTORNEY_REVIEW")
        self.assertEqual(run("A car hit me.", "A while back.", "Atlanta").status, "ASK")


if __name__ == "__main__":
    unittest.main()
