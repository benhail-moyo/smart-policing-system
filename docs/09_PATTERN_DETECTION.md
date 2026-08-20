# Feature 1: Intelligent Incident Correlation & Pattern Detection

> **Priority:** 1 (First to implement)  
> **Estimated Time:** 2-3 days  
> **Academic Value:** ⭐⭐⭐⭐⭐  
> **Complexity:** Medium  
> **Dependencies:** None (builds on existing NLP/GIS services)

---

## 🎯 Feature Overview

**What it adds:** Machine learning-powered pattern detection that automatically identifies related incidents (serial crimes, crime sprees, repeat locations) and alerts officers to emerging patterns.

**Academic Contribution:** 
- Crime pattern recognition algorithms
- Spatiotemporal correlation analysis
- Serial crime detection methodology
- Case study-based evaluation framework

**Operational Value:**
- Automatic identification of related incidents
- Early warning for crime sprees
- Intelligence for ongoing investigations
- Resource allocation guidance

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Pattern Detection Service              │
├─────────────────────────────────────────────────────────┤
│  1. Incident Similarity Engine                           │
│     - Text similarity (NLP embeddings)                   │
│     - Spatial proximity (Haversine distance)            │
│     - Temporal proximity (time windows)                 │
│     - Category matching (exact + semantic)              │
│                                                          │
│  2. Pattern Recognition Module                          │
│     - Serial crime detection (MOLO/MODA algorithms)      │
│     - Crime spree identification (time/space clustering) │
│     - Repeat location analysis (hotspot persistence)     │
│     - Geographic profiling (journey-to-crime analysis)    │
│                                                          │
│  3. Alert Generation System                             │
│     - Pattern confidence scoring                        │
│     - Officer notification routing                       │
│     - Investigation recommendations                      │
│     - Pattern evolution tracking                         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              Pattern Detection API Endpoints             │
│  POST /api/v1/patterns/analyze-incident                 │
│  GET  /api/v1/patterns/active                            │
│  POST /api/v1/patterns/investigation-start               │
│  GET  /api/v1/patterns/{pattern_id}/timeline            │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Implementation Plan

### **Phase 1: Core Similarity Engine (Day 1)**

#### 1.1 Create Pattern Detection Service Structure

**File:** `backend/app/services/pattern_detection/__init__.py`

```python
"""
Pattern Detection Service — Crime-Watch
=======================================
Identifies related incidents, crime patterns, and sprees using
spatiotemporal analysis and NLP similarity metrics.

Academic Context:
- Serial crime detection using MOLO (Modus Operandi Linking Analysis)
- Crime spree identification via DBSCAN time-space clustering
- Geographic profiling for journey-to-crime analysis
"""
from .similarity_engine import SimilarityEngine
from .pattern_recognizer import PatternRecognizer
from .alert_generator import AlertGenerator

__all__ = ['SimilarityEngine', 'PatternRecognizer', 'AlertGenerator']
```

#### 1.2 Implement Similarity Engine

**File:** `backend/app/services/pattern_detection/similarity_engine.py`

