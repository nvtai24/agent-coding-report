import copy
import unittest

from cartkit.money import calculate_totals


class CalculateTotalsTests(unittest.TestCase):
    def test_zero_quantity_contributes_nothing(self):
        self.assertEqual(
            calculate_totals([
                {'unit_price_cents': 999, 'quantity': 0},
                {'unit_price_cents': 101},
            ], discount_percent=50, shipping_cents=25),
            {
                'subtotal_cents': 101,
                'discount_cents': 51,
                'shipping_cents': 25,
                'total_cents': 75,
            },
        )

    def test_invalid_explicit_quantities(self):
        for quantity in (None, False, True, -1, -0.5, 0.5, 1.0):
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValueError):
                    calculate_totals([
                        {'unit_price_cents': 100, 'quantity': quantity},
                    ])

    def test_zero_subtotal_has_no_shipping(self):
        for lines in (
            [],
            [{'unit_price_cents': 999, 'quantity': 0}],
            [{'unit_price_cents': 0, 'quantity': 2}],
        ):
            with self.subTest(lines=lines):
                self.assertEqual(
                    calculate_totals(lines, shipping_cents=25),
                    {
                        'subtotal_cents': 0,
                        'discount_cents': 0,
                        'shipping_cents': 0,
                        'total_cents': 0,
                    },
                )

    def test_full_discount_still_charges_shipping(self):
        self.assertEqual(
            calculate_totals([{'unit_price_cents': 100}], 100, 25),
            {
                'subtotal_cents': 100,
                'discount_cents': 100,
                'shipping_cents': 25,
                'total_cents': 25,
            },
        )

    def test_discount_rounds_half_up_in_integer_cents(self):
        for price, expected_discount in ((149, 1), (150, 2), (151, 2)):
            with self.subTest(price=price):
                result = calculate_totals([{'unit_price_cents': price}], 1)
                self.assertEqual(result['discount_cents'], expected_discount)
                self.assertTrue(all(type(value) is int for value in result.values()))

    def test_input_lines_are_not_mutated(self):
        lines = [
            {'unit_price_cents': 100},
            {'unit_price_cents': 200, 'quantity': 0},
            {'unit_price_cents': 300, 'quantity': 2},
        ]
        original = copy.deepcopy(lines)
        calculate_totals(lines, 25, 50)
        self.assertEqual(lines, original)


if __name__ == '__main__':
    unittest.main()
