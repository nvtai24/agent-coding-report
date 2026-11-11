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
    def test_grouping_order_duplicates_and_zeroes(self):
        text = (' unit_price_cents , sku , order_id , quantity \n'
                ' 00150 , BOOK , A1 , 02 \n'
                '0,PEN,B2,0\n'
                '20,BOOK,A1,1\n')
        self.assertEqual(load_orders(text), [
            {'order_id': 'A1', 'lines': [
                {'sku': 'BOOK', 'quantity': 2, 'unit_price_cents': 150},
                {'sku': 'BOOK', 'quantity': 1, 'unit_price_cents': 20}]},
            {'order_id': 'B2', 'lines': [
                {'sku': 'PEN', 'quantity': 0, 'unit_price_cents': 0}]},
        ])

    def test_quoted_commas_newlines_and_escaped_quotes(self):
        result = load_orders(HEADER + '" A,1 "," Book\r\n""title"" ",2,150\r\n')
        self.assertEqual(result, [{'order_id': 'A,1', 'lines': [
            {'sku': 'Book\r\n"title"', 'quantity': 2, 'unit_price_cents': 150}]}])

    def test_header_only_and_blank_rows(self):
        self.assertEqual(load_orders(HEADER), [])
        self.assertEqual(load_orders(HEADER + '\n  \n,,,\n'), [])
        self.assertEqual(load_orders(HEADER + '\nA,BOOK,1,2\n\n'), [
            {'order_id': 'A', 'lines': [
                {'sku': 'BOOK', 'quantity': 1, 'unit_price_cents': 2}]}])

    def test_invalid_headers(self):
        for text in ('', '\n', 'order_id,sku,quantity\n',
                     'order_id,sku,quantity,unit_price_cents,extra\n',
                     'order_id,sku,quantity,quantity\n',
                     'order_id,sku,quantity,price\n',
                     'order_id,sku,quantity, unit_price_cents ,sku\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                load_orders(text)

    def test_invalid_rows(self):
        for row in ('A,BOOK,1', 'A,BOOK,1,2,extra', ',BOOK,1,2',
                    'A, ,1,2', 'A,BOOK,,2', 'A,BOOK,1,'):
            with self.subTest(row=row), self.assertRaises(ValueError):
                load_orders(HEADER + row)

    def test_numeric_fields_require_ascii_digits(self):
        for value in ('-1', '+1', '1.0', 'True', 'false', '1e2',
                      '١', '１２', '²', '1 2'):
            for field in (2, 3):
                cells = ['A', 'BOOK', '1', '2']
                cells[field] = value
                with self.subTest(value=value, field=field), self.assertRaises(ValueError):
                    load_orders(HEADER + ','.join(cells))

    def test_malformed_csv_is_value_error(self):
        for row in ('A,"BOOK,1,2', 'A,"BOOK"x,1,2'):
            with self.subTest(row=row), self.assertRaises(ValueError):
                load_orders(HEADER + row)


class CliTests(unittest.TestCase):
    def run_cli(self, command, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input'
            path.write_bytes(text.encode('utf-8'))
            result = subprocess.run(
                [sys.executable, '-m', 'cartkit.cli', command, str(path)],
                capture_output=True, text=True, check=True,
            )
        return json.loads(result.stdout)

    def test_import_csv(self):
        text = HEADER + 'A,"BOOK,\r\nvolume",2,150\r\n'
        self.assertEqual(self.run_cli('import-csv', text), load_orders(text))

    def test_existing_commands(self):
        lines = [{'sku': 'BOOK', 'quantity': 2, 'unit_price_cents': 150}]
        self.assertEqual(self.run_cli('totals', json.dumps(lines)), calculate_totals(lines))
        orders = [{'customer': 'A', 'status': 'paid', 'total_cents': 300}]
        self.assertEqual(self.run_cli('summary', json.dumps(orders)), summarize_orders(orders))


if __name__ == '__main__':
    unittest.main()
