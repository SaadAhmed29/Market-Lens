import pandas as pd
import numpy as np
import base64
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from utils.config import load_config
from data.data_downloader import DataFetcher
from signals.main import get_signal_df


class BacktestEngine:
    def __init__(self, config_path: str):
        self.config = load_config(config_path)
        self.ohlcv_df = None
        self.signal_df = None

        # Populated by prepare()
        self.mapped_signals = None   # one row per candidate signal, pre-filter
        self.trades = None           # one row per ACCEPTED trade (post max_open_positions filter)

        # Populated by run()
        self.trade_ledger = None
        self.balance_history = None
        self.equity_curve = None
        self.drawdown_series = None
        self.final_balance = None
        self.total_net_profit = None
        self.total_trades = None
        self.win_count = None
        self.loss_count = None

    # Data / signal loading
    def load_data(self):
        df, _ = DataFetcher.get_updated_df(
            exchange=self.config.get('exchange', 'binance'),
            symbol=self.config.get('symbol', 'BTC'),
            start=self.config.get('start_date'),
            end=self.config.get('end_date'),
            time_frame="1m",
            resample_1m=False
        )
        self.ohlcv_df = df

    def load_signals(self):
        try:
            self.signal_df = get_signal_df(
                save_csv=False,
                exchange=self.config.get('exchange', 'binance'),
                symbol=self.config.get('symbol', 'BTC'),
                start=self.config.get('start_date'),
                end=self.config.get('end_date')
            )
        except TypeError:
            self.signal_df = get_signal_df()

    # Preparation pipeline
    def prepare(self):
        self.load_data()
        self.load_signals()

        if self.signal_df is not None and not self.signal_df.empty:
            self._map_signals_to_1m()
            if not self.mapped_signals.empty:
                self._build_trades()

        return self.ohlcv_df, self.signal_df

    def _map_signals_to_1m(self):
        """
        Signals are generated on an hourly timeframe, but the timestamp on
        each signal row is already the intended ACTION time (the signal
        dataframe has already been shifted upstream, e.g. the row labeled
        10:00 represents "act now, using the 9:00 candle's info"). So the
        trade enters at that exact hourly timestamp -- we just need to find
        the corresponding row in the 1-minute data, no additional shift.
        """
        signal_col = 'signal' if 'signal' in self.signal_df.columns else self.signal_df.columns[0]
        sig = self.signal_df[self.signal_df[signal_col] != 0].copy()

        allow_long = self.config.get('allow_long', True)
        allow_short = self.config.get('allow_short', True)
        if not allow_long:
            sig = sig[sig[signal_col] != 1]
        if not allow_short:
            sig = sig[sig[signal_col] != -1]

        if sig.empty:
            self.mapped_signals = pd.DataFrame()
            return

        entry_time = sig.index  # already the correct action timestamp
        ohlcv_index = self.ohlcv_df.index

        entry_positions = ohlcv_index.searchsorted(entry_time, side='left')

        valid = entry_positions < len(ohlcv_index)
        sig = sig.loc[valid]
        entry_positions = entry_positions[valid]

        self.mapped_signals = pd.DataFrame({
            'signal': sig[signal_col].values,
            'signal_time': sig.index,
            'entry_idx': entry_positions
        }).sort_values('entry_idx').reset_index(drop=True)

    def _scan_for_tp_sl(self, direction, tp_price, sl_price, start, end, highs, lows):
        """
        Look for the first TP or SL touch strictly after `start`, up to and
        including `end` (which may be a hard boundary like the next
        opposite signal, or the last row of data).

        Returns a dict {'idx', 'price', 'reason'} or None if neither is hit
        in this window.
        """
        scan_start = start + 1
        if scan_start > end:
            return None

        h = highs[scan_start:end + 1]
        l = lows[scan_start:end + 1]

        if direction == 1:  # Long
            tp_hit = h >= tp_price if not np.isnan(tp_price) else np.zeros_like(h, dtype=bool)
            sl_hit = l <= sl_price if not np.isnan(sl_price) else np.zeros_like(l, dtype=bool)
        else:  # Short
            tp_hit = l <= tp_price if not np.isnan(tp_price) else np.zeros_like(l, dtype=bool)
            sl_hit = h >= sl_price if not np.isnan(sl_price) else np.zeros_like(h, dtype=bool)

        tp_idx = int(np.argmax(tp_hit)) if tp_hit.any() else None
        sl_idx = int(np.argmax(sl_hit)) if sl_hit.any() else None

        candidates = []
        if tp_idx is not None:
            candidates.append((tp_idx, 'TP', tp_price))
        if sl_idx is not None:
            candidates.append((sl_idx, 'SL', sl_price))

        if not candidates:
            return None

        # Earliest wins; if both hit on the same bar, SL wins (conservative)
        candidates.sort(key=lambda c: (c[0], 0 if c[1] == 'SL' else 1))
        best_offset, reason, price = candidates[0]
        return {'idx': scan_start + best_offset, 'price': price, 'reason': reason}

    def _build_trades(self):
        """
        Event-driven trade builder (loops over signal EVENTS, not 1m rows --
        typically a few hundred/thousand events vs. potentially millions of
        1m rows, so this stays cheap).

        Rules:
        - A signal in the SAME direction as the currently open trade is
          ignored; the trade just continues.
        - A signal in the OPPOSITE direction is only treated as an exit
          trigger if `exit_on_opposite_signal` is True in config. When it
          is, the trade closes at whichever comes first: TP, SL, or that
          opposite signal (using its 1m open price). The opposite signal
          then immediately opens a new trade in the new direction.
        - If `exit_on_opposite_signal` is False, opposite signals are
          ignored entirely (same as same-direction signals) -- only TP/SL
          can end a trade.
        - max_open_positions is effectively always 1 here: a new trade can
          only start once the previous one has closed.
        """
        exit_on_opp = self.config.get('exit_on_opposite_signal', False)
        tp_enabled = self.config['take_profit'].get('enabled', True)
        sl_enabled = self.config['stop_loss'].get('enabled', True)
        tp_pct = self.config['take_profit']['value'] / 100
        sl_pct = self.config['stop_loss']['value'] / 100
        allow_long = self.config.get('allow_long', True)
        allow_short = self.config.get('allow_short', True)

        opens = self.ohlcv_df['open'].values
        highs = self.ohlcv_df['high'].values
        lows = self.ohlcv_df['low'].values
        closes = self.ohlcv_df['close'].values
        N = len(self.ohlcv_df)

        def tp_sl_for(direction, entry_price):
            tp = np.nan
            sl = np.nan
            if tp_enabled:
                tp = entry_price * (1 + tp_pct) if direction == 1 else entry_price * (1 - tp_pct)
            if sl_enabled:
                sl = entry_price * (1 - sl_pct) if direction == 1 else entry_price * (1 + sl_pct)
            return tp, sl

        def open_trade(direction, idx):
            entry_price = opens[idx]
            tp, sl = tp_sl_for(direction, entry_price)
            return {
                'signal': direction,
                'entry_idx': idx,
                'entry_price': entry_price,
                'tp_price': tp,
                'sl_price': sl,
            }

        trades = []
        position = None

        for row in self.mapped_signals.itertuples(index=False):
            idx = row.entry_idx
            sig = row.signal

            # -- If a position is open, check whether TP/SL already closed
            #    it before this signal's candle.  This is essential when
            #    exit_on_opposite_signal is False, because in that mode
            #    the loop would otherwise just `continue` past every signal
            #    and only resolve TP/SL after all signals are exhausted
            #    (i.e. only the very last trade would ever be recorded).
            if position is not None:
                hit = self._scan_for_tp_sl(
                    position['signal'], position['tp_price'], position['sl_price'],
                    position['entry_idx'], idx - 1, highs, lows
                )
                if hit is not None:
                    # TP/SL was hit before this signal's candle
                    trades.append({
                        **position,
                        'exit_idx': hit['idx'],
                        'exit_price': hit['price'],
                        'exit_reason': hit['reason'],
                        'forced_exit': False,
                    })
                    position = None
                    # Fall through: this signal may now open a new trade
                    # (handled by the `position is None` block below).

            if position is None:
                if sig == 1 and allow_long:
                    position = open_trade(1, idx)
                elif sig == -1 and allow_short:
                    position = open_trade(-1, idx)
                continue

            if sig == position['signal']:
                continue  # same direction: trade just continues

            # Opposite signal
            if not exit_on_opp:
                continue  # ignored: only TP/SL can close this trade

            hit = self._scan_for_tp_sl(
                position['signal'], position['tp_price'], position['sl_price'],
                position['entry_idx'], idx, highs, lows
            )

            if hit is not None:
                # TP/SL triggered before the opposite signal arrived
                exit_idx, exit_price, reason = hit['idx'], hit['price'], hit['reason']
            else:
                # No TP/SL yet -> the opposite signal itself is the exit
                exit_idx, exit_price, reason = idx, opens[idx], 'SIGNAL'

            trades.append({
                **position,
                'exit_idx': exit_idx,
                'exit_price': exit_price,
                'exit_reason': reason,
                'forced_exit': False,
            })

            position = None
            # The opposite signal immediately opens a new trade in the new direction
            if sig == 1 and allow_long:
                position = open_trade(1, idx)
            elif sig == -1 and allow_short:
                position = open_trade(-1, idx)

        # Resolve whatever trade is still open once signals run out
        if position is not None:
            hit = self._scan_for_tp_sl(
                position['signal'], position['tp_price'], position['sl_price'],
                position['entry_idx'], N - 1, highs, lows
            )
            if hit is not None:
                exit_idx, exit_price, reason, forced = hit['idx'], hit['price'], hit['reason'], False
            else:
                exit_idx, exit_price, reason, forced = N - 1, closes[-1], 'END_OF_DATA', True

            trades.append({
                **position,
                'exit_idx': exit_idx,
                'exit_price': exit_price,
                'exit_reason': reason,
                'forced_exit': forced,
            })

        self.trades = pd.DataFrame(trades)
        if not self.trades.empty:
            self.trades['entry_time'] = self.ohlcv_df.index[self.trades['entry_idx']]
            self.trades['exit_time'] = self.ohlcv_df.index[self.trades['exit_idx']]

    # Execution: position sizing, commission/slippage, PnL, balance
    def execute(self):
        if self.trades is None or self.trades.empty:
            self.trade_ledger = pd.DataFrame()
            self._build_flat_curves()
            return self._collect_results()

        pos_type = self.config['position_size']['type']
        pos_val = self.config['position_size']['value']
        commission_rate = self.config.get('commission', 0.0)
        slippage_rate = self.config.get('slippage', 0.0)
        initial_balance = self.config.get('initial_balance', 10000)

        n = len(self.trades)
        entry_price = self.trades['entry_price'].values
        exit_price = self.trades['exit_price'].values
        signal = self.trades['signal'].values

        quantities = np.zeros(n)
        gross_pnls = np.zeros(n)
        entry_commissions = np.zeros(n)
        exit_commissions = np.zeros(n)
        entry_slippages = np.zeros(n)
        exit_slippages = np.zeros(n)
        net_pnls = np.zeros(n)
        balances_after = np.zeros(n)

        # Balance compounds trade-by-trade; since trades never overlap
        # (enforced above), this sequential dependency is unavoidable, but
        # the loop runs over trades (small N) rather than 1m rows (large N).
        balance = initial_balance
        for i in range(n):
            if pos_type == 'fixed_percentage':
                position_value = balance * (pos_val / 100)
            else:
                raise ValueError(f"Unsupported position_size type: {pos_type}")

            qty = position_value / entry_price[i]
            quantities[i] = qty

            if signal[i] == 1:  # Long
                gross_pnl = (exit_price[i] - entry_price[i]) * qty
            else:  # Short
                gross_pnl = (entry_price[i] - exit_price[i]) * qty
            gross_pnls[i] = gross_pnl

            entry_value = entry_price[i] * qty
            exit_value = exit_price[i] * qty

            entry_comm = entry_value * commission_rate
            exit_comm = exit_value * commission_rate
            entry_slip = entry_value * slippage_rate
            exit_slip = exit_value * slippage_rate

            entry_commissions[i] = entry_comm
            exit_commissions[i] = exit_comm
            entry_slippages[i] = entry_slip
            exit_slippages[i] = exit_slip

            net_pnl = gross_pnl - (entry_comm + exit_comm + entry_slip + exit_slip)
            net_pnls[i] = net_pnl

            balance += net_pnl
            balances_after[i] = balance

        self.trade_ledger = pd.DataFrame({
            'entry_time': self.trades['entry_time'].values,
            'exit_time': self.trades['exit_time'].values,
            'direction': np.where(signal == 1, 'long', 'short'),
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantities,
            'gross_pnl': gross_pnls,
            'commission': entry_commissions + exit_commissions,
            'slippage': entry_slippages + exit_slippages,
            'net_pnl': net_pnls,
            'balance_after_trade': balances_after,
            'exit_reason': self.trades['exit_reason'].values,
            'forced_exit': self.trades['forced_exit'].values,
        })

        self._build_curves(initial_balance)
        return self._collect_results()

    # Equity curve / balance history / drawdown (per 1m row across full timeline)
    def _build_flat_curves(self):
        initial_balance = self.config.get('initial_balance', 10000)
        idx = self.ohlcv_df.index
        self.balance_history = pd.Series(initial_balance, index=idx)
        self.equity_curve = pd.Series(initial_balance, index=idx)
        self.drawdown_series = pd.Series(0.0, index=idx)

    def _build_curves(self, initial_balance):
        idx = self.ohlcv_df.index
        n_rows = len(idx)

        # Balance history: flat at initial_balance, then step-jumps at each
        # trade's exit_idx (vectorized: build a delta array and cumsum it).
        balance_delta = np.zeros(n_rows)
        exit_positions = self.trades['exit_idx'].values
        net_pnls = self.trade_ledger['net_pnl'].values
        np.add.at(balance_delta, exit_positions, net_pnls)
        balance_history = initial_balance + np.cumsum(balance_delta)
        self.balance_history = pd.Series(balance_history, index=idx)

        # Equity curve: balance history plus mark-to-market unrealized PnL
        # while a trade is open (assigned per-trade, over each trade's own
        # window -- a loop over trades, not over every 1m row independently).
        equity = balance_history.copy()
        closes = self.ohlcv_df['close'].values
        # Balance *before* each trade (i.e. balance_history frozen from the
        # previous trade's exit up to this trade's own exit) is needed to mark
        # the open position to market correctly.
        balance_before_trade = np.concatenate(([initial_balance], balance_history[:-1]))
        # (balance_before_trade indexed by 1m row; we only need it at each
        # trade's own entry/exit window, pulled below.)

        for i, row in enumerate(self.trades.itertuples(index=False)):
            start, end = row.entry_idx, row.exit_idx
            qty = self.trade_ledger.loc[i, 'quantity']
            entry_p = row.entry_price
            balance_at_entry = balance_history[start - 1] if start > 0 else initial_balance
            window_closes = closes[start:end + 1]
            if row.signal == 1:
                unrealized = (window_closes - entry_p) * qty
            else:
                unrealized = (entry_p - window_closes) * qty
            equity[start:end + 1] = balance_at_entry + unrealized
            equity[end] = balance_history[end]  # exact realized value at exit bar

        self.equity_curve = pd.Series(equity, index=idx)

        running_max = self.equity_curve.cummax()
        self.drawdown_series = (self.equity_curve - running_max) / running_max

    # Results
    def _collect_results(self):
        if self.trade_ledger is not None and not self.trade_ledger.empty:
            self.final_balance = self.trade_ledger['balance_after_trade'].iloc[-1]
            self.total_net_profit = self.trade_ledger['net_pnl'].sum()
            self.total_trades = len(self.trade_ledger)
            self.win_count = int((self.trade_ledger['net_pnl'] > 0).sum())
            self.loss_count = int((self.trade_ledger['net_pnl'] <= 0).sum())
        else:
            self.final_balance = self.config.get('initial_balance', 10000)
            self.total_net_profit = 0.0
            self.total_trades = 0
            self.win_count = 0
            self.loss_count = 0

        return {
            'trade_ledger': self.trade_ledger,
            'equity_curve': self.equity_curve,
            'balance_history': self.balance_history,
            'drawdown_series': self.drawdown_series,
            'final_balance': self.final_balance,
            'total_net_profit': self.total_net_profit,
            'total_trades': self.total_trades,
            'win_count': self.win_count,
            'loss_count': self.loss_count,
        }

    # HTML report
    def _fig_to_base64(self, fig):
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')

    def _render_curve_chart(self):
        bg = '#0B0E14'
        grid = '#1C2230'
        text = '#8B92A5'
        equity_color = '#00D9A3'
        balance_color = '#5B8DEF'

        fig, ax = plt.subplots(figsize=(11, 3.6), facecolor=bg)
        ax.set_facecolor(bg)

        ax.plot(self.equity_curve.index, self.equity_curve.values,
                color=equity_color, linewidth=1.4, label='Equity (mark-to-market)')
        ax.plot(self.balance_history.index, self.balance_history.values,
                color=balance_color, linewidth=1.1, linestyle='--', label='Balance (realized)', alpha=0.8)

        ax.fill_between(self.equity_curve.index, self.equity_curve.values,
                         self.equity_curve.min(), color=equity_color, alpha=0.06)

        ax.grid(True, color=grid, linewidth=0.6)
        ax.tick_params(colors=text, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(grid)
        ax.set_ylabel('Balance', color=text, fontsize=9)
        legend = ax.legend(loc='upper left', frameon=False, fontsize=8, labelcolor=text)
        fig.tight_layout()
        return self._fig_to_base64(fig)

    def _render_drawdown_chart(self):
        bg = '#0B0E14'
        grid = '#1C2230'
        text = '#8B92A5'
        dd_color = '#FF5C5C'

        fig, ax = plt.subplots(figsize=(11, 2.0), facecolor=bg)
        ax.set_facecolor(bg)

        dd_pct = self.drawdown_series.values * 100
        ax.fill_between(self.drawdown_series.index, dd_pct, 0, color=dd_color, alpha=0.25)
        ax.plot(self.drawdown_series.index, dd_pct, color=dd_color, linewidth=1.0)

        ax.grid(True, color=grid, linewidth=0.6)
        ax.tick_params(colors=text, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(grid)
        ax.set_ylabel('Drawdown %', color=text, fontsize=9)
        fig.tight_layout()
        return self._fig_to_base64(fig)

    def _ledger_rows_html(self):
        if self.trade_ledger is None or self.trade_ledger.empty:
            return '<tr><td colspan="11" class="empty">No trades were executed.</td></tr>'

        rows = []
        for i, r in self.trade_ledger.iterrows():
            pnl_class = 'pos' if r['net_pnl'] > 0 else 'neg'
            dir_class = 'long' if r['direction'] == 'long' else 'short'
            reason = r.get('exit_reason', '')
            rows.append(f"""
            <tr>
              <td>{i + 1}</td>
              <td>{r['entry_time']}</td>
              <td>{r['exit_time']}</td>
              <td><span class="badge {dir_class}">{r['direction'].upper()}</span></td>
              <td class="num">{r['entry_price']:.4f}</td>
              <td class="num">{r['exit_price']:.4f}</td>
              <td class="num">{r['quantity']:.6f}</td>
              <td class="num">{r['gross_pnl']:.2f}</td>
              <td class="num">{r['commission'] + r['slippage']:.2f}</td>
              <td class="num {pnl_class}">{r['net_pnl']:+.2f}</td>
              <td class="num">{r['balance_after_trade']:.2f}</td>
              <td><span class="tag">{reason}</span></td>
            </tr>""")
        return ''.join(rows)

    def generate_html_report(self, output_path='backtest_report.html'):
        """
        Renders a single self-contained HTML file: summary stats, the
        equity/balance/drawdown curves, and the full trade ledger table.
        Charts are embedded as base64 PNGs, so the file works completely
        offline once generated.
        """
        curve_img = self._render_curve_chart()
        dd_img = self._render_drawdown_chart()

        initial_balance = self.config.get('initial_balance', 10000)
        final_balance = self.final_balance if self.final_balance is not None else initial_balance
        total_return_pct = ((final_balance / initial_balance) - 1) * 100
        win_rate = (self.win_count / self.total_trades * 100) if self.total_trades else 0.0
        max_dd_pct = self.drawdown_series.min() * 100 if self.drawdown_series is not None else 0.0

        summary_cards = f"""
        <div class="card"><div class="label">Final Balance</div><div class="value">{final_balance:,.2f}</div></div>
        <div class="card"><div class="label">Total Net Profit</div><div class="value {'pos' if self.total_net_profit >= 0 else 'neg'}">{self.total_net_profit:+,.2f}</div></div>
        <div class="card"><div class="label">Total Return</div><div class="value {'pos' if total_return_pct >= 0 else 'neg'}">{total_return_pct:+.2f}%</div></div>
        <div class="card"><div class="label">Total Trades</div><div class="value">{self.total_trades}</div></div>
        <div class="card"><div class="label">Win Rate</div><div class="value">{win_rate:.1f}%</div></div>
        <div class="card"><div class="label">Wins / Losses</div><div class="value">{self.win_count} / {self.loss_count}</div></div>
        <div class="card"><div class="label">Max Drawdown</div><div class="value neg">{max_dd_pct:.2f}%</div></div>
        """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Backtest Report</title>
<style>
  :root {{
    --bg: #0B0E14;
    --panel: #10141D;
    --border: #1C2230;
    --text: #E8EAED;
    --muted: #8B92A5;
    --pos: #00D9A3;
    --neg: #FF5C5C;
    --accent: #5B8DEF;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    padding: 32px;
  }}
  h1 {{
    font-family: -apple-system, ui-sans-serif, system-ui, sans-serif;
    font-weight: 600;
    font-size: 20px;
    letter-spacing: 0.02em;
    color: var(--text);
    margin: 0 0 4px 0;
  }}
  .subtitle {{
    color: var(--muted);
    font-size: 12px;
    margin-bottom: 24px;
  }}
  .cards {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
    margin-bottom: 28px;
  }}
  .card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 14px 16px;
  }}
  .card .label {{
    color: var(--muted);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
  }}
  .card .value {{
    font-size: 20px;
    font-weight: 600;
  }}
  .pos {{ color: var(--pos); }}
  .neg {{ color: var(--neg); }}
  .panel {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 16px;
    margin-bottom: 20px;
  }}
  .panel h2 {{
    font-family: -apple-system, ui-sans-serif, system-ui, sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 12px 0;
  }}
  .panel img {{ width: 100%; display: block; }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }}
  th {{
    text-align: left;
    color: var(--muted);
    font-weight: 500;
    text-transform: uppercase;
    font-size: 10px;
    letter-spacing: 0.05em;
    padding: 8px 10px;
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    background: var(--panel);
  }}
  td {{
    padding: 7px 10px;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
  }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  tr:hover td {{ background: #151A24; }}
  .table-wrap {{ max-height: 520px; overflow-y: auto; }}
  .badge {{
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.03em;
  }}
  .badge.long {{ background: rgba(0,217,163,0.15); color: var(--pos); }}
  .badge.short {{ background: rgba(255,92,92,0.15); color: var(--neg); }}
  .tag {{
    color: var(--muted);
    font-size: 10px;
    border: 1px solid var(--border);
    padding: 2px 6px;
    border-radius: 3px;
  }}
  .empty {{ text-align: center; color: var(--muted); padding: 24px; }}
</style>
</head>
<body>
  <h1>Backtest Report</h1>
  <div class="subtitle">Generated from {self.total_trades} executed trade(s) &middot; initial balance {initial_balance:,.2f}</div>

  <div class="cards">
    {summary_cards}
  </div>

  <div class="panel">
    <h2>Equity &amp; Balance</h2>
    <img src="data:image/png;base64,{curve_img}" alt="Equity and balance curve">
  </div>

  <div class="panel">
    <h2>Drawdown</h2>
    <img src="data:image/png;base64,{dd_img}" alt="Drawdown curve">
  </div>

  <div class="panel">
    <h2>Trade Ledger</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>#</th><th>Entry Time</th><th>Exit Time</th><th>Dir</th>
            <th>Entry</th><th>Exit</th><th>Qty</th><th>Gross PnL</th>
            <th>Costs</th><th>Net PnL</th><th>Balance</th><th>Exit Reason</th>
          </tr>
        </thead>
        <tbody>
          {self._ledger_rows_html()}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>"""

        with open(output_path, 'w') as f:
            f.write(html)

        return output_path

    # Entry point
    def run(self, html_report_path='backtest_report.html'):
        self.prepare()
        results = self.execute()
        report_path = self.generate_html_report(html_report_path)
        results['html_report_path'] = report_path
        return results