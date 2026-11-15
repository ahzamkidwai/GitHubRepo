
from fastapi import FastAPI


def calculate_total(price, quantity):
    total = price * quantity
    return total


class PaymentService:

    def process_payment(self, amount):
        return calculate_total(amount, 1)
