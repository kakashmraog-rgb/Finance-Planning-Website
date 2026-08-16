from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from flask import Flask, render_template, request

app = Flask(__name__)
app.config["SECRET_KEY"] = "local-development-only"

SECTOR_GROWTH = {
    "technology": 0.08, "finance": 0.07, "healthcare": 0.065,
    "education": 0.05, "government": 0.045, "manufacturing": 0.055,
    "other": 0.055,
}
LOCATION_INFLATION = {
    "metro": 0.065, "large_city": 0.06, "small_city": 0.055,
    "town_rural": 0.05,
}
INVESTMENT_RETURN = 0.10  # Nominal long-term planning assumption, before fees and tax.


@dataclass
class PlanInput:
    age: int
    retirement_age: int
    income: float
    expenses: float
    loan: float
    loan_rate: float
    existing_investment: float
    monthly_investment: float
    sector: str
    location: str
    desired_corpus: float | None


def money(value: float) -> str:
    return f"₹{value:,.0f}"


def validate(form) -> Tuple[PlanInput | None, List[str]]:
    errors: List[str] = []
    values: Dict[str, float] = {}
    numeric = {
        "age": ("Age", 18, 75), "retirement_age": ("Retirement age", 40, 90),
        "income": ("Monthly income", 1, 1_000_000_000), "expenses": ("Monthly expenses", 0, 1_000_000_000),
        "loan": ("Outstanding loan", 0, 1_000_000_000), "loan_rate": ("Loan interest rate", 0, 100),
        "existing_investment": ("Existing investment", 0, 1_000_000_000),
        "monthly_investment": ("Monthly investment", 0, 1_000_000_000),
    }
    for key, (label, low, high) in numeric.items():
        try:
            value = float(form.get(key, ""))
            if not low <= value <= high:
                raise ValueError
            values[key] = value
        except (TypeError, ValueError):
            errors.append(f"{label} must be between {low:g} and {high:g}.")
    try:
        desired = float(form.get("desired_corpus", "") or 0)
        if desired < 0:
            raise ValueError
    except ValueError:
        errors.append("Desired retirement corpus must be a positive amount.")
        desired = 0
    if values and values.get("retirement_age", 0) <= values.get("age", 100):
        errors.append("Retirement age must be greater than your current age.")
    sector, location = form.get("sector"), form.get("location")
    if sector not in SECTOR_GROWTH or location not in LOCATION_INFLATION:
        errors.append("Choose a valid sector and location.")
    if values and values.get("income", 0) <= values.get("expenses", 0):
        errors.append("Monthly income must exceed monthly expenses to create a repayment plan.")
    if errors:
        return None, errors
    return PlanInput(
        age=int(values["age"]), retirement_age=int(values["retirement_age"]),
        income=values["income"], expenses=values["expenses"], loan=values["loan"],
        loan_rate=values["loan_rate"] / 100, existing_investment=values["existing_investment"],
        monthly_investment=values["monthly_investment"], sector=sector, location=location,
        desired_corpus=desired or None,
    ), []


def simulate(data: PlanInput, strategy: str) -> dict:
    """Monthly nominal cash-flow projection; raises if cash flow cannot service debt."""
    horizon = (data.retirement_age - data.age) * 12
    income_growth, expense_growth = SECTOR_GROWTH[data.sector], LOCATION_INFLATION[data.location]
    income, expenses, debt, portfolio = data.income, data.expenses, data.loan, data.existing_investment
    months_to_payoff = None
    timeline = []
    annual = []
    for month in range(1, horizon + 1):
        if month > 1 and month % 12 == 1:
            income *= 1 + income_growth
            expenses *= 1 + expense_growth
        surplus = income - expenses
        if debt > 0:
            # Strategy allocation is capped by actual surplus. Debt-first only redirects the user's planned SIP.
            if strategy == "debt_first":
                invest = min(data.monthly_investment * 0.25, surplus * 0.20)
            elif strategy == "investment_first":
                invest = min(max(data.monthly_investment, surplus * 0.55), surplus * 0.75)
            else:
                invest = min(data.monthly_investment, surplus * 0.50)
            payment = surplus - invest
            monthly_interest = debt * data.loan_rate / 12
            if payment <= monthly_interest and debt > 0:
                return {"name": strategy,
                         "feasible": False, 
                        "reason": "The projected monthly surplus does not cover loan interest under this strategy."
                        , "annual":[],
                        "income_growth": income_growth,
                        "expense_growth": expense_growth,}
            debt = max(0.0, debt + monthly_interest - payment)
            if debt == 0 and months_to_payoff is None:
                months_to_payoff = month
        else:
            invest = surplus  # once debt clears, direct all available cash flow to investments
            if months_to_payoff is None:
                months_to_payoff = 0
        portfolio = portfolio * (1 + INVESTMENT_RETURN / 12) + invest
        if month % 12 == 0 or month == horizon:
            annual.append({"year": data.age + month // 12, "portfolio": round(portfolio), "debt": round(debt)})
    final_annual_expenses = expenses * 12
    target = data.desired_corpus or final_annual_expenses * 25
    return {"feasible": True, "name": strategy, "months_to_payoff": months_to_payoff,
            "payoff_years": (months_to_payoff / 12 if months_to_payoff is not None else None),
            "portfolio": portfolio, "target": target, "gap": portfolio - target,
            "annual": annual, "income_growth": income_growth, "expense_growth": expense_growth}


@app.route("/", methods=["GET", "POST"])
def index():
    defaults = {"age": 30, "retirement_age": 60, "income": 100000, "expenses": 50000,
                "loan": 2000000, "loan_rate": 9, "existing_investment": 300000,
                "monthly_investment": 15000, "sector": "technology", "location": "metro", "desired_corpus": ""}
    if request.method == "GET":
        return render_template("index.html", form=defaults, results=None, errors=[])
    form = request.form.to_dict()
    data, errors = validate(form)
    if errors:
       return render_template("index.html", form=form, results=None, errors=errors)
    labels = {
    "debt_first": "Debt-first",
    "balanced": "Balanced",
    "investment_first": "Investment-first",
     }
    results = []

    for name in ("debt_first", "balanced", "investment_first"):
        result = simulate(data, name)
        result["name"] = name
        result["label"] = labels[name]
        results.append(result)
        result["portfolio_display"] = money(result.get("portfolio", 0))
        result["target_display"] = money(result.get("target", 0))
        result["gap_display"] = money(abs(result.get("gap", 0)))
    return render_template("index.html", form=form, results=results, errors=[])


if __name__ == "__main__":
    app.run(debug=True)
