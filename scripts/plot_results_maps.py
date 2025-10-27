import os
import sys
import pandas as pd
import folium
from folium import plugins
import geopandas as gpd
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def load_results():
    """Load simulation results from CSV files"""
    base_dir = os.path.join(os.path.dirname(__file__), '..', 'results', 'raw')
    
    # Load original synthetic orders (with coordinates)
    synth_orders = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic_lapaz_orders_limited.csv'))
    
    # Load order results (status, times, etc.)
    fcfs_orders = pd.read_csv(os.path.join(base_dir, 'synthetic_lapaz_orders_limited_fcfs_results.csv'))
    rh_orders = pd.read_csv(os.path.join(base_dir, 'synthetic_lapaz_orders_limited_rh_results.csv'))
    
    # Merge with original orders to get coordinates
    fcfs_orders = fcfs_orders.merge(synth_orders[['order_id', 'rest_lat', 'rest_lon', 'dest_lat', 'dest_lon']], 
                                      on='order_id', how='left')
    rh_orders = rh_orders.merge(synth_orders[['order_id', 'rest_lat', 'rest_lon', 'dest_lat', 'dest_lon']], 
                                  on='order_id', how='left')
    
    # Load courier results
    fcfs_couriers = pd.read_csv(os.path.join(base_dir, 'synthetic_lapaz_orders_limited_fcfs_couriers.csv'))
    rh_couriers = pd.read_csv(os.path.join(base_dir, 'synthetic_lapaz_orders_limited_rh_couriers.csv'))
    
    # Load restaurants
    rest_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'la_paz_restaurants.geojson')
    restaurants = gpd.read_file(rest_path)
    
    return fcfs_orders, rh_orders, fcfs_couriers, rh_couriers, restaurants


