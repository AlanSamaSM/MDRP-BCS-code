import os
import argparse
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point


def load_orders(path):
    df = pd.read_csv(path, parse_dates=[col for col in ['created_at','ready_at'] if col in pd.read_csv(path, nrows=0).columns])
    return df


def make_gdf_from_coords(df, lon_col, lat_col, crs="EPSG:4326"):
    pts = [Point(xy) for xy in zip(df[lon_col].astype(float), df[lat_col].astype(float))]
    gdf = gpd.GeoDataFrame(df.copy(), geometry=pts, crs=crs)
    return gdf


def plot_points(csv_path, restaurants_geojson=None, out_path=None, show=False):
    df = load_orders(csv_path)

    # Create GeoDataFrames
    gdf_dest = make_gdf_from_coords(df, 'dest_lon', 'dest_lat')
    gdf_rest_points = make_gdf_from_coords(
        df.drop_duplicates('restaurant_id'), 'rest_lon', 'rest_lat'
    )

    # Attempt to load restaurants geojson (polygon/points) if provided or exists in data/
    land_gdf = None
    if restaurants_geojson and os.path.exists(restaurants_geojson):
        try:
            land_gdf = gpd.read_file(restaurants_geojson)
        except Exception:
            land_gdf = None
    else:
        alt = os.path.join('data', 'la_paz_restaurants.geojson')
        if os.path.exists(alt):
            try:
                land_gdf = gpd.read_file(alt)
            except Exception:
                land_gdf = None

    # Setup plot
    fig, ax = plt.subplots(figsize=(9, 9))

    if land_gdf is not None and not land_gdf.empty:
        # If the geojson contains polygons, plot them faintly
        try:
            polys = land_gdf[land_gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]
            if not polys.empty:
                polys.plot(ax=ax, color='#e6f2ff', edgecolor='none')
        except Exception:
            pass

    # plot restaurants and destinations
    gdf_rest_points.plot(ax=ax, marker='^', color='black', markersize=40, label='Restaurants')
    gdf_dest.plot(ax=ax, marker='o', color='red', markersize=6, alpha=0.7, label='Destinations')

    # set bounds with a small margin
    try:
        bounds = gdf_dest.total_bounds if not gdf_dest.empty else gdf_rest_points.total_bounds
        minx, miny, maxx, maxy = bounds
        dx = (maxx - minx) * 0.1 if (maxx - minx) > 0 else 0.01
        dy = (maxy - miny) * 0.1 if (maxy - miny) > 0 else 0.01
        ax.set_xlim(minx - dx, maxx + dx)
        ax.set_ylim(miny - dy, maxy + dy)
    except Exception:
        pass

    ax.set_title(f'Synthetic orders: {os.path.basename(csv_path)}')
    ax.legend()
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')

    if out_path is None:
        out_dir = os.path.join('results', 'maps')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, os.path.basename(csv_path).replace('.csv', '.png'))
    else:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

    fig.savefig(out_path, dpi=200, bbox_inches='tight')
    print('Saved plot to', out_path)

    if show:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description='Plot synthetic orders (restaurants + destinations)')
    parser.add_argument('csv', nargs='?', default=os.path.join('data', 'synthetic_lapaz_orders_limited.csv'),
                        help='Path to synthetic orders CSV')
    parser.add_argument('--restaurants', '-r', default=None, help='Optional restaurants geojson path')
    parser.add_argument('--out', '-o', default=None, help='Output image path')
    parser.add_argument('--show', action='store_true', help='Show matplotlib window')
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print('CSV file not found:', args.csv)
        return

    plot_points(args.csv, restaurants_geojson=args.restaurants, out_path=args.out, show=args.show)


if __name__ == '__main__':
    main()
