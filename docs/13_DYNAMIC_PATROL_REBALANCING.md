# Feature 5: Dynamic Patrol Route Rebalancing

> **Priority:** 5 (Fifth to implement)  
> **Estimated Time:** 2-3 days  
> **Academic Value:** ⭐⭐⭐⭐  
> **Complexity:** Medium  
> **Dependencies:** Real-time alerts, predictive hotspots

---

## 🎯 Feature Overview

**What it adds:** Real-time patrol route adjustment system that dynamically redistributes patrol resources based on new incidents, officer availability, and changing threat conditions.

**Academic Contribution:**
- Dynamic resource optimization algorithms
- Real-time decision-making in law enforcement DSS
- Coverage gap analysis and resolution
- Adaptive routing with constraint satisfaction

**Operational Value:**
- Automatic patrol route optimization based on current conditions
- Improved response times through dynamic resource allocation
- Better coverage of emerging high-risk areas
- Reduced fuel consumption through efficient routing

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│           Dynamic Patrol Rebalancing System                │
├─────────────────────────────────────────────────────────┤
│  1. Real-Time Patrol Tracking                           │
│     - Officer location monitoring                        │
│     - Patrol status tracking (active, idle, responding)   │
│     - Availability management                            │
│     - Performance metrics collection                     │
│                                                          │
│  2. Coverage Gap Analysis                                │
│     - Real-time hotspot analysis                         │
│     - Predictive risk integration                        │
│     - Geographic coverage assessment                     │
│     - Response time optimization                          │
│                                                          │
│  3. Dynamic Rebalancing Engine                           │
│     - Resource allocation optimization                    │
│     - Route adjustment algorithms                        │
│     - Priority-based dispatching                          │
│     - Constraint satisfaction (time, fuel, safety)       │
│                                                          │
│  4. Recommendation System                                │
│     - Route modification suggestions                      │
│     - Reallocation recommendations                        │
│     - Impact analysis (response time, fuel)               │
│     - Human override capabilities                         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              Dynamic Rebalancing API                      │
│  GET  /api/v1/patrol/dynamic/status                     │
│  POST /api/v1/patrol/dynamic/rebalance                   │
│  GET  /api/v1/patrol/dynamic/coverage-gaps              │
│  POST /api/v1/patrol/dynamic/officer-location           │
│  GET  /api/v1/patrol/dynamic/recommendations            │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Implementation Plan

### **Phase 1: Patrol Tracking System (Day 1)**

#### 1.1 Create Patrol Tracking Model

**File:** `backend/app/models/patrol_tracking.py`

