"""Import order lines from CSV text."""

import csv
import io


def load_orders(text):
    """Return orders in first-seen order, rejecting invalid CSV input."""
    required = {'order_id', 'sku', 'quantity', 'unit_price_cents'}
    reader = csv.reader(io.StringIO(text, newline=''), strict=True)
    orders = {}
    try:
        headers = next(reader, None)
        if headers is None:
            raise ValueError('Missing CSV headers')
        headers = [header.strip() for header in headers]
        if len(headers) != len(required) or set(headers) != required:
            raise ValueError('Expected exactly order_id, sku, quantity, unit_price_cents')

        for row in reader:
            row = [cell.strip() for cell in row]
            if not any(row):
                continue
            if len(row) != len(headers):
                raise ValueError('Incorrect number of CSV cells')
            values = dict(zip(headers, row))
            if not values['order_id'] or not values['sku']:
                raise ValueError('order_id and sku must not be empty')
            for field in ('quantity', 'unit_price_cents'):
                value = values[field]
                if not value or any(char not in '0123456789' for char in value):
                    raise ValueError(f'{field} must contain only ASCII decimal digits')
            order_id = values['order_id']
            if order_id not in orders:
                orders[order_id] = {'order_id': order_id, 'lines': []}
            orders[order_id]['lines'].append({
                'sku': values['sku'],
                'quantity': int(values['quantity']),
                'unit_price_cents': int(values['unit_price_cents']),
            })
    except csv.Error as error:
        raise ValueError(f'Invalid CSV: {error}') from error
    return list(orders.values())
