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


class LoadOrdersTests(unittest.TestCase):
    def test_grouping_order_and_duplicate_skus(self):
        self.assertEqual(load_orders(HEADER +
                                    'A1,BOOK,2,150\nB2,PEN,1,20\nA1,BOOK,3,160\n'), [
            {'order_id': 'A1', 'lines': [
                {'sku': 'BOOK', 'quantity': 2, 'unit_price_cents': 150},
                {'sku': 'BOOK', 'quantity': 3, 'unit_price_cents': 160},
            ]},
            {'order_id': 'B2', 'lines': [
                {'sku': 'PEN', 'quantity': 1, 'unit_price_cents': 20},
            ]},
        ])

    def test_reordered_trimmed_headers_values_and_zeroes(self):
        self.assertEqual(load_orders(
            ' unit_price_cents , quantity , sku , order_id \n 00150 , 00 , BOOK , A1 \n'
        ), [{'order_id': 'A1', 'lines': [
            {'sku': 'BOOK', 'quantity': 0, 'unit_price_cents': 150},
        ]}])

    def test_quoted_commas_and_newlines(self):
        self.assertEqual(load_orders(HEADER + '"A,1"," BOOK\r\nSET ",2,150\r\n'), [
            {'order_id': 'A,1', 'lines': [
                {'sku': 'BOOK\r\nSET', 'quantity': 2, 'unit_price_cents': 150},
            ]},
        ])

    def test_blank_rows_and_header_only(self):
        for text in (HEADER, HEADER + '\n  \n , , , \n'):
            with self.subTest(text=text):
                self.assertEqual(load_orders(text), [])
        self.assertEqual(len(load_orders(HEADER + '\nA1,BOOK,1,0\n\n')), 1)

    def test_invalid_headers(self):
        for header in ('', 'order_id,sku,quantity\n',
                       'order_id,sku,quantity,unit_price_cents,extra\n',
                       'order_id,sku,quantity,quantity\n',
                       'order_id,sku,quantity, quantity \n',
                       'order_id,sku,quantity,price\n'):
            with self.subTest(header=header), self.assertRaises(ValueError):
                load_orders(header)

    def test_missing_extra_cells_and_empty_identifiers(self):
        for row in ('A1,BOOK,1', 'A1,BOOK,1,150,extra',
                    'A1,BOOK,1,150,', ' ,BOOK,1,150', 'A1, ,1,150'):
            with self.subTest(row=row), self.assertRaises(ValueError):
                load_orders(HEADER + row + '\n')

    def test_invalid_numeric_fields(self):
        for value in ('', '-1', '+1', '1.0', 'True', 'false', '1e2',
                      '1_000', '1 0', '١', '１２', '²'):
            for field in (2, 3):
                row = ['A1', 'BOOK', '1', '150']
                row[field] = value
                with self.subTest(value=value, field=field), self.assertRaises(ValueError):
                    load_orders(HEADER + ','.join(row) + '\n')

    def test_malformed_csv_raises_value_error(self):
        for row in ('A1,"BOOK,1,150\n', 'A1,"BOOK"oops,1,150\n'):
            with self.subTest(row=row), self.assertRaises(ValueError):
                load_orders(HEADER + row)


class CliTests(unittest.TestCase):
    def run_cli(self, command, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input'
            path.write_bytes(text.encode('utf-8'))
            result = subprocess.run(
                [sys.executable, '-m', 'cartkit.cli', command, str(path)],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True, text=True, check=True,
            )
        return json.loads(result.stdout)

    def test_import_csv(self):
        text = HEADER + 'A1,"BOOK\r\nSET",2,150\r\n'
        self.assertEqual(self.run_cli('import-csv', text), load_orders(text))

    def test_existing_commands(self):
        lines = [{'sku': 'BOOK', 'quantity': 2, 'unit_price_cents': 150}]
        orders = [{'customer': 'A', 'status': 'paid', 'total_cents': 300}]
        self.assertEqual(self.run_cli('totals', json.dumps(lines)), calculate_totals(lines))
        self.assertEqual(self.run_cli('summary', json.dumps(orders)), summarize_orders(orders))


if __name__ == '__main__':
    unittest.main()
