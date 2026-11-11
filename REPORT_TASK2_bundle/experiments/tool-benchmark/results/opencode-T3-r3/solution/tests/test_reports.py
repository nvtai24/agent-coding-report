import copy
import unittest

from cartkit.reports import customer_totals, summarize_orders


class OneShotOrders:
    def __init__(self, orders):
        self.orders = orders
        self.iterations = 0
        self.yielded = 0

    def __iter__(self):
        self.iterations += 1
        if self.iterations != 1:
            raise AssertionError('Orders must only be iterated once')
        return self._items()

    def _items(self):
        for order in self.orders:
            self.yielded += 1
            yield order


class ReportTests(unittest.TestCase):
    def test_mixed_statuses(self):
        orders = [
            {'customer': 'ignored', 'status': 'pending', 'total_cents': 900},
            {'customer': 'B', 'status': 'paid', 'total_cents': 0},
            {'customer': 'cancelled', 'status': 'cancelled', 'total_cents': 800},
            {'customer': 'A', 'status': 'paid', 'total_cents': 200},
            {'customer': 'A', 'status': 'paid', 'total_cents': 100},
            {'customer': 'C', 'status': 'paid', 'total_cents': 0},
            {'customer': 'A', 'status': 'cancelled', 'total_cents': 700},
            {'customer': 'A', 'status': 'pending', 'total_cents': 600},
        ]
        original = copy.deepcopy(orders)
        expected_customers = {'B': 0, 'A': 300, 'C': 0}
        expected_summary = {
            'paid_count': 4,
            'paid_total_cents': 300,
            'cancelled_count': 2,
            'customers': expected_customers,
        }
        for report, expected in (
            (customer_totals, expected_customers),
            (summarize_orders, expected_summary),
        ):
            for kind in ('list', 'generator', 'one-shot'):
                with self.subTest(report=report.__name__, kind=kind):
                    if kind == 'list':
                        source = orders
                    elif kind == 'generator':
                        source = (order for order in orders)
                    else:
                        source = OneShotOrders(orders)
                    result = report(source)
                    self.assertEqual(result, expected)
                    customers = result if report is customer_totals else result['customers']
                    self.assertEqual(list(customers), ['B', 'A', 'C'])
                    self.assertEqual(orders, original)
                    if kind == 'generator':
                        self.assertEqual(list(source), [])
                    elif kind == 'one-shot':
                        self.assertEqual(source.iterations, 1)
                        self.assertEqual(source.yielded, len(orders))

    def test_empty_inputs(self):
        for report, expected in (
            (customer_totals, {}),
            (summarize_orders, {
                'paid_count': 0,
                'paid_total_cents': 0,
                'cancelled_count': 0,
                'customers': {},
            }),
        ):
            for source in ([], (order for order in []), OneShotOrders([])):
                with self.subTest(report=report.__name__, source=type(source).__name__):
                    self.assertEqual(report(source), expected)
                    if isinstance(source, OneShotOrders):
                        self.assertEqual(source.iterations, 1)
                        self.assertEqual(source.yielded, 0)

    def test_no_paid_orders(self):
        orders = [{'status': 'pending'}, {'status': 'cancelled'}]
        self.assertEqual(customer_totals(iter(orders)), {})
        self.assertEqual(summarize_orders(iter(orders)), {
            'paid_count': 0,
            'paid_total_cents': 0,
            'cancelled_count': 1,
            'customers': {},
        })


if __name__ == '__main__':
    unittest.main()
