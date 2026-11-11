import copy
import unittest

from cartkit.money import calculate_totals


class CalculateTotalsTests(unittest.TestCase):
    def test_zero_quantity_contributes_nothing_and_has_no_shipping(self):
        self.assertEqual(
            calculate_totals([{'unit_price_cents': 200, 'quantity': 0}], 10, 25),
            {
                'subtotal_cents': 0,
                'discount_cents': 0,
                'shipping_cents': 0,
                'total_cents': 0,
            },
        )

    def test_missing_quantity_defaults_to_one_alongside_zero(self):
        self.assertEqual(
            calculate_totals([
                {'unit_price_cents': 200, 'quantity': 0},
                {'unit_price_cents': 101},
            ])['subtotal_cents'],
            101,
        )

    def test_invalid_explicit_quantities(self):
        for quantity in (None, False, True, -1, 0.0, 1.0, 0.5, -0.5):
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValueError):
                    calculate_totals([
                        {'unit_price_cents': 200, 'quantity': quantity},
                    ])

    def test_discount_rounds_half_up_in_integer_cents(self):
        for price, expected_discount in ((49, 0), (50, 1), (51, 1), (150, 2)):
            with self.subTest(price=price):
                result = calculate_totals([{'unit_price_cents': price}], 1)
                self.assertEqual(result['discount_cents'], expected_discount)
                self.assertEqual(result['total_cents'], price - expected_discount)
                self.assertIs(type(result['discount_cents']), int)

    def test_shipping_uses_original_subtotal(self):
        self.assertEqual(
            calculate_totals([{'unit_price_cents': 100}], 100, 25),
            {
                'subtotal_cents': 100,
                'discount_cents': 100,
                'shipping_cents': 25,
                'total_cents': 25,
            },
        )
        for lines in ([], [{'unit_price_cents': 0}]):
            with self.subTest(lines=lines):
                self.assertEqual(calculate_totals(lines, 0, 25)['shipping_cents'], 0)

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
