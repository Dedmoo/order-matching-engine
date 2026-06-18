# Order Matching Engine

Price-time priority limit order book for a single instrument. Useful for studying exchange matching, market microstructure and trading-system design (crypto or traditional).

## Features

- Limit and market orders
- Price-time priority at each price level
- Partial fills, resting liquidity and cancel
- Deterministic trade prints

## How matching works

```mermaid
flowchart TD
    A[Incoming order] --> B{Market or limit?}
    B -->|Market| C[Take liquidity until filled or book empty]
    B -->|Limit| D{Crosses opposite side?}
    D -->|Yes| E[Match at resting price]
    D -->|No| F[Rest on book]
    E --> G{Remaining qty?}
    G -->|Yes| F
    G -->|No| H[Done]
    C --> H
```

## Quick start

```bash
python -m pip install -e ".[dev]"
pytest -q
```

```python
from decimal import Decimal
from order_matching_engine import Order, OrderBook, OrderType, Side

book = OrderBook("BTC-USDT")
book.submit(Order("s1", Side.SELL, Decimal("1"), Decimal("100")))
trades = book.submit(Order("b1", Side.BUY, Decimal("1"), Decimal("100")))
print(trades[0].price, trades[0].quantity)
```

## Domain model

```mermaid
classDiagram
    direction TB
    class OrderBook {
        +symbol: str
        +submit(order) List~Trade~
        +cancel(orderId) bool
        +best_bid() Decimal
        +best_ask() Decimal
    }
    class Order {
        +order_id: str
        +side: Side
        +quantity: Decimal
        +price: Decimal
        +remaining: Decimal
    }
    class Trade {
        +trade_id: str
        +price: Decimal
        +quantity: Decimal
    }
    class Side {
        <<enumeration>>
        BUY
        SELL
    }
    OrderBook o-- Order
    OrderBook ..> Trade
    Order --> Side
```

## License

MIT
