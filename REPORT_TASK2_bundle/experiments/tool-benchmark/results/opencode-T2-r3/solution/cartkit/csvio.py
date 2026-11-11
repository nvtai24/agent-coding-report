import csv
import io


def load_orders(text):
    """Parse CSV order lines, preserving order and validating every field."""
    headers = {'order_id', 'sku', 'quantity', 'unit_price_cents'}
    reader = csv.reader(io.StringIO(text, newline=''), strict=True)
    orders = {}
    try:
        fields = next(reader, None)
        if fields is None:
            raise ValueError('Missing CSV headers')
        fields = [field.strip() for field in fields]
        if len(fields) != len(headers) or set(fields) != headers:
            raise ValueError('CSV headers must be exactly: ' + ', '.join(sorted(headers)))

        for row in reader:
            row = [cell.strip() for cell in row]
            if not row or all(not cell for cell in row):
                continue
            if len(row) != len(fields):
                raise ValueError('CSV row has missing or extra cells')
            values = dict(zip(fields, row))
            if not values['order_id'] or not values['sku']:
                raise ValueError('order_id and sku must not be empty')
            for name in ('quantity', 'unit_price_cents'):
                value = values[name]
                if not value or any(char < '0' or char > '9' for char in value):
                    raise ValueError(name + ' must contain only ASCII decimal digits')
            order_id = values['order_id']
            if order_id not in orders:
                orders[order_id] = {'order_id': order_id, 'lines': []}
            orders[order_id]['lines'].append({
                'sku': values['sku'],
                'quantity': int(values['quantity']),
                'unit_price_cents': int(values['unit_price_cents']),
            })
    except csv.Error as error:
        raise ValueError('Invalid CSV: ' + str(error)) from error
    return list(orders.values())