def create_comparison_map(fcfs_orders, rh_orders, restaurants):
    """Create a map comparing FCFS vs Rolling Horizon deliveries"""
    
    # Center map on La Paz
    center_lat = 24.14
    center_lon = -110.31
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    
    # Add restaurants
    for idx, row in restaurants.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=8,
            popup=f"Restaurant {idx}",
            color='orange',
            fill=True,
            fillColor='orange',
            fillOpacity=0.7,
            weight=2
        ).add_to(m)
    
    # FCFS deliveries (delivered only)
    fcfs_delivered = fcfs_orders[fcfs_orders['status'] == 'delivered']
    for idx, row in fcfs_delivered.iterrows():
        # Line from restaurant to delivery
        folium.PolyLine(
            locations=[
                [row['rest_lat'], row['rest_lon']],
                [row['dest_lat'], row['dest_lon']]
            ],
            color='red',
            weight=2,
            opacity=0.3,
            popup=f"FCFS Order {row['order_id']}<br>CTD: {row['click_to_door']:.1f} min"
        ).add_to(m)
        
        # Delivery point
        folium.CircleMarker(
            location=[row['dest_lat'], row['dest_lon']],
            radius=3,
            color='red',
            fill=True,
            fillColor='red',
            fillOpacity=0.5,
            popup=f"FCFS: {row['click_to_door']:.1f} min"
        ).add_to(m)
    
    # Rolling Horizon deliveries (delivered only)
    rh_delivered = rh_orders[rh_orders['status'] == 'delivered']
    for idx, row in rh_delivered.iterrows():
        # Line from restaurant to delivery
        folium.PolyLine(
            locations=[
                [row['rest_lat'], row['rest_lon']],
                [row['dest_lat'], row['dest_lon']]
            ],
            color='blue',
            weight=2,
            opacity=0.3,
            popup=f"RH Order {row['order_id']}<br>CTD: {row['click_to_door']:.1f} min"
        ).add_to(m)
        
        # Delivery point
        folium.CircleMarker(
            location=[row['dest_lat'], row['dest_lon']],
            radius=3,
            color='blue',
            fill=True,
            fillColor='blue',
            fillOpacity=0.5,
            popup=f"RH: {row['click_to_door']:.1f} min"
        ).add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 220px; height: 140px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p><b>Legend</b></p>
    <p><span style="color:orange;">●</span> Restaurants</p>
    <p><span style="color:red;">—</span> FCFS Deliveries ({} orders)</p>
    <p><span style="color:blue;">—</span> Rolling Horizon ({} orders)</p>
    </div>
    '''.format(len(fcfs_delivered), len(rh_delivered))
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m


def create_heatmap(orders, title, output_file):
    """Create a heatmap of delivery times"""
    
    # Filter delivered orders
    delivered = orders[orders['status'] == 'delivered'].copy()
    
    if len(delivered) == 0:
        print(f"No delivered orders for {title}")
        return None
    
    # Center map on La Paz
    center_lat = 24.14
    center_lon = -110.31
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    
    # Prepare data for heatmap (location + click_to_door as weight)
    heat_data = []
    for idx, row in delivered.iterrows():
        if pd.notna(row['click_to_door']):
            heat_data.append([
                row['dest_lat'],
                row['dest_lon'],
                row['click_to_door']
            ])
    
    # Add heatmap
    plugins.HeatMap(
        heat_data,
        min_opacity=0.3,
        max_val=delivered['click_to_door'].quantile(0.95),
        radius=15,
        blur=20,
        gradient={
            0.0: 'green',
            0.5: 'yellow',
            0.75: 'orange',
            1.0: 'red'
        }
    ).add_to(m)
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 300px; height: 50px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:16px; padding: 10px">
    <b>{title}</b><br>
    Avg CTD: {delivered['click_to_door'].mean():.1f} min
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(title_html))
    
    return m


def create_courier_performance_map(courier_data, orders, title):
    """Create a map showing courier performance"""
    
    # Center map on La Paz
    center_lat = 24.14
    center_lon = -110.31
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    
    # For each courier, show their deliveries
    delivered = orders[orders['status'] == 'delivered'].copy()
    
    # Assign random colors to couriers for visualization
    import random
    random.seed(42)
    courier_colors = {}
    for cid in courier_data['courier_id'].unique():
        courier_colors[cid] = "#{:06x}".format(random.randint(0, 0xFFFFFF))
    
    # Draw delivery points colored by courier efficiency
    for idx, row in delivered.iterrows():
        # Use click_to_door to determine color intensity
        ctd = row.get('click_to_door', 30)
        
        # Color scale: green (fast) to red (slow)
        if ctd < 20:
            color = 'green'
        elif ctd < 35:
            color = 'yellow'
        elif ctd < 50:
            color = 'orange'
        else:
            color = 'red'
        
        folium.CircleMarker(
            location=[row['dest_lat'], row['dest_lon']],
            radius=4,
            popup=f"Order {row['order_id']}<br>CTD: {ctd:.1f} min",
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.6,
            weight=1
        ).add_to(m)
    
    # Add courier statistics
    stats_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 280px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <b>{title}</b><br>
    Total Couriers: {len(courier_data)}<br>
    Total Deliveries: {len(delivered)}<br>
    Avg Orders/Courier: {courier_data['orders_delivered'].mean():.1f}<br>
    Avg Distance: {courier_data['total_distance_km'].mean():.1f} km<br>
    Avg Utilization: {(courier_data['driving_time_minutes'] / (courier_data['shift_duration_hours'] * 60) * 100).mean():.1f}%
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(stats_html))
    
    return m


def create_first_orders_map(orders_df, restaurants, title, policy_name, n_orders=10):
    """Create a map showing the first N delivered orders"""
    
    # Get first N delivered orders
    delivered = orders_df[orders_df['status'] == 'delivered'].copy()
    if len(delivered) == 0:
        print(f"No delivered orders for {policy_name}")
        return None
    
    # Sort by delivery time and take first N
    delivered = delivered.sort_values('delivery_time').head(n_orders)
    
    # Center map on La Paz
    center_lat = 24.14
    center_lon = -110.31
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    
    # Add restaurants
    for idx, row in restaurants.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=6,
            popup=f"Restaurant {idx}",
            color='orange',
            fill=True,
            fillColor='orange',
            fillOpacity=0.7,
            weight=2
        ).add_to(m)
    
    # Color palette for orders (from earliest to latest)
    colors = ['darkgreen', 'green', 'lightgreen', 'yellow', 'gold', 
              'orange', 'darkorange', 'red', 'darkred', 'purple']
    
    # Plot each order with different color
    for idx, (_, row) in enumerate(delivered.iterrows()):
        order_num = idx + 1
        color = colors[idx % len(colors)]
        
        # Line from restaurant to delivery
        folium.PolyLine(
            locations=[
                [row['rest_lat'], row['rest_lon']],
                [row['dest_lat'], row['dest_lon']]
            ],
            color=color,
            weight=3,
            opacity=0.7,
            popup=f"Order #{order_num} (ID: {row['order_id']})<br>CTD: {row['click_to_door']:.1f} min"
        ).add_to(m)
        
        # Restaurant pickup point
        folium.CircleMarker(
            location=[row['rest_lat'], row['rest_lon']],
            radius=8,
            color=color,
            fill=True,
            fillColor='white',
            fillOpacity=0.8,
            weight=2,
            popup=f"Pickup #{order_num}"
        ).add_to(m)
        
        # Delivery point with number
        folium.Marker(
            location=[row['dest_lat'], row['dest_lon']],
            popup=f"Delivery #{order_num}<br>Order ID: {row['order_id']}<br>CTD: {row['click_to_door']:.1f} min",
            icon=folium.DivIcon(html=f'''
                <div style="font-size: 14pt; color: {color}; font-weight: bold;">
                    <i class="fa fa-map-marker" style="font-size: 24pt;"></i>
                    <span style="position: absolute; top: -5px; left: 8px; color: white; text-shadow: 1px 1px 2px black;">
                        {order_num}
                    </span>
                </div>
            ''')
        ).add_to(m)
    
    # Add title and statistics
    avg_ctd = delivered['click_to_door'].mean()
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 350px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <b>{title}</b><br>
    First {len(delivered)} Delivered Orders<br>
    Avg CTD: {avg_ctd:.1f} min<br>
    Min CTD: {delivered['click_to_door'].min():.1f} min<br>
    Max CTD: {delivered['click_to_door'].max():.1f} min
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 250px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px">
    <p><b>Order Sequence</b></p>
    <p style="color:darkgreen;">● 1st order (earliest)</p>
    <p style="color:yellow;">● Middle orders</p>
    <p style="color:darkred;">● Last order (latest)</p>
    <p><span style="color:orange;">●</span> Restaurants</p>
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m


def main():
    print("Loading simulation results...")
    fcfs_orders, rh_orders, fcfs_couriers, rh_couriers, restaurants = load_results()
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'results', 'maps')
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n1. Creating comparison map...")
    comparison_map = create_comparison_map(fcfs_orders, rh_orders, restaurants)
    comparison_map.save(os.path.join(output_dir, 'comparison_fcfs_vs_rh.html'))
    print(f"   ✓ Saved: results/maps/comparison_fcfs_vs_rh.html")
    
    print("\n2. Creating first 10 orders map (FCFS)...")
    fcfs_first10 = create_first_orders_map(fcfs_orders, restaurants, "FCFS - First 10 Deliveries", "FCFS", n_orders=10)
    if fcfs_first10:
        fcfs_first10.save(os.path.join(output_dir, 'fcfs_first_10_orders.html'))
        print(f"   ✓ Saved: results/maps/fcfs_first_10_orders.html")
    
    print("\n3. Creating first 10 orders map (Rolling Horizon)...")
    rh_first10 = create_first_orders_map(rh_orders, restaurants, "Rolling Horizon - First 10 Deliveries", "RH", n_orders=10)
    if rh_first10:
        rh_first10.save(os.path.join(output_dir, 'rh_first_10_orders.html'))
        print(f"   ✓ Saved: results/maps/rh_first_10_orders.html")
    
    print("\n4. Creating FCFS heatmap...")
    fcfs_heatmap = create_heatmap(fcfs_orders, "FCFS - Click-to-Door Times", "fcfs_heatmap.html")
    if fcfs_heatmap:
        fcfs_heatmap.save(os.path.join(output_dir, 'fcfs_heatmap.html'))
        print(f"   ✓ Saved: results/maps/fcfs_heatmap.html")
    
    print("\n5. Creating Rolling Horizon heatmap...")
    rh_heatmap = create_heatmap(rh_orders, "Rolling Horizon - Click-to-Door Times", "rh_heatmap.html")
    if rh_heatmap:
        rh_heatmap.save(os.path.join(output_dir, 'rh_heatmap.html'))
        print(f"   ✓ Saved: results/maps/rh_heatmap.html")
    
    print("\n6. Creating FCFS courier performance map...")
    fcfs_courier_map = create_courier_performance_map(fcfs_couriers, fcfs_orders, "FCFS - Courier Performance")
    fcfs_courier_map.save(os.path.join(output_dir, 'fcfs_courier_performance.html'))
    print(f"   ✓ Saved: results/maps/fcfs_courier_performance.html")
    
    print("\n7. Creating Rolling Horizon courier performance map...")
    rh_courier_map = create_courier_performance_map(rh_couriers, rh_orders, "RH - Courier Performance")
    rh_courier_map.save(os.path.join(output_dir, 'rh_courier_performance.html'))
    print(f"   ✓ Saved: results/maps/rh_courier_performance.html")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"\nFCFS Results:")
    print(f"  - Delivered: {len(fcfs_orders[fcfs_orders['status'] == 'delivered'])} orders")
    print(f"  - Avg Click-to-Door: {fcfs_orders[fcfs_orders['status'] == 'delivered']['click_to_door'].mean():.2f} min")
    print(f"  - Total Distance: {fcfs_couriers['total_distance_km'].sum():.2f} km")
    
    print(f"\nRolling Horizon Results:")
    print(f"  - Delivered: {len(rh_orders[rh_orders['status'] == 'delivered'])} orders")
    print(f"  - Avg Click-to-Door: {rh_orders[rh_orders['status'] == 'delivered']['click_to_door'].mean():.2f} min")
    print(f"  - Total Distance: {rh_couriers['total_distance_km'].sum():.2f} km")
    
    print(f"\nAll maps saved to: {output_dir}")
    print("\nOpen the HTML files in your browser to view the interactive maps!")


if __name__ == "__main__":
    main()
