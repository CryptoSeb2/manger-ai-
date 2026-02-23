"""Paper trading for futures: contracts, entry prices, P&L, 1:4 risk–reward."""

from dataclasses import dataclass, field
from config import (
    INITIAL_BALANCE,
    POSITION_SIZE_PCT,
    MAX_CONTRACTS_PER_TRADE,
    FIXED_CONTRACTS,
    USE_ATR_POSITION_SIZING,
    ATR_PERIOD,
    ATR_SIZING_CAP,
    USE_SL_TP,
    SL_TP_TICKS,
    TICK_SIZES,
    RISK_REWARD_RATIO,
    STOP_LOSS_ATR_MULT,
    get_multiplier,
)
from data import get_latest_price, get_atr_ratio, get_atr


@dataclass
class PaperTrader:
    """Futures paper trading: positions in contracts, P&L = (exit - entry) × multiplier. 1:4 R:R via SL/TP."""

    balance: float = INITIAL_BALANCE  # Cash + realized P&L
    positions: dict[str, int] = field(default_factory=dict)   # symbol -> contracts (int)
    entry_prices: dict[str, float] = field(default_factory=dict)  # symbol -> volume-weighted avg entry
    sl_prices: dict[str, float] = field(default_factory=dict)   # symbol -> stop loss price (long: below entry)
    tp_prices: dict[str, float] = field(default_factory=dict)   # symbol -> take profit price (long: above entry)

    def cash(self) -> float:
        return self.balance

    def position(self, symbol: str) -> int:
        """Number of contracts (long)."""
        return self.positions.get(symbol, 0)

    def _equity_before_open(self, symbol: str) -> float:
        """Total equity for sizing (balance + unrealized P&L on other symbols)."""
        eq = self.balance
        for sym, contracts in self.positions.items():
            if contracts <= 0 or sym == symbol:
                continue
            entry = self.entry_prices.get(sym)
            if entry is None:
                continue
            p = get_latest_price(sym)
            if p is not None:
                mult = get_multiplier(sym)
                eq += contracts * (p - entry) * mult
        return eq

    def buy(self, symbol: str, contracts: int, price: float) -> bool:
        if contracts <= 0:
            return False
        prev = self.positions.get(symbol, 0)
        prev_entry = self.entry_prices.get(symbol)
        if prev == 0:
            self.entry_prices[symbol] = price
        else:
            total_cost = prev * prev_entry + contracts * price
            self.entry_prices[symbol] = total_cost / (prev + contracts)
        self.positions[symbol] = prev + contracts
        entry = self.entry_prices[symbol]
        if USE_SL_TP:
            if symbol in SL_TP_TICKS and symbol in TICK_SIZES:
                risk_ticks, reward_ticks = SL_TP_TICKS[symbol]
                tick = TICK_SIZES[symbol]
                risk_dist = risk_ticks * tick
                reward_dist = reward_ticks * tick
                self.sl_prices[symbol] = entry - risk_dist
                self.tp_prices[symbol] = entry + reward_dist
            else:
                atr = get_atr(symbol, period=ATR_PERIOD)
                if atr is not None and atr > 0:
                    risk_dist = STOP_LOSS_ATR_MULT * atr
                    reward_dist = RISK_REWARD_RATIO * risk_dist
                    self.sl_prices[symbol] = entry - risk_dist
                    self.tp_prices[symbol] = entry + reward_dist
                else:
                    self.sl_prices[symbol] = entry - 0.01
                    self.tp_prices[symbol] = entry + 0.01 * RISK_REWARD_RATIO
        return True

    def sell(self, symbol: str, contracts: int, price: float) -> bool:
        held = self.positions.get(symbol, 0)
        to_sell = min(contracts, held)
        if to_sell <= 0:
            return False
        entry = self.entry_prices.get(symbol)
        if entry is None:
            entry = price
        mult = get_multiplier(symbol)
        realized_pnl = to_sell * (price - entry) * mult
        self.balance += realized_pnl
        self.positions[symbol] = held - to_sell
        if self.positions[symbol] <= 0:
            del self.positions[symbol]
            if symbol in self.entry_prices:
                del self.entry_prices[symbol]
            if symbol in self.sl_prices:
                del self.sl_prices[symbol]
            if symbol in self.tp_prices:
                del self.tp_prices[symbol]
        return True

    def should_stop_loss(self, symbol: str, price: float) -> bool:
        """True if long position should be closed by stop loss (price <= SL)."""
        if not USE_SL_TP or symbol not in self.sl_prices:
            return False
        return price <= self.sl_prices[symbol]

    def should_take_profit(self, symbol: str, price: float) -> bool:
        """True if long position should be closed by take profit (price >= TP)."""
        if not USE_SL_TP or symbol not in self.tp_prices:
            return False
        return price >= self.tp_prices[symbol]

    def total_value(self) -> float:
        """Equity = balance + unrealized P&L on all open positions."""
        total = self.balance
        for sym, contracts in self.positions.items():
            if contracts <= 0:
                continue
            entry = self.entry_prices.get(sym)
            if entry is None:
                continue
            p = get_latest_price(sym)
            if p is not None:
                mult = get_multiplier(sym)
                total += contracts * (p - entry) * mult
        return total

    def contracts_to_buy(self, symbol: str, price: float) -> int:
        """
        Number of contracts to open. If symbol is in FIXED_CONTRACTS, use that; else
        use POSITION_SIZE_PCT of equity (notional) with ATR sizing.
        """
        if symbol in FIXED_CONTRACTS:
            return max(0, FIXED_CONTRACTS[symbol])
        if price <= 0:
            return 0
        mult = get_multiplier(symbol)
        notional_per_contract = price * mult
        if notional_per_contract <= 0:
            return 0
        equity = self._equity_before_open(symbol)
        size_pct = POSITION_SIZE_PCT
        if USE_ATR_POSITION_SIZING:
            ratio = get_atr_ratio(symbol, period=ATR_PERIOD)
            if ratio is not None:
                size_pct *= min(ratio, ATR_SIZING_CAP)
        risk_notional = equity * size_pct
        contracts = int(risk_notional / notional_per_contract)
        contracts = min(contracts, MAX_CONTRACTS_PER_TRADE)
        return max(0, contracts)
