import pandas as pd

from parser import parse_mt_report
from equity import build_equity_curve
from statistics import daily_summary, calc_daily_maxVolume_minFPLN, calc_net_deposit
from excel_report import export_excel_report


START_BALANCE = 10000


def main():
    REPORT_FILE = "reports/FPG-8799939.htm"
    PRICE_FILE = "market_data/MT4-XAUUSD-P1-M5.csv"

    print ("Read .html ..........")
    trades = parse_mt_report(REPORT_FILE)
    print(
        trades[
            trades["type"].isin(["deposit", "withdrawal"])
        ][["time", "type", "amount"]]
    )
    # MT4/MT5 CSV:
    # Date	Time	Open	High	Low	Close	Volume
    print ("Read the price info.csv ..........")
    prices = pd.read_csv(
        PRICE_FILE,
        sep=",",
        header=None,
        names=[
            "Date",
            "Time",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]
    )
    print(prices.head())
    print(prices.columns.tolist())

    print ("calculating ..........")
    curve = build_equity_curve(
        trades,
        prices,
        START_BALANCE
    )
    print(curve.head())
    print(curve.tail())

    print("MIN BALANCE:", curve["balance"].min())
    print("MIN EQUITY :", curve["equity"].min())

    daily_statictis = daily_summary(
        curve=curve,
        trades=trades,
        prices=prices
    )

    summary = {
        "start_balance": START_BALANCE,
        "final_balance": curve["balance"].iloc[-1],
        "final_equity": curve["equity"].iloc[-1],
        "net_deposit": calc_net_deposit(trades)
    }

    print ("export to excel ..........")
    export_excel_report(
        html_path=REPORT_FILE,
        trades=trades,
        curve=curve,
        summary=summary,
        daily_equity=daily_statictis
    )
    print ("DONE !!!")


if __name__ == "__main__":
    main()