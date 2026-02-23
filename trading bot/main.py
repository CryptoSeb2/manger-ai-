"""
Quant futures bot – paper trading with volume + math + news.
Positions are in contracts (futures). P&L = (exit - entry) × multiplier.

Run once:
  python main.py

Run continuously (check every N minutes):
  python main.py --loop
"""

import argparse
import time
from config import SYMBOLS, INITIAL_BALANCE, CHECK_INTERVAL_MINUTES
from data import get_latest_price
from strategy import get_signals
from paper_trader import PaperTrader


def run_once(trader: PaperTrader) -> None:
    """Execute trades from math-based signals; exit by 1:4 SL/TP or SELL signal."""
    for symbol in SYMBOLS:
        price = get_latest_price(symbol)
        if price is None:
            print(f"  [{symbol}] No price data, skipping.")
            continue

        position = trader.position(symbol)

        # Open: only when math-based strategy says BUY
        if position == 0:
            signal = get_signals(symbol)
            if signal == "BUY":
                contracts = trader.contracts_to_buy(symbol, price)
                if contracts >= 1 and trader.buy(symbol, contracts, price):
                    entry = trader.entry_prices.get(symbol, price)
                    sl = trader.sl_prices.get(symbol)
                    tp = trader.tp_prices.get(symbol)
                    print(f"  [PAPER] BUY  {contracts} contract(s) {symbol} @ {price:.2f}  (SL: {sl:.2f}, TP: {tp:.2f})")
            continue

        # Close: 1) SL/TP (math-based 1:4) first, then 2) strategy SELL
        if trader.should_stop_loss(symbol, price):
            if trader.sell(symbol, position, price):
                print(f"  [PAPER] SELL {position} contract(s) {symbol} @ {price:.2f}  [STOP LOSS]")
        elif trader.should_take_profit(symbol, price):
            if trader.sell(symbol, position, price):
                print(f"  [PAPER] SELL {position} contract(s) {symbol} @ {price:.2f}  [TAKE PROFIT 1:4]")
        else:
            signal = get_signals(symbol)
            if signal == "SELL" and trader.sell(symbol, position, price):
                print(f"  [PAPER] SELL {position} contract(s) {symbol} @ {price:.2f}  [SIGNAL]")


def main():
    parser = argparse.ArgumentParser(description="Quant futures paper trading (volume + math + news)")
    parser.add_argument("--loop", action="store_true", help="Run continuously every N minutes")
    args = parser.parse_args()

    trader = PaperTrader()
    print(f"Futures paper trading started. Starting equity: ${trader.balance:,.2f}")
    print(f"Symbols (contracts): {', '.join(SYMBOLS)}")
    print("-" * 50)

    if args.loop:
        interval_sec = CHECK_INTERVAL_MINUTES * 60
        while True:
            print(f"\n[{time.strftime('%Y-%m-%d %H:%M')}] Checking...")
            run_once(trader)
            total = trader.total_value()
            print(f"  Equity: ${total:,.2f}  |  Cash (realized): ${trader.cash():,.2f}")
            time.sleep(interval_sec)
    else:
        run_once(trader)
        print(f"\nEquity: ${trader.total_value():,.2f}")
        print("Done. Use --loop to run continuously.")


if __name__ == "__main__":
    main()
