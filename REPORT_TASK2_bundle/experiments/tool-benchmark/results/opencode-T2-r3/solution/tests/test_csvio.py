import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cartkit.csvio import load_orders


HEADER = 'order_id,sku,quantity,unit_price_cents\n'


class CSVTests(unittest.TestCase):
    def test_grouping_and_line_order(self):
        self.assertEqual(load_orders(HEADER +
                                    'B,BOOK,2,150\nA,PEN,1,20\nB,BOOK,3,100\n'), [
            {'order_id': 'B', 'lines': [
                {'sku': 'BOOK', 'quantity': 2, 'unit_price_cents': 150},
                {'sku': 'BOOK', 'quantity': 3, 'unit_price_cents': 100},
            ]},
            {'order_id': 'A', 'lines': [
                {'sku': 'PEN', 'quantity': 1, 'unit_price_cents': 20},
            ]},
        ])

    def test_reordered_trimmed_headers_cells_and_zero(self):
        self.assertEqual(load_orders(
            ' unit_price_cents , quantity , sku , order_id \n'
            ' 00150 , 00 , BOOK , A1 \n'), [
                {'order_id': 'A1', 'lines': [
                    {'sku': 'BOOK', 'quantity': 0, 'unit_price_cents': 150},
                ]},
            ])

    def test_quoted_commas_newlines_and_escaped_quotes(self):
        self.assertEqual(load_orders(HEADER + '"A,1","BOOK\n""special""",2,150\n'), [
            {'order_id': 'A,1', 'lines': [
                {'sku': 'BOOK\n"special"', 'quantity': 2, 'unit_price_cents': 150},
            ]},
        ])

    def test_header_only_and_blank_rows(self):
        self.assertEqual(load_orders(HEADER), [])
        self.assertEqual(load_orders(HEADER + '\n   \n,,,\n'), [])
        self.assertEqual(load_orders(HEADER + '\nA,BOOK,0,0\n\n')[0]['lines'], [
            {'sku': 'BOOK', 'quantity': 0, 'unit_price_cents': 0},
        ])

    def test_invalid_headers(self):
        for text in ('', '\n', 'order_id,sku,quantity\n',
                     HEADER.rstrip() + ',extra\n',
                     'order_id,sku,quantity,quantity\n',
                     'order_id,sku,quantity, quantity \n',
                     'order_id,sku,quantity,price\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                load_orders(text)

    def test_invalid_rows(self):
        for row in ('A,BOOK,1', 'A,BOOK,1,2,extra', ',BOOK,1,2',
                    'A, ,1,2', 'A,BOOK,,2', 'A,BOOK,1,',
                    'A,"BOOK,1,2', 'A,"BOOK"junk,1,2'):
            with self.subTest(row=row), self.assertRaises(ValueError):
                load_orders(HEADER + row)

    def test_invalid_numbers(self):
        for value in ('-1', '+1', '1.0', 'True', 'false', '١', '１２', '1 0'):
            for quantity, price in ((value, '1'), ('1', value)):
                with self.subTest(quantity=quantity, price=price):
                    with self.assertRaises(ValueError):
                        load_orders(HEADER + f'A,BOOK,{quantity},{price}\n')

    def test_cli_commands(self):
        cases = [
            ('import-csv', HEADER + 'A,BOOK,2,150\n', [
                {'order_id': 'A', 'lines': [
                    {'sku': 'BOOK', 'quantity': 2, 'unit_price_cents': 150},
                ]},
            ]),
            ('totals', '[{"unit_price_cents": 150, "quantity": 2}]', None),
            ('summary', '[]', None),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for command, text, expected in cases:
                with self.subTest(command=command):
                    path = Path(directory) / 'input'
                    path.write_text(text)
                    result = subprocess.run(
                        [sys.executable, '-m', 'cartkit.cli', command, str(path)],
                        capture_output=True, text=True, check=True,
                        cwd=Path(__file__).resolve().parents[1],
                    )
                    actual = json.loads(result.stdout)
                    if expected is not None:
                        self.assertEqual(actual, expected)
                    elif command == 'totals':
                        self.assertEqual(actual['total_cents'], 300)
                    else:
                        self.assertEqual(actual['paid_count'], 0)


if __name__ == '__main__':
    unittest.main()
