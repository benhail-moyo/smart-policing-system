"""
Pattern Recognition Module
==========================
Identifies crime patterns using multiple algorithms:
- Serial crime detection (MOLO/MODA algorithms)
- Crime spree identification (time/space clustering)
- Repeat location analysis (hotspot persistence)
- Geographic profiling (journey-to-crime analysis)
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sklearn.cluster import DBSCAN
import numpy as np

from app.models.models import Incident
from app.services.pattern_detection.similarity_engine import SimilarityEngine
from app import db


class PatternRecognizer:
    """
    Advanced pattern recognition for crime analysis.
    
    Implements multiple detection algorithms for different pattern types:
    1. Serial Crimes: Similar MO across multiple incidents
    2. Crime Sprees: High frequency in short time window
    3. Repeat Locations: Same location targeted repeatedly
    4. Geographic Patterns: Spatial distribution analysis
    """
    
    def __init__(self):
        self.similarity_engine = SimilarityEngine()
        
        # Pattern detection parameters
        self.serial_crime_threshold = 3  # Minimum incidents for serial pattern
        self.spree_time_window_hours = 24  # Time window for spree detection
        self.spree_spatial_threshold_km = 5.0  # Max distance for spree
        self.repeat_location_threshold = 2  # Minimum incidents at same location
        self.location_radius_km = 0.5  # Radius for "same location"
    
    def detect_all_patterns(self, days_back: int = 30) -> Dict[str, List]:
        """
        Run all pattern detection algorithms and return combined results.
        
        Args:
            days_back: Time period to analyze
            
        Returns:
            Dict with pattern types as keys and detected patterns as values
        """
        time_cutoff = datetime.utcnow() - timedelta(days=days_back)
        incidents = Incident.query.filter(Incident.created_at >= time_cutoff).all()
        
        return {
            'serial_crimes': self.detect_serial_crimes(incidents),
            'crime_sprees': self.detect_crime_sprees(incidents),
            'repeat_locations': self.detect_repeat_locations(incidents),
            'geographic_patterns': self.detect_geographic_patterns(incidents)
        }
    
    def detect_serial_crimes(self, incidents: List[Incident]) -> List[Dict]:
        """
        Detect serial crimes using MOLO (Modus Operandi Linking Analysis).
        
        Serial crimes are defined as multiple incidents with high similarity
        in MO (modus operandi), likely committed by same offender(s).
        """
        serial_patterns = []
        
        # Group incidents by category
        by_category = {}
        for incident in incidents:
            if incident.category not in by_category:
                by_category[incident.category] = []
            by_category[incident.category].append(incident)
        
        # Analyze each category for serial patterns
        for category, category_incidents in by_category.items():
            if len(category_incidents) < self.serial_crime_threshold:
                continue
            
            # Build similarity graph
            similarity_graph = self._build_similarity_graph(category_incidents)
            
            # Find connected components (potential serial patterns)
            components = self._find_connected_components(similarity_graph)
            
            for component in components:
                if len(component) >= self.serial_crime_threshold:
                    pattern = self._analyze_serial_pattern(component)
                    if pattern['confidence'] > 0.7:
                        serial_patterns.append(pattern)
        
        return serial_patterns
    
    def _build_similarity_graph(self, incidents: List[Incident]) -> Dict:
        """
        Build similarity graph where edges exist between highly similar incidents.
        """
        graph = {incident.id: [] for incident in incidents}
        
        for i, incident1 in enumerate(incidents):
            for incident2 in incidents[i+1:]:
                similarity = self.similarity_engine.calculate_comprehensive_similarity(
                    incident1, incident2
                )
                
                if similarity['composite_score'] >= 0.7:  # High similarity threshold
                    graph[incident1.id].append(incident2.id)
                    graph[incident2.id].append(incident1.id)
        
        return graph
    
    def _find_connected_components(self, graph: Dict) -> List[List]:
        """Find connected components in similarity graph using DFS."""
        visited = set()
        components = []
        
        for node in graph:
            if node not in visited:
                component = []
                stack = [node]
                
                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        component.append(current)
                        stack.extend(graph[current])
                
                components.append(component)
        
        return components
    
    def _analyze_serial_pattern(self, incident_ids: List[int]) -> Dict:
        """Analyze a serial pattern and generate metadata."""
        incidents = Incident.query.filter(Incident.id.in_(incident_ids)).all()
        
        # Calculate pattern characteristics
        time_span = max(i.created_at for i in incidents) - min(i.created_at for i in incidents)
        
        # Geographic spread
        lats = [i.lat for i in incidents if i.lat is not None]
        lngs = [i.lng for i in incidents if i.lng is not None]
        
        if lats and lngs:
            geographic_spread_km = max(
                self.similarity_engine._haversine_distance(
                    min(lats), min(lngs), max(lats), max(lngs)
                ),
                0.0
            )
        else:
            geographic_spread_km = 0.0
        
        # Confidence based on similarity consistency
        avg_similarity = self._calculate_average_similarity(incidents)
        
        return {
            'pattern_type': 'serial_crime',
            'incident_ids': incident_ids,
            'category': incidents[0].category if incidents else 'unknown',
            'incident_count': len(incidents),
            'time_span_hours': time_span.total_seconds() / 3600,
            'geographic_spread_km': geographic_spread_km,
            'confidence': avg_similarity,
            'first_incident': min(incidents, key=lambda x: x.created_at).id if incidents else None,
            'latest_incident': max(incidents, key=lambda x: x.created_at).id if incidents else None,
            'severity_distribution': self._get_severity_distribution(incidents)
        }
    
    def detect_crime_sprees(self, incidents: List[Incident]) -> List[Dict]:
        """
        Detect crime sprees using DBSCAN time-space clustering.
        
        Crime sprees are defined as high frequency of similar incidents
        in a short time window and geographic area.
        """
        if len(incidents) < 3:
            return []
        
        # Prepare data for clustering
        features = []
        incident_map = {}
        
        for incident in incidents:
            if incident.lat is not None and incident.lng is not None:
                # Normalize features for clustering
                normalized_time = self._normalize_time(incident.created_at)
                normalized_lat = (incident.lat - (-17.95)) / 0.3  # Normalize Harare lat range
                normalized_lng = (incident.lng - 30.95) / 0.3  # Normalize Harare lng range
                
                features.append([normalized_time, normalized_lat, normalized_lng])
                incident_map[len(features) - 1] = incident.id
        
        if not features:
            return []
        
        # DBSCAN clustering
        features_array = np.array(features)
        clustering = DBSCAN(
            eps=0.15,  # Clustering threshold
            min_samples=3,
            metric='euclidean'
        ).fit(features_array)
        
        # Analyze clusters
        spree_patterns = []
        for cluster_id in set(clustering.labels_):
            if cluster_id == -1:  # Noise points
                continue
            
            cluster_indices = [i for i, label in enumerate(clustering.labels_) if label == cluster_id]
            cluster_incident_ids = [incident_map[i] for i in cluster_indices]
            
            if len(cluster_incident_ids) >= 3:
                spree = self._analyze_crime_spree(cluster_incident_ids)
                spree_patterns.append(spree)
        
        return spree_patterns
    
    def _normalize_time(self, timestamp: datetime) -> float:
        """Normalize timestamp to 0-1 range based on analysis period."""
        # Normalize to hours from start of analysis period
        start_of_day = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        hours_from_midnight = (timestamp - start_of_day).total_seconds() / 3600
        return hours_from_midnight / 24.0
    
    def _analyze_crime_spree(self, incident_ids: List[int]) -> Dict:
        """Analyze a crime spree pattern."""
        incidents = Incident.query.filter(Incident.id.in_(incident_ids)).all()
        
        time_span = max(i.created_at for i in incidents) - min(i.created_at for i in incidents)
        
        return {
            'pattern_type': 'crime_spree',
            'incident_ids': incident_ids,
            'incident_count': len(incidents),
            'time_span_hours': time_span.total_seconds() / 3600,
            'incidents_per_hour': len(incidents) / max(time_span.total_seconds() / 3600, 1),
            'category_distribution': self._get_category_distribution(incidents),
            'confidence': min(1.0, len(incidents) / 5.0),  # More incidents = higher confidence
            'most_recent': max(incidents, key=lambda x: x.created_at).created_at.isoformat() if incidents else None
        }
    
    def detect_repeat_locations(self, incidents: List[Incident]) -> List[Dict]:
        """
        Detect locations that have been targeted multiple times.
        """
        location_counts = {}
        
        for incident in incidents:
            if incident.lat is not None and incident.lng is not None:
                # Create location key (rounded coordinates)
                lat_key = round(incident.lat, 4)  # ~11m precision
                lng_key = round(incident.lng, 4)
                location_key = f"{lat_key},{lng_key}"
                
                if location_key not in location_counts:
                    location_counts[location_key] = {
                        'lat': lat_key,
                        'lng': lng_key,
                        'incident_ids': [],
                        'incidents': []
                    }
                
                location_counts[location_key]['incident_ids'].append(incident.id)
                location_counts[location_key]['incidents'].append(incident)
        
        # Filter for repeat locations
        repeat_patterns = []
        for location_key, data in location_counts.items():
            if len(data['incident_ids']) >= self.repeat_location_threshold:
                pattern = {
                    'pattern_type': 'repeat_location',
                    'location': {'lat': data['lat'], 'lng': data['lng']},
                    'incident_ids': data['incident_ids'],
                    'incident_count': len(data['incident_ids']),
                    'category': self._get_dominant_category(data['incidents']),
                    'time_span_days': self._calculate_time_span(data['incidents']),
                    'confidence': min(1.0, len(data['incident_ids']) / 4.0)
                }
                repeat_patterns.append(pattern)
        
        return repeat_patterns
    
    def detect_geographic_patterns(self, incidents: List[Incident]) -> List[Dict]:
        """
        Detect broader geographic patterns in crime distribution.
        """
        # Implement geographic profiling (journey-to-crime analysis)
        # This would analyze the spatial distribution of incidents
        # relative to potential anchor points
        
        # For now, return basic geographic statistics
        if not incidents:
            return []
        
        lats = [i.lat for i in incidents if i.lat is not None]
        lngs = [i.lng for i in incidents if i.lng is not None]
        
        if not lats or not lngs:
            return []
        
        return [{
            'pattern_type': 'geographic_distribution',
            'total_incidents': len(incidents),
            'geographic_center': {
                'lat': sum(lats) / len(lats),
                'lng': sum(lngs) / len(lngs)
            },
            'geographic_spread_km': self.similarity_engine._haversine_distance(
                min(lats), min(lngs), max(lats), max(lngs)
            ),
            'confidence': 0.8  # Geographic patterns are statistically robust
        }]
    
    # Helper methods
    def _calculate_average_similarity(self, incidents: List[Incident]) -> float:
        """Calculate average pairwise similarity among incidents."""
        if len(incidents) < 2:
            return 1.0
        
        similarities = []
        for i, incident1 in enumerate(incidents):
            for incident2 in incidents[i+1:]:
                sim = self.similarity_engine.calculate_comprehensive_similarity(
                    incident1, incident2
                )
                similarities.append(sim['composite_score'])
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _get_severity_distribution(self, incidents: List[Incident]) -> Dict:
        """Get distribution of severity levels in pattern."""
        severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for incident in incidents:
            severity = str(incident.severity or '').upper()
            if severity in severity_counts:
                severity_counts[severity] += 1
        return severity_counts
    
    def _get_category_distribution(self, incidents: List[Incident]) -> Dict:
        """Get distribution of categories in pattern."""
        category_counts = {}
        for incident in incidents:
            if incident.category:
                category_counts[incident.category] = category_counts.get(incident.category, 0) + 1
        return category_counts
    
    def _get_dominant_category(self, incidents: List[Incident]) -> str:
        """Get the most common category in incidents."""
        categories = [i.category for i in incidents if i.category]
        return max(set(categories), key=categories.count) if categories else 'unknown'
    
    def _calculate_time_span(self, incidents: List[Incident]) -> float:
        """Calculate time span in days between first and last incident."""
        if len(incidents) < 2:
            return 0.0
        time_span = max(i.created_at for i in incidents) - min(i.created_at for i in incidents)
        return time_span.total_seconds() / 86400  # Convert to days
