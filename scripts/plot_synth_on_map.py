import os
import argparse
import pandas as pd
import folium
from folium.plugins import MarkerCluster


def load_orders(csv_path):
    return pd.read_csv(csv_path, parse_dates=[c for c in ['created_at','ready_at'] if c in pd.read_csv(csv_path, nrows=0).columns])


def build_map(df, restaurants_geojson=None, out_path=None, map_zoom=13):
    # center map on mean of destinations
    mean_lat = df['dest_lat'].astype(float).mean()
    mean_lon = df['dest_lon'].astype(float).mean()

    m = folium.Map(location=[mean_lat, mean_lon], zoom_start=map_zoom, tiles='OpenStreetMap')

    # If restaurants geojson provided, overlay it
    if restaurants_geojson and os.path.exists(restaurants_geojson):
        try:
            folium.GeoJson(restaurants_geojson, name='restaurants').add_to(m)
        except Exception:
            pass

    # Add restaurants as black triangle markers (unique)
    rest = df[['restaurant_id','rest_lat','rest_lon']].drop_duplicates('restaurant_id')
    for _, r in rest.iterrows():
        folium.CircleMarker(
            location=[float(r['rest_lat']), float(r['rest_lon'])],
            radius=6,
            color='black',
            fill=True,
            fill_color='black',
            popup=f"Restaurant {int(r['restaurant_id'])}",
        ).add_to(m)

    # Add destinations with MarkerCluster for performance
    cluster = MarkerCluster(name='destinations', control=False).add_to(m)
    for _, row in df.iterrows():
        popup = folium.Popup(f"Order {int(row['order_id'])}<br>R: {int(row['restaurant_id'])}<br>ready: {row.get('ready_at','')}")
        folium.CircleMarker(
            location=[float(row['dest_lat']), float(row['dest_lon'])],
            radius=3,
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.7,
            popup=popup,
        ).add_to(cluster)

    folium.LayerControl().add_to(m)

    if out_path is None:
        out_dir = os.path.join('results', 'maps')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'synthetic_map.html')
    m.save(out_path)
    return out_path


def main():
    parser = argparse.ArgumentParser(description='Plot synthetic orders on an interactive folium map')
    parser.add_argument('csv', nargs='?', default=os.path.join('data','synthetic_lapaz_orders_limited.csv'))
    parser.add_argument('--restaurants','-r', default=os.path.join('data','la_paz_restaurants.geojson'))
    parser.add_argument('--out','-o', default=None)
    parser.add_argument('--zoom', type=int, default=13)
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print('CSV not found:', args.csv)
        return

    df = load_orders(args.csv)
    out = build_map(df, restaurants_geojson=args.restaurants, out_path=args.out, map_zoom=args.zoom)
    print('Saved interactive map to', out)


if __name__ == '__main__':
    main()
