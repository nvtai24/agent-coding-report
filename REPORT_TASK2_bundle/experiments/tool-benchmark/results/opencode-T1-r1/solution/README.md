# Cartkit benchmark project

Python 3.12, standard library only. Run existing tests with
`python3 -m unittest discover -s tests -v`.

- `cartkit.money.calculate_totals` calculates integer cents. Missing quantity defaults to one. Explicit quantities must be nonnegative integers, including zero. Booleans and null are invalid. Discounts round half up. Shipping is charged only when the original subtotal is positive.
- `cartkit.reports.customer_totals` and `summarize_orders` summarize paid, pending and cancelled orders. Preserve public signatures and JSON key names.
- `python3 -m cartkit.cli totals input.json` and `summary input.json` are the existing CLI commands.

Example order data is in `sample_orders.json`. Keep changes within this project. Do not change or remove existing tests. Implement the requested task and run relevant checks. Do not delegate work.
