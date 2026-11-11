import copy
import unittest

from cartkit.reports import customer_totals, summarize_orders


class OneShotOrders:
    """Reject a second traversal and record every yielded order."""

    def __init__(self, orders):
        self.orders = orders
        self.iterations = 0
        self.yielded = []

    def __iter__(self):
        self.iterations += 1
        if self.iterations != 1:
            raise AssertionError('Orders were traversed more than once')
        for order in self.orders:
            self.yielded.append(order)
            yield order


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.orders = [
            {'customer': 'pending-only', 'status': 'pending', 'total_cents': 900},
            {'customer': 'B', 'status': 'paid', 'total_cents': 200},
            {'customer': 'cancelled-only', 'status': 'cancelled', 'total_cents': 500},
            {'customer': 'zero-only', 'status': 'paid', 'total_cents': 0},
            {'customer': 'A', 'status': 'paid', 'total_cents': 100},
            {'customer': 'B', 'status': 'paid', 'total_cents': 50},
            {'customer': 'B', 'status': 'cancelled', 'total_cents': 800},
            {'customer': 'A', 'status': 'pending', 'total_cents': 700},
        ]
        self.customers = {'B': 250, 'zero-only': 0, 'A': 100}
        self.summary = {
            'paid_count': 4,
            'paid_total_cents': 350,
            'cancelled_count': 2,
            'customers': self.customers,
        }

    def test_mixed_statuses_lists_and_generators(self):
        original = copy.deepcopy(self.orders)
        for report, expected in (
            (customer_totals, self.customers),
            (summarize_orders, self.summary),
        ):
            for use_generator in (False, True):
                with self.subTest(report=report.__name__, generator=use_generator):
                    orders = (order for order in self.orders) if use_generator else self.orders
                    result = report(orders)
                    self.assertEqual(result, expected)
                    customers = result if report is customer_totals else result['customers']
                    self.assertEqual(list(customers), ['B', 'zero-only', 'A'])
                    self.assertEqual(self.orders, original)

    def test_each_report_consumes_input_exactly_once(self):
        for report, expected in (
            (customer_totals, self.customers),
            (summarize_orders, self.summary),
        ):
            with self.subTest(report=report.__name__):
                orders = OneShotOrders(self.orders)
                self.assertEqual(report(orders), expected)
                self.assertEqual(orders.iterations, 1)
                self.assertEqual(orders.yielded, self.orders)

    def test_empty_lists_and_generators(self):
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
            for orders in ([], (order for order in []), OneShotOrders([])):
                with self.subTest(report=report.__name__, input_type=type(orders).__name__):
                    self.assertEqual(report(orders), expected)

    def test_unpaid_orders_do_not_require_paid_fields(self):
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
