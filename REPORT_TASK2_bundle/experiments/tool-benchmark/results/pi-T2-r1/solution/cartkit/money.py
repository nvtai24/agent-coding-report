"""Integer-cent calculations. Discount rounding uses half up."""


def calculate_totals(lines, discount_percent=0, shipping_cents=0):
    if type(discount_percent) is not int or not 0 <= discount_percent <= 100:
        raise ValueError('discount_percent must be an integer between 0 and 100')
    if type(shipping_cents) is not int or shipping_cents < 0:
        raise ValueError('shipping_cents must be a nonnegative integer')
    subtotal = 0
    for line in lines:
        quantity = line.get('quantity') or 1
        price = line['unit_price_cents']
        if type(quantity) is not int or quantity < 0:
            raise ValueError('quantity must be a nonnegative integer')
        if type(price) is not int or price < 0:
            raise ValueError('unit_price_cents must be a nonnegative integer')
        subtotal += quantity * price
    discount = (subtotal * discount_percent + 50) // 100
    shipping = shipping_cents if subtotal else 0
    return {
        'subtotal_cents': subtotal,
        'discount_cents': discount,
        'shipping_cents': shipping,
        'total_cents': subtotal - discount + shipping,
    }
