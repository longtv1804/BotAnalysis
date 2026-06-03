import pandas as pd
from pathlib import Path


def export_excel_report(trades, curve, daily_pnl, summary, daily_equity=None):
    Path("output").mkdir(exist_ok=True)
    with pd.ExcelWriter("output/report.xlsx", engine="xlsxwriter") as writer:
        pd.DataFrame([summary]).to_excel(
            writer,
            sheet_name="Summary",
            index=False
        )

        trades.to_excel(
            writer,
            sheet_name="Trades",
            index=False
        )

        daily_pnl.to_excel(
            writer,
            sheet_name="Daily_PnL",
            index=False
        )

        curve.to_excel(
            writer,
            sheet_name="Equity_Curve",
            index=False
        )

        workbook = writer.book
        worksheet = writer.sheets["Equity_Curve"]

        chart = workbook.add_chart({"type": "line"})
        max_row = len(curve)
        chart.add_series({
            "name": "Equity",
            "categories": ["Equity_Curve", 1, 0, max_row, 0],
            "values": ["Equity_Curve", 1, 2, max_row, 2],
            "line": {"color": "blue"}
        })
        chart.add_series({
            "name": "Balance",
            "categories": ["Equity_Curve", 1, 0, max_row, 0],
            "values": ["Equity_Curve", 1, 1, max_row, 1],
            "line": {"color": "green"}
        })

        worksheet.insert_chart("H2", chart)

        if daily_equity is not None:
            daily_equity.to_excel(
                writer,
                sheet_name="Daily_Statictis",
                index=False
            )