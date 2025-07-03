import pandas as pd
import matplotlib.pyplot as plt


def main():
    df = pd.read_csv("synthetic_lapaz_orders.csv", parse_dates=["created_at", "ready_at"])

    df["prep_minutes"] = (df["ready_at"] - df["created_at"]).dt.total_seconds() / 60
    df["created_hour"] = df["created_at"].dt.hour + df["created_at"].dt.minute / 60

    plt.figure(figsize=(8, 4))
    plt.hist(df["created_hour"], bins=12, edgecolor="black")
    plt.xlabel("Hour of Day")
    plt.ylabel("Number of Orders")
    plt.title("Order Creation Time Distribution")
    plt.tight_layout()

    plt.figure(figsize=(8, 4))
    plt.hist(df["prep_minutes"], bins=20, edgecolor="black")
    plt.xlabel("Prep Time (min)")
    plt.ylabel("Number of Orders")
    plt.title("Preparation Time Distribution")
    plt.tight_layout()

    plt.figure(figsize=(6, 6))
    plt.scatter(df["rest_lon"], df["rest_lat"], s=10, c="blue", label="Restaurants", alpha=0.5)
    plt.scatter(df["dest_lon"], df["dest_lat"], s=10, c="red", label="Destinations", alpha=0.5)
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Restaurant and Destination Locations")
    plt.legend()
    plt.tight_layout()

    plt.show()


if __name__ == "__main__":
    main()
