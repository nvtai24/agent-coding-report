import copy
import unittest

from cartkit.reports import customer_totals, summarize_orders


class OneShotOrders:
    def __init__(self, orders):
        self.orders = orders
        self.iterations = 0
        self.consumed = 0

    def __iter__(self):
        self.iterations += 1
        if self.iterations != 1:
            raise AssertionError('Orders were iterated more than once')
        return self._items()

    def _items(self):
        for order in self.orders:
            self.consumed += 1
            yield order


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.orders = [
            {'customer': 'pending', 'status': 'pending', 'total_cents': 900},
            {'customer': 'B', 'status': 'paid', 'total_cents': 0},
            {'customer': 'cancelled', 'status': 'cancelled', 'total_cents': 500},
            {'customer': 'A', 'status': 'paid', 'total_cents': 200},
            {'customer': 'A', 'status': 'pending', 'total_cents': 700},
            {'customer': 'A', 'status': 'paid', 'total_cents': 100},
            {'customer': 'A', 'status': 'cancelled', 'total_cents': 600},
        ]
        self.customers = {'B': 0, 'A': 300}
        self.summary = {
            'paid_count': 3,
            'paid_total_cents': 300,
            'cancelled_count': 2,
            'customers': self.customers,
        }

    def test_mixed_statuses_lists_and_generators(self):
        for report, expected in (
            (customer_totals, self.customers),
            (summarize_orders, self.summary),
        ):
            for as_generator in (False, True):
                with self.subTest(report=report.__name__, generator=as_generator):
                    before = copy.deepcopy(self.orders)
                    orders = (order for order in self.orders) if as_generator else self.orders
                    result = report(orders)
                    self.assertEqual(result, expected)
                    customers = result if report is customer_totals else result['customers']
                    self.assertEqual(list(customers), ['B', 'A'])
                    self.assertEqual(self.orders, before)

    def test_inputs_are_consumed_exactly_once(self):
        for report, expected in (
            (customer_totals, self.customers),
            (summarize_orders, self.summary),
        ):
            with self.subTest(report=report.__name__):
                orders = OneShotOrders(self.orders)
                self.assertEqual(report(orders), expected)
                self.assertEqual(orders.iterations, 1)
                self.assertEqual(orders.consumed, len(self.orders))

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
            for orders in ([], iter(()), OneShotOrders([])):
                with self.subTest(report=report.__name__, input_type=type(orders).__name__):
                    self.assertEqual(report(orders), expected)


if __name__ == '__main__':
    unittest.main()
