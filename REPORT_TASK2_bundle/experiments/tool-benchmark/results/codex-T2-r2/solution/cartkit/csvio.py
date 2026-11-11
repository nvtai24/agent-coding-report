"""Import order lines from CSV text."""

import csv
from io import StringIO


def load_orders(text):
    """Return orders grouped in first-seen order, or raise ValueError."""
    if not isinstance(text, str):
        raise ValueError('CSV input must be text')

    required = {'order_id', 'sku', 'quantity', 'unit_price_cents'}
    headers = None
    orders = {}
    try:
        for row in csv.reader(StringIO(text, newline=''), strict=True):
            cells = [cell.strip() for cell in row]
            if not any(cells):
                continue
            if headers is None:
                if len(cells) != len(required) or set(cells) != required:
                    raise ValueError('CSV requires exactly the order headers')
                headers = cells
                continue
            if len(cells) != len(headers):
                raise ValueError('CSV row has missing or extra cells')
            values = dict(zip(headers, cells))
            if not values['order_id'] or not values['sku']:
                raise ValueError('order_id and sku must not be empty')
            for field in ('quantity', 'unit_price_cents'):
                value = values[field]
                if not value.isascii() or not value.isdecimal():
                    raise ValueError(f'{field} must contain only ASCII decimal digits')
            order_id = values['order_id']
            if order_id not in orders:
                orders[order_id] = {'order_id': order_id, 'lines': []}
            orders[order_id]['lines'].append({
                'sku': values['sku'],
                'quantity': int(values['quantity']),
                'unit_price_cents': int(values['unit_price_cents']),
            })
    except csv.Error as exc:
        raise ValueError(f'Invalid CSV: {exc}') from exc
    if headers is None:
        raise ValueError('CSV header is missing')
    return list(orders.values())
