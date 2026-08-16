# Horizon financial planner

A local Flask web app that compares debt repayment and retirement-investment paths.



## Planning model

- Income grows annually by the selected sector assumption; expenses grow annually by the selected location assumption.
- The loan accrues at the stated annual interest rate each month.
- Investments are projected at a nominal 10% annual return, compounded monthly, before taxes and fees.
- A blank retirement-corpus field uses 25 times projected annual expenses at retirement (a 4% withdrawal-rate guideline).
- The planner compares three monthly-surplus allocations: debt-first, balanced, and investment-first. Once a loan is paid off, all available surplus is invested.

This is an educational projection, not financial advice, a guarantee, or a complete financial plan. It deliberately does not model taxes, insurance, emergency reserves, investment fees, loan fees, or market volatility.