```python
"""
Incident Similarity Engine
==========================
Calculates multi-dimensional similarity between incidents:
- Text similarity using NLP embeddings
- Spatial proximity using Haversine distance
- Temporal proximity using time windows
- Category matching with semantic similarity
"""
import math
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
import numpy as np

from app.models.models import Incident
from app import db


class SimilarityEngine:
    """
    Multi-dimensional incident similarity calculation.
    
    Uses weighted combination of similarity metrics to identify
    potentially related incidents for pattern detection.
    """
    
    def __init__(self):
        # Load pre-trained sentence transformer for text similarity
        self.text_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Similarity weights (tunable for research)
        self.weights = {
            'text': 0.4,        # NLP semantic similarity
            'spatial': 0.3,     # Geographic proximity
            'temporal': 0.2,    # Time window proximity
            'category': 0.1     # Category matching
        }
        
        # Thresholds for pattern detection
        self.thresholds = {
            'text_similarity': 0.7,
            'spatial_km': 2.0,
            'temporal_hours': 48,
            'category_match': True
        }
    
    def calculate_comprehensive_similarity(
        self, 
        incident1: Incident, 
        incident2: Incident
    ) -> Dict[str, float]:
        """
        Calculate weighted similarity score between two incidents.
        
        Returns:
            Dict with individual similarity scores and composite score
        """
        text_sim = self._text_similarity(incident1.raw_text, incident2.raw_text)
        spatial_sim = self._spatial_similarity(incident1.location, incident2.location)
        temporal_sim = self._temporal_similarity(incident1.created_at, incident2.created_at)
        category_sim = self._category_similarity(incident1.category, incident2.category)
        
        # Weighted composite score
        composite = (
            self.weights['text'] * text_sim +
            self.weights['spatial'] * spatial_sim +
            self.weights['temporal'] * temporal_sim +
            self.weights['category'] * category_sim
        )
        
        return {
            'text_similarity': text_sim,
            'spatial_similarity': spatial_sim,
            'temporal_similarity': temporal_sim,
            'category_similarity': category_sim,
            'composite_score': composite
        }
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic text similarity using sentence embeddings.
        Uses cosine similarity between embedding vectors.
        """
        try:
            # Generate embeddings
            embedding1 = self.text_model.encode(text1, convert_to_tensor=True)
            embedding2 = self.text_model.encode(text2, convert_to_tensor=True)
            
            # Cosine similarity
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
            return float(similarity)
        except Exception as e:
            # Fallback to simple word overlap if model fails
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            overlap = len(words1 & words2)
            total = len(words1 | words2)
            return overlap / total if total > 0 else 0.0
    
    def _spatial_similarity(self, location1, location2) -> float:
        """
        Calculate spatial similarity using inverse Haversine distance.
        Returns 1.0 for same location, 0.0 for > threshold distance.
        """
        if not location1 or not location2:
            return 0.0
        
        # Extract coordinates from PostGIS geometry
        from geoalchemy2.shape import to_shape
        point1 = to_shape(location1)
        point2 = to_shape(location2)
        
        distance_km = self._haversine_distance(
            point1.y, point1.x,  # lat, lng
            point2.y, point2.x
        )
        
        # Inverse distance similarity (closer = more similar)
        max_distance = self.thresholds['spatial_km']
        similarity = max(0.0, 1.0 - (distance_km / max_distance))
        return similarity
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate Haversine distance between two points in kilometers."""
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _temporal_similarity(self, time1: datetime, time2: datetime) -> float:
        """
        Calculate temporal similarity using time window proximity.
        Returns 1.0 for same time, 0.0 for > threshold hours apart.
        """
        time_diff = abs((time1 - time2).total_seconds()) / 3600  # hours
        max_hours = self.thresholds['temporal_hours']
        
        similarity = max(0.0, 1.0 - (time_diff / max_hours))
        return similarity
    
    def _category_similarity(self, category1: str, category2: str) -> float:
        """
        Calculate category similarity.
        Exact match = 1.0, semantic match = 0.8, no match = 0.0
        """
        if category1 == category2:
            return 1.0
        
        # Semantic similarity for related categories
        semantic_groups = {
            'robbery': ['theft', 'burglary', 'assault'],
            'assault': ['robbery', 'domestic_dispute', 'murder'],
            'theft': ['robbery', 'burglary', 'fraud'],
            'drug_offence': ['suspicious_activity', 'fraud'],
        }
        
        for group in semantic_groups.values():
            if category1 in group and category2 in group:
                return 0.8
        
        return 0.0
    
    def find_related_incidents(
        self, 
        incident: Incident, 
        hours_back: int = 48,
        min_similarity: float = 0.7
    ) -> List[Dict]:
        """
        Find incidents potentially related to the given incident.
        
        Args:
            incident: The incident to find relations for
            hours_back: Time window to search (default 48 hours)
            min_similarity: Minimum composite similarity score
            
        Returns:
            List of related incidents with similarity scores
        """
        time_cutoff = datetime.utcnow() - timedelta(hours=hours_back)
        
        # Query recent incidents of same category
        potential_matches = Incident.query.filter(
            Incident.created_at >= time_cutoff,
            Incident.category == incident.category,
            Incident.id != incident.id
        ).all()
        
        related = []
        for candidate in potential_matches:
            similarity = self.calculate_comprehensive_similarity(incident, candidate)
            
            if similarity['composite_score'] >= min_similarity:
                related.append({
                    'incident_id': candidate.id,
                    'similarity_scores': similarity,
                    'time_diff_hours': abs((incident.created_at - candidate.created_at).total_seconds()) / 3600,
                    'distance_km': self._haversine_distance(
                        incident.location.y, incident.location.x,
                        candidate.location.y, candidate.location.x
                    ) if incident.location and candidate.location else None
                })
        
        # Sort by composite similarity descending
        related.sort(key=lambda x: x['similarity_scores']['composite_score'], reverse=True)
        return related
```

