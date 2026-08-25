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
        spatial_sim = self._spatial_similarity(
            (incident1.lat, incident1.lng), 
            (incident2.lat, incident2.lng)
        )
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
        Calculate semantic text similarity using word overlap and token matching.
        Uses Jaccard similarity between token sets.
        """
        try:
            # Tokenize and normalize
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            # Remove common stop words
            stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'at', 'in', 'on', 'by', 'for', 'with', 'to', 'of'}
            words1 = words1 - stop_words
            words2 = words2 - stop_words
            
            # Jaccard similarity
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            
            return intersection / union if union > 0 else 0.0
        except Exception as e:
            # Fallback to simple word overlap if processing fails
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            overlap = len(words1 & words2)
            total = len(words1 | words2)
            return overlap / total if total > 0 else 0.0
    
    def _spatial_similarity(self, location1: Tuple[float, float], location2: Tuple[float, float]) -> float:
        """
        Calculate spatial similarity using inverse Haversine distance.
        Returns 1.0 for same location, 0.0 for > threshold distance.
        """
        if not location1 or not location2:
            return 0.0
        
        lat1, lng1 = location1
        lat2, lng2 = location2
        
        # Handle None values
        if lat1 is None or lng1 is None or lat2 is None or lng2 is None:
            return 0.0
        
        distance_km = self._haversine_distance(lat1, lng1, lat2, lng2)
        
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
        if not time1 or not time2:
            return 0.0
        
        time_diff = abs((time1 - time2).total_seconds()) / 3600  # hours
        max_hours = self.thresholds['temporal_hours']
        
        similarity = max(0.0, 1.0 - (time_diff / max_hours))
        return similarity
    
    def _category_similarity(self, category1: str, category2: str) -> float:
        """
        Calculate category similarity.
        Exact match = 1.0, semantic match = 0.8, no match = 0.0
        """
        if not category1 or not category2:
            return 0.0
        
        if category1 == category2:
            return 1.0
        
        # Semantic similarity for related categories
        semantic_groups = {
            'robbery': ['theft', 'burglary', 'assault'],
            'assault': ['robbery', 'domestic_dispute', 'murder'],
            'theft': ['robbery', 'burglary', 'fraud'],
            'drug_offence': ['suspicious_activity', 'fraud'],
        }
        
        # Check if category2 is in category1's related list
        if category1 in semantic_groups and category2 in semantic_groups[category1]:
            return 0.8
        
        # Check if category1 is in category2's related list
        if category2 in semantic_groups and category1 in semantic_groups[category2]:
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
                        incident.lat or 0, incident.lng or 0,
                        candidate.lat or 0, candidate.lng or 0
                    ) if incident.lat and incident.lng and candidate.lat and candidate.lng else None
                })
        
        # Sort by composite similarity descending
        related.sort(key=lambda x: x['similarity_scores']['composite_score'], reverse=True)
        return related
