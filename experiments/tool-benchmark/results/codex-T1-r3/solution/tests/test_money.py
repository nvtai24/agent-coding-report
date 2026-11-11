import copy
import unittest

from cartkit.money import calculate_totals


class CalculateTotalsTests(unittest.TestCase):
    def test_zero_quantity_contributes_nothing(self):
        self.assertEqual(
            calculate_totals([
                {'unit_price_cents': 200, 'quantity': 0},
                {'unit_price_cents': 101},
            ], 50, 25),
            {
                'subtotal_cents': 101,
                'discount_cents': 51,
                'shipping_cents': 25,
                'total_cents': 75,
            },
        )

    def test_invalid_explicit_quantities(self):
        for quantity in (None, False, True, -1, 0.5, 1.0):
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValueError):
                    calculate_totals([
                        {'unit_price_cents': 100, 'quantity': quantity},
                    ])

    def test_zero_subtotal_has_no_shipping(self):
        for lines in ([], [{'unit_price_cents': 100, 'quantity': 0}],
                      [{'unit_price_cents': 0}]):
            with self.subTest(lines=lines):
                self.assertEqual(calculate_totals(lines, 50, 25), {
                    'subtotal_cents': 0,
                    'discount_cents': 0,
                    'shipping_cents': 0,
                    'total_cents': 0,
                })

    def test_fully_discounted_positive_subtotal_still_has_shipping(self):
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
        for subtotal, percent, expected in (
            (1, 49, 0), (1, 50, 1), (3, 50, 2),
            (10**20 + 1, 50, 5 * 10**19 + 1),
        ):
            with self.subTest(subtotal=subtotal, percent=percent):
                result = calculate_totals(
                    [{'unit_price_cents': subtotal}], percent,
                )
                self.assertEqual(result['discount_cents'], expected)
                self.assertIs(type(result['discount_cents']), int)

    def test_input_lines_are_unchanged(self):
        lines = [
            {'unit_price_cents': 100},
            {'unit_price_cents': 200, 'quantity': 0},
            {'unit_price_cents': 300, 'quantity': 2},
        ]
        original = copy.deepcopy(lines)
        calculate_totals(lines, 10, 25)
        self.assertEqual(lines, original)


if __name__ == '__main__':
    unittest.main()
