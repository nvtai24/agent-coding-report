import copy
import unittest
from cartkit.money import calculate_totals


class Acceptance(unittest.TestCase):
    def test_zero_quantity(self):
        self.assertEqual(calculate_totals([{'unit_price_cents': 999, 'quantity': 0}])['total_cents'], 0)

    def test_mixed_quantities(self):
        lines=[{'unit_price_cents': 999, 'quantity': 0}, {'unit_price_cents': 125, 'quantity': 3}]
        self.assertEqual(calculate_totals(lines)['subtotal_cents'],375)

    def test_missing_defaults_to_one(self):
        self.assertEqual(calculate_totals([{'unit_price_cents': 99}])['total_cents'],99)

    def test_null_rejected(self):
        with self.assertRaises(ValueError):calculate_totals([{'unit_price_cents':100,'quantity':None}])

    def test_false_rejected(self):
        with self.assertRaises(ValueError):calculate_totals([{'unit_price_cents':100,'quantity':False}])

    def test_negative_and_fraction_rejected(self):
        for q in [-1,1.5,'2',True]:
            with self.subTest(quantity=q):
                with self.assertRaises(ValueError):calculate_totals([{'unit_price_cents':100,'quantity':q}])

    def test_rounding_half_up(self):
        self.assertEqual(calculate_totals([{'unit_price_cents':101}],50),{'subtotal_cents':101,'discount_cents':51,'shipping_cents':0,'total_cents':50})

    def test_zero_avoids_shipping(self):
        self.assertEqual(calculate_totals([{'unit_price_cents':999,'quantity':0}],50,25),{'subtotal_cents':0,'discount_cents':0,'shipping_cents':0,'total_cents':0})

    def test_no_mutation_and_generator(self):
        lines=[{'unit_price_cents':15,'quantity':0},{'unit_price_cents':100}]
        before=copy.deepcopy(lines)
        self.assertEqual(calculate_totals(iter(lines),20,5)['total_cents'],85)
        self.assertEqual(lines,before)
