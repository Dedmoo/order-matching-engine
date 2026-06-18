from order_matching_engine import Order, OrderBook, OrderType, Side
from decimal import Decimal


def test_limit_cross_creates_trade():
    book = OrderBook("BTC-USDT")
    book.submit(Order("s1", Side.SELL, Decimal("1"), Decimal("100"), OrderType.LIMIT))
    trades = book.submit(Order("b1", Side.BUY, Decimal("1"), Decimal("100"), OrderType.LIMIT))
    assert len(trades) == 1
    assert trades[0].price == Decimal("100")
    assert trades[0].quantity == Decimal("1")
    assert book.best_bid() is None
    assert book.best_ask() is None


def test_price_time_priority():
    book = OrderBook("ETH-USDT")
    book.submit(Order("s1", Side.SELL, Decimal("1"), Decimal("50"), OrderType.LIMIT))
    book.submit(Order("s2", Side.SELL, Decimal("1"), Decimal("50"), OrderType.LIMIT))
    trades = book.submit(Order("b1", Side.BUY, Decimal("1"), Decimal("50"), OrderType.LIMIT))
    assert trades[0].sell_order_id == "s1"


def test_partial_fill_and_rest():
    book = OrderBook("BTC-USDT")
    book.submit(Order("s1", Side.SELL, Decimal("2"), Decimal("10"), OrderType.LIMIT))
    trades = book.submit(Order("b1", Side.BUY, Decimal("1"), Decimal("10"), OrderType.LIMIT))
    assert trades[0].quantity == Decimal("1")
    assert book.best_ask() == Decimal("10")


def test_cancel():
    book = OrderBook("BTC-USDT")
    book.submit(Order("s1", Side.SELL, Decimal("1"), Decimal("20"), OrderType.LIMIT))
    assert book.cancel("s1") is True
    assert book.best_ask() is None


def test_market_buy_sweeps_asks():
    book = OrderBook("BTC-USDT")
    book.submit(Order("s1", Side.SELL, Decimal("1"), Decimal("10"), OrderType.LIMIT))
    book.submit(Order("s2", Side.SELL, Decimal("1"), Decimal("11"), OrderType.LIMIT))
    trades = book.submit(Order("b1", Side.BUY, Decimal("2"), order_type=OrderType.MARKET))
    assert len(trades) == 2
    assert trades[0].price == Decimal("10")
    assert trades[1].price == Decimal("11")
