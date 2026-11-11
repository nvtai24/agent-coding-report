"""Import order lines from CSV text."""

import csv
import io


_HEADERS = {'order_id', 'sku', 'quantity', 'unit_price_cents'}


def load_orders(text):
    """Return orders grouped in first-seen order, or raise ValueError."""
    reader = csv.reader(io.StringIO(text, newline=''), strict=True)
    orders = {}
    try:
        headers = next(reader, None)
        if headers is None:
            raise ValueError('Missing CSV headers')
        headers = [cell.strip() for cell in headers]
        if len(headers) != len(_HEADERS) or set(headers) != _HEADERS:
            raise ValueError('Expected exactly order_id, sku, quantity, unit_price_cents')

        for cells in reader:
            cells = [cell.strip() for cell in cells]
            if not any(cells):
                continue
            if len(cells) != len(headers):
                raise ValueError('CSV row has missing or extra cells')
            row = dict(zip(headers, cells))
            if not row['order_id'] or not row['sku']:
                raise ValueError('order_id and sku must not be empty')
            for field in ('quantity', 'unit_price_cents'):
                value = row[field]
                if not value or any(char not in '0123456789' for char in value):
                    raise ValueError(f'{field} must contain only ASCII decimal digits')
            order = orders.setdefault(row['order_id'], {
                'order_id': row['order_id'], 'lines': [],
            })
            order['lines'].append({
                'sku': row['sku'],
                'quantity': int(row['quantity']),
                'unit_price_cents': int(row['unit_price_cents']),
            })
    except csv.Error as exc:
        raise ValueError(f'Invalid CSV: {exc}') from exc
    return list(orders.values())
