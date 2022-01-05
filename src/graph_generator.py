import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def main():
    filename = "robin_nyc_short_03-01-22-16-03_50"
    path = "../results/" + filename + ".csv"
    df = pd.read_csv(path)
    convert_dict = {"count": int}
    df = df.astype(convert_dict)

    draw_bar_chart(df, filename)

def draw_bar_chart(df, filename):
    plt.rcParams['figure.figsize'] = [50, 20]
    df.plot(
        x="count", y=["time_taken_for_job", "time_taken_for_process"], kind="bar"
    )
    plt.title(filename)
    plt.xlabel("request number")
    plt.ylabel("time taken (seconds)")

    plt.savefig("../graphs/" + filename + ".png")


if __name__ == '__main__':
    main()
