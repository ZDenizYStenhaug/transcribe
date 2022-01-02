import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def main():
    filename = "robin_nyc_02-01-22-20-13_1"
    path = "../results/" + filename + ".csv"
    df = pd.read_csv(path)
    print(df)
    df.plot(
        x="count", y=["time_taken_for_job", "time_taken_for_process"], kind="bar"
    )
    plt.title(filename)
    plt.xlabel("request number")
    plt.ylabel("time taken (seconds)")
    plt.savefig("../graphs/" + filename + ".png")


if __name__ == '__main__':
    main()
