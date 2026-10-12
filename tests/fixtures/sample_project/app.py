"""Tiny order-processing app used as a smoke-test target. Deliberately not well-structured."""

from utils import format_money


def process_order(order):
    # Validation, pricing, persistence and output are all mixed in one function.
    if not order.get("items"):
        raise ValueError("empty order")
    total = 0
    for item in order["items"]:
        if item["qty"] <= 0:
            raise ValueError("bad qty")
        price = item["price"] * item["qty"]
        if order.get("customer_type") == "vip":
            price = price * 0.9
        elif order.get("customer_type") == "staff":
            price = price * 0.7
        total += price
    if total > 1000:
        total = total - 50
    with open("orders.log", "a") as log:
        log.write(f"{order['id']},{total}\n")
    print("Order", order["id"], "total", format_money(total))
    return total
