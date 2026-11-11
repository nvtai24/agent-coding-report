import copy
import unittest

from cartkit.money import calculate_totals


class CalculateTotalsRegressionTests(unittest.TestCase):
    def test_zero_quantity_has_no_subtotal_or_shipping(self):
        self.assertEqual(
            calculate_totals(
                [{'unit_price_cents': 200, 'quantity': 0}],
                discount_percent=25,
                shipping_cents=50,
            ),
            {
                'subtotal_cents': 0,
                'discount_cents': 0,
                'shipping_cents': 0,
                'total_cents': 0,
            },
        )

    def test_missing_quantity_defaults_to_one_without_mutating_lines(self):
        lines = [
            {'unit_price_cents': 200, 'quantity': 0},
            {'unit_price_cents': 101},
            {'unit_price_cents': 50, 'quantity': 2},
        ]
        original = copy.deepcopy(lines)
        self.assertEqual(calculate_totals(lines)['subtotal_cents'], 201)
        self.assertEqual(lines, original)

    def test_invalid_explicit_quantities_raise_value_error(self):
        for quantity in (None, False, True, -1, 0.5, 1.5, 0.0, 1.0):
            with self.subTest(quantity=quantity):
                lines = [{'unit_price_cents': 200, 'quantity': quantity}]
                original = copy.deepcopy(lines)
                with self.assertRaises(ValueError):
                    calculate_totals(lines)
                self.assertEqual(lines, original)

    def test_discount_rounds_half_up_in_integer_cents(self):
        for price, expected_discount in ((49, 0), (50, 1), (51, 1)):
            with self.subTest(price=price):
                totals = calculate_totals(
                    [{'unit_price_cents': price}], discount_percent=1
                )
                self.assertEqual(totals['discount_cents'], expected_discount)
                self.assertEqual(totals['total_cents'], price - expected_discount)

    def test_shipping_uses_subtotal_before_discount(self):
        self.assertEqual(
            calculate_totals(
                [{'unit_price_cents': 100}],
                discount_percent=100,
                shipping_cents=25,
            ),
            {
                'subtotal_cents': 100,
                'discount_cents': 100,
                'shipping_cents': 25,
                'total_cents': 25,
            },
        )

    def test_zero_subtotal_never_charges_shipping(self):
        for lines in ([], [{'unit_price_cents': 0, 'quantity': 2}]):
            with self.subTest(lines=lines):
                totals = calculate_totals(lines, shipping_cents=25)
                self.assertEqual(totals['shipping_cents'], 0)
                self.assertEqual(totals['total_cents'], 0)


if __name__ == '__main__':
    unittest.main()
