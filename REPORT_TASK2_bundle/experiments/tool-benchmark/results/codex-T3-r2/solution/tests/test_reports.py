import copy
import unittest

from cartkit.reports import customer_totals, summarize_orders


class OneShotIterable:
    def __init__(self, orders):
        self.orders = orders
        self.iterations = 0
        self.consumed = []

    def __iter__(self):
        self.iterations += 1
        if self.iterations != 1:
            raise AssertionError('Input was iterated more than once')
        return self._items()

    def _items(self):
        for order in self.orders:
            self.consumed.append(order)
            yield order


class ReportTests(unittest.TestCase):
    def test_mixed_statuses_and_input_types(self):
        orders = [
            {'customer': 'pending', 'status': 'pending', 'total_cents': 900},
            {'customer': 'Z', 'status': 'paid', 'total_cents': 0},
            {'customer': 'B', 'status': 'paid', 'total_cents': 200},
            {'customer': 'cancelled', 'status': 'cancelled', 'total_cents': 500},
            {'customer': 'A', 'status': 'paid', 'total_cents': 100},
            {'customer': 'B', 'status': 'pending', 'total_cents': 800},
            {'customer': 'B', 'status': 'paid', 'total_cents': 50},
            {'customer': 'A', 'status': 'cancelled', 'total_cents': 100},
        ]
        original = copy.deepcopy(orders)
        customers = {'Z': 0, 'B': 250, 'A': 100}
        summary = {
            'paid_count': 4,
            'paid_total_cents': 350,
            'cancelled_count': 2,
            'customers': customers,
        }
        for report, expected in (
            (customer_totals, customers), (summarize_orders, summary)
        ):
            for input_type in ('list', 'generator', 'one_shot'):
                with self.subTest(report=report.__name__, input_type=input_type):
                    if input_type == 'list':
                        source = orders
                    elif input_type == 'generator':
                        source = (order for order in orders)
                    else:
                        source = OneShotIterable(orders)
                    result = report(source)
                    self.assertEqual(result, expected)
                    actual_customers = (
                        result if report is customer_totals else result['customers']
                    )
                    self.assertEqual(list(actual_customers), ['Z', 'B', 'A'])
                    self.assertEqual(orders, original)
                    if input_type == 'one_shot':
                        self.assertEqual(source.iterations, 1)
                        self.assertEqual(source.consumed, orders)
                    elif input_type == 'generator':
                        self.assertEqual(list(source), [])

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
            for source in ([], (order for order in []), OneShotIterable([])):
                with self.subTest(report=report.__name__, source=type(source).__name__):
                    self.assertEqual(report(source), expected)
                    if isinstance(source, OneShotIterable):
                        self.assertEqual(source.iterations, 1)


if __name__ == '__main__':
    unittest.main()
