import pandas as pd
from pathlib import Path


def export_excel_report(html_path, trades, curve, summary, daily_equity=None):
    Path("output").mkdir(exist_ok=True)
    html_name = Path(html_path).stem
    output_file = Path("output") / f"{html_name}.xlsx"
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
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

            ws = writer.sheets["Daily_Statictis"]

            yellow = workbook.add_format({"bg_color": "#FFFF99"})
            orange = workbook.add_format({"bg_color": "#F5C58B"})
            purple = workbook.add_format({"bg_color": "#E5CCFF"})

            cols = {
                c: i
                for i, c in enumerate(daily_equity.columns)
            }
            COL_WIDTH = 15
            for i in range(len(daily_equity.columns)):
                ws.set_column(i, i, COL_WIDTH)

            for c in [
                "min_floating_curve",
                "min_floating_realtime"
            ]:
                if c in cols:
                    ws.set_column(cols[c], cols[c], COL_WIDTH, yellow)

            for c in [
                "max_buy_volume_curve",
                "max_buy_volume_realtime"
            ]:
                if c in cols:
                    ws.set_column(cols[c], cols[c], COL_WIDTH, orange)

            for c in [
                "max_sell_volume_curve",
                "max_sell_volume_realtime"
            ]:
                if c in cols:
                    ws.set_column(cols[c], cols[c], COL_WIDTH, purple)