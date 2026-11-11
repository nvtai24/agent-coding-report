import copy
import unittest

from cartkit.reports import customer_totals, summarize_orders


class OneShotIterable:
    """Fail if a report attempts to iterate over its input twice."""

    def __init__(self, orders):
        self.orders = orders
        self.iterations = 0
        self.consumed = 0

    def __iter__(self):
        self.iterations += 1
        if self.iterations != 1:
            raise AssertionError('input iterated more than once')
        return self._items()

    def _items(self):
        for order in self.orders:
            self.consumed += 1
            yield order


class ReportTests(unittest.TestCase):
    def check_reports(self, orders, expected):
        original = copy.deepcopy(orders)
        for report, result in (
            (customer_totals, expected['customers']),
            (summarize_orders, expected),
        ):
            for input_kind in ('list', 'generator', 'one-shot'):
                with self.subTest(report=report.__name__, input_kind=input_kind):
                    if input_kind == 'list':
                        source = orders
                    elif input_kind == 'generator':
                        source = (order for order in orders)
                    else:
                        source = OneShotIterable(orders)
                    actual = report(source)
                    self.assertEqual(actual, result)
                    customers = actual if report is customer_totals else actual['customers']
                    self.assertEqual(list(customers), list(expected['customers']))
                    self.assertEqual(orders, original)
                    if input_kind == 'generator':
                        self.assertEqual(list(source), [])
                    elif input_kind == 'one-shot':
                        self.assertEqual(source.iterations, 1)
                        self.assertEqual(source.consumed, len(orders))

    def test_empty_inputs(self):
        self.check_reports([], {
            'paid_count': 0,
            'paid_total_cents': 0,
            'cancelled_count': 0,
            'customers': {},
        })

    def test_mixed_statuses_and_zero_paid_orders(self):
        self.check_reports([
            {'customer': 'ignored', 'status': 'pending', 'total_cents': 900},
            {'customer': 'Z', 'status': 'paid', 'total_cents': 0},
            {'customer': 'B', 'status': 'paid', 'total_cents': 200},
            {'customer': 'A', 'status': 'cancelled', 'total_cents': 500},
            {'customer': 'A', 'status': 'paid', 'total_cents': 100},
            {'customer': 'B', 'status': 'paid', 'total_cents': 50},
            {'customer': 'B', 'status': 'cancelled', 'total_cents': 700},
            {'customer': 'A', 'status': 'pending', 'total_cents': 800},
        ], {
            'paid_count': 4,
            'paid_total_cents': 350,
            'cancelled_count': 2,
            'customers': {'Z': 0, 'B': 250, 'A': 100},
        })

    def test_no_paid_orders(self):
        self.check_reports([
            {'status': 'cancelled'},
            {'status': 'pending'},
            {'status': 'cancelled'},
        ], {
            'paid_count': 0,
            'paid_total_cents': 0,
            'cancelled_count': 2,
            'customers': {},
        })


if __name__ == '__main__':
    unittest.main()
