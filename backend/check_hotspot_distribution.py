#!/usr/bin/env python
"""Check geographic distribution of hotspots for partitioning."""
from app import create_app
from app.models.models import Hotspot

app = create_app()

with app.app_context():
    hotspots = Hotspot.query.all()
    print(f"Total hotspots: {len(hotspots)}")
    
    print("\nHotspot coordinates:")
    for i, h in enumerate(hotspots[:20]):
        print(f"{i+1}. ID: {str(h.hotspot_id)[:8]}... Lat: {h.lat:.6f}, Lng: {h.lng:.6f}")
    
    # Calculate geographic spread
    if hotspots:
        lats = [h.lat for h in hotspots]
        lngs = [h.lng for h in hotspots]
        
        lat_range = max(lats) - min(lats)
        lng_range = max(lngs) - min(lngs)
        
        print(f"\nGeographic spread:")
        print(f"Latitude range: {lat_range:.6f} degrees (~{lat_range * 111:.2f} km)")
        print(f"Longitude range: {lng_range:.6f} degrees (~{lng_range * 111:.2f} km at this latitude)")
        
        # Calculate centroid
        avg_lat = sum(lats) / len(lats)
        avg_lng = sum(lngs) / len(lngs)
        print(f"Centroid: ({avg_lat:.6f}, {avg_lng:.6f})")