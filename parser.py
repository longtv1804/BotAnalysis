import pandas as pd
from bs4 import BeautifulSoup


def parse_mt_report(html_file):

    with open(html_file, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    rows = soup.find_all("tr")

    trades = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        text = row.get_text(" ", strip=True).lower()

        # deposit
        if "balance" in text and "deposit" in text:
            try:
                trades.append({
                    "type": "deposit",
                    "time": pd.to_datetime(cols[1].get_text(strip=True)),
                    "amount": float(cols[-1].get_text(strip=True).replace(" ", ""))
                })
            except:
                pass
            continue

        # withdrawal
        if "balance" in text and "withdrawal" in text:
            try:
                trades.append({
                    "type": "withdrawal",
                    "time": pd.to_datetime(cols[1].get_text(strip=True)),
                    "amount": float(cols[-1].get_text(strip=True).replace(" ", ""))
                })
            except:
                pass
            continue

        trade_type = cols[2].get_text(strip=True).lower()

        if trade_type in ["buy", "sell"]:
            try:
                trades.append({
                    "type": trade_type,
                    "ticket": cols[0].get_text(strip=True),
                    "open_time": pd.to_datetime(cols[1].get_text(strip=True)),
                    "size": float(cols[3].get_text(strip=True)),
                    "symbol": cols[4].get_text(strip=True),
                    "open_price": float(cols[5].get_text(strip=True)),
                    "sl": float(cols[6].get_text(strip=True) or 0),
                    "tp": float(cols[7].get_text(strip=True) or 0),
                    "close_time": pd.to_datetime(cols[8].get_text(strip=True)),
                    "close_price": float(cols[9].get_text(strip=True)),
                    "commission": float(cols[10].get_text(strip=True) or 0),
                    "taxes": float(cols[11].get_text(strip=True) or 0),
                    "swap": float(cols[12].get_text(strip=True) or 0),
                    "profit": float(cols[13].get_text(strip=True))
                })
            except:
                pass

    return pd.DataFrame(trades)