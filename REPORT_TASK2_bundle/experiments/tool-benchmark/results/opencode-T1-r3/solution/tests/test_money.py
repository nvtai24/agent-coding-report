import copy
import unittest

from cartkit.money import calculate_totals


class CalculateTotalsTests(unittest.TestCase):
    def test_zero_quantity_contributes_nothing(self):
        self.assertEqual(
            calculate_totals([{'unit_price_cents': 200, 'quantity': 0}], 10, 25),
            {
                'subtotal_cents': 0,
                'discount_cents': 0,
                'shipping_cents': 0,
                'total_cents': 0,
            },
        )

    def test_missing_quantity_defaults_to_one_in_mixed_cart(self):
        lines = [
            {'unit_price_cents': 200, 'quantity': 0},
            {'unit_price_cents': 101},
            {'unit_price_cents': 50, 'quantity': 2},
        ]
        self.assertEqual(calculate_totals(lines)['subtotal_cents'], 201)

    def test_invalid_explicit_quantities(self):
        for quantity in (None, False, True, -1, -0.5, 0.5, 0.0, 1.0):
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValueError):
                    calculate_totals([{'unit_price_cents': 100, 'quantity': quantity}])

    def test_discount_rounds_half_up_in_integer_cents(self):
        for subtotal, discount in ((49, 0), (50, 1), (51, 1), (150, 2),
                                   (10**20 + 50, 10**18 + 1)):
            with self.subTest(subtotal=subtotal):
                result = calculate_totals([{'unit_price_cents': subtotal}], 1)
                self.assertEqual(result['discount_cents'], discount)
                self.assertEqual(result['total_cents'], subtotal - discount)

    def test_shipping_uses_original_subtotal_before_discount(self):
        self.assertEqual(
            calculate_totals([{'unit_price_cents': 100}], 100, 25),
            {
                'subtotal_cents': 100,
                'discount_cents': 100,
                'shipping_cents': 25,
                'total_cents': 25,
            },
        )

    def test_no_shipping_for_empty_or_free_cart(self):
        for lines in ([], [{'unit_price_cents': 0, 'quantity': 2}]):
            with self.subTest(lines=lines):
                result = calculate_totals(lines, shipping_cents=25)
                self.assertEqual(result['shipping_cents'], 0)
                self.assertEqual(result['total_cents'], 0)

    def test_input_lines_are_not_mutated(self):
        lines = [
            {'unit_price_cents': 200, 'quantity': 0},
            {'unit_price_cents': 101},
            {'unit_price_cents': 50, 'quantity': 2},
        ]
        original = copy.deepcopy(lines)
        calculate_totals(lines, 10, 25)
        self.assertEqual(lines, original)


if __name__ == '__main__':
    unittest.main()
