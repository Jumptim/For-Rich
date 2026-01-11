import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def _extract_xy(series: dict) -> tuple[list[int], list[float]]:
    # LEAN backtest json stores series values as: [[unixSeconds, y], ...]
    values = series.get("values") or []
    xs_ms: list[int] = []
    ys: list[float] = []
    for item in values:
        if isinstance(item, list) and len(item) == 2:
            x_s, y = item
        elif isinstance(item, dict) and "x" in item and "y" in item:
            x_s, y = item["x"], item["y"]
        else:
            continue
        try:
            xs_ms.append(int(x_s) * 1000)
            ys.append(float(y))
        except Exception:
            continue
    return xs_ms, ys


def _ms_to_utc_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _build_trades_table(
    buy_x: list[int],
    buy_y: list[float],
    sell_x: list[int],
    sell_y: list[float],
) -> tuple[str, list[tuple[str, str, float]]]:
    trades: list[tuple[str, str, float]] = []
    for x, y in zip(buy_x, buy_y):
        trades.append((_ms_to_utc_iso(x), "BUY", y))
    for x, y in zip(sell_x, sell_y):
        trades.append((_ms_to_utc_iso(x), "SELL", y))
    trades.sort(key=lambda t: t[0])

    rows = []
    for time_utc, side, price in trades:
        rows.append(
            "<tr>"
            f"<td style=\"padding: 6px; border-bottom: 1px solid #eee;\">{time_utc}</td>"
            f"<td style=\"padding: 6px; border-bottom: 1px solid #eee;\">{side}</td>"
            f"<td style=\"padding: 6px; border-bottom: 1px solid #eee; text-align: right;\">{price:.4f}</td>"
            "</tr>"
        )
    return "\n".join(rows) if rows else "<tr><td colspan=\"3\" style=\"padding: 6px;\">No trades</td></tr>", trades


