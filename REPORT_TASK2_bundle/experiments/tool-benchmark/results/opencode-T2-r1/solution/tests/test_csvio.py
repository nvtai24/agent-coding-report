import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cartkit.csvio import load_orders


HEADER = 'order_id,sku,quantity,unit_price_cents\n'


class LoadOrdersTests(unittest.TestCase):
    def test_grouping_and_line_order_with_duplicate_skus(self):
        self.assertEqual(load_orders(
            HEADER + 'A1,BOOK,2,150\nB2,PEN,1,25\nA1,BOOK,3,100\n'
        ), [
            {'order_id': 'A1', 'lines': [
                {'sku': 'BOOK', 'quantity': 2, 'unit_price_cents': 150},
                {'sku': 'BOOK', 'quantity': 3, 'unit_price_cents': 100},
            ]},
            {'order_id': 'B2', 'lines': [
                {'sku': 'PEN', 'quantity': 1, 'unit_price_cents': 25},
            ]},
        ])

    def test_reordered_trimmed_headers_and_values(self):
        self.assertEqual(load_orders(
            ' unit_price_cents , quantity , sku , order_id \n'
            ' 00150 , 000 , BOOK , A1 \n'
        ), [{'order_id': 'A1', 'lines': [
            {'sku': 'BOOK', 'quantity': 0, 'unit_price_cents': 150},
        ]}])

    def test_quoted_commas_newlines_and_escaped_quotes(self):
        self.assertEqual(load_orders(
            HEADER + '"A,1","BOOK\r\n""special""",2,150\r\n'
        ), [{'order_id': 'A,1', 'lines': [
            {'sku': 'BOOK\r\n"special"', 'quantity': 2, 'unit_price_cents': 150},
        ]}])

    def test_header_only_and_blank_rows(self):
        self.assertEqual(load_orders(HEADER), [])
        self.assertEqual(load_orders(HEADER + '\n  \n , , , \n'), [])
        self.assertEqual(load_orders(
            HEADER + '\nA1,BOOK,0,0\n\n'
        )[0]['lines'], [{'sku': 'BOOK', 'quantity': 0, 'unit_price_cents': 0}])

    def test_invalid_headers(self):
        for header in (
            '', '\n', 'order_id,sku,quantity\n',
            'order_id,sku,quantity,unit_price_cents,extra\n',
            'order_id,sku,quantity,quantity\n',
            'order_id,sku,quantity, quantity \n',
            'order_id,sku,quantity,price\n',
        ):
            with self.subTest(header=header), self.assertRaises(ValueError):
                load_orders(header)

    def test_invalid_row_shapes_and_identifiers(self):
        for row in (
            'A1,BOOK,1', 'A1,BOOK,1,150,extra', 'A1,BOOK,1,150,',
            ',BOOK,1,150', 'A1, ,1,150', ' ,BOOK,1,150',
        ):
            with self.subTest(row=row), self.assertRaises(ValueError):
                load_orders(HEADER + row + '\n')

    def test_invalid_numeric_values(self):
        for value in ('', '-1', '+1', '1.0', 'True', 'false', '1e2', '1 2', '١', '１２', '²'):
            for field in ('quantity', 'unit_price_cents'):
                fields = {'quantity': '1', 'unit_price_cents': '150'}
                fields[field] = value
                with self.subTest(value=value, field=field), self.assertRaises(ValueError):
                    load_orders(HEADER + f'A1,BOOK,{fields["quantity"]},{fields["unit_price_cents"]}\n')

    def test_malformed_csv_raises_value_error(self):
        with self.assertRaises(ValueError):
            load_orders(HEADER + 'A1,"unterminated,1,150\n')


class CsvCliTests(unittest.TestCase):
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
        text = HEADER + 'A1,"BOOK\r\nSET",2,150\r\n'
        self.assertEqual(self.run_cli('import-csv', text), load_orders(text))

    def test_totals_still_accepts_json(self):
        result = self.run_cli('totals', '[{"quantity": 2, "unit_price_cents": 150}]')
        self.assertEqual(result['total_cents'], 300)

    def test_summary_still_accepts_json(self):
        result = self.run_cli('summary', '[{"customer": "A", "status": "paid", "total_cents": 300}]')
        self.assertEqual(result['paid_total_cents'], 300)
        self.assertEqual(result['customers'], {'A': 300})


if __name__ == '__main__':
    unittest.main()
