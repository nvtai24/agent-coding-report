import copy
import unittest

from cartkit.reports import customer_totals, summarize_orders


class OneShotIterable:
    """Fail if a report requests a second traversal."""

    def __init__(self, orders):
        self.orders = orders
        self.iterations = 0
        self.visited = []

    def __iter__(self):
        self.iterations += 1
        if self.iterations != 1:
            raise AssertionError('orders traversed more than once')
        return self._items()

    def _items(self):
        for order in self.orders:
            self.visited.append(order)
            yield order


class ReportTests(unittest.TestCase):
    def check_reports(self, orders, expected):
        original = copy.deepcopy(orders)
        for report, result in (
            (customer_totals, expected['customers']),
            (summarize_orders, expected),
        ):
            for kind in ('list', 'generator', 'one-shot'):
                with self.subTest(report=report.__name__, input=kind):
                    if kind == 'list':
                        source = orders
                    elif kind == 'generator':
                        source = (order for order in orders)
                    else:
                        source = OneShotIterable(orders)
                    actual = report(source)
                    self.assertEqual(actual, result)
                    customers = actual if report is customer_totals else actual['customers']
                    self.assertEqual(list(customers), list(expected['customers']))
                    if kind == 'generator':
                        self.assertEqual(list(source), [])
                    elif kind == 'one-shot':
                        self.assertEqual(source.iterations, 1)
                        self.assertEqual(source.visited, orders)
                    self.assertEqual(orders, original)

    def test_mixed_statuses(self):
        self.check_reports([
            {'customer': 'ignored', 'status': 'pending', 'total_cents': 900},
            {'customer': 'Z', 'status': 'paid', 'total_cents': 0},
            {'customer': 'A', 'status': 'paid', 'total_cents': 200},
            {'customer': 'cancelled-only', 'status': 'cancelled', 'total_cents': 700},
            {'customer': 'B', 'status': 'paid', 'total_cents': 50},
            {'customer': 'A', 'status': 'paid', 'total_cents': 100},
            {'customer': 'A', 'status': 'cancelled', 'total_cents': 800},
        ], {
            'paid_count': 4,
            'paid_total_cents': 350,
            'cancelled_count': 2,
            'customers': {'Z': 0, 'A': 300, 'B': 50},
        })

    def test_empty(self):
        self.check_reports([], {
            'paid_count': 0,
            'paid_total_cents': 0,
            'cancelled_count': 0,
            'customers': {},
        })

    def test_no_paid_orders(self):
        self.check_reports([
            {'status': 'pending'},
            {'status': 'cancelled'},
            {'status': 'cancelled'},
        ], {
            'paid_count': 0,
            'paid_total_cents': 0,
            'cancelled_count': 2,
            'customers': {},
        })


if __name__ == '__main__':
    unittest.main()
