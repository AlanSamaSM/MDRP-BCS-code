#!/usr/bin/env python3
"""
Genera un índice HTML interactivo de los primeros 5 y últimos 5 mapas de bundles por courier.
Esto reduce la cantidad de archivos mientras mantiene información sobre inicio y final de cada courier.
"""

import os
import glob
from datetime import datetime

def generate_complete_bundles_index():
    """Genera un índice HTML de los primeros 5 y últimos 5 bundles por courier."""
    
    base_path = os.path.dirname(__file__)
    complete_bundles_dir = os.path.join(
        base_path, '..', 'results', 'maps', 'rh', 'complete_bundles'
    )
    
    if not os.path.exists(complete_bundles_dir):
        print(f"No complete bundles directory found at {complete_bundles_dir}")
        return
    
    # Buscar todos los mapas
    all_map_files = sorted(glob.glob(os.path.join(complete_bundles_dir, '*.html')))
    
    if not all_map_files:
        print("No complete bundle maps found.")
        return
    
    print(f"Found {len(all_map_files)} complete bundle maps")
    
    # Agrupar por courier
    couriers_bundles = {}
    for map_file in all_map_files:
        filename = os.path.basename(map_file)
        # Parse: courier_<id>_bundle_<n>.html
        parts = filename.replace('courier_', '').replace('_bundle_', '_').replace('.html', '').split('_')
        if len(parts) >= 2:
            courier_id = parts[0]
            bundle_num = int(parts[1])
            if courier_id not in couriers_bundles:
                couriers_bundles[courier_id] = {}
            couriers_bundles[courier_id][bundle_num] = map_file
    
    # Filtrar: solo primeros 5 y últimos 5 por courier
    filtered_bundles = {}
    for courier_id, bundles_dict in couriers_bundles.items():
        sorted_nums = sorted(bundles_dict.keys())
        total = len(sorted_nums)
        
        selected_nums = []
        # Primeros 5
        selected_nums.extend(sorted_nums[:5])
        # Últimos 5
        if total > 10:
            selected_nums.extend(sorted_nums[-5:])
        else:
            # Si hay menos de 10, incluir todos después de los primeros 5
            selected_nums.extend(sorted_nums[5:])
        
        # Eliminar duplicados y ordenar
        selected_nums = sorted(set(selected_nums))
        
        filtered_bundles[courier_id] = [(num, bundles_dict[num]) for num in selected_nums]
    
    # Calcular estadísticas
    total_selected = sum(len(v) for v in filtered_bundles.values())
    total_available = len(all_map_files)
    
    print(f"Filtering bundles: {total_selected} de {total_available} seleccionados")
    print(f"(Primeros 5 + Últimos 5 por courier)")
    
    # Generar HTML
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Índice de Bundles Completos - MDRP RH (Primeros 5 + Últimos 5)</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
        }}
        
        header p {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            padding: 20px;
            background: #f5f5f5;
            border-bottom: 1px solid #ddd;
        }}
        
        .stat-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-card .label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .filter-info {{
            background: #e3f2fd;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 30px;
            border-radius: 4px;
        }}
        
        .filter-info strong {{
            color: #667eea;
        }}
        
        .courier-section {{
            margin-bottom: 40px;
            border: 2px solid #667eea;
            border-radius: 8px;
            padding: 20px;
            background: #f9f9f9;
        }}
        
        .courier-header {{
            background: #667eea;
            color: white;
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 15px;
            font-weight: bold;
            font-size: 1.1em;
        }}
        
        .bundle-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
        }}
        
        .bundle-card {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        
        .bundle-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.15);
            border-color: #667eea;
        }}
        
        .bundle-card a {{
            text-decoration: none;
            color: inherit;
            display: block;
        }}
        
        .bundle-number {{
            font-size: 1.3em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        
        .bundle-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: bold;
            margin-right: 5px;
        }}
        
        .badge-first {{
            background: #c8e6c9;
            color: #2e7d32;
        }}
        
        .badge-last {{
            background: #ffccbc;
            color: #d84315;
        }}
        
        .bundle-filename {{
            font-size: 0.85em;
            color: #666;
            word-break: break-all;
            font-family: monospace;
        }}
        
        .bundle-link {{
            display: inline-block;
            margin-top: 10px;
            padding: 8px 12px;
            background: #667eea;
            color: white;
            border-radius: 4px;
            font-size: 0.9em;
            transition: background 0.3s;
        }}
        
        .bundle-link:hover {{
            background: #764ba2;
        }}
        
        footer {{
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #ddd;
            font-size: 0.9em;
        }}
        
        .timestamp {{
            color: #999;
            font-size: 0.85em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🗺️ Índice de Bundles Completos (Filtrado)</h1>
            <p>Rolling Horizon - Primeros 5 + Últimos 5 por Courier</p>
        </header>
        
        <div class="stats">
            <div class="stat-card">
                <div class="value">{len(filtered_bundles)}</div>
                <div class="label">Couriers</div>
            </div>
            <div class="stat-card">
                <div class="value">{total_selected}</div>
                <div class="label">Bundles Mostrados</div>
            </div>
            <div class="stat-card">
                <div class="value">{total_available}</div>
                <div class="label">Bundles Totales</div>
            </div>
        </div>
        
        <div class="content">
            <div class="filter-info">
                <strong>ℹ️ Filtro Aplicado:</strong> Mostrando los <strong>primeros 5</strong> y <strong>últimos 5</strong> bundles de cada courier.
                Esto reduce {total_available - total_selected} archivos mientras mantiene visibilidad del inicio y final de cada ruta.
            </div>
"""
    
    # Agregar secciones por courier
    for courier_id in sorted(filtered_bundles.keys(), key=lambda x: int(x)):
        bundles = filtered_bundles[courier_id]
        total_for_courier = len(couriers_bundles[courier_id])
        
        html_content += f"""
            <div class="courier-section">
                <div class="courier-header">
                    👤 Courier ID: {courier_id} ({len(bundles)}/{total_for_courier} bundles mostrados)
                </div>
                <div class="bundle-grid">
"""
        
        all_bundle_nums = sorted([num for num, _ in bundles])
        first_5 = all_bundle_nums[:5]
        last_5 = all_bundle_nums[-5:] if len(all_bundle_nums) > 5 else []
        
        for bundle_num, map_file in bundles:
            filename = os.path.basename(map_file)
            rel_path = os.path.relpath(map_file, os.path.join(base_path, '..', 'results'))
            
            # Determinar badge
            badge_html = ""
            if bundle_num in first_5:
                badge_html = f'<span class="bundle-badge badge-first">Primero</span>'
            if bundle_num in last_5 and bundle_num not in first_5:
                badge_html = f'<span class="bundle-badge badge-last">Último</span>'
            
            html_content += f"""
                    <div class="bundle-card">
                        <a href="../{rel_path}">
                            <div class="bundle-number">Bundle #{bundle_num}</div>
                            {badge_html}
                            <div class="bundle-filename">{filename}</div>
                            <div class="bundle-link">📍 Abrir Mapa</div>
                        </a>
                    </div>
"""
        
        html_content += """
                </div>
            </div>
"""
    
    html_content += f"""
        </div>
        
        <footer>
            <p>Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p class="timestamp">Proyecto: MDRP-BCS | Política: Rolling Horizon</p>
            <p class="timestamp">Filtro: Primeros 5 + Últimos 5 bundles por courier ({total_available - total_selected} archivos no mostrados)</p>
        </footer>
    </div>
</body>
</html>
"""
    
    # Guardar index
    output_path = os.path.join(
        base_path, '..', 'results', 'maps', 'rh', 'complete_bundles_index.html'
    )
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Index generado: {output_path}")
    print(f"  - {len(filtered_bundles)} couriers")
    print(f"  - {total_selected} bundles mostrados (de {total_available})")
    print(f"  - Reducción: {total_available - total_selected} archivos no mostrados")
    print(f"\nAbre en navegador: results/maps/rh/complete_bundles_index.html")

if __name__ == "__main__":
    generate_complete_bundles_index()
