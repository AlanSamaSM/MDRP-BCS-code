import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt


def plot_simple(csv_path, out_path=None, show=False):
    df = pd.read_csv(csv_path)

    # Expect columns rest_lon/rest_lat and dest_lon/dest_lat
    if not {'rest_lon','rest_lat','dest_lon','dest_lat'}.issubset(df.columns):
        print('CSV missing required columns (rest_lon, rest_lat, dest_lon, dest_lat)')
        return

    fig, ax = plt.subplots(figsize=(8,8))
    ax.scatter(df['dest_lon'], df['dest_lat'], s=8, c='red', alpha=0.6, label='destinations')
    # plot unique restaurants
    rest = df[['restaurant_id','rest_lon','rest_lat']].drop_duplicates('restaurant_id')
    ax.scatter(rest['rest_lon'], rest['rest_lat'], s=50, c='black', marker='^', label='restaurants')

    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title(os.path.basename(csv_path))
    ax.legend()

    if out_path is None:
        out_dir = os.path.join('results','maps')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, os.path.basename(csv_path).replace('.csv','.png'))
    else:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    print('Saved plot to', out_path)
    if show:
        plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('csv', nargs='?', default=os.path.join('data','synthetic_lapaz_orders_limited.csv'))
    parser.add_argument('--out','-o', default=None)
    parser.add_argument('--show', action='store_true')
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print('CSV not found:', args.csv)
        return
    plot_simple(args.csv, out_path=args.out, show=args.show)


if __name__ == '__main__':
    main()