def _build_html(
    *,
    title: str,
    price_x: list[int],
    price_y: list[float],
    buy_x: list[int],
    buy_y: list[float],
    sell_x: list[int],
    sell_y: list[float],
    fast_x: list[int],
    fast_y: list[float],
    slow_x: list[int],
    slow_y: list[float],
    trades_rows_html: str,
) -> str:
    # Keep it self-contained: use Plotly CDN, but do NOT block initial render.
    # Some environments (corporate networks / VS Code webviews) may block the CDN.
    return f"""<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{title}</title>
</head>
<body>
  <div style=\"max-width: 1200px; margin: 0 auto; padding: 12px;\">
    <h2 style=\"margin: 0 0 8px; font-family: sans-serif;\">{title}</h2>
    <div id=\"chartsStatus\" style=\"font-family: sans-serif; color: #444; margin-bottom: 8px;\">
      Loading charts… (if this stays blank, Plotly may be blocked; the Trades table below should still render)
    </div>
    <noscript>
      <div style=\"font-family: sans-serif; color: #b00; margin-bottom: 8px;\">
        JavaScript is disabled. Charts require JavaScript; Trades table is still available.
      </div>
    </noscript>
    <div id=\"price\" style=\"height: 520px;\"></div>
    <div id=\"sma\" style=\"height: 360px; margin-top: 14px;\"></div>
    <h3 style=\"margin: 16px 0 8px; font-family: sans-serif;\">Trades</h3>
    <table style=\"border-collapse: collapse; width: 100%; font-family: sans-serif;\">
      <thead>
        <tr>
          <th style=\"text-align:left; border-bottom: 1px solid #ccc; padding: 6px;\">Time (UTC)</th>
          <th style=\"text-align:left; border-bottom: 1px solid #ccc; padding: 6px;\">Side</th>
          <th style=\"text-align:right; border-bottom: 1px solid #ccc; padding: 6px;\">Fill Price</th>
        </tr>
      </thead>
      <tbody>
        {trades_rows_html}
      </tbody>
    </table>
    <p style=\"font-family: sans-serif; color: #444;\">
      Tip: hover points to see exact timestamps and prices.
    </p>
  </div>

  <!-- Load Plotly after the page content so we don't white-screen if the CDN is blocked -->
  <script src=\"https://cdn.plot.ly/plotly-2.30.0.min.js\" async
          onerror=\"document.getElementById('chartsStatus').textContent='Plotly failed to load (CDN blocked/offline). Open this file in a normal browser with internet access, or rely on the Trades table above.';\"></script>

  <script>
    const priceX = {price_x};
    const priceY = {price_y};
    const buyX   = {buy_x};
    const buyY   = {buy_y};
    const sellX  = {sell_x};
    const sellY  = {sell_y};

    const fastX  = {fast_x};
    const fastY  = {fast_y};
    const slowX  = {slow_x};
    const slowY  = {slow_y};

    function setStatus(msg) {{
      const el = document.getElementById('chartsStatus');
      if (el) el.textContent = msg;
    }}

    function renderCharts() {{
      const priceTraces = [
        {{
          x: priceX,
          y: priceY,
          type: 'scatter',
          mode: 'lines',
          name: 'Price',
          line: {{ width: 2 }}
        }},
        {{
          x: buyX,
          y: buyY,
          type: 'scatter',
          mode: 'markers',
          name: 'Buy',
          marker: {{ size: 10, symbol: 'triangle-up', color: 'green' }}
        }},
        {{
          x: sellX,
          y: sellY,
          type: 'scatter',
          mode: 'markers',
          name: 'Sell',
          marker: {{ size: 10, symbol: 'triangle-down', color: 'red' }}
        }}
      ];

      const commonLayout = {{
        margin: {{ l: 50, r: 20, t: 30, b: 40 }},
        xaxis: {{ type: 'date' }},
        legend: {{ orientation: 'h' }}
      }};

      Plotly.newPlot('price', priceTraces, Object.assign({{}}, commonLayout, {{
        title: 'Price with Buy/Sell markers',
        yaxis: {{ title: 'Price' }}
      }}), {{ responsive: true }});

      const smaTraces = [
        {{
          x: fastX,
          y: fastY,
          type: 'scatter',
          mode: 'lines',
          name: 'FastSMA',
          line: {{ width: 2 }}
        }},
        {{
          x: slowX,
          y: slowY,
          type: 'scatter',
          mode: 'lines',
          name: 'SlowSMA',
          line: {{ width: 2 }}
        }}
      ];

      Plotly.newPlot('sma', smaTraces, Object.assign({{}}, commonLayout, {{
        title: 'SMA',
        yaxis: {{ title: 'Value' }}
      }}), {{ responsive: true }});

      setStatus('Charts loaded.');
    }}

    (function waitForPlotly(maxWaitMs) {{
      const started = Date.now();
      (function tick() {{
        if (window.Plotly && typeof window.Plotly.newPlot === 'function') {{
          try {{
            renderCharts();
          }} catch (e) {{
            setStatus('Chart rendering failed: ' + (e && e.message ? e.message : String(e)));
          }}
          return;
        }}

        if (Date.now() - started > maxWaitMs) {{
          setStatus('Plotly did not load (offline or blocked). Trades table is still shown.');
          return;
        }}
        setTimeout(tick, 100);
      }})();
    }})(5000);
  </script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Visualize LEAN backtest chart series (Price/FastSMA/SlowSMA + Buy/Sell markers) "
            "from the generated backtest .json file."
        )
    )
    parser.add_argument(
        "input",
        help="Path to LEAN backtest result json (e.g. Launcher/bin/Debug/<Algo>.json)",
    )
    parser.add_argument(
        "--chart",
        default="SPY",
        help="Chart name to read from the json (default: SPY)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output html path (default: <input>-viz.html)",
    )

    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input json not found: {input_path}")

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else input_path.with_suffix("").with_name(input_path.stem + "-viz.html")
    )

    with input_path.open("r", encoding="utf-8") as f:
        result = json.load(f)

    charts = result.get("charts") or {}
    chart = charts.get(args.chart)
    if chart is None:
        available = ", ".join(sorted(charts.keys()))
        raise SystemExit(f"Chart '{args.chart}' not found. Available: {available}")

    series = chart.get("series") or {}

    price_x, price_y = _extract_xy(series.get("Price") or {})
    fast_x, fast_y = _extract_xy(series.get("FastSMA") or {})
    slow_x, slow_y = _extract_xy(series.get("SlowSMA") or {})
    buy_x, buy_y = _extract_xy(series.get("Buy") or {})
    sell_x, sell_y = _extract_xy(series.get("Sell") or {})

    trades_rows_html, trades = _build_trades_table(buy_x, buy_y, sell_x, sell_y)

    title = f"LEAN Backtest: {args.chart} (Price + Trades + SMA)"
    html = _build_html(
        title=title,
        price_x=price_x,
        price_y=price_y,
        buy_x=buy_x,
        buy_y=buy_y,
        sell_x=sell_x,
        sell_y=sell_y,
        fast_x=fast_x,
        fast_y=fast_y,
        slow_x=slow_x,
        slow_y=slow_y,
        trades_rows_html=trades_rows_html,
    )

    output_path.write_text(html, encoding="utf-8")

    if trades:
        print("Trades (UTC):")
        for time_utc, side, price in trades:
            print(f"- {time_utc} {side} @ {price:.4f}")
    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
