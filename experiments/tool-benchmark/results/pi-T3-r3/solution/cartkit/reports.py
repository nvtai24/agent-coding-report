"""Reports for orders with status paid, pending or cancelled."""


def _aggregate_orders(orders):
    """Aggregate report data in one pass without changing the orders."""
    paid_count = 0
    paid_total = 0
    cancelled_count = 0
    customers = {}
    for order in orders:
        status = order['status']
        if status == 'paid':
            customer = order['customer']
            total = order['total_cents']
            paid_count += 1
            paid_total += total
            customers[customer] = customers.get(customer, 0) + total
        elif status == 'cancelled':
            cancelled_count += 1
    return {
        'paid_count': paid_count,
        'paid_total_cents': paid_total,
        'cancelled_count': cancelled_count,
        'customers': customers,
    }


def customer_totals(orders):
    return _aggregate_orders(orders)['customers']


def summarize_orders(orders):
    return _aggregate_orders(orders)