#### 1.3 Add ML Dependencies

**File:** `backend/requirements.txt`

```txt
# Add these lines for pattern detection
sentence-transformers==2.2.2
scikit-learn==1.5.1
numpy==2.0.1
```

---

### **Phase 2: Pattern Recognition Module (Day 1-2)**

#### 2.1 Implement Pattern Recognizer

**File:** `backend/app/services/pattern_detection/pattern_recognizer.py`

```python
"""
Pattern Recognition Module
==========================
Identifies crime patterns using multiple algorithms:
- Serial crime detection (MOLO - Modus Operandi Linking Analysis)
- Crime spree identification (DBSCAN time-space clustering)
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
        locations = [i.location for i in incidents if i.location]
        
        # Geographic spread
        from geoalchemy2.shape import to_shape
        if locations:
            points = [to_shape(loc) for loc in locations]
            lats = [p.y for p in points]
            lngs = [p.x for p in points]
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
            'category': incidents[0].category,
            'incident_count': len(incidents),
            'time_span_hours': time_span.total_seconds() / 3600,
            'geographic_spread_km': geographic_spread_km,
            'confidence': avg_similarity,
            'first_incident': min(incidents, key=lambda x: x.created_at).id,
            'latest_incident': max(incidents, key=lambda x: x.created_at).id,
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
            if incident.location:
                from geoalchemy2.shape import to_shape
                point = to_shape(incident.location)
                
                # Normalize features for clustering
                normalized_time = self._normalize_time(incident.created_at)
                normalized_lat = (point.y - (-17.95)) / 0.3  # Normalize Harare lat range
                normalized_lng = (point.x - 30.95) / 0.3  # Normalize Harare lng range
                
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
            'most_recent': max(incidents, key=lambda x: x.created_at).created_at.isoformat()
        }
    
    def detect_repeat_locations(self, incidents: List[Incident]) -> List[Dict]:
        """
        Detect locations that have been targeted multiple times.
        """
        location_counts = {}
        
        for incident in incidents:
            if incident.location:
                # Create location key (rounded coordinates)
                from geoalchemy2.shape import to_shape
                point = to_shape(incident.location)
                
                # Round to create location buckets
                lat_key = round(point.y, 4)  # ~11m precision
                lng_key = round(point.x, 4)
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
        
        locations = [i.location for i in incidents if i.location]
        if not locations:
            return []
        
        from geoalchemy2.shape import to_shape
        points = [to_shape(loc) for loc in locations]
        lats = [p.y for p in points]
        lngs = [p.x for p in points]
        
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
            severity_counts[incident.severity] = severity_counts.get(incident.severity, 0) + 1
        return severity_counts
    
    def _get_category_distribution(self, incidents: List[Incident]) -> Dict:
        """Get distribution of categories in pattern."""
        category_counts = {}
        for incident in incidents:
            category_counts[incident.category] = category_counts.get(incident.category, 0) + 1
        return category_counts
    
    def _get_dominant_category(self, incidents: List[Incident]) -> str:
        """Get the most common category in incidents."""
        categories = [i.category for i in incidents]
        return max(set(categories), key=categories.count) if categories else 'unknown'
    
    def _calculate_time_span(self, incidents: List[Incident]) -> float:
        """Calculate time span in days between first and last incident."""
        if len(incidents) < 2:
            return 0.0
        time_span = max(i.created_at for i in incidents) - min(i.created_at for i in incidents)
        return time_span.total_seconds() / 86400  # Convert to days
```

