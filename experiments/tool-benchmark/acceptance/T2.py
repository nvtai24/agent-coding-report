import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


def load(text):return importlib.import_module('cartkit.csvio').load_orders(text)
HEADER='order_id,sku,quantity,unit_price_cents\n'


class Acceptance(unittest.TestCase):
    def test_grouping_order_and_duplicate_sku(self):
        self.assertEqual(load(HEADER+'A,X,1,10\nB,Y,2,20\nA,X,3,30\n'),[
            {'order_id':'A','lines':[{'sku':'X','quantity':1,'unit_price_cents':10},{'sku':'X','quantity':3,'unit_price_cents':30}]},
            {'order_id':'B','lines':[{'sku':'Y','quantity':2,'unit_price_cents':20}]}])

    def test_header_order_and_trimming(self):
        self.assertEqual(load(' quantity , sku ,unit_price_cents, order_id \n 2 , BOOK , 150 , A \n'),[{'order_id':'A','lines':[{'sku':'BOOK','quantity':2,'unit_price_cents':150}]}])

    def test_quoted_csv(self):
        self.assertEqual(load(HEADER+'A,"BOOK, LARGE\nEDITION",1,99\n')[0]['lines'][0]['sku'],'BOOK, LARGE\nEDITION')

    def test_zero_and_leading_zeros(self):
        self.assertEqual(load(HEADER+'A,X,000,0005\n')[0]['lines'][0],{'sku':'X','quantity':0,'unit_price_cents':5})

    def test_empty_valid_input(self):
        self.assertEqual(load(HEADER),[])

    def test_blank_rows_ignored(self):
        self.assertEqual(len(load(HEADER+'\n,,,\nA,X,1,1\n')),1)

    def test_invalid_headers(self):
        for text in ['', 'order_id,sku,quantity\n', 'order_id,sku,quantity,quantity\n','order_id,sku,quantity,unit_price_cents,extra\n']:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):load(text)

    def test_missing_and_extra_cells(self):
        for row in ['A,X,1\n','A,X,1,2,3\n']:
            with self.subTest(row=row):
                with self.assertRaises(ValueError):load(HEADER+row)

    def test_blank_identifiers(self):
        for row in [',X,1,2\n','A, ,1,2\n']:
            with self.subTest(row=row):
                with self.assertRaises(ValueError):load(HEADER+row)

    def test_invalid_numeric_values(self):
        for value in ['-1','1.5','true','+1','1e2','']:
            for column in [2,3]:
                cells=['A','X','1','2'];cells[column]=value
                with self.subTest(value=value,column=column):
                    with self.assertRaises(ValueError):load(HEADER+','.join(cells)+'\n')

    def test_ascii_digits_only(self):
        with self.assertRaises(ValueError):load(HEADER+'A,X,١,2\n')

    def test_cli_json(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'orders.csv';file.write_text(HEADER+'A,X,2,150\n')
            result=subprocess.run([sys.executable,'-m','cartkit.cli','import-csv',str(file)],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout),[{'order_id':'A','lines':[{'sku':'X','quantity':2,'unit_price_cents':150}]}])
