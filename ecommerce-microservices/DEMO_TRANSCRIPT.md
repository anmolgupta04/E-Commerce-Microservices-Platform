# Live Demo Transcript

This is real output captured from running all 5 services locally (SQLite,
`EVENT_BUS_MODE=http`), exercising the full order lifecycle. No mocking of
HTTP calls -- every request below hit an actual running Django service.

## 1. Register + login (Auth service)
```
POST /api/auth/register/  {"username":"ansh","email":"ansh@example.com","password":"SuperSecret123!"}
-> 201 {"id":1,"username":"ansh","email":"ansh@example.com"}

POST /api/auth/login/  {"username":"ansh","password":"SuperSecret123!"}
-> 200 {"refresh": "...", "access": "..."}   # JWT embeds user_id + username claims
```

## 2. Seed catalog (Catalog service)
```
Wireless Bluetooth Headphones  $59.99  stock=50
Mechanical Keyboard            $89.00  stock=30
USB-C Hub 7-in-1               $24.50  stock=100
```

## 3. Happy path: place an order (Orders orchestrates Auth + Catalog synchronously)
```
POST /api/orders/  Authorization: Bearer <jwt>
{"items":[{"product_id":2,"quantity":1}]}

-> 201 {"id":2,"status":"pending_payment","total_amount":"89.00", ...}
```
Behind that one call: Orders -> Auth `/verify/` (confirms JWT is real) ->
Orders -> Catalog `/products/2/` (price) -> Orders -> Catalog
`/products/2/adjust-stock/` (reserve 1 unit) -> order row written ->
`order.created` event published.

```
GET /api/orders/2/          -> status: "paid"                (~50ms later)
GET /api/payments/          -> [{"order_id":2,"status":"succeeded","gateway_reference":"mock_4910e9fa6018"}]
GET /api/notifications/     -> order.created, order.paid messages logged for "ansh"
```

## 4. Failure path A: insufficient stock (rolled back automatically)
```
POST /api/orders/  {"items":[{"product_id":2,"quantity":9999}]}
-> 409 {"detail":"insufficient stock for product 2"}
```
No order row is created; no partial stock reservation is left behind.

## 5. Failure path B: payment declined (mock gateway rule: amount % 666 == 0)
```
POST /api/orders/  {"items":[{"product_id":4,"quantity":1}]}   # price 666.00
-> 201 {"id":3,"status":"pending_payment","total_amount":"666.00"}

GET /api/orders/3/          -> status: "payment_failed"
GET /api/catalog/products/4/ -> stock: 10   (back to original -- Payments told Orders to
                                              fail, Orders rolled the reservation back via Catalog)
GET /api/payments/          -> [{"order_id":3,"status":"failed","failure_reason":"card_declined (mock gateway rule)"}]
GET /api/notifications/     -> order.payment_failed message logged for "ansh"
```

## What this proves
- **Real service boundaries**: each service owns its own SQLite DB; nothing
  reaches across into another service's tables.
- **Sync REST where correctness matters**: Orders can't create an order
  without Auth confirming the token and Catalog confirming/reserving stock.
- **Async events where coupling should be loose**: Payments and
  Notifications react to `order.created` independently; Orders doesn't wait
  on either of them.
- **Compensation, not just happy-path code**: both an over-order and a
  declined payment leave the system in a consistent state (no ghost
  reservations, correct final order status).
