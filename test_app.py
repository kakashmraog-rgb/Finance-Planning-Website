import unittest

from app import app


VALID_INPUT = {
    "age": "30", "retirement_age": "60", "income": "100000", "expenses": "50000",
    "sector": "technology", "location": "metro", "loan": "2000000", "loan_rate": "9",
    "existing_investment": "300000", "monthly_investment": "15000", "desired_corpus": "",
}


class PlannerRoutesTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_home_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Build your plan", response.data)

    def test_valid_plan_displays_strategy_comparison(self):
        response = self.client.post("/", data=VALID_INPUT)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Debt-first", response.data)
        self.assertIn(b"Portfolio & debt over time", response.data)

    def test_invalid_plan_shows_validation_message(self):
        invalid = {**VALID_INPUT, "retirement_age": "25", "income": "0", "sector": "invalid"}
        response = self.client.post("/", data=invalid)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please review", response.data)


if __name__ == "__main__":
    unittest.main()
