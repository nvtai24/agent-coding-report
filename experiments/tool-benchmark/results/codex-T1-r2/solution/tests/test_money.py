import copy
import unittest

from cartkit.money import calculate_totals


class CalculateTotalsTests(unittest.TestCase):
    def test_zero_quantity_has_no_subtotal_or_shipping(self):
        self.assertEqual(
            calculate_totals(
                [{'unit_price_cents': 200, 'quantity': 0}], 50, 25
            ),
            {
                'subtotal_cents': 0,
                'discount_cents': 0,
                'shipping_cents': 0,
                'total_cents': 0,
            },
        )

    def test_missing_quantity_defaults_to_one_in_mixed_cart(self):
        self.assertEqual(
            calculate_totals([
                {'unit_price_cents': 200, 'quantity': 0},
                {'unit_price_cents': 101},
                {'unit_price_cents': 50, 'quantity': 2},
            ])['subtotal_cents'],
            201,
        )

    def test_invalid_quantities_raise_value_error(self):
        for quantity in (None, False, True, -1, 0.5, 1.0):
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValueError):
                    calculate_totals([
                        {'unit_price_cents': 100, 'quantity': quantity}
                    ])

    def test_discount_rounds_half_up_in_integer_cents(self):
        for price, discount in ((4, 0), (5, 1), (6, 1)):
            with self.subTest(price=price):
                totals = calculate_totals([{'unit_price_cents': price}], 10)
                self.assertEqual(totals['discount_cents'], discount)
                self.assertEqual(totals['total_cents'], price - discount)

    def test_shipping_uses_original_subtotal_with_full_discount(self):
        self.assertEqual(
            calculate_totals([{'unit_price_cents': 100}], 100, 25),
            {
                'subtotal_cents': 100,
                'discount_cents': 100,
                'shipping_cents': 25,
                'total_cents': 25,
            },
        )

    def test_empty_cart_has_no_shipping(self):
        self.assertEqual(calculate_totals([], shipping_cents=25)['shipping_cents'], 0)

    def test_input_lines_are_unchanged(self):
        lines = [
            {'unit_price_cents': 100},
            {'unit_price_cents': 200, 'quantity': 0},
            {'unit_price_cents': 50, 'quantity': 2},
        ]
        original = copy.deepcopy(lines)
        calculate_totals(lines, 10, 25)
        self.assertEqual(lines, original)


if __name__ == '__main__':
    unittest.main()
