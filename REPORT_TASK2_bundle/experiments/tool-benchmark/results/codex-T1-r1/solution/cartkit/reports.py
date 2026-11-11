"""Reports for orders with status paid, pending or cancelled."""


def customer_totals(orders):
    totals = {}
    for order in orders:
        if order['status'] == 'paid':
            customer = order['customer']
            totals[customer] = totals.get(customer, 0) + order['total_cents']
    return totals


def summarize_orders(orders):
    paid = [order for order in orders if order['status'] == 'paid']
    paid_total = sum(order['total_cents'] for order in paid)
    cancelled_count = sum(order['status'] == 'cancelled' for order in orders)
    customers = {}
    for order in orders:
        if order['status'] == 'paid':
            customer = order['customer']
            customers[customer] = customers.get(customer, 0) + order['total_cents']
    return {
        'paid_count': len(paid),
        'paid_total_cents': paid_total,
        'cancelled_count': cancelled_count,
        'customers': customers,
    }
