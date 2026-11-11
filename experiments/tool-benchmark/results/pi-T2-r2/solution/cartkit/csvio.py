"""Import order lines from CSV text."""

import csv
import io


_HEADERS = {'order_id', 'sku', 'quantity', 'unit_price_cents'}


def load_orders(text):
    """Parse CSV text into orders, preserving order and line encounter order.

    Invalid headers, row shapes, identifiers, or numeric values raise ValueError.
    """
    orders = {}
    headers = None
    try:
        for row in csv.reader(io.StringIO(text, newline=''), strict=True):
            cells = [cell.strip() for cell in row]
            if not any(cells):
                continue
            if headers is None:
                if len(cells) != len(_HEADERS) or set(cells) != _HEADERS:
                    raise ValueError('CSV must contain exactly the required headers')
                headers = cells
                continue
            if len(cells) != len(headers):
                raise ValueError('CSV row has missing or extra cells')
            values = dict(zip(headers, cells))
            if not values['order_id'] or not values['sku']:
                raise ValueError('order_id and sku must not be empty')
            for name in ('quantity', 'unit_price_cents'):
                value = values[name]
                if not value or any(char < '0' or char > '9' for char in value):
                    raise ValueError(f'{name} must contain only ASCII decimal digits')
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
        raise ValueError('CSV headers are required')
    return list(orders.values())
