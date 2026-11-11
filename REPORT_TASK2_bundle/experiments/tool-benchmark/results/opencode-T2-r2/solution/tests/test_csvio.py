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
    def test_grouping_preserves_order_and_duplicate_skus(self):
        self.assertEqual(load_orders(HEADER + (
            'A1,BOOK,2,150\nB2,PEN,1,25\nA1,BOOK,3,200\n'
        )), [
            {'order_id': 'A1', 'lines': [
                {'sku': 'BOOK', 'quantity': 2, 'unit_price_cents': 150},
                {'sku': 'BOOK', 'quantity': 3, 'unit_price_cents': 200},
            ]},
            {'order_id': 'B2', 'lines': [
                {'sku': 'PEN', 'quantity': 1, 'unit_price_cents': 25},
            ]},
        ])

    def test_reordered_headers_whitespace_and_zeroes(self):
        self.assertEqual(load_orders(
            ' unit_price_cents , quantity , sku , order_id \n'
            ' 00150 , 00 , BOOK , A1 \n'
        ), [{'order_id': 'A1', 'lines': [
            {'sku': 'BOOK', 'quantity': 0, 'unit_price_cents': 150},
        ]}])

    def test_quoted_commas_newlines_and_quotes(self):
        self.assertEqual(load_orders(
            HEADER + '"A,1","BOOK\r\n""special""",2,150\r\n'
        ), [{'order_id': 'A,1', 'lines': [
            {'sku': 'BOOK\r\n"special"', 'quantity': 2, 'unit_price_cents': 150},
        ]}])

    def test_header_only_and_blank_rows(self):
        self.assertEqual(load_orders(HEADER), [])
        self.assertEqual(load_orders(HEADER + '\n  \n , , , \n'), [])
        self.assertEqual(load_orders(HEADER + '\nA1,BOOK,0,0\n\n'), [
            {'order_id': 'A1', 'lines': [
                {'sku': 'BOOK', 'quantity': 0, 'unit_price_cents': 0},
            ]},
        ])

    def test_invalid_headers(self):
        for text in (
            '', '\n', 'order_id,sku,quantity\n',
            'order_id,sku,quantity,unit_price_cents,extra\n',
            'order_id,sku,quantity,quantity\n',
            'order_id,sku,quantity, unit_price_cents ,sku\n',
            'ORDER_ID,sku,quantity,unit_price_cents\n',
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                load_orders(text)

    def test_missing_extra_and_empty_cells(self):
        for row in (
            'A1,BOOK,2', 'A1,BOOK,2,150,extra', 'A1,BOOK,2,150,',
            ',BOOK,2,150', 'A1, ,2,150', 'A1,BOOK,,150', 'A1,BOOK,2,',
        ):
            with self.subTest(row=row), self.assertRaises(ValueError):
                load_orders(HEADER + row)

    def test_numeric_fields_require_ascii_digits(self):
        for value in ('-1', '+1', '1.0', 'True', 'false', '١', '１２', '²', '1 2'):
            for field in (2, 3):
                cells = ['A1', 'BOOK', '2', '150']
                cells[field] = value
                with self.subTest(value=value, field=field), self.assertRaises(ValueError):
                    load_orders(HEADER + ','.join(cells))

    def test_malformed_csv_raises_value_error(self):
        for row in ('A1,"BOOK,2,150', 'A1,"BOOK"oops,2,150'):
            with self.subTest(row=row), self.assertRaises(ValueError):
                load_orders(HEADER + row)


class CliTests(unittest.TestCase):
    def run_command(self, command, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input'
            path.write_bytes(text.encode('utf-8'))
            result = subprocess.run(
                [sys.executable, '-m', 'cartkit.cli', command, str(path)],
                capture_output=True, text=True, check=True,
            )
        return json.loads(result.stdout)

    def test_import_csv(self):
        text = HEADER + 'A1,"BOOK\r\nPART",2,150\r\n'
        self.assertEqual(self.run_command('import-csv', text), load_orders(text))

    def test_existing_json_commands(self):
        lines = [{'unit_price_cents': 150, 'quantity': 2}]
        orders = [{'customer': 'A', 'status': 'paid', 'total_cents': 300}]
        self.assertEqual(self.run_command('totals', json.dumps(lines)), calculate_totals(lines))
        self.assertEqual(self.run_command('summary', json.dumps(orders)), summarize_orders(orders))


if __name__ == '__main__':
    unittest.main()
