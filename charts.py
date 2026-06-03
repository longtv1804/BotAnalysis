import matplotlib.pyplot as plt


def plot_balance_equity(curve):

    plt.figure(
        figsize=(16, 8)
    )

    plt.plot(
        curve["time"],
        curve["balance"],
        label="Balance",
        linewidth=2
    )

    plt.plot(
        curve["time"],
        curve["equity"],
        label="Equity",
        alpha=0.8
    )

    plt.title(
        "Balance vs Equity"
    )

    plt.legend()

    plt.grid(True)

    plt.tight_layout()

    plt.savefig(
        "output/balance_equity.png",
        dpi=300
    )

    plt.show()