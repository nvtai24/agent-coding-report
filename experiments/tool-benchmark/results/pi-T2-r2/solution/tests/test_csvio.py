import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cartkit.csvio import load_orders


HEADER = 'order_id,sku,quantity,unit_price_cents\n'


class CsvImportTests(unittest.TestCase):
    def test_grouping_preserves_order_and_duplicate_skus(self):
        self.assertEqual(load_orders(
            HEADER + 'B,BOOK,2,150\nA,PEN,1,25\nB,BOOK,3,100\n'
        ), [
            {'order_id': 'B', 'lines': [
                {'sku': 'BOOK', 'quantity': 2, 'unit_price_cents': 150},
                {'sku': 'BOOK', 'quantity': 3, 'unit_price_cents': 100},
            ]},
            {'order_id': 'A', 'lines': [
                {'sku': 'PEN', 'quantity': 1, 'unit_price_cents': 25},
            ]},
        ])

    def test_reordered_trimmed_headers_and_values(self):
        self.assertEqual(load_orders(
            ' unit_price_cents , sku , order_id , quantity \n'
            ' 00150 , BOOK , A1 , 00 \n'
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
        self.assertEqual(load_orders('\n  \n' + HEADER + '\n, , ,\n'), [])
        self.assertEqual(len(load_orders(
            HEADER + '\nA,BOOK,1,2\n  \n,,,\n'
        )), 1)

    def test_invalid_headers(self):
        for text in (
            '', '\n  \n', 'order_id,sku,quantity\n',
            'order_id,sku,quantity,unit_price_cents,extra\n',
            'order_id,sku,quantity,quantity\n',
            'order_id,sku,quantity, quantity \n',
            'ORDER_ID,sku,quantity,unit_price_cents\n',
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                load_orders(text)

    def test_invalid_row_shapes_and_identifiers(self):
        for row in (
            'A,BOOK,1', 'A,BOOK,1,2,extra', 'A,BOOK,1,2,',
            ',BOOK,1,2', 'A, ,1,2', '  ,BOOK,1,2',
        ):
            with self.subTest(row=row), self.assertRaises(ValueError):
                load_orders(HEADER + row + '\n')

    def test_numeric_fields_require_ascii_digits(self):
        for value in ('', '-1', '+1', '1.0', 'true', 'False', '1e2',
                      '1_000', '1 2', '١', '１２', '²'):
            for field in (2, 3):
                row = ['A', 'BOOK', '1', '2']
                row[field] = value
                with self.subTest(value=value, field=field):
                    with self.assertRaises(ValueError):
                        load_orders(HEADER + ','.join(row) + '\n')

    def test_malformed_csv_raises_value_error(self):
        with self.assertRaises(ValueError):
            load_orders(HEADER + 'A,"unterminated,1,2\n')

    def run_cli(self, command, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input'
            path.write_bytes(text.encode('utf-8'))
            result = subprocess.run(
                [sys.executable, '-m', 'cartkit.cli', command, str(path)],
                check=True, capture_output=True, text=True,
            )
        return json.loads(result.stdout)

    def test_cli_import_csv(self):
        text = HEADER + 'A,"BOOK\r\npart,2",0,0150\r\n'
        self.assertEqual(self.run_cli('import-csv', text), load_orders(text))

    def test_cli_existing_commands(self):
        from cartkit.money import calculate_totals
        from cartkit.reports import summarize_orders

        lines = [{'quantity': 2, 'unit_price_cents': 150}]
        self.assertEqual(self.run_cli('totals', json.dumps(lines)),
                         calculate_totals(lines))
        orders = [{'customer': 'A', 'status': 'paid', 'total_cents': 300}]
        self.assertEqual(self.run_cli('summary', json.dumps(orders)),
                         summarize_orders(orders))


if __name__ == '__main__':
    unittest.main()
