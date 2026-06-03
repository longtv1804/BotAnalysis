import pandas as pd
from collections import defaultdict

CONTRACT_SIZE = 100

def daily_pnl(trades):

    df = trades.copy()

    df = df[df["type"].isin(["buy", "sell"])]

    if df.empty:
        return pd.DataFrame(columns=["date", "pnl"])

    df["date"] = pd.to_datetime(df["close_time"]).dt.date

    return (
        df.groupby("date")["profit"]
        .sum()
        .reset_index(name="pnl")
        .sort_values("date")
    )

def calc_net_deposit(trades):
    deposits = trades.loc[trades["type"] == "deposit", "amount"].sum()
    withdrawals = trades.loc[trades["type"] == "withdrawal", "amount"].sum()
    return deposits - withdrawals

def calc_daily_maxVolume_minFPLN(trades, prices):

    trade_df = trades.copy()

    trade_df = trade_df[
        trade_df["type"].isin(["buy", "sell"])
    ]

    trade_list = (
        trade_df
        .sort_values("open_time")
        .to_dict("records")
    )

    prices = prices.copy()

    prices["time"] = pd.to_datetime(
        prices["Date"].astype(str)
        + " "
        + prices["Time"].astype(str)
    )

    prices = prices.sort_values("time")

    price_list = prices.to_dict("records")

    result = defaultdict(
        lambda: {
            "max_buy_volume_realtime": 0.0,
            "max_sell_volume_realtime": 0.0,
            "min_floating_realtime": None
        }
    )

    if len(price_list) == 0:
        return pd.DataFrame()

    price_start = price_list[0]["time"]

    alive = []

    for tr in trade_list:

        if (
            tr["open_time"] <= price_start
            and tr["close_time"] > price_start
        ):
            alive.append(tr)

    trade_ptr = 0

    while (
        trade_ptr < len(trade_list)
        and trade_list[trade_ptr]["open_time"] <= price_start
    ):
        trade_ptr += 1

    for row in price_list:

        now = row["time"]
        day = now.date()

        price = float(row["Close"])

        while (
            trade_ptr < len(trade_list)
            and trade_list[trade_ptr]["open_time"] <= now
        ):

            tr = trade_list[trade_ptr]

            if tr["close_time"] > now:
                alive.append(tr)

            trade_ptr += 1

        alive = [
            tr
            for tr in alive
            if tr["close_time"] > now
        ]

        buy_volume = 0.0
        sell_volume = 0.0
        floating = 0.0

        for tr in alive:

            if tr["type"] == "buy":

                buy_volume += tr["size"]

                floating += (
                    price
                    - tr["open_price"]
                ) * tr["size"] * CONTRACT_SIZE

            else:

                sell_volume += tr["size"]

                floating += (
                    tr["open_price"]
                    - price
                ) * tr["size"] * CONTRACT_SIZE

        result[day]["max_buy_volume_realtime"] = max(
            result[day]["max_buy_volume_realtime"],
            buy_volume
        )

        result[day]["max_sell_volume_realtime"] = max(
            result[day]["max_sell_volume_realtime"],
            sell_volume
        )

        current = result[day]["min_floating_realtime"]

        if current is None:
            result[day]["min_floating_realtime"] = floating
        else:
            result[day]["min_floating_realtime"] = min(
                current,
                floating
            )

    rows = []

    for day in sorted(result.keys()):

        row = {"date": day}

        row.update(result[day])

        rows.append(row)

    return pd.DataFrame(rows)


def daily_summary(curve, trades, prices):

    df = curve.copy()

    df["time"] = pd.to_datetime(df["time"])

    df["date"] = df["time"].dt.date

    curve_daily = (
        df.groupby("date")
        .agg(
            balance_end=("balance", "last"),
            equity_end=("equity", "last"),

            equity_min=("equity", "min"),
            equity_max=("equity", "max"),

            min_floating_curve=("floating_pnl", "min"),
            max_floating_curve=("floating_pnl", "max"),

            max_buy_volume_curve=("buy_volume", "max"),
            max_sell_volume_curve=("sell_volume", "max"),
        )
        .reset_index()
    )

    pnl_daily = daily_pnl(trades)

    pnl_daily = pnl_daily.rename(
        columns={
            "pnl": "daily_pnl"
        }
    )

    realtime_daily = calc_daily_maxVolume_minFPLN(
        trades,
        prices
    )

    result = curve_daily.merge(
        pnl_daily,
        on="date",
        how="left"
    )

    result = result.merge(
        realtime_daily,
        on="date",
        how="left"
    )

    result["daily_pnl"] = (
        result["daily_pnl"]
        .fillna(0)
    )

    return result