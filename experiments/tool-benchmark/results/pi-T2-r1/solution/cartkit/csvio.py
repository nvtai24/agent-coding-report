"""Import order lines from CSV text."""

import csv
import io


_HEADERS = {'order_id', 'sku', 'quantity', 'unit_price_cents'}


def load_orders(text):
    """Return orders grouped in input order, rejecting invalid CSV data."""
    reader = csv.reader(io.StringIO(text, newline=''), strict=True)
    orders = {}
    try:
        headers = next(reader, None)
        if headers is None:
            raise ValueError('Missing CSV headers')
        headers = [cell.strip() for cell in headers]
        if len(headers) != len(_HEADERS) or set(headers) != _HEADERS:
            raise ValueError('CSV headers must be exactly: ' + ', '.join(sorted(_HEADERS)))

        for row in reader:
            cells = [cell.strip() for cell in row]
            if not cells or not any(cells):
                continue
            if len(cells) != len(headers):
                raise ValueError('CSV row has missing or extra cells')
            values = dict(zip(headers, cells))
            if not values['order_id'] or not values['sku']:
                raise ValueError('order_id and sku must not be empty')
            for field in ('quantity', 'unit_price_cents'):
                value = values[field]
                if not value or any(char not in '0123456789' for char in value):
                    raise ValueError(field + ' must contain only ASCII decimal digits')
            order_id = values['order_id']
            if order_id not in orders:
                orders[order_id] = {'order_id': order_id, 'lines': []}
            orders[order_id]['lines'].append({
                'sku': values['sku'],
                'quantity': int(values['quantity']),
                'unit_price_cents': int(values['unit_price_cents']),
            })
    except csv.Error as exc:
        raise ValueError('Invalid CSV: ' + str(exc)) from exc
    return list(orders.values())
