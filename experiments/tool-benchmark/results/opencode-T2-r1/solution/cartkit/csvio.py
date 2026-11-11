"""Read order lines from CSV text."""

import csv
import io


def load_orders(text):
    required = {'order_id', 'sku', 'quantity', 'unit_price_cents'}
    orders = {}
    try:
        reader = csv.reader(io.StringIO(text, newline=''), strict=True)
        headers = next(reader, [])
        headers = [header.strip() for header in headers]
        if len(headers) != len(required) or set(headers) != required:
            raise ValueError('CSV headers must be exactly: order_id, sku, quantity, unit_price_cents')

        for row in reader:
            values = [cell.strip() for cell in row]
            if not any(values):
                continue
            if len(values) != len(headers):
                raise ValueError('CSV row must have exactly four cells')
            fields = dict(zip(headers, values))
            if not fields['order_id'] or not fields['sku']:
                raise ValueError('order_id and sku must not be empty')
            for name in ('quantity', 'unit_price_cents'):
                value = fields[name]
                if not value or any(char not in '0123456789' for char in value):
                    raise ValueError(f'{name} must contain only ASCII decimal digits')
            order_id = fields['order_id']
            if order_id not in orders:
                orders[order_id] = {'order_id': order_id, 'lines': []}
            orders[order_id]['lines'].append({
                'sku': fields['sku'],
                'quantity': int(fields['quantity']),
                'unit_price_cents': int(fields['unit_price_cents']),
            })
    except csv.Error as exc:
        raise ValueError(f'Invalid CSV: {exc}') from exc
    return list(orders.values())
