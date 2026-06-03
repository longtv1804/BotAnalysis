import pandas as pd


def daily_summary(curve):

    df = curve.copy()

    df["time"] = pd.to_datetime(df["time"])
    df["date"] = df["time"].dt.date

    if "floating_pnl" not in df.columns:
        df["floating_pnl"] = (
            df["equity"] - df["balance"]
        )

    return (
        df.groupby("date")
        .agg(
            # cuối ngày
            balance_end=("balance", "last"),
            equity_end=("equity", "last"),

            # balance
            balance_min=("balance", "min"),
            balance_max=("balance", "max"),

            # equity
            equity_min=("equity", "min"),
            equity_max=("equity", "max"),

            # floating pnl
            floating_min=("floating_pnl", "min"),
            floating_max=("floating_pnl", "max"),
            floating_last=("floating_pnl", "last"),

            # volume đồng thời lớn nhất
            buy_volume_max=("buy_volume", "max"),
            sell_volume_max=("sell_volume", "max"),
        )
        .reset_index()
    )


def daily_pnl(trades):

    df = trades.copy()

    df = df[
        df["type"].isin(
            ["buy", "sell"]
        )
    ]

    if df.empty:

        return pd.DataFrame(
            columns=["date", "pnl"]
        )

    df["date"] = (
        pd.to_datetime(
            df["close_time"]
        ).dt.date
    )

    return (
        df.groupby("date")["profit"]
        .sum()
        .reset_index(name="pnl")
        .sort_values("date")
    )


def pnl_statistics(trades):

    daily = daily_pnl(trades)

    if daily.empty:

        return {
            "best_day": None,
            "best_pnl": 0.0,
            "worst_day": None,
            "worst_pnl": 0.0,
        }

    best_row = daily.loc[
        daily["pnl"].idxmax()
    ]

    worst_row = daily.loc[
        daily["pnl"].idxmin()
    ]

    return {

        "best_day":
            best_row["date"],

        "best_pnl":
            float(best_row["pnl"]),

        "worst_day":
            worst_row["date"],

        "worst_pnl":
            float(worst_row["pnl"]),
    }


def floating_statistics(curve):

    df = curve.copy()

    if "floating_pnl" not in df.columns:

        df["floating_pnl"] = (
            df["equity"] - df["balance"]
        )

    worst_row = df.loc[
        df["floating_pnl"].idxmin()
    ]

    best_row = df.loc[
        df["floating_pnl"].idxmax()
    ]

    return {

        "worst_time":
            worst_row["time"],

        "worst_floating":
            float(
                worst_row["floating_pnl"]
            ),

        "best_time":
            best_row["time"],

        "best_floating":
            float(
                best_row["floating_pnl"]
            ),
    }


def calc_net_deposit(trades):

    deposits = trades.loc[
        trades["type"] == "deposit",
        "amount"
    ].sum()

    withdrawals = trades.loc[
        trades["type"] == "withdrawal",
        "amount"
    ].sum()

    return deposits - withdrawals