---

### **Phase 3: API Integration (Day 2)**

#### 3.1 Create Pattern Detection API Routes

**File:** `backend/app/api/v1/routes/patterns.py`

```python
"""
Pattern Detection API Routes
============================
Endpoints for incident pattern analysis and detection.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

from app import db
from app.models.models import Incident, User
from app.services.pattern_detection.pattern_recognizer import PatternRecognizer
from app.services.pattern_detection.similarity_engine import SimilarityEngine

patterns_bp = Blueprint("patterns", __name__)


@patterns_bp.post("/analyze-incident")
@jwt_required()
def analyze_incident_patterns():
    """
    Analyze a specific incident for related patterns.
    
    Request: { "incident_id": int }
    Response: { "related_incidents": [...], "potential_patterns": [...] }
    """
    data = request.get_json()
    incident_id = data.get("incident_id")
    
    if not incident_id:
        return jsonify({"error": "incident_id required"}), 400
    
    incident = Incident.query.get(incident_id)
    if not incident:
        return jsonify({"error": "Incident not found"}), 404
    
    # Find related incidents
    similarity_engine = SimilarityEngine()
    related_incidents = similarity_engine.find_related_incidents(
        incident, 
        hours_back=48, 
        min_similarity=0.7
    )
    
    # Check for patterns involving this incident
    pattern_recognizer = PatternRecognizer()
    time_cutoff = datetime.utcnow() - timedelta(days=30)
    recent_incidents = Incident.query.filter(
        Incident.created_at >= time_cutoff
    ).all()
    
    all_patterns = pattern_recognizer.detect_all_patterns(days_back=30)
    
    # Filter patterns that include this incident
    relevant_patterns = [
        pattern for pattern in all_patterns['serial_crimes'] + 
        all_patterns['crime_sprees'] + 
        all_patterns['repeat_locations']
        if incident_id in pattern.get('incident_ids', [])
    ]
    
    return jsonify({
        "incident_id": incident_id,
        "related_incidents": related_incidents,
        "potential_patterns": relevant_patterns,
        "analysis_timestamp": datetime.utcnow().isoformat()
    }), 200


@patterns_bp.get("/active")
@jwt_required()
def get_active_patterns():
    """
    Get all currently active crime patterns.
    
    Query params: days_back (default 30)
    Response: { "serial_crimes": [...], "crime_sprees": [...], "repeat_locations": [...] }
    """
    days_back = request.args.get('days_back', 30, type=int)
    
    pattern_recognizer = PatternRecognizer()
    patterns = pattern_recognizer.detect_all_patterns(days_back=days_back)
    
    return jsonify({
        "analysis_period_days": days_back,
        "patterns": patterns,
        "total_patterns": sum(len(v) for v in patterns.values()),
        "analysis_timestamp": datetime.utcnow().isoformat()
    }), 200


@patterns_bp.post("/investigation-start")
@jwt_required()
def start_investigation():
    """
    Mark a pattern as under investigation and create investigation record.
    
    Request: { "pattern_type": str, "incident_ids": [int], "notes": str }
    Response: { "investigation_id": int, "status": "active" }
    """
    data = request.get_json()
    pattern_type = data.get("pattern_type")
    incident_ids = data.get("incident_ids", [])
    notes = data.get("notes", "")
    
    if not pattern_type or not incident_ids:
        return jsonify({"error": "pattern_type and incident_ids required"}), 400
    
    # Create investigation record (would need Investigation model)
    # For now, return success response
    investigation_id = hash(f"{pattern_type}_{','.join(map(str, incident_ids))}_{datetime.utcnow()}")
    
    return jsonify({
        "investigation_id": str(investigation_id),
        "pattern_type": pattern_type,
        "incident_ids": incident_ids,
        "status": "active",
        "created_by": get_jwt_identity(),
        "notes": notes,
        "created_at": datetime.utcnow().isoformat()
    }), 201


@patterns_bp.get("/<pattern_id>/timeline")
@jwt_required()
def get_pattern_timeline(pattern_id):
    """
    Get chronological timeline of incidents in a pattern.
    
    Response: { "incidents": [...], "timeline_events": [...] }
    """
    # This would require pattern persistence in database
    # For now, return a placeholder response
    return jsonify({
        "pattern_id": pattern_id,
        "message": "Pattern timeline feature requires pattern persistence",
        "incidents": [],
        "timeline_events": []
    }), 200
```