```python
"""
Patrol Tracking Model
====================
Real-time tracking of patrol officers and their status.
"""
from datetime import datetime
from app import db


class PatrolOfficer(db.Model):
    """
    Real-time patrol officer tracking.
    
    Tracks officer location, status, and availability
    for dynamic patrol rebalancing.
    """
    __tablename__ = 'patrol_officers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Location tracking
    current_lat = db.Column(db.Float, nullable=True)
    current_lng = db.Column(db.Float, nullable=True)
    last_location_update = db.Column(db.DateTime, nullable=True)
    
    # Status tracking
    status = db.Column(db.String(20), default='idle')
    # Values: 'idle', 'patrolling', 'responding', 'unavailable', 'break'
    
    # Patrol assignment
    current_patrol_id = db.Column(db.Integer, db.ForeignKey('patrol_routes.id'), nullable=True)
    patrol_start_time = db.Column(db.DateTime, nullable=True)
    
    # Availability
    available_for_reassignment = db.Column(db.Boolean, default=True)
    assigned_zone = db.Column(db.String(20), nullable=True)
    
    # Performance metrics
    total_response_time_minutes = db.Column(db.Float, default=0)
    incidents_responded = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='patrol_tracking')
    current_patrol = db.relationship('PatrolRoute', backref='assigned_officers')
    
    def __repr__(self):
        return f'<PatrolOfficer {self.user_id}: {self.status}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'location': {
                'lat': self.current_lat,
                'lng': self.current_lng,
                'last_updated': self.last_location_update.isoformat() if self.last_location_update else None
            },
            'status': self.status,
            'current_patrol_id': self.current_patrol_id,
            'available_for_reassignment': self.available_for_reassignment,
            'assigned_zone': self.assigned_zone,
            'performance': {
                'total_response_time_minutes': self.total_response_time_minutes,
                'incidents_responded': self.incidents_responded,
                'avg_response_time': self.total_response_time_minutes / max(self.incidents_responded, 1)
            }
        }


class DynamicRebalancingLog(db.Model):
    """
    Log of dynamic rebalancing decisions and outcomes.
    """
    __tablename__ = 'dynamic_rebalancing_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Rebalancing trigger
    trigger_type = db.Column(db.String(50), nullable=False)
    # Values: 'new_high_severity', 'coverage_gap', 'officer_unavailable', 'predictive_alert'
    
    trigger_details = db.Column(db.JSON, nullable=True)
    
    # Rebalancing actions
    actions_taken = db.Column(db.JSON, nullable=True)
    # { 'officer_id': {'new_location': {...}, 'new_patrol_id': int} }
    
    # Expected outcomes
    expected_improvement = db.Column(db.JSON, nullable=True)
    # { 'response_time_improvement_minutes': float, 'coverage_improvement_pct': float }
    
    # Actual outcomes (measured later)
    actual_outcome = db.Column(db.JSON, nullable=True)
    outcome_measured = db.Column(db.Boolean, default=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    measured_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<DynamicRebalancingLog {self.trigger_type}>'
```

#### 1.2 Create Database Migration

**File:** `backend/migrations/versions/002_add_patrol_tracking.py`

```python
"""
Add patrol tracking tables for dynamic rebalancing
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


def upgrade():
    # Create patrol_officers table
    op.create_table(
        'patrol_officers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('current_lat', sa.Float(), nullable=True),
        sa.Column('current_lng', sa.Float(), nullable=True),
        sa.Column('last_location_update', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), default='idle'),
        sa.Column('current_patrol_id', sa.Integer(), sa.ForeignKey('patrol_routes.id'), nullable=True),
        sa.Column('patrol_start_time', sa.DateTime(), nullable=True),
        sa.Column('available_for_reassignment', sa.Boolean(), default=True),
        sa.Column('assigned_zone', sa.String(20), nullable=True),
        sa.Column('total_response_time_minutes', sa.Float(), default=0),
        sa.Column('incidents_responded', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)
    )
    
    # Create dynamic_rebalancing_logs table
    op.create_table(
        'dynamic_rebalancing_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('trigger_type', sa.String(50), nullable=False),
        sa.Column('trigger_details', sa.JSON(), nullable=True),
        sa.Column('actions_taken', sa.JSON(), nullable=True),
        sa.Column('expected_improvement', sa.JSON(), nullable=True),
        sa.Column('actual_outcome', sa.JSON(), nullable=True),
        sa.Column('outcome_measured', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('measured_at', sa.DateTime(), nullable=True)
    )
    
    # Create indexes
    op.create_index('ix_patrol_officers_user_id', 'patrol_officers', ['user_id'])
    op.create_index('ix_patrol_officers_status', 'patrol_officers', ['status'])
    op.create_index('ix_patrol_officers_available', 'patrol_officers', ['available_for_reassignment'])


def downgrade():
    op.drop_index('ix_patrol_officers_available')
    op.drop_index('ix_patrol_officers_status')
    op.drop_index('ix_patrol_officers_user_id')
    op.drop_table('dynamic_rebalancing_logs')
    op.drop_table('patrol_officers')
```

---

### **Phase 2: Coverage Gap Analysis (Day 1-2)**

#### 2.1 Create Coverage Analysis Service

**File:** `backend/app/services/dynamic_rebalancing/coverage_analysis.py`

