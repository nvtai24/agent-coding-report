import copy
import unittest
from cartkit.reports import customer_totals,summarize_orders

ORDERS=[{'customer':'B','status':'paid','total_cents':0},{'customer':'A','status':'paid','total_cents':100},
        {'customer':'B','status':'paid','total_cents':50},{'customer':'C','status':'cancelled','total_cents':90},
        {'customer':'A','status':'pending','total_cents':70}]
EXPECTED={'paid_count':3,'paid_total_cents':150,'cancelled_count':1,'customers':{'B':50,'A':100}}


class OneShot:
    def __init__(self,items):self.items=items;self.iterations=0
    def __iter__(self):
        self.iterations+=1
        if self.iterations>1:raise AssertionError('Input iterable consumed more than once')
        yield from self.items


class Acceptance(unittest.TestCase):
    def test_list_compatibility(self):self.assertEqual(summarize_orders(ORDERS),EXPECTED)
    def test_generator_summary(self):self.assertEqual(summarize_orders(o for o in ORDERS),EXPECTED)
    def test_one_iteration_summary(self):
        source=OneShot(ORDERS);self.assertEqual(summarize_orders(source),EXPECTED);self.assertEqual(source.iterations,1)
    def test_one_iteration_customers(self):
        source=OneShot(ORDERS);self.assertEqual(customer_totals(source),EXPECTED['customers']);self.assertEqual(source.iterations,1)
    def test_empty(self):
        self.assertEqual(summarize_orders(iter([])),{'paid_count':0,'paid_total_cents':0,'cancelled_count':0,'customers':{}})
        self.assertEqual(customer_totals(iter([])),{})
    def test_no_mutation(self):
        before=copy.deepcopy(ORDERS);summarize_orders(ORDERS);customer_totals(ORDERS);self.assertEqual(ORDERS,before)
    def test_zero_paid_customer_preserved(self):
        order={'customer':'Z','status':'paid','total_cents':0}
        self.assertEqual(summarize_orders(iter([order]))['paid_count'],1)
        self.assertEqual(customer_totals(iter([order])),{'Z':0})
    def test_customer_key_order(self):self.assertEqual(list(customer_totals(iter(ORDERS))),['B','A'])
