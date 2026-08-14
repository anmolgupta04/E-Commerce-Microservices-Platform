"""
Mocked payment gateway. No real card network is called -- this is what
lets the whole platform demo end-to-end with zero external dependencies
and zero real money. Swap this module for a Stripe/Razorpay client and
nothing else in the service has to change.
"""
import uuid
from decimal import Decimal


def charge(order_id: int, amount: Decimal) -> dict:
    # Demo rule so failure is reachable in the demo: amounts that are exact
    # multiples of 666 "decline". Everything else succeeds.
    if int(amount) != 0 and int(amount) % 666 == 0:
        return {"success": False, "reason": "card_declined (mock gateway rule)"}
    return {"success": True, "reference": f"mock_{uuid.uuid4().hex[:12]}"}