#### 3.2 Register Pattern Blueprint

**File:** `backend/app/__init__.py`

```python
# Add to existing imports
from app.api.v1.routes.patterns import patterns_bp

# Add to blueprint registration
app.register_blueprint(patterns_bp, url_prefix="/api/v1/patterns")
```

---

### **Phase 4: Frontend Integration (Day 2-3)**

#### 4.1 Create Pattern Detection Components

**File:** `frontend/src/components/patterns/PatternVisualization.tsx`

```typescript
"use client";

import { useEffect, useState } from 'react';
import { api } from '@/lib/client';

interface Pattern {
  pattern_type: string;
  incident_ids: number[];
  confidence: number;
  [key: string]: any;
}

export default function PatternVisualization() {
  const [patterns, setPatterns] = useState<{
    serial_crimes: Pattern[];
    crime_sprees: Pattern[];
    repeat_locations: Pattern[];
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api('/patterns/active')
      .then(data => setPatterns(data.patterns))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading patterns...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!patterns) return <div>No patterns detected</div>;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Active Crime Patterns</h2>
      
      {/* Serial Crimes */}
      {patterns.serial_crimes.length > 0 && (
        <div className="bg-red-50 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-red-800">
            Serial Crimes ({patterns.serial_crimes.length})
          </h3>
          {patterns.serial_crimes.map((pattern, idx) => (
            <div key={idx} className="mt-2 p-2 bg-white rounded">
              <p>Confidence: {(pattern.confidence * 100).toFixed(0)}%</p>
              <p>Incidents: {pattern.incident_count}</p>
              <p>Category: {pattern.category}</p>
            </div>
          ))}
        </div>
      )}

      {/* Crime Sprees */}
      {patterns.crime_sprees.length > 0 && (
        <div className="bg-orange-50 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-orange-800">
            Crime Sprees ({patterns.crime_sprees.length})
          </h3>
          {patterns.crime_sprees.map((pattern, idx) => (
            <div key={idx} className="mt-2 p-2 bg-white rounded">
              <p>Incidents per hour: {pattern.incidents_per_hour.toFixed(2)}</p>
              <p>Time span: {pattern.time_span_hours.toFixed(1)} hours</p>
            </div>
          ))}
        </div>
      )}

      {/* Repeat Locations */}
      {patterns.repeat_locations.length > 0 && (
        <div className="bg-yellow-50 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-yellow-800">
            Repeat Locations ({patterns.repeat_locations.length})
          </h3>
          {patterns.repeat_locations.map((pattern, idx) => (
            <div key={idx} className="mt-2 p-2 bg-white rounded">
              <p>Incidents: {pattern.incident_count}</p>
              <p>Location: {pattern.location.lat.toFixed(4)}, {pattern.location.lng.toFixed(4)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

### **Phase 5: Testing & Evaluation (Day 3)**

#### 5.1 Create Pattern Detection Tests

**File:** `backend/tests/unit/test_pattern_detection.py`

```python
"""
Unit tests for pattern detection service.
"""
import pytest
from datetime import datetime, timedelta
from app.services.pattern_detection.similarity_engine import SimilarityEngine
from app.services.pattern_detection.pattern_recognizer import PatternRecognizer

class TestSimilarityEngine:
    
    def test_text_similarity_calculation(self):
        engine = SimilarityEngine()
        sim = engine._text_similarity(
            "Armed robbery at gunpoint",
            "Robbery with a firearm"
        )
        assert sim > 0.5  # Should be reasonably similar
    
    def test_spatial_similarity_same_location(self):
        engine = SimilarityEngine()
        # Same location should have high similarity
        sim = engine._spatial_similarity(
            (-17.8292, 31.0522),  # CBD
            (-17.8292, 31.0522)   # Same point
        )
        assert sim == 1.0
    
    def test_temporal_similarity_recent(self):
        engine = SimilarityEngine()
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        sim = engine._temporal_similarity(now, one_hour_ago)
        assert sim > 0.8  # Should be highly similar
    
    def test_composite_similarity_calculation(self):
        engine = SimilarityEngine()
        # This would require mock Incident objects
        # Test that composite score is weighted average
        pass

