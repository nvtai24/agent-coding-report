import copy
import unittest

from cartkit.reports import customer_totals, summarize_orders


class OneShotOrders:
    """Reject a second traversal and track every yielded order."""

    def __init__(self, orders):
        self.orders = orders
        self.iterations = 0
        self.yielded = 0

    def __iter__(self):
        self.iterations += 1
        if self.iterations != 1:
            raise AssertionError('Orders traversed more than once')
        return self._iterate()

    def _iterate(self):
        for order in self.orders:
            self.yielded += 1
            yield order


class ReportTests(unittest.TestCase):
    def check_reports(self, orders, expected):
        original = copy.deepcopy(orders)
        for report in (customer_totals, summarize_orders):
            for input_kind in ('list', 'generator', 'one-shot'):
                with self.subTest(report=report.__name__, input_kind=input_kind):
                    source = copy.deepcopy(orders)
                    if input_kind == 'generator':
                        source = (order for order in source)
                    elif input_kind == 'one-shot':
                        source = OneShotOrders(source)
                    result = report(source)
                    if report is customer_totals:
                        self.assertEqual(result, expected['customers'])
                        customers = result
                    else:
                        self.assertEqual(result, expected)
                        customers = result['customers']
                    self.assertEqual(list(customers), list(expected['customers']))
                    if input_kind == 'one-shot':
                        self.assertEqual(source.iterations, 1)
                        self.assertEqual(source.yielded, len(orders))
                        self.assertEqual(source.orders, original)
                    elif input_kind == 'list':
                        self.assertEqual(source, original)
        self.assertEqual(orders, original)

    def test_mixed_statuses_and_zero_paid_orders(self):
        self.check_reports([
            {'customer': 'A', 'status': 'pending', 'total_cents': 900},
            {'customer': 'B', 'status': 'paid', 'total_cents': 200},
            {'customer': 'C', 'status': 'paid', 'total_cents': 0},
            {'customer': 'D', 'status': 'cancelled', 'total_cents': 500},
            {'customer': 'A', 'status': 'paid', 'total_cents': 100},
            {'customer': 'B', 'status': 'paid', 'total_cents': 50},
            {'customer': 'B', 'status': 'cancelled', 'total_cents': 300},
        ], {
            'paid_count': 4,
            'paid_total_cents': 350,
            'cancelled_count': 2,
            'customers': {'B': 250, 'C': 0, 'A': 100},
        })

    def test_empty_inputs(self):
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
