"""Import order lines from CSV text."""

import csv
import io


def load_orders(text):
    """Return orders grouped in first-seen order, validating every CSV field."""
    required = {'order_id', 'sku', 'quantity', 'unit_price_cents'}
    reader = csv.reader(io.StringIO(text, newline=''), strict=True)
    orders = {}
    try:
        headers = next(reader, None)
        if headers is None:
            raise ValueError('Missing CSV headers')
        headers = [header.strip() for header in headers]
        if len(headers) != len(required) or set(headers) != required:
            raise ValueError('CSV headers must be exactly: ' + ', '.join(sorted(required)))

        for row in reader:
            cells = [cell.strip() for cell in row]
            if not any(cells):
                continue
            if len(cells) != len(headers):
                raise ValueError('CSV row has missing or extra cells')
            fields = dict(zip(headers, cells))
            if not fields['order_id'] or not fields['sku']:
                raise ValueError('order_id and sku must not be empty')
            for name in ('quantity', 'unit_price_cents'):
                value = fields[name]
                if not value or any(char not in '0123456789' for char in value):
                    raise ValueError(name + ' must contain only ASCII decimal digits')
            order_id = fields['order_id']
            if order_id not in orders:
                orders[order_id] = {'order_id': order_id, 'lines': []}
            orders[order_id]['lines'].append({
                'sku': fields['sku'],
                'quantity': int(fields['quantity']),
                'unit_price_cents': int(fields['unit_price_cents']),
            })
    except csv.Error as exc:
        raise ValueError('Invalid CSV: ' + str(exc)) from exc
    return list(orders.values())