```python
"""
Coverage Gap Analysis Service
===========================
Analyzes real-time patrol coverage and identifies gaps.
"""
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from geoalchemy2.shape import to_shape

from app.models.models import Incident, Hotspot, PatrolOfficer
from app.models.patrol_tracking import PatrolOfficer as PatrolTracking
from app import db


class CoverageAnalyzer:
    """
    Analyze patrol coverage and identify gaps.
    
    Considers:
    - Current officer locations and status
    - Active patrol routes
    - Recent incident patterns
    - Predictive risk areas
    - Response time optimization
    """
    
    def __init__(self):
        self.coverage_radius_km = 2.0  # Officers cover 2km radius
        self.response_time_target_minutes = 10  # Target response time
        self.high_risk_threshold = 0.7  # Predictive risk threshold
    
    def analyze_coverage_gaps(self) -> List[Dict]:
        """
        Identify current coverage gaps in the patrol area.
        
        Returns:
            List of coverage gaps with priority scores
        """
        # Get active officers
        active_officers = PatrolTracking.query.filter(
            PatrolTracking.status.in_(['patrolling', 'idle']),
            PatrolTracking.current_lat.isnot(None),
            PatrolTracking.current_lng.isnot(None)
        ).all()
        
        # Get recent high-severity incidents
        recent_high_severity = Incident.query.filter(
            Incident.severity == 'HIGH',
            Incident.created_at >= datetime.utcnow() - timedelta(hours=1),
            Incident.location.isnot(None)
        ).all()
        
        # Get active hotspots
        active_hotspots = Hotspot.query.filter(
            Hotspot.risk_score >= self.high_risk_threshold
        ).all()
        
        coverage_gaps = []
        
        # Check coverage of recent high-severity incidents
        for incident in recent_high_severity:
            gap = self._check_incident_coverage(incident, active_officers)
            if gap:
                coverage_gaps.append(gap)
        
        # Check coverage of high-risk hotspots
        for hotspot in active_hotspots:
            gap = self._check_hotspot_coverage(hotspot, active_officers)
            if gap:
                coverage_gaps.append(gap)
        
        # Check for geographic areas with no coverage
        geographic_gaps = self._identify_geographic_gaps(active_officers)
        coverage_gaps.extend(geographic_gaps)
        
        # Prioritize gaps
        coverage_gaps = self._prioritize_gaps(coverage_gaps)
        
        return coverage_gaps
    
    def _check_incident_coverage(
        self, 
        incident: Incident, 
        active_officers: List[PatrolTracking]
    ) -> Dict:
        """Check if recent incident has adequate officer coverage."""
        if not incident.location:
            return None
        
        incident_point = to_shape(incident.location)
        
        # Find nearby officers
        nearby_officers = []
        for officer in active_officers:
            distance_km = self._haversine_distance(
                officer.current_lat, officer.current_lng,
                incident_point.y, incident_point.x
            )
            
            if distance_km <= self.coverage_radius_km:
                nearby_officers.append({
                    'officer_id': officer.user_id,
                    'distance_km': distance_km,
                    'status': officer.status,
                    'available': officer.available_for_reassignment
                })
        
        # If no nearby officers, this is a coverage gap
        if not nearby_officers:
            return {
                'gap_type': 'incident_coverage',
                'severity': 'HIGH',
                'location': {
                    'lat': incident_point.y,
                    'lng': incident_point.x
                },
                'incident_id': incident.id,
                'incident_category': incident.category,
                'nearby_officers': 0,
                'priority_score': 0.9  # High priority for uncovered incidents
            }
        
        # If nearby officers but all unavailable
        available_nearby = [o for o in nearby_officers if o['available']]
        if not available_nearby:
            return {
                'gap_type': 'incident_coverage',
                'severity': 'MEDIUM',
                'location': {
                    'lat': incident_point.y,
                    'lng': incident_point.x
                },
                'incident_id': incident.id,
                'nearby_officers': len(nearby_officers),
                'available_officers': 0,
                'priority_score': 0.7
            }
        
        return None  # Adequate coverage
    
    def _check_hotspot_coverage(
        self, 
        hotspot: Hotspot, 
        active_officers: List[PatrolTracking]
    ) -> Dict:
        """Check if high-risk hotspot has adequate patrol coverage."""
        if not hotspot.centroid:
            return None
        
        centroid_point = to_shape(hotspot.centroid)
        
        # Find officers near hotspot
        nearby_officers = []
        for officer in active_officers:
            distance_km = self._haversine_distance(
                officer.current_lat, officer.current_lng,
                centroid_point.y, centroid_point.x
            )
            
            if distance_km <= self.coverage_radius_km:
                nearby_officers.append({
                    'officer_id': officer.user_id,
                    'distance_km': distance_km,
                    'status': officer.status
                })
        
        # High-risk hotspots need at least 2 officers nearby
        required_officers = 2 if hotspot.risk_score >= 0.8 else 1
        
        if len(nearby_officers) < required_officers:
            return {
                'gap_type': 'hotspot_coverage',
                'severity': 'HIGH' if hotspot.risk_score >= 0.8 else 'MEDIUM',
                'location': {
                    'lat': centroid_point.y,
                    'lng': centroid_point.x
                },
                'hotspot_id': hotspot.id,
                'risk_score': hotspot.risk_score,
                'nearby_officers': len(nearby_officers),
                'required_officers': required_officers,
                'priority_score': hotspot.risk_score
            }
        
        return None
    
    def _identify_geographic_gaps(
        self, 
        active_officers: List[PatrolTracking]
    ) -> List[Dict]:
        """Identify geographic areas with no patrol coverage."""
        # Create a grid over Harare and check coverage
        lat_bounds = (-17.95, -17.70)
        lng_bounds = (30.95, 31.20)
        grid_resolution = 0.02  # ~2km grid
        
        uncovered_areas = []
        
        # Create grid points
        lat_steps = int((lat_bounds[1] - lat_bounds[0]) / grid_resolution)
        lng_steps = int((lng_bounds[1] - lng_bounds[0]) / grid_resolution)
        
        for i in range(lat_steps):
            for j in range(lng_steps):
                lat = lat_bounds[0] + i * grid_resolution
                lng = lng_bounds[0] + j * grid_resolution
                
                # Check if this grid point is covered
                covered = False
                for officer in active_officers:
                    distance_km = self._haversine_distance(
                        officer.current_lat, officer.current_lng,
                        lat, lng
                    )
                    if distance_km <= self.coverage_radius_km:
                        covered = True
                        break
                
                if not covered:
                    uncovered_areas.append({
                        'gap_type': 'geographic_coverage',
                        'severity': 'LOW',
                        'location': {'lat': lat, 'lng': lng},
                        'priority_score': 0.3  # Lower priority for general gaps
                    })
        
        return uncovered_areas
    
    def _prioritize_gaps(self, gaps: List[Dict]) -> List[Dict]:
        """Prioritize coverage gaps based on severity and other factors."""
        # Sort by priority score descending
        gaps.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        
        # Add timestamp and recommendations
        for gap in gaps:
            gap['detected_at'] = datetime.utcnow().isoformat()
            gap['recommended_action'] = self._get_recommended_action(gap)
        
        return gaps
    
    def _get_recommended_action(self, gap: Dict) -> str:
        """Get recommended action for coverage gap."""
        gap_type = gap.get('gap_type')
        severity = gap.get('severity')
        
        if gap_type == 'incident_coverage' and severity == 'HIGH':
            return 'Immediate officer dispatch required'
        elif gap_type == 'hotspot_coverage':
            return 'Redirect nearest available patrol'
        elif gap_type == 'geographic_coverage':
            return 'Consider patrol route adjustment'
        else:
            return 'Monitor situation'
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate Haversine distance between two points in kilometers."""
        import math
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
```

