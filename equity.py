import pandas as pd
import numpy as np

CONTRACT_SIZE = 100


def calc_floating(tr, price):

    if tr["type"] == "buy":
        return (
            price - tr["open_price"]
        ) * tr["size"] * CONTRACT_SIZE

    return (
        tr["open_price"] - price
    ) * tr["size"] * CONTRACT_SIZE


def build_equity_curve(
    trades,
    price_df,
    start_balance
):

    trades = trades.sort_values("time").reset_index(drop=True)

    price_df = price_df.copy()

    # =====================================================
    # CASE 1: có cột time
    # =====================================================

    if "time" in price_df.columns:

        price_df["time"] = pd.to_datetime(
            price_df["time"]
        )

        if "close" not in price_df.columns:
            raise ValueError(
                f"Column 'close' not found. Available columns: {price_df.columns.tolist()}"
            )

    # =====================================================
    # CASE 2: Date + Time
    # =====================================================

    elif {"Date", "Time"}.issubset(price_df.columns):

        price_df["time"] = pd.to_datetime(
            price_df["Date"].astype(str)
            + " "
            + price_df["Time"].astype(str),
            errors="coerce"
        )

        if "close" not in price_df.columns:

            for col in ["Close", "CLOSE", "close"]:

                if col in price_df.columns:
                    price_df["close"] = price_df[col]
                    break

    # =====================================================
    # CASE 3: MT5 export
    # =====================================================

    elif {"<DATE>", "<TIME>"}.issubset(price_df.columns):

        price_df["time"] = pd.to_datetime(
            price_df["<DATE>"].astype(str)
            + " "
            + price_df["<TIME>"].astype(str),
            errors="coerce"
        )

        price_df["close"] = price_df["<CLOSE>"]

    # =====================================================
    # CASE 4: CSV không có header
    # =====================================================

    else:

        cols = list(price_df.columns)

        if len(cols) >= 6:

            try:

                first_date = str(cols[0])
                first_time = str(cols[1])

                pd.to_datetime(
                    first_date + " " + first_time,
                    format="%Y.%m.%d %H:%M"
                )

                first_row = list(cols)
                body_rows = price_df.values.tolist()

                all_rows = [first_row] + body_rows

                fixed = pd.DataFrame(
                    all_rows,
                    columns=[
                        "Date",
                        "Time",
                        "Open",
                        "High",
                        "Low",
                        "Close",
                        "Volume"
                    ][:len(first_row)]
                )

                fixed["time"] = pd.to_datetime(
                    fixed["Date"].astype(str)
                    + " "
                    + fixed["Time"].astype(str),
                    format="%Y.%m.%d %H:%M",
                    errors="coerce"
                )

                fixed["close"] = pd.to_numeric(
                    fixed["Close"],
                    errors="coerce"
                )

                price_df = fixed

            except Exception:

                raise ValueError(
                    f"Cannot find datetime columns. Available columns: {price_df.columns.tolist()}"
                )

        else:

            raise ValueError(
                f"Cannot find datetime columns. Available columns: {price_df.columns.tolist()}"
            )

    # =====================================================
    # CLEAN DATA
    # =====================================================

    price_df = price_df.dropna(subset=["time"])

    price_df["close"] = pd.to_numeric(
        price_df["close"],
        errors="coerce"
    )

    price_df = price_df.dropna(subset=["close"])

    price_df = (
        price_df
        .sort_values("time")
        .reset_index(drop=True)
    )

    price_time = price_df["time"].values
    price_close = price_df["close"].values

    trade_list = trades.to_dict("records")

    cashflows = [
        t for t in trade_list
        if t["type"] in [
            "deposit",
            "withdrawal"
        ]
    ]

    trade_events = [
        t for t in trade_list
        if t["type"] in [
            "buy",
            "sell"
        ]
    ]

    # =====================================================
    # BALANCE TẠI THỜI ĐIỂM CSV BẮT ĐẦU
    # =====================================================

    csv_start_time = price_df["time"].iloc[0]

    balance = start_balance

    floating_trades = []

    for tr in trade_list:

        if tr["type"] == "deposit":

            if tr["time"] < csv_start_time:
                balance += tr["amount"]

        elif tr["type"] == "withdrawal":

            if tr["time"] < csv_start_time:
                balance += tr["amount"]

        elif tr["type"] in ["buy", "sell"]:

            if tr["close_time"] < csv_start_time:

                balance += tr["profit"]

            elif (
                tr["open_time"] <= csv_start_time
                and tr["close_time"] > csv_start_time
            ):

                floating_trades.append(tr)

    # =====================================================
    # POINTER
    # =====================================================

    cash_ptr = len([
        x for x in cashflows
        if x["time"] < csv_start_time
    ])

    trade_ptr = len([
        x for x in trade_events
        if x["open_time"] <= csv_start_time
    ])

    # =====================================================
    # RESULT
    # =====================================================

    times = []
    balances = []
    equities = []

    buy_volumes = []
    sell_volumes = []

    floating_pnls = []

    # =====================================================
    # LOOP TIMELINE
    # =====================================================

    for i in range(len(price_df)):

        t = price_time[i]

        price = price_close[i]

        # ---------------------------------

        while (
            cash_ptr < len(cashflows)
            and cashflows[cash_ptr]["time"] <= t
        ):

            cf = cashflows[cash_ptr]

            balance += cf["amount"]

            cash_ptr += 1

        # ---------------------------------

        while (
            trade_ptr < len(trade_events)
            and trade_events[trade_ptr]["open_time"] <= t
        ):

            tr = trade_events[trade_ptr]

            if tr not in floating_trades:
                floating_trades.append(tr)

            trade_ptr += 1

        # ---------------------------------

        still_open = []

        for tr in floating_trades:

            if tr["close_time"] <= t:

                balance += tr["profit"]

            else:

                still_open.append(tr)

        floating_trades = still_open

        # ---------------------------------

        floating = 0.0

        current_buy_volume = 0.0
        current_sell_volume = 0.0

        for tr in floating_trades:

            floating += calc_floating(
                tr,
                price
            )

            if tr["type"] == "buy":

                current_buy_volume += tr["size"]

            elif tr["type"] == "sell":

                current_sell_volume += tr["size"]

        equity = balance + floating

        # ---------------------------------

        times.append(t)
        balances.append(balance)
        equities.append(equity)

        floating_pnls.append(floating)

        buy_volumes.append(
            current_buy_volume
        )

        sell_volumes.append(
            current_sell_volume
        )

    # =====================================================
    # OUTPUT
    # =====================================================

    return pd.DataFrame({

        "time": times,

        "balance": balances,

        "equity": equities,

        "floating_pnl": floating_pnls,

        "buy_volume": buy_volumes,

        "sell_volume": sell_volumes

    })