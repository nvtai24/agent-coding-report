import copy
import unittest

from cartkit.money import calculate_totals


class CalculateTotalsTests(unittest.TestCase):
    def test_zero_quantity_has_no_subtotal_or_shipping(self):
        self.assertEqual(
            calculate_totals([{'unit_price_cents': 199, 'quantity': 0}], 50, 75),
            {
                'subtotal_cents': 0,
                'discount_cents': 0,
                'shipping_cents': 0,
                'total_cents': 0,
            },
        )

    def test_missing_quantity_defaults_to_one_without_mutating_lines(self):
        lines = [
            {'unit_price_cents': 101},
            {'unit_price_cents': 500, 'quantity': 0},
            {'unit_price_cents': 25, 'quantity': 2},
        ]
        original = copy.deepcopy(lines)
        self.assertEqual(calculate_totals(lines)['subtotal_cents'], 151)
        self.assertEqual(lines, original)

    def test_invalid_explicit_quantities(self):
        for quantity in (None, False, True, -1, 0.5, 0.0, 1.0):
            with self.subTest(quantity=quantity):
                lines = [{'unit_price_cents': 100, 'quantity': quantity}]
                original = copy.deepcopy(lines)
                with self.assertRaises(ValueError):
                    calculate_totals(lines)
                self.assertEqual(lines, original)

    def test_discount_rounds_half_up_in_integer_cents(self):
        for price, percent, discount in (
            (100, 50, 50), (101, 50, 51), (300, 50, 150),
            (1, 25, 0), (2, 25, 1), (3, 25, 1),
        ):
            with self.subTest(price=price, percent=percent):
                totals = calculate_totals([{'unit_price_cents': price}], percent)
                self.assertEqual(totals['discount_cents'], discount)

    def test_shipping_uses_original_subtotal(self):
        self.assertEqual(
            calculate_totals([{'unit_price_cents': 100}], 100, 75),
            {
                'subtotal_cents': 100,
                'discount_cents': 100,
                'shipping_cents': 75,
                'total_cents': 75,
            },
        )
        for lines in ([], [{'unit_price_cents': 0}]):
            with self.subTest(lines=lines):
                self.assertEqual(calculate_totals(lines, 0, 75)['shipping_cents'], 0)


if __name__ == '__main__':
    unittest.main()