---

### **Phase 3: Dynamic Rebalancing Engine (Day 2)**

#### 3.1 Create Rebalancing Service

**File:** `backend/app/services/dynamic_rebalancing/rebalancing_engine.py`

```python
"""
Dynamic Patrol Rebalancing Engine
================================
Optimizes patrol resource allocation in real-time.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import numpy as np

from app.models.models import Incident, PatrolRoute
from app.models.patrol_tracking import PatrolOfficer, DynamicRebalancingLog
from app.services.dynamic_rebalancing.coverage_analysis import CoverageAnalyzer
from app.services.routing.route_engine import RouteEngine
from app import db


class RebalancingEngine:
    """
    Dynamic patrol rebalancing optimization.
    
    Optimizes patrol resource allocation based on:
    - Real-time coverage gaps
    - Incident priority
    - Officer availability
    - Route efficiency
    - Response time targets
    """
    
    def __init__(self):
        self.coverage_analyzer = CoverageAnalyzer()
        self.route_engine = RouteEngine()
        
        # Rebalancing parameters
        self.max_rebalance_distance_km = 5.0  # Max distance to redirect officer
        self.min_response_time_improvement = 2.0  # Minimum improvement to justify rebalance
        self.max_officers_per_rebalance = 3  # Max officers to redirect at once
    
    def analyze_rebalancing_needs(self) -> Dict:
        """
        Analyze current patrol situation and determine if rebalancing is needed.
        
        Returns:
            Dict with rebalancing recommendations
        """
        # Analyze coverage gaps
        coverage_gaps = self.coverage_analyzer.analyze_coverage_gaps()
        
        # Filter high-priority gaps
        high_priority_gaps = [
            gap for gap in coverage_gaps 
            if gap.get('priority_score', 0) >= 0.7
        ]
        
        if not high_priority_gaps:
            return {
                'rebalancing_needed': False,
                'reason': 'No high-priority coverage gaps detected',
                'coverage_gaps': coverage_gaps
            }
        
        # Generate rebalancing recommendations
        recommendations = self._generate_rebalancing_recommendations(high_priority_gaps)
        
        return {
            'rebalancing_needed': True,
            'reason': f'{len(high_priority_gaps)} high-priority coverage gaps detected',
            'coverage_gaps': high_priority_gaps,
            'recommendations': recommendations,
            'estimated_improvement': self._estimate_improvement(recommendations)
        }
    
    def _generate_rebalancing_recommendations(
        self, 
        coverage_gaps: List[Dict]
    ) -> List[Dict]:
        """Generate specific rebalancing recommendations for coverage gaps."""
        recommendations = []
        
        # Get available officers
        available_officers = PatrolOfficer.query.filter(
            PatrolOfficer.status.in_(['patrolling', 'idle']),
            PatrolOfficer.available_for_reassignment == True,
            PatrolOfficer.current_lat.isnot(None),
            PatrolOfficer.current_lng.isnot(None)
        ).all()
        
        for gap in coverage_gaps:
            recommendation = self._create_gap_recommendation(gap, available_officers)
            if recommendation:
                recommendations.append(recommendation)
        
        return recommendations
    
    def _create_gap_recommendation(
        self, 
        gap: Dict, 
        available_officers: List[PatrolOfficer]
    ) -> Optional[Dict]:
        """Create rebalancing recommendation for a specific coverage gap."""
        gap_location = gap.get('location')
        if not gap_location:
            return None
        
        # Find nearest available officers
        officer_distances = []
        for officer in available_officers:
            distance_km = self.coverage_analyzer._haversine_distance(
                officer.current_lat, officer.current_lng,
                gap_location['lat'], gap_location['lng']
            )
            
            if distance_km <= self.max_rebalance_distance_km:
                officer_distances.append({
                    'officer_id': officer.user_id,
                    'distance_km': distance_km,
                    'current_status': officer.status,
                    'estimated_redirect_time': distance_km * 2  # Rough estimate
                })
        
        if not officer_distances:
            return None
        
        # Sort by distance
        officer_distances.sort(key=lambda x: x['distance_km'])
        
        # Select best officers (up to max_officers_per_rebalance)
        selected_officers = officer_distances[:self.max_officers_per_rebalance]
        
        return {
            'gap_id': f"gap_{gap.get('incident_id', gap.get('hotspot_id', 'geo'))}",
            'gap_type': gap.get('gap_type'),
            'gap_severity': gap.get('severity'),
            'target_location': gap_location,
            'officers_to_redirect': selected_officers,
            'estimated_response_time_reduction': self._calculate_response_time_reduction(
                gap, selected_officers
            ),
            'fuel_impact_liters': self._calculate_fuel_impact(selected_officers),
            'priority_score': gap.get('priority_score', 0),
            'recommended': True
        }
    
    def _calculate_response_time_reduction(
        self, 
        gap: Dict, 
        officers: List[Dict]
    ) -> float:
        """Calculate estimated response time improvement."""
        # Simplified calculation
        current_response_time = 15.0  # Assume 15 min current response time
        new_response_time = officers[0]['estimated_redirect_time'] if officers else 15.0
        
        return max(0, current_response_time - new_response_time)
    
    def _calculate_fuel_impact(self, officers: List[Dict]) -> float:
        """Calculate fuel impact of redirection."""
        # Simplified: 0.15 L/km urban consumption
        total_distance_km = sum(o['distance_km'] for o in officers)
        return total_distance_km * 0.15
    
    def _estimate_improvement(self, recommendations: List[Dict]) -> Dict:
        """Estimate overall improvement from rebalancing."""
        total_response_time_reduction = sum(
            r.get('estimated_response_time_reduction', 0) 
            for r in recommendations
        )
        
        total_fuel_impact = sum(
            r.get('fuel_impact_liters', 0) 
            for r in recommendations
        )
        
        return {
            'response_time_reduction_minutes': total_response_time_reduction,
            'additional_fuel_consumption_liters': total_fuel_impact,
            'officers_affected': len(set(
                o['officer_id'] for r in recommendations 
                for o in r['officers_to_redirect']
            )),
            'coverage_gaps_addressed': len(recommendations)
        }
    
    def execute_rebalancing(self, recommendations: List[Dict]) -> Dict:
        """
        Execute rebalancing recommendations.
        
        Args:
            recommendations: List of rebalancing recommendations
            
        Returns:
            Dict with execution results
        """
        executed_actions = []
        
        for recommendation in recommendations:
            # Update officer locations and patrol assignments
            for officer_data in recommendation['officers_to_redirect']:
                officer_id = officer_data['officer_id']
                
                officer = PatrolOfficer.query.filter_by(user_id=officer_id).first()
                if officer:
                    # Update officer location to target
                    officer.current_lat = recommendation['target_location']['lat']
                    officer.current_lng = recommendation['target_location']['lng']
                    officer.last_location_update = datetime.utcnow()
                    officer.status = 'responding'
                    
                    executed_actions.append({
                        'officer_id': officer_id,
                        'action': 'redirected',
                        'new_location': recommendation['target_location'],
                        'previous_status': officer_data['current_status']
                    })
        
        # Log the rebalancing decision
        rebalancing_log = DynamicRebalancingLog(
            trigger_type='coverage_gap',
            trigger_details={'gap_count': len(recommendations)},
            actions_taken={'officer_actions': executed_actions},
            expected_improvement=self._estimate_improvement(recommendations)
        )
        
        db.session.add(rebalancing_log)
        db.session.commit()
        
        return {
            'status': 'executed',
            'actions_taken': executed_actions,
            'log_id': rebalancing_log.id,
            'timestamp': datetime.utcnow().isoformat()
        }
```

