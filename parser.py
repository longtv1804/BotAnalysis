import pandas as pd
from bs4 import BeautifulSoup


# =====================================================
# Common
# =====================================================

TRADE_COLUMNS = [
    "type",
    "ticket",
    "symbol",
    "open_time",
    "size",
    "open_price",
    "sl",
    "tp",
    "close_time",
    "close_price",
    "commission",
    "taxes",
    "swap",
    "profit",
    "time",
    "amount"
]


def _read_html(html_file):

    with open(html_file, "rb") as f:
        raw = f.read()

    # UTF16 (đa số MT5)
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16", errors="ignore")

    # UTF8
    return raw.decode("utf-8", errors="ignore")


def _to_float(value):

    if value is None:
        return 0.0

    value = str(value).strip()

    if value == "":
        return 0.0

    value = value.replace(" ", "")
    value = value.replace(",", "")

    return float(value)


# =====================================================
# Main parser
# =====================================================

def parse_mt_report(html_file):

    print(f"Loading report: {html_file}")

    html = _read_html(html_file)

    soup = BeautifulSoup(html, "html.parser")

    rows = soup.find_all("tr")

    print(f"Found {len(rows)} rows")

    trades = []

    # -------------------------------------------------
    # MT4
    # -------------------------------------------------

    mt4_trades = _parse_mt4(rows)

    print(f"MT4 trades found: {len(mt4_trades)}")

    trades.extend(mt4_trades)

    # -------------------------------------------------
    # MT5 fallback
    # -------------------------------------------------

    if len(mt4_trades) == 0:

        print("Trying MT5 parser...")

        positions = _parse_mt5_positions(rows)

        print(
            f"MT5 positions found: {len(positions)}"
        )

        balances = _parse_mt5_deals(rows)

        print(
            f"MT5 balance records found: {len(balances)}"
        )

        trades.extend(positions)
        trades.extend(balances)

    df = pd.DataFrame(
        trades,
        columns=TRADE_COLUMNS
    )

    print(f"Final rows: {len(df)}")

    return df


# =====================================================
# MT4
# =====================================================

def _parse_mt4(rows):

    trades = []

    for row in rows:

        cols = row.find_all("td")

        if len(cols) < 5:
            continue

        text = row.get_text(
            " ",
            strip=True
        ).lower()

        # Deposit

        if "balance" in text and "deposit" in text:

            try:

                trades.append({
                    "type": "deposit",
                    "time": pd.to_datetime(
                        cols[1].get_text(strip=True)
                    ),
                    "amount": _to_float(
                        cols[-1].get_text(strip=True)
                    )
                })

            except Exception as e:

                print(
                    "MT4 deposit parse error:",
                    e
                )

            continue

        # Withdrawal

        if "balance" in text and "withdrawal" in text:

            try:

                trades.append({
                    "type": "withdrawal",
                    "time": pd.to_datetime(
                        cols[1].get_text(strip=True)
                    ),
                    "amount": _to_float(
                        cols[-1].get_text(strip=True)
                    )
                })

            except Exception as e:

                print(
                    "MT4 withdrawal parse error:",
                    e
                )

            continue

        try:

            trade_type = (
                cols[2]
                .get_text(strip=True)
                .lower()
            )

            if trade_type not in [
                "buy",
                "sell"
            ]:
                continue

            trades.append({

                "type": trade_type,

                "ticket":
                    cols[0].get_text(strip=True),

                "open_time":
                    pd.to_datetime(
                        cols[1].get_text(strip=True)
                    ),

                "size":
                    _to_float(
                        cols[3].get_text(strip=True)
                    ),

                "symbol":
                    cols[4].get_text(strip=True),

                "open_price":
                    _to_float(
                        cols[5].get_text(strip=True)
                    ),

                "sl":
                    _to_float(
                        cols[6].get_text(strip=True)
                    ),

                "tp":
                    _to_float(
                        cols[7].get_text(strip=True)
                    ),

                "close_time":
                    pd.to_datetime(
                        cols[8].get_text(strip=True)
                    ),

                "close_price":
                    _to_float(
                        cols[9].get_text(strip=True)
                    ),

                "commission":
                    _to_float(
                        cols[10].get_text(strip=True)
                    ),

                "taxes":
                    _to_float(
                        cols[11].get_text(strip=True)
                    ),

                "swap":
                    _to_float(
                        cols[12].get_text(strip=True)
                    ),

                "profit":
                    _to_float(
                        cols[13].get_text(strip=True)
                    )
            })

        except Exception:
            pass

    return trades


