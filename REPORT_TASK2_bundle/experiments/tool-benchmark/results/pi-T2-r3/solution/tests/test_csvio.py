import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cartkit.csvio import load_orders
from cartkit.money import calculate_totals
from cartkit.reports import summarize_orders


HEADER = 'order_id,sku,quantity,unit_price_cents\n'


class CsvImportTests(unittest.TestCase):
    def test_grouping_order_and_duplicate_skus(self):
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

    def test_reordered_trimmed_headers_and_values(self):
        self.assertEqual(load_orders(
            ' unit_price_cents , quantity , sku , order_id \n'
            ' 00150 , 00 , BOOK , A1 \n'), [
                {'order_id': 'A1', 'lines': [
                    {'sku': 'BOOK', 'quantity': 0, 'unit_price_cents': 150},
                ]},
            ])

    def test_quoted_commas_newlines_and_escaped_quotes(self):
        self.assertEqual(load_orders(HEADER +
            '" A,1 ","BOOK\r\n""Special""",2,150\r\n'), [
                {'order_id': 'A,1', 'lines': [
                    {'sku': 'BOOK\r\n"Special"', 'quantity': 2,
                     'unit_price_cents': 150},
                ]},
            ])

    def test_header_only_and_blank_rows(self):
        self.assertEqual(load_orders(HEADER), [])
        self.assertEqual(load_orders(HEADER + '\n  \n , , , \n'), [])
        self.assertEqual(load_orders(HEADER + '\nA,BOOK,0,0\n\n'), [
            {'order_id': 'A', 'lines': [
                {'sku': 'BOOK', 'quantity': 0, 'unit_price_cents': 0},
            ]},
        ])

    def test_invalid_headers(self):
        for text in ('', '\n', 'order_id,sku,quantity\n',
                     'order_id,sku,quantity,unit_price_cents,extra\n',
                     'order_id,sku,quantity,quantity\n',
                     'order_id,sku,quantity, quantity \n',
                     'order_id,sku,quantity,price\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                load_orders(text)

    def test_invalid_row_shapes_and_identifiers(self):
        for row in ('A,BOOK,1', 'A,BOOK,1,2,extra', 'A,BOOK,1,2,',
                    ',BOOK,1,2', 'A, ,1,2'):
            with self.subTest(row=row), self.assertRaises(ValueError):
                load_orders(HEADER + row + '\n')

    def test_invalid_numeric_cells(self):
        for value in ('', '-1', '+1', '1.0', 'True', 'false', '١', '２',
                      '1 2', '1e2'):
            for quantity, price in ((value, '10'), ('1', value)):
                with self.subTest(quantity=quantity, price=price):
                    with self.assertRaises(ValueError):
                        load_orders(HEADER + f'A,BOOK,{quantity},{price}\n')

    def test_malformed_csv_raises_value_error(self):
        with self.assertRaises(ValueError):
            load_orders(HEADER + 'A,"unterminated,1,2\n')


class CliTests(unittest.TestCase):
    def run_cli(self, command, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input'
            path.write_bytes(text.encode('utf-8'))
            result = subprocess.run(
                [sys.executable, '-m', 'cartkit.cli', command, str(path)],
                check=True, capture_output=True, text=True,
            )
        return json.loads(result.stdout)

    def test_import_csv(self):
        text = HEADER + 'A,"BOOK\r\nSPECIAL",2,150\r\n'
        self.assertEqual(self.run_cli('import-csv', text), load_orders(text))

    def test_existing_commands(self):
        lines = [{'sku': 'BOOK', 'quantity': 2, 'unit_price_cents': 150}]
        self.assertEqual(self.run_cli('totals', json.dumps(lines)),
                         calculate_totals(lines))
        orders = [{'customer': 'A', 'status': 'paid', 'total_cents': 300}]
        self.assertEqual(self.run_cli('summary', json.dumps(orders)),
                         summarize_orders(orders))


if __name__ == '__main__':
    unittest.main()