---

### **Phase 4: API Integration (Day 2-3)**

#### 4.1 Create Dynamic Rebalancing API

**File:** `backend/app/api/v1/routes/dynamic_patrol.py`

```python
"""
Dynamic Patrol Rebalancing API Routes
=====================================
Endpoints for real-time patrol optimization.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app import db
from app.models.patrol_tracking import PatrolOfficer
from app.services.dynamic_rebalancing.coverage_analysis import CoverageAnalyzer
from app.services.dynamic_rebalancing.rebalancing_engine import RebalancingEngine

dynamic_patrol_bp = Blueprint("dynamic_patrol", __name__)


@dynamic_patrol_bp.get("/status")
@jwt_required()
def get_patrol_status():
    """
    Get current patrol status and coverage.
    
    Response: { "active_officers": [...], "coverage_analysis": {...} }
    """
    try:
        # Get active officers
        active_officers = PatrolOfficer.query.filter(
            PatrolOfficer.status.in_(['patrolling', 'idle', 'responding'])
        ).all()
        
        # Analyze coverage
        coverage_analyzer = CoverageAnalyzer()
        coverage_gaps = coverage_analyzer.analyze_coverage_gaps()
        
        return jsonify({
            'active_officers': [officer.to_dict() for officer in active_officers],
            'coverage_analysis': {
                'total_officers': len(active_officers),
                'coverage_gaps': coverage_gaps,
                'high_priority_gaps': len([g for g in coverage_gaps if g.get('priority_score', 0) >= 0.7])
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dynamic_patrol_bp.post("/rebalance")
@jwt_required()
def trigger_rebalancing():
    """
    Trigger dynamic patrol rebalancing.
    
    Request: { "auto_execute": bool }
    Response: { "recommendations": [...], "execution_results": {...} }
    """
    data = request.get_json()
    auto_execute = data.get('auto_execute', False)
    
    # Only officers and admins can trigger rebalancing
    current_user_id = get_jwt_identity()
    # (Add role check here)
    
    try:
        rebalancing_engine = RebalancingEngine()
        analysis = rebalancing_engine.analyze_rebalancing_needs()
        
        if not analysis['rebalancing_needed']:
            return jsonify({
                'status': 'no_rebalancing_needed',
                'reason': analysis['reason'],
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        
        recommendations = analysis['recommendations']
        
        if auto_execute:
            execution_results = rebalancing_engine.execute_rebalancing(recommendations)
            return jsonify({
                'status': 'executed',
                'recommendations': recommendations,
                'execution_results': execution_results,
                'estimated_improvement': analysis['estimated_improvement'],
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({
                'status': 'recommendations_generated',
                'recommendations': recommendations,
                'estimated_improvement': analysis['estimated_improvement'],
                'requires_approval': True,
                'timestamp': datetime.utcnow().isoformat()
            }), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dynamic_patrol_bp.get("/coverage-gaps")
@jwt_required()
def get_coverage_gaps():
    """
    Get current coverage gaps analysis.
    
    Response: { "coverage_gaps": [...], "summary": {...} }
    """
    try:
        coverage_analyzer = CoverageAnalyzer()
        coverage_gaps = coverage_analyzer.analyze_coverage_gaps()
        
        # Generate summary
        summary = {
            'total_gaps': len(coverage_gaps),
            'high_priority_gaps': len([g for g in coverage_gaps if g.get('priority_score', 0) >= 0.7]),
            'medium_priority_gaps': len([g for g in coverage_gaps if 0.4 <= g.get('priority_score', 0) < 0.7]),
            'low_priority_gaps': len([g for g in coverage_gaps if g.get('priority_score', 0) < 0.4])
        }
        
        return jsonify({
            'coverage_gaps': coverage_gaps,
            'summary': summary,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dynamic_patrol_bp.post("/officer-location")
@jwt_required()
def update_officer_location():
    """
    Update officer location for real-time tracking.
    
    Request: { "lat": float, "lng": float, "status": str }
    Response: { "status": "updated" }
    """
    data = request.get_json()
    lat = data.get('lat')
    lng = data.get('lng')
    status = data.get('status')
    
    current_user_id = get_jwt_identity()
    
    try:
        officer = PatrolOfficer.query.filter_by(user_id=current_user_id).first()
        
        if not officer:
            # Create patrol tracking record if doesn't exist
            officer = PatrolOfficer(user_id=current_user_id)
            db.session.add(officer)
        
        officer.current_lat = lat
        officer.current_lng = lng
        officer.last_location_update = datetime.utcnow()
        
        if status:
            officer.status = status
        
        db.session.commit()
        
        return jsonify({
            'status': 'updated',
            'officer_id': current_user_id,
            'location': {'lat': lat, 'lng': lng},
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dynamic_patrol_bp.get("/recommendations")
@jwt_required()
def get_rebalancing_recommendations():
    """
    Get current rebalancing recommendations without executing.
    
    Response: { "recommendations": [...], "analysis": {...} }
    """
    try:
        rebalancing_engine = RebalancingEngine()
        analysis = rebalancing_engine.analyze_rebalancing_needs()
        
        return jsonify({
            'recommendations': analysis.get('recommendations', []),
            'analysis': analysis,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

#### 4.2 Register Dynamic Patrol Blueprint

**File:** `backend/app/__init__.py`

```python
# Add to existing imports
from app.api.v1.routes.dynamic_patrol import dynamic_patrol_bp

