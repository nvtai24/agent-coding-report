import copy
import unittest

from cartkit.reports import customer_totals, summarize_orders


class OneShotIterable:
    def __init__(self, orders):
        self.orders = orders
        self.iterations = 0
        self.yielded = 0

    def __iter__(self):
        self.iterations += 1
        if self.iterations != 1:
            raise AssertionError('Input must be iterated exactly once')
        return self._items()

    def _items(self):
        for order in self.orders:
            self.yielded += 1
            yield order


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.orders = [
            {'customer': 'pending-only', 'status': 'pending', 'total_cents': 900},
            {'customer': 'Z', 'status': 'paid', 'total_cents': 0},
            {'customer': 'B', 'status': 'paid', 'total_cents': 200},
            {'customer': 'cancelled-only', 'status': 'cancelled', 'total_cents': 500},
            {'customer': 'A', 'status': 'paid', 'total_cents': 100},
            {'customer': 'B', 'status': 'pending', 'total_cents': 800},
            {'customer': 'B', 'status': 'paid', 'total_cents': 50},
            {'customer': 'A', 'status': 'cancelled', 'total_cents': 100},
        ]
        self.customers = {'Z': 0, 'B': 250, 'A': 100}
        self.summary = {
            'paid_count': 4,
            'paid_total_cents': 350,
            'cancelled_count': 2,
            'customers': self.customers,
        }

    def test_mixed_statuses_preserve_orders_and_customer_order(self):
        original = copy.deepcopy(self.orders)
        for report, expected in (
            (customer_totals, self.customers),
            (summarize_orders, self.summary),
        ):
            with self.subTest(report=report.__name__):
                result = report(self.orders)
                self.assertEqual(result, expected)
                customers = result if report is customer_totals else result['customers']
                self.assertEqual(list(customers), ['Z', 'B', 'A'])
                self.assertEqual(self.orders, original)

    def test_generators(self):
        self.assertEqual(customer_totals(order for order in self.orders), self.customers)
        self.assertEqual(summarize_orders(order for order in self.orders), self.summary)

    def test_inputs_are_consumed_exactly_once(self):
        for report, expected in (
            (customer_totals, self.customers),
            (summarize_orders, self.summary),
        ):
            with self.subTest(report=report.__name__):
                orders = OneShotIterable(self.orders)
                self.assertEqual(report(orders), expected)
                self.assertEqual(orders.iterations, 1)
                self.assertEqual(orders.yielded, len(self.orders))

    def test_empty_inputs(self):
        empty_summary = {
            'paid_count': 0,
            'paid_total_cents': 0,
            'cancelled_count': 0,
            'customers': {},
        }
        for report, expected in (
            (customer_totals, {}),
            (summarize_orders, empty_summary),
        ):
            for orders in ([], iter(()), OneShotIterable([])):
                with self.subTest(report=report.__name__, input_type=type(orders).__name__):
                    self.assertEqual(report(orders), expected)
                    if isinstance(orders, OneShotIterable):
                        self.assertEqual(orders.iterations, 1)


if __name__ == '__main__':
    unittest.main()
