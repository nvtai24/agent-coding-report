import unittest
from cartkit.money import calculate_totals
from cartkit.reports import customer_totals, summarize_orders


class ExistingTests(unittest.TestCase):
    def test_regular_total(self):
        self.assertEqual(calculate_totals([{'unit_price_cents': 200, 'quantity': 2}], 10, 25)['total_cents'], 385)

    def test_default_quantity(self):
        self.assertEqual(calculate_totals([{'unit_price_cents': 101}])['total_cents'], 101)

    def test_invalid_discount(self):
        with self.assertRaises(ValueError):
            calculate_totals([], 101)

    def test_list_report(self):
        orders = [
            {'customer': 'A', 'status': 'paid', 'total_cents': 200},
            {'customer': 'B', 'status': 'cancelled', 'total_cents': 500},
            {'customer': 'A', 'status': 'paid', 'total_cents': 100},
        ]
        self.assertEqual(customer_totals(orders), {'A': 300})
        self.assertEqual(summarize_orders(orders), {'paid_count': 2, 'paid_total_cents': 300, 'cancelled_count': 1, 'customers': {'A': 300}})


if __name__ == '__main__':
    unittest.main()