# Add to blueprint registration
app.register_blueprint(dynamic_patrol_bp, url_prefix="/api/v1/patrol/dynamic")
```

---

## 📊 Academic Evaluation Framework

### **Research Questions:**
1. How does dynamic rebalancing affect overall response times?
2. What is the optimal threshold for triggering rebalancing?
3. How do officers respond to automated rebalancing recommendations?

### **Evaluation Metrics:**
- **Response Time Improvement:** Average reduction in response times
- **Coverage Efficiency:** Improvement in area coverage
- **Fuel Impact:** Additional fuel consumption from rebalancing
- **Officer Acceptance:** Rate of recommendation acceptance

### **Success Criteria:**
- Response time improvement ≥ 10%
- Coverage gap reduction ≥ 20%
- Fuel impact ≤ 15% increase
- Officer acceptance rate ≥ 70%

---

## 🎯 Acceptance Checklist

### **Backend Requirements:**
- ✅ Patrol tracking model created and migrated
- ✅ Coverage analysis identifies gaps correctly
- ✅ Rebalancing engine generates valid recommendations
- ✅ API endpoints provide rebalancing functionality
- ✅ Officer location updates working

### **Frontend Requirements:**
- ✅ Real-time patrol status display
- ✅ Coverage gap visualization on map
- ✅ Rebalancing recommendations interface
- ✅ Officer location update functionality

### **Testing Requirements:**
- ✅ Unit tests for coverage analysis algorithms
- ✅ Integration tests for rebalancing engine
- ✅ Performance tests for real-time analysis
- ✅ Usability testing with officer feedback

### **Academic Requirements:**
- ✅ Dynamic optimization methodology documented
- ✅ Coverage analysis algorithms explained
- ✅ Rebalancing decision process described
- ✅ Performance evaluation framework implemented

---

## 🚀 Next Steps

After completing Dynamic Patrol Rebalancing:

1. **Move to Priority 6:** Implement Multi-Objective Route Optimization with Real Constraints
2. **Documentation:** Update dissertation with dynamic optimization methodology
3. **Field Testing:** Conduct real-world testing with patrol officers
4. **Refinement:** Optimize rebalancing thresholds based on operational feedback

**Implementation Guide:** `docs/14_MULTI_OBJECTIVE_ROUTING.md`

---

## 📝 Notes for Dissertation

### **Chapter 3 - Methodology Additions:**
- **Section 3.X: Dynamic Resource Optimization**
  - Real-time patrol tracking methodology
  - Coverage gap analysis algorithms
  - Dynamic rebalancing optimization approach
  - Constraint satisfaction for operational constraints

### **Chapter 4 - Results Additions:**
- **Section 4.X: Dynamic Optimization Results**
  - Response time improvement analysis
  - Coverage efficiency metrics
  - Fuel consumption impact assessment
  - Operator acceptance and feedback analysis

### **Academic Contributions:**
- Real-time dynamic resource optimization for law enforcement
- Coverage gap analysis methodology for patrol systems
- Adaptive constraint satisfaction for operational decisions
- Quantitative analysis of dynamic vs static routing

This feature provides advanced dynamic optimization while being implementable within 2-3 days.