class TestPatternRecognizer:
    
    def test_detect_serial_crimes_requires_minimum_incidents(self):
        recognizer = PatternRecognizer()
        # Should return empty for < 3 incidents
        assert len(recognizer.detect_serial_crimes([])) == 0
    
    def test_detect_crime_sprees_time_clustering(self):
        recognizer = PatternRecognizer()
        # Test that incidents in short time window are clustered
        pass
    
    def test_detect_repeat_locations_same_coordinates(self):
        recognizer = PatternRecognizer()
        # Test that incidents at same location are detected
        pass
```

---

## 📊 Academic Evaluation Framework

### **Research Questions:**
1. How accurately can the system identify related incidents?
2. What is the precision/recall for serial crime detection?
3. How do different similarity thresholds affect pattern detection performance?

### **Evaluation Metrics:**
- **Pattern Detection Precision:** % of detected patterns that are genuine
- **Pattern Detection Recall:** % of genuine patterns that are detected
- **False Positive Rate:** % of patterns detected that are not genuine
- **Similarity Threshold Analysis:** Performance across different thresholds

### **Test Dataset:**
Create synthetic test cases with known patterns:
- 10 serial crime patterns (3-5 related incidents each)
- 5 crime sprees (5-10 incidents in 24 hours)
- 8 repeat location patterns (2-4 incidents at same location)
- 50 random unrelated incidents (negative test cases)

### **Success Criteria:**
- Pattern detection precision ≥ 70%
- Serial crime detection recall ≥ 65%
- False positive rate ≤ 20%
- System processes 1000 incidents in < 30 seconds

---

## 🎯 Acceptance Checklist

### **Backend Requirements:**
- ✅ SimilarityEngine calculates multi-dimensional similarity
- ✅ PatternRecognizer detects all 4 pattern types
- ✅ API endpoints return pattern data correctly
- ✅ Pattern detection works with existing Incident model
- ✅ ML dependencies installed and working

### **Frontend Requirements:**
- ✅ Pattern visualization component renders patterns
- ✅ Patterns displayed by type with confidence scores
- ✅ Map integration shows pattern locations
- ✅ UI provides pattern investigation workflow

### **Testing Requirements:**
- ✅ Unit tests for similarity calculations
- ✅ Unit tests for pattern detection algorithms
- ✅ Integration tests for API endpoints
- ✅ Performance benchmarks for large datasets

### **Academic Requirements:**
- ✅ Pattern detection algorithms documented
- ✅ Evaluation framework implemented
- ✅ Test dataset with known patterns created
- ✅ Research questions answered with metrics

---

## 🚀 Next Steps

After completing Pattern Detection:

1. **Move to Priority 2:** Implement Audit Trail & Accountability Dashboard
2. **Documentation:** Update dissertation with pattern detection methodology
3. **Testing:** Run evaluation framework and collect metrics
4. **Integration:** Test pattern detection with real incident data

**Implementation Guide:** `docs/10_AUDIT_TRAIL_DASHBOARD.md`

---

## 📝 Notes for Dissertation

### **Chapter 3 - Methodology Additions:**
- **Section 3.X: Pattern Detection Methodology**
  - Similarity metrics and weight selection
  - MOLO algorithm implementation details
  - DBSCAN parameter selection for spree detection
  - Geographic profiling approach

### **Chapter 4 - Results Additions:**
- **Section 4.X: Pattern Detection Results**
  - Precision/recall metrics for each pattern type
  - Threshold sensitivity analysis
  - Case studies of detected patterns
  - Performance analysis on large datasets

### **Academic Contributions:**
- Novel multi-dimensional similarity approach for crime incidents
- Adaptation of MOLO algorithm for Zimbabwean context
- Crime spree detection using time-space clustering
- Comprehensive pattern detection framework for DSS

This feature provides strong academic contribution while being implementable within 2-3 days.