# =====================================================
# MT5 Positions
# =====================================================

def _parse_mt5_positions(rows):

    trades = []

    in_positions = False

    for row in rows:

        row_text = row.get_text(
            " ",
            strip=True
        )

        if "Positions" in row_text:

            in_positions = True

            print(
                "Found Positions section"
            )

            continue

        if (
            in_positions
            and "Orders" in row_text
        ):
            print(
                "End Positions section"
            )
            break

        if not in_positions:
            continue

        tds = row.find_all("td")

        if len(tds) < 14:
            continue

        cells = [
            td.get_text(
                " ",
                strip=True
            )
            for td in tds
        ]

        try:

            trade_type = (
                cells[3]
                .lower()
            )

            if trade_type not in [
                "buy",
                "sell"
            ]:
                continue

            # Vị trí cuối luôn ổn định
            volume = _to_float(
                cells[-9]
            )

            open_price = _to_float(
                cells[-8]
            )

            sl = _to_float(
                cells[-7]
            )

            tp = _to_float(
                cells[-6]
            )

            close_time = pd.to_datetime(
                cells[-5],
                format="%Y.%m.%d %H:%M:%S"
            )

            close_price = _to_float(
                cells[-4]
            )

            commission = _to_float(
                cells[-3]
            )

            swap = _to_float(
                cells[-2]
            )

            profit = _to_float(
                cells[-1]
            )

            trades.append({

                "type":
                    trade_type,

                "ticket":
                    cells[1],

                "symbol":
                    cells[2],

                "open_time":
                    pd.to_datetime(
                        cells[0],
                        format="%Y.%m.%d %H:%M:%S"
                    ),

                "size":
                    volume,

                "open_price":
                    open_price,

                "sl":
                    sl,

                "tp":
                    tp,

                "close_time":
                    close_time,

                "close_price":
                    close_price,

                "commission":
                    commission,

                "taxes":
                    0,

                "swap":
                    swap,

                "profit":
                    profit
            })

        except Exception as e:

            print(
                "Position parse error:",
                cells,
                e
            )

    return trades


# =====================================================
# MT5 Deals
# =====================================================

def _parse_mt5_deals(rows):

    deals = []

    in_deals = False

    for row in rows:

        row_text = row.get_text(
            " ",
            strip=True
        )

        if "Deals" in row_text:

            in_deals = True

            print(
                "Found Deals section"
            )

            continue

        if (
            in_deals
            and "Open Positions" in row_text
        ):
            print(
                "End Deals section"
            )
            break

        if not in_deals:
            continue

        tds = row.find_all("td")

        if len(tds) < 15:
            continue

        cells = [
            td.get_text(
                " ",
                strip=True
            )
            for td in tds
        ]

        try:

            deal_type = (
                cells[3]
                .lower()
            )

            if deal_type != "balance":
                continue

            comment = (
                cells[14]
                .lower()
            )

            if "deposit" in comment:

                deals.append({
                    "type": "deposit",
                    "time": pd.to_datetime(
                        cells[0],
                        format="%Y.%m.%d %H:%M:%S"
                    ),
                    "amount": _to_float(
                        cells[12]
                    )
                })

            elif (
                "withdraw" in comment
                or "withdrawal" in comment
            ):

                deals.append({
                    "type": "withdrawal",
                    "time": pd.to_datetime(
                        cells[0],
                        format="%Y.%m.%d %H:%M:%S"
                    ),
                    "amount": abs(
                        _to_float(
                            cells[12]
                        )
                    )
                })

        except Exception as e:

            print(
                "Balance parse error:",
                cells,
                e
            )

    return deals