import copy
import unittest

from cartkit.money import calculate_totals


class CalculateTotalsTests(unittest.TestCase):
    def test_zero_quantity_contributes_nothing(self):
        self.assertEqual(
            calculate_totals([
                {'unit_price_cents': 500, 'quantity': 0},
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
        for quantity in (None, False, True, -1, 0.0, 1.0, 1.5):
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValueError):
                    calculate_totals([
                        {'unit_price_cents': 100, 'quantity': quantity},
                    ])

    def test_zero_subtotal_has_no_shipping(self):
        for lines in ([], [{'unit_price_cents': 500, 'quantity': 0}],
                      [{'unit_price_cents': 0}]):
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
        for price, discount in ((49, 0), (50, 1), (51, 1),
                                (10**18 + 50, 10**16 + 1)):
            with self.subTest(price=price):
                totals = calculate_totals([{'unit_price_cents': price}], 1)
                self.assertEqual(totals['discount_cents'], discount)
                self.assertIs(type(totals['discount_cents']), int)

    def test_input_lines_are_unchanged(self):
        lines = [
            {'unit_price_cents': 500, 'quantity': 0},
            {'unit_price_cents': 101},
            {'unit_price_cents': 25, 'quantity': 2},
        ]
        original = copy.deepcopy(lines)
        calculate_totals(lines, 50, 25)
        self.assertEqual(lines, original)


if __name__ == '__main__':
    unittest.main()
