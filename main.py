import sys
import os
import math
import asyncio
import json
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# Import from local db module
from db import execute_query, execute_single_query, init_db, close_db

class TPH:
    def __init__(self, id: int, nomor: int, dept_abbr: str, divisi_abbr: str, 
                 blok_kode: str, latitude: float, longitude: float, kode_tph: str = None):
        self.id = id
        self.nomor = nomor
        self.dept_abbr = dept_abbr
        self.divisi_abbr = divisi_abbr
        self.blok_kode = blok_kode
        # Ensure lat and lng are float values
        self.lat = float(latitude) if latitude is not None else 0.0
        self.lng = float(longitude) if longitude is not None else 0.0
        self.kode_tph = kode_tph
    
    def __str__(self):
        return f"TPH {self.nomor}: {self.kode_tph} ({self.lat}, {self.lng})"
    
    def to_dict(self):
        return {
            "id": self.id,
            "nomor": self.nomor,
            "tph": self.kode_tph,
            "dept_abbr": self.dept_abbr,
            "divisi_abbr": self.divisi_abbr,
            "lat": self.lat,
            "lon": self.lng
        }

def calculate_distance(point1: TPH, point2: TPH) -> float:
    """
    Calculate Euclidean distance between two points
    For more accurate geographic distance, consider using Haversine formula
    """
    return math.sqrt((point1.lat - point2.lat)**2 + (point1.lng - point2.lng)**2)

def haversine_distance(point1: TPH, point2: TPH) -> float:
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    try:
        # Convert decimal degrees to radians
        lat1, lon1 = math.radians(point1.lat), math.radians(point1.lng)
        lat2, lon2 = math.radians(point2.lat), math.radians(point2.lng)
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r
    except Exception as e:
        print(f"Error calculating distance between {point1} and {point2}: {str(e)}")
        # Return a large value as fallback
        return 999999.9

async def get_tph_data(dept_abbr: Optional[str] = None, 
                       divisi_abbr: Optional[str] = None, 
                       blok_kode: Optional[str] = None) -> List[TPH]:
    """Retrieve TPH data from database with optional filters"""
    query = """
        SELECT id, nomor, dept_abbr, divisi_abbr, blok_kode, 
               lat, lon as lng, kode_tph 
        FROM tph 
        WHERE status = 1
        AND lat IS NOT NULL AND lat != ''
        AND lon IS NOT NULL AND lon != ''
    """
    params = []
    
    if dept_abbr:
        query += " AND dept_abbr = %s"
        params.append(dept_abbr)
        
    if divisi_abbr:
        query += " AND divisi_abbr LIKE %s"
        params.append(f"%{divisi_abbr}%")
    
    if blok_kode:
        query += " AND blok_kode LIKE %s"
        params.append(f"%{blok_kode}%")
    
    query += " ORDER BY nomor ASC"
    
    results = await execute_query(query, params)
    
    tph_list = []
    for row in results:
        try:
            # Skip rows with empty lat/lng
            if not row['lat'] or not row['lng']:
                print(f"Skipping TPH {row['id']} due to missing coordinates")
                continue
                
            tph = TPH(
                id=row['id'],
                nomor=row['nomor'],
                dept_abbr=row['dept_abbr'],
                divisi_abbr=row['divisi_abbr'],
                blok_kode=row['blok_kode'],
                latitude=row['lat'],
                longitude=row['lng'],
                kode_tph=row['kode_tph']
            )
            tph_list.append(tph)
        except Exception as e:
            print(f"Error processing TPH data row {row['id']}: {str(e)}")
            # Skip points with invalid data
    
    return tph_list

def nearest_neighbor_algorithm(points: List[TPH], start_index: int = 0) -> List[TPH]:
    """
    Implement Nearest Neighbor algorithm to reorder points
    based on proximity
    """
    if not points:
        return []
    
    # Start with the point at the given index
    ordered_points = [points[start_index]]
    unvisited = points.copy()
    unvisited.pop(start_index)
    
    # While there are unvisited points
    while unvisited:
        current_point = ordered_points[-1]
        
        # Find nearest unvisited point
        nearest_point = None
        min_distance = float('inf')
        nearest_idx = -1
        
        for i, point in enumerate(unvisited):
            try:
                distance = haversine_distance(current_point, point)
                if distance < min_distance:
                    min_distance = distance
                    nearest_point = point
                    nearest_idx = i
            except Exception as e:
                print(f"Error calculating distance: {str(e)}")
        
        # Add the nearest point to our ordered list
        if nearest_point and nearest_idx >= 0:
            ordered_points.append(nearest_point)
            unvisited.pop(nearest_idx)
        else:
            print("Warning: Could not find nearest point, breaking loop")
            # Add remaining points in original order
            ordered_points.extend(unvisited)
            break
    
    return ordered_points

async def update_tph_order(ordered_tph: List[TPH]) -> None:
    """Update the display order of TPH in the database"""
    for new_order, tph in enumerate(ordered_tph, 1):
        query = "UPDATE tph SET display_order = %s WHERE id = %s"
        await execute_query(query, (new_order, tph.id))
    print(f"Successfully updated display order for {len(ordered_tph)} TPH points")

async def update_tph_numbers(ordered_tph: List[TPH]) -> None:
    """Update the actual TPH numbers to match the optimized route order"""
    for new_number, tph in enumerate(ordered_tph, 1):
        query = "UPDATE tph SET nomor = %s WHERE id = %s"
        await execute_query(query, (new_number, tph.id))
    print(f"Successfully renumbered {len(ordered_tph)} TPH points to match route order")

