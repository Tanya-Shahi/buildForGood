import osmnx as ox
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def download_spatial_priors(city_name="Guwahati, Assam, India"):
    print(f"🌍 Downloading walking network for {city_name} from OpenStreetMap...")
    # Pull the graph (this might take 1-3 minutes depending on your internet)
    G = ox.graph_from_place(city_name, network_type='walk')
    
    # Extract the nodes (intersections/points) and edges (streets)
    nodes, edges = ox.graph_to_gdfs(G)
    
    print(f"✅ Successfully downloaded {len(nodes)} street nodes.")
    return nodes, edges

def generate_synthetic_dataset(nodes, num_records=100000):
    print(f"🧬 Generating {num_records} synthetic incident records...")
    
    data = []
    node_ids = nodes.index.tolist()
    
    # We will simulate data over the last 30 days
    start_date = datetime.now() - timedelta(days=30)
    
    for _ in range(num_records):
        # 1. Pick a random street node
        node_id = random.choice(node_ids)
        node = nodes.loc[node_id]
        
        # 2. Simulate temporal data
        random_days = random.randint(0, 30)
        random_hours = random.randint(0, 23)
        random_minutes = random.randint(0, 59)
        incident_time = start_date + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
        
        hour_of_day = incident_time.hour
        is_weekend = 1 if incident_time.weekday() >= 5 else 0
        
        # 3. Simulate Spatial Features (Since OSM often lacks 'lit' tags in India, we bootstrap them)
        # We assign a 30% chance a street is unlit to simulate infrastructure gaps
        street_lit = 0 if random.random() < 0.3 else 1
        
        # Simulate commercial density (0.0 to 1.0)
        commercial_density = round(random.uniform(0.1, 0.9), 2)
        
        # 4. The Logic Engine: Calculate Target Risk Score based on environment
        base_risk = 2.0
        
        # Nighttime penalty (10 PM to 4 AM)
        if hour_of_day >= 22 or hour_of_day <= 4:
            base_risk += 3.0
            
        # Unlit penalty (compounds heavily at night)
        if street_lit == 0:
            base_risk += 2.0
            if hour_of_day >= 22 or hour_of_day <= 4:
                base_risk += 1.5 # The "Dark Alley" multiplier
                
        # Commercial safety buffer (eyes on the street)
        if 8 <= hour_of_day <= 21:
            base_risk -= (commercial_density * 2) 
            
        # Weekend anomaly (slight bump in late-night incidents)
        if is_weekend and (hour_of_day >= 23 or hour_of_day <= 3):
            base_risk += 1.0
            
        # Add some random noise so the AI actually has to learn a distribution
        noise = np.random.normal(0, 0.5)
        target_risk_score = min(max(base_risk + noise, 0.0), 10.0) # Clamp between 0-10
        
        # 5. Compile the row
        data.append({
            "latitude": node.y,
            "longitude": node.x,
            "hour_of_day": hour_of_day,
            "is_weekend": is_weekend,
            "street_lit": street_lit,
            "commercial_density": commercial_density,
            "recent_incidents_count": random.randint(0, 5), # Simulating recent crowd reports
            "target_risk_score": round(target_risk_score, 2)
        })

    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    # Configure osmnx to use a local cache so if you run this twice, it's instant
    ox.settings.use_cache = True
    
    # Execute the pipeline
    nodes, edges = download_spatial_priors()
    synthetic_df = generate_synthetic_dataset(nodes, num_records=100000)
    
    # Save to CSV
    output_path = "synthetic_risk_data.csv"
    synthetic_df.to_csv(output_path, index=False)
    
    print(f"🎯 Success! Dataset saved to backend/scripts/{output_path}")
    print(synthetic_df.head())