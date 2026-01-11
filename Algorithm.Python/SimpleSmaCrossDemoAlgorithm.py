# QUANTCONNECT.COM - Democratizing Finance, Empowering Individuals.
# Lean Algorithmic Trading Engine v2.0. Copyright 2014 QuantConnect Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from AlgorithmImports import *


### <summary>
### Simple demo: SMA crossover on a single equity (SPY) using daily data.
### - fast SMA crosses above slow SMA -> invest 100%
### - fast SMA crosses below slow SMA -> liquidate
### </summary>
class SimpleSmaCrossDemoAlgorithm(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2018, 1, 1)
        self.set_end_date(2020, 1, 1)
        self.set_cash(100000)

        self._ticker = "SPY"
        self._symbol = self.add_equity(self._ticker, Resolution.DAILY).symbol

        self._fast_period = 20
        self._slow_period = 50

        self._fast = self.sma(self._symbol, self._fast_period, Resolution.DAILY)
        self._slow = self.sma(self._symbol, self._slow_period, Resolution.DAILY)

        price_chart = Chart(self._ticker)
        price_chart.add_series(Series("Price", SeriesType.LINE, 0))
        price_chart.add_series(Series("FastSMA", SeriesType.LINE, 0))
        price_chart.add_series(Series("SlowSMA", SeriesType.LINE, 0))
        price_chart.add_series(Series("Buy", SeriesType.SCATTER, 0))
        price_chart.add_series(Series("Sell", SeriesType.SCATTER, 0))
        self.add_chart(price_chart)

        # Ensure indicators are ready before trading
        self.set_warm_up(self._slow_period, Resolution.DAILY)

        self._was_fast_above = None

    def on_data(self, data: Slice):
        if self.is_warming_up:
            return

        if not (self._fast.is_ready and self._slow.is_ready):
            return

        if not data.contains_key(self._symbol) or data[self._symbol] is None:
            return

        bar = data[self._symbol]
        self.plot(self._ticker, "Price", bar.close)
        self.plot(self._ticker, "FastSMA", self._fast.current.value)
        self.plot(self._ticker, "SlowSMA", self._slow.current.value)

        is_fast_above = self._fast.current.value > self._slow.current.value

        # Initialize state without trading on the first ready sample
        if self._was_fast_above is None:
            self._was_fast_above = is_fast_above
            return

        # Cross up -> enter
        if is_fast_above and not self._was_fast_above:
            self.set_holdings(self._symbol, 1.0)

        # Cross down -> exit
        elif (not is_fast_above) and self._was_fast_above:
            self.liquidate(self._symbol)

        self._was_fast_above = is_fast_above

    def on_order_event(self, order_event: OrderEvent):
        if order_event.status != OrderStatus.FILLED:
            return

        # Use fill price so markers align with actual fills (e.g. MarketOnOpen for daily data)
        if order_event.fill_quantity > 0:
            self.plot(self._ticker, "Buy", order_event.fill_price)
        elif order_event.fill_quantity < 0:
            self.plot(self._ticker, "Sell", order_event.fill_price)