def create_kml(ordered_tph: List[TPH], output_file: str):
    """Generate KML file for Google Earth visualization"""
    if not ordered_tph:
        print("No TPH points to generate KML")
        return

    # Get location info for the KML title
    dept = ordered_tph[0].dept_abbr
    div = ordered_tph[0].divisi_abbr
    blk = ordered_tph[0].blok_kode
    
    # Create KML file
    with open(output_file, 'w') as f:
        # Header
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
        f.write('  <Document>\n')
        f.write(f'    <name>TPH Route - {dept} {div} {blk}</name>\n')
        f.write('    <description>Optimized TPH Route using Nearest Neighbor Algorithm</description>\n')
        
        # Styles
        f.write('    <Style id="tphStyle">\n')
        f.write('      <IconStyle>\n')
        f.write('        <Icon>\n')
        f.write('          <href>http://maps.google.com/mapfiles/kml/paddle/grn-circle.png</href>\n')
        f.write('        </Icon>\n')
        f.write('      </IconStyle>\n')
        f.write('      <LabelStyle>\n')
        f.write('        <scale>1.0</scale>\n')
        f.write('      </LabelStyle>\n')
        f.write('    </Style>\n')
        
        f.write('    <Style id="pathStyle">\n')
        f.write('      <LineStyle>\n')
        f.write('        <color>ff00ffff</color>\n')
        f.write('        <width>4</width>\n')
        f.write('      </LineStyle>\n')
        f.write('    </Style>\n')
        
        # Place markers for each TPH point
        for i, tph in enumerate(ordered_tph, 1):
            f.write('    <Placemark>\n')
            f.write(f'      <name>{i}. TPH {tph.nomor}</name>\n')
            f.write('      <description>\n')
            f.write(f'ID: {tph.id}\n')
            f.write(f'KodeTph: {tph.kode_tph}\n')
            f.write(f'Coordinates: {tph.lat}, {tph.lng}\n')
            f.write('      </description>\n')
            f.write('      <styleUrl>#tphStyle</styleUrl>\n')
            f.write('      <Point>\n')
            f.write(f'        <coordinates>{tph.lng},{tph.lat},0</coordinates>\n')
            f.write('      </Point>\n')
            f.write('    </Placemark>\n')
        
        # Path connecting all TPH points
        f.write('    <Placemark>\n')
        f.write('      <name>TPH Route</name>\n')
        f.write('      <description>Optimized route through all TPH points</description>\n')
        f.write('      <styleUrl>#pathStyle</styleUrl>\n')
        f.write('      <LineString>\n')
        f.write('        <tessellate>1</tessellate>\n')
        f.write('        <coordinates>\n')
        
        # Add coordinates for each point on the path
        for tph in ordered_tph:
            f.write(f'          {tph.lng},{tph.lat},0\n')
        
        f.write('        </coordinates>\n')
        f.write('      </LineString>\n')
        f.write('    </Placemark>\n')
        
        # Close document
        f.write('  </Document>\n')
        f.write('</kml>\n')
    
    print(f"KML file generated: {output_file}")

async def main():
    """Main function to reorder TPH points"""
    try:
        await init_db()
        
        # Get filter parameters
        dept_abbr = input("Enter dept_abbr (press Enter for all): ").strip() or None
        divisi_abbr = input("Enter divisi_abbr (press Enter for all): ").strip() or None
        blok_kode = input("Enter blok_kode (press Enter for all): ").strip() or None
        
        print(f"Retrieving TPH data for filters: dept_abbr={dept_abbr}, divisi_abbr={divisi_abbr}, blok_kode={blok_kode}")
        tph_data = await get_tph_data(dept_abbr, divisi_abbr, blok_kode)
        
        if not tph_data:
            print("No TPH data found with the specified filters")
            return
        
        print(f"Found {len(tph_data)} TPH points")
        
        # Choose starting point (default: first TPH in the list)
        start_index = 0
        print(f"Starting reordering from {tph_data[start_index]}")
        
        # Apply Nearest Neighbor algorithm
        ordered_tph = nearest_neighbor_algorithm(tph_data, start_index)
        
        print("\nReordered TPH points (from nearest to farthest):")
        
        # Create a list of dictionaries for JSON output
        result = []
        for i, tph in enumerate(ordered_tph, 1):
            result.append({
                "new_order": i,
                "id": tph.id,
                "nomor": tph.nomor,
                "tph": tph.kode_tph,
                "dept_abbr": tph.dept_abbr,
                "divisi_abbr": tph.divisi_abbr,
                "lat": tph.lat,
                "lon": tph.lng
            })
            
        # Print formatted JSON
        print(json.dumps(result, indent=2))
        
        # Export to KML
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filter_text = f"{dept_abbr or 'all'}_{divisi_abbr or 'all'}_{blok_kode or 'all'}"
        kml_file = f"tph_route_{filter_text}_{timestamp}.kml"
        create_kml(ordered_tph, kml_file)
        
        # Ask user if they want to update the TPH numbers
        update_option = input("\nDo you want to:\n1. Update display order only\n2. Renumber TPH points to match route order\n3. Skip database updates\nEnter option (1/2/3): ").strip()
        
        if update_option == "1":
            await update_tph_order(ordered_tph)
        elif update_option == "2":
            await update_tph_numbers(ordered_tph)
        else:
            print("Skipping database updates.")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())
