from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Deque, Dict, List, Optional
from collections import deque


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


@dataclass
class Order:
    order_id: str
    side: Side
    quantity: Decimal
    price: Optional[Decimal] = None
    order_type: OrderType = OrderType.LIMIT
    remaining: Decimal = field(init=False)

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.order_type == OrderType.LIMIT and (self.price is None or self.price <= 0):
            raise ValueError("limit orders require a positive price")
        if self.order_type == OrderType.MARKET:
            self.price = None
        self.remaining = self.quantity


@dataclass(frozen=True)
class Trade:
    trade_id: str
    price: Decimal
    quantity: Decimal
    buy_order_id: str
    sell_order_id: str


class OrderBook:
    """Single-instrument limit order book with price-time priority."""

    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self._bids: Dict[Decimal, Deque[Order]] = {}
        self._asks: Dict[Decimal, Deque[Order]] = {}
        self._orders: Dict[str, Order] = {}
        self._trade_seq = 0

    def best_bid(self) -> Optional[Decimal]:
        return max(self._bids) if self._bids else None

    def best_ask(self) -> Optional[Decimal]:
        return min(self._asks) if self._asks else None

    def submit(self, order: Order) -> List[Trade]:
        if order.order_id in self._orders:
            raise ValueError(f"duplicate order_id: {order.order_id}")
        trades: List[Trade] = []
        if order.order_type == OrderType.MARKET:
            trades.extend(self._match_market(order))
        else:
            trades.extend(self._match_limit(order))
            if order.remaining > 0:
                self._rest(order)
        return trades

    def cancel(self, order_id: str) -> bool:
        order = self._orders.get(order_id)
        if order is None or order.remaining <= 0:
            return False
        book = self._bids if order.side == Side.BUY else self._asks
        assert order.price is not None
        level = book.get(order.price)
        if level is None:
            return False
        for i, resting in enumerate(level):
            if resting.order_id == order_id:
                del level[i]
                break
        if level is not None and not level:
            del book[order.price]
        order.remaining = Decimal("0")
        del self._orders[order_id]
        return True

    def _rest(self, order: Order) -> None:
        assert order.price is not None
        book = self._bids if order.side == Side.BUY else self._asks
        book.setdefault(order.price, deque()).append(order)
        self._orders[order.order_id] = order

    def _match_limit(self, order: Order) -> List[Trade]:
        trades: List[Trade] = []
        if order.side == Side.BUY:
            while order.remaining > 0 and self._asks and order.price is not None and min(self._asks) <= order.price:
                trades.append(self._take(order, self._asks, min(self._asks)))
        else:
            while order.remaining > 0 and self._bids and order.price is not None and max(self._bids) >= order.price:
                trades.append(self._take(order, self._bids, max(self._bids)))
        return trades

    def _match_market(self, order: Order) -> List[Trade]:
        trades: List[Trade] = []
        book = self._asks if order.side == Side.BUY else self._bids
        while order.remaining > 0 and book:
            price = min(book) if order.side == Side.BUY else max(book)
            trades.append(self._take(order, book, price))
        return trades

    def _take(self, aggressor: Order, book: Dict[Decimal, Deque[Order]], price: Decimal) -> Trade:
        level = book[price]
        resting = level[0]
        qty = min(aggressor.remaining, resting.remaining)
        aggressor.remaining -= qty
        resting.remaining -= qty
        if resting.remaining == 0:
            level.popleft()
            del self._orders[resting.order_id]
            if not level:
                del book[price]
        self._trade_seq += 1
        buy_id = aggressor.order_id if aggressor.side == Side.BUY else resting.order_id
        sell_id = resting.order_id if aggressor.side == Side.BUY else aggressor.order_id
        return Trade(
            trade_id=f"T{self._trade_seq}",
            price=price,
            quantity=qty,
            buy_order_id=buy_id,
            sell_order_id=sell_id,
        )
