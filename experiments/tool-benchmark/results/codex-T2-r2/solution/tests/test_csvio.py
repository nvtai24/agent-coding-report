import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cartkit.csvio import load_orders


HEADER = 'order_id,sku,quantity,unit_price_cents\n'


class CsvImportTests(unittest.TestCase):
    def test_groups_orders_and_preserves_duplicate_lines(self):
        result = load_orders(HEADER + 'A1,BOOK,2,150\nB2,PEN,1,20\nA1,BOOK,3,150\n')
        self.assertEqual(result, [
            {'order_id': 'A1', 'lines': [
                {'sku': 'BOOK', 'quantity': 2, 'unit_price_cents': 150},
                {'sku': 'BOOK', 'quantity': 3, 'unit_price_cents': 150},
            ]},
            {'order_id': 'B2', 'lines': [
                {'sku': 'PEN', 'quantity': 1, 'unit_price_cents': 20},
            ]},
        ])

    def test_reordered_headers_whitespace_zeros_and_blank_rows(self):
        self.assertEqual(load_orders(
            ' unit_price_cents , quantity , sku , order_id \r\n'
            '\r\n , , , \r\n 00150 , 00 , BOOK , A1 \r\n'
        ), [{'order_id': 'A1', 'lines': [
            {'sku': 'BOOK', 'quantity': 0, 'unit_price_cents': 150},
        ]}])

    def test_quoted_commas_newlines_and_escaped_quotes(self):
        self.assertEqual(load_orders(HEADER + '" A,1 ","BOOK\r\n""Special""",2,150\r\n'), [
            {'order_id': 'A,1', 'lines': [
                {'sku': 'BOOK\r\n"Special"', 'quantity': 2, 'unit_price_cents': 150},
            ]},
        ])

    def test_header_only(self):
        self.assertEqual(load_orders(HEADER), [])

    def test_invalid_headers(self):
        for text in ('', '\n  \n', 'order_id,sku,quantity\n',
                     'order_id,sku,quantity,unit_price_cents,extra\n',
                     'order_id,sku,quantity, quantity \n',
                     'order_id,sku,quantity,price\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                load_orders(text)

    def test_invalid_row_shapes_and_identifiers(self):
        for row in ('A1,BOOK,2', 'A1,BOOK,2,150,extra',
                    ',BOOK,2,150', 'A1,  ,2,150'):
            with self.subTest(row=row), self.assertRaises(ValueError):
                load_orders(HEADER + row)

    def test_invalid_numbers_in_both_columns(self):
        for value in ('', '-1', '+1', '1.5', 'True', 'false', '1e2', '1 2', '١', '２', '²'):
            for field in (2, 3):
                row = ['A1', 'BOOK', '2', '150']
                row[field] = value
                with self.subTest(value=value, field=field), self.assertRaises(ValueError):
                    load_orders(HEADER + ','.join(row))

    def test_malformed_csv(self):
        with self.assertRaises(ValueError):
            load_orders(HEADER + 'A1,"unterminated,2,150')


class CliTests(unittest.TestCase):
    def run_command(self, command, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.txt'
            path.write_bytes(text.encode('utf-8'))
            process = subprocess.run(
                [sys.executable, '-m', 'cartkit.cli', command, str(path)],
                capture_output=True, text=True, check=True,
            )
        return json.loads(process.stdout)

    def test_import_csv(self):
        text = HEADER + 'A1,"BOOK\r\nSpecial",2,150\r\n'
        self.assertEqual(self.run_command('import-csv', text), load_orders(text))

    def test_totals_still_work(self):
        result = self.run_command('totals', '[{"quantity": 2, "unit_price_cents": 150}]')
        self.assertEqual(result['total_cents'], 300)

    def test_summary_still_works(self):
        self.assertEqual(self.run_command('summary', '[]'), {
            'paid_count': 0, 'paid_total_cents': 0,
            'cancelled_count': 0, 'customers': {},
        })
