"""Import order lines from CSV text."""

import csv
import io


def load_orders(text):
    """Return orders grouped in input order, rejecting invalid CSV data."""
    required = {'order_id', 'sku', 'quantity', 'unit_price_cents'}
    orders = {}
    headers = None
    try:
        for row in csv.reader(io.StringIO(text, newline=''), strict=True):
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
                raise ValueError('order_id and sku must be nonempty')
            for field in ('quantity', 'unit_price_cents'):
                value = values[field]
                if not value or any(char not in '0123456789' for char in value):
                    raise ValueError(f'{field} must contain only ASCII decimal digits')
            order = orders.setdefault(values['order_id'], {
                'order_id': values['order_id'], 'lines': [],
            })
            order['lines'].append({
                'sku': values['sku'],
                'quantity': int(values['quantity']),
                'unit_price_cents': int(values['unit_price_cents']),
            })
    except csv.Error as exc:
        raise ValueError(f'Invalid CSV: {exc}') from exc
    if headers is None:
        raise ValueError('CSV headers are required')
    return list(orders.values())
