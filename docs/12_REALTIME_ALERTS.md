# Feature 4: Real-Time Incident Severity Alerts with WebSockets

> **Priority:** 4 (Fourth to implement)  
> **Estimated Time:** 3-4 days  
> **Academic Value:** ⭐⭐⭐⭐  
> **Complexity:** Medium-High  
> **Dependencies:** Pattern detection (for smart alerting)

---

## 🎯 Feature Overview

**What it adds:** Real-time push notification system using WebSockets that instantly alerts officers when HIGH severity incidents are submitted, with location-based proximity alerts and smart escalation logic.

**Academic Contribution:**
- Real-time DSS architecture for law enforcement
- Location-based alert prioritization algorithms
- WebSocket integration patterns for critical systems
- Real-time event processing and escalation methodology

**Operational Value:**
- Instant notification for HIGH severity incidents
- Location-based alerts for nearby officers
- Reduced response times for critical incidents
- Smart escalation based on incident patterns

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              Real-Time Alert System                       │
├─────────────────────────────────────────────────────────┤
│  1. WebSocket Server Integration                         │
│     - Flask-SocketIO server setup                         │
│     - Room-based broadcasting (officers, zones)           │
│     - Connection management and authentication            │
│     - Reconnection handling and heartbeat                 │
│                                                          │
│  2. Alert Generation Engine                              │
│     - Severity-based alert routing                        │
│     - Location-based proximity alerts                     │
│     - Pattern-based smart escalation                      │
│     - Priority queue management                          │
│                                                          │
│  3. Alert Delivery System                               │
│     - Multi-channel delivery (WebSocket, in-app, mobile)  │
│     - Acknowledgment and read receipts                    │
│     - Alert escalation and timeout handling               │
│     - Do-not-disturb and availability management         │
│                                                          │
│  4. Analytics & Monitoring                              │
│     - Alert delivery tracking                            │
│     - Response time analysis                             │
│     - Alert effectiveness metrics                         │
│     - System performance monitoring                       │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              Real-Time Alert API                         │
│  WebSocket: /socket.io/                                 │
│  POST /api/v1/alerts/test                               │
│  GET  /api/v1/alerts/history                            │
│  POST /api/v1/alerts/acknowledge                        │
│  GET  /api/v1/alerts/stats                              │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Implementation Plan

### **Phase 1: WebSocket Infrastructure (Day 1)**

#### 1.1 Install WebSocket Dependencies

**File:** `backend/requirements.txt`

```txt
# Add these lines for WebSocket support
flask-socketio==5.3.6
python-socketio==5.11.0
eventlet==0.33.3
```

#### 1.2 Create WebSocket Service

**File:** `backend/app/services/realtime/socket_service.py`

```python
"""
Real-Time WebSocket Service
==========================
WebSocket server for real-time incident alerts and notifications.
"""
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from datetime import datetime
import json

from app.models.models import User, Incident
from app import db

# Initialize SocketIO
socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')


class SocketService:
    """
    Real-time WebSocket service for incident alerts.
    
    Manages WebSocket connections, room assignments, and
    real-time message broadcasting for law enforcement operations.
    """
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize SocketIO with Flask app."""
        self.socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
        self.setup_event_handlers()
    
    def setup_event_handlers(self):
        """Setup WebSocket event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            try:
                # Verify JWT token
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                
                user = User.query.get(user_id)
                if not user:
                    return False  # Reject connection
                
                # Join role-based rooms
                if user.role in ['officer', 'admin']:
                    join_room('officers')
                    print(f"User {user_id} joined officers room")
                
                if user.role == 'admin':
                    join_room('admins')
                    print(f"User {user_id} joined admins room")
                
                # Join location-based room if officer has location
                if user.role == 'officer' and hasattr(user, 'location_lat') and user.location_lat:
                    zone = self._get_geohash(user.location_lat, user.location_lng, precision=5)
                    join_room(f'zone_{zone}')
                    print(f"User {user_id} joined zone_{zone}")
                
                # Send acknowledgment
                emit('connection_success', {
                    'user_id': user_id,
                    'role': user.role,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                return True
                
            except Exception as e:
                print(f"Connection failed: {e}")
                return False
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            print(f"Client disconnected")
        
        @self.socketio.on('join_patrol')
        def handle_join_patrol(data):
            """Handle officer joining active patrol."""
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                
                patrol_id = data.get('patrol_id')
                if patrol_id:
                    join_room(f'patrol_{patrol_id}')
                    emit('patrol_joined', {
                        'patrol_id': patrol_id,
                        'user_id': user_id,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
            except Exception as e:
                print(f"Failed to join patrol: {e}")
        
        @self.socketio.on('leave_patrol')
        def handle_leave_patrol(data):
            """Handle officer leaving active patrol."""
            try:
                verify_jwt_in_request()
                patrol_id = data.get('patrol_id')
                if patrol_id:
                    leave_room(f'patrol_{patrol_id}')
                    emit('patrol_left', {
                        'patrol_id': patrol_id,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
            except Exception as e:
                print(f"Failed to leave patrol: {e}")
        
        @self.socketio.on('update_location')
        def handle_location_update(data):
            """Handle officer location update for proximity alerts."""
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                
                lat = data.get('lat')
                lng = data.get('lng')
                
                if lat and lng:
                    # Leave old zone room
                    current_rooms = rooms()
                    for room in current_rooms:
                        if room.startswith('zone_'):
                            leave_room(room)
                    
                    # Join new zone room
                    zone = self._get_geohash(lat, lng, precision=5)
                    join_room(f'zone_{zone}')
                    
                    emit('location_updated', {
                        'user_id': user_id,
                        'zone': zone,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
            except Exception as e:
                print(f"Failed to update location: {e}")
    
    def _get_geohash(self, lat: float, lng: float, precision: int = 5) -> str:
        """
        Simple geohash implementation for location-based rooms.
        
        For production, use the 'geohash' library for proper implementation.
        """
        # Simplified geohash-like encoding
        lat_int = int((lat + 90) * 100000)
        lng_int = int((lng + 180) * 100000)
        combined = (lat_int << 32) | lng_int
        return str(combined)[:precision]
    
    def broadcast_urgent_incident(self, incident: Incident):
        """
        Broadcast HIGH severity incident to all officers.
        
        Args:
            incident: The incident to broadcast
        """
        if incident.severity != 'HIGH':
            return
        
        alert_data = {
            'alert_type': 'urgent_incident',
            'incident_id': incident.id,
            'severity': incident.severity,
            'category': incident.category,
            'location': {
                'lat': incident.location.y if incident.location else None,
                'lng': incident.location.x if incident.location else None
            },
            'location_description': incident.location_description,
            'summary': incident.triage_summary,
            'confidence': incident.triage_confidence,
            'created_at': incident.created_at.isoformat(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Broadcast to all officers
        self.socketio.emit('urgent_incident', alert_data, room='officers')
        
        # Also send to admins
        self.socketio.emit('urgent_incident', alert_data, room='admins')
        
        print(f"Broadcast urgent incident {incident.id} to officers")
    
    def send_proximity_alert(self, incident: Incident, officer_id: int):
        """
        Send proximity alert to specific officer.
        
        Args:
            incident: The incident to alert about
            officer_id: The officer to alert
        """
        officer = User.query.get(officer_id)
        if not officer or not officer.location_lat:
            return
        
        # Calculate distance
        from geoalchemy2.shape import to_shape
        incident_point = to_shape(incident.location)
        distance_km = self._haversine_distance(
            officer.location_lat, officer.location_lng,
            incident_point.y, incident_point.x
        )
        
        if distance_km > 5.0:  # Only alert if within 5km
            return
        
        alert_data = {
            'alert_type': 'proximity_alert',
            'incident_id': incident.id,
            'severity': incident.severity,
            'distance_km': round(distance_km, 2),
            'incident_location': {
                'lat': incident_point.y,
                'lng': incident_point.x
            },
            'your_location': {
                'lat': officer.location_lat,
                'lng': officer.location_lng
            },
            'estimated_response_time_minutes': round(distance_km * 2),  # Rough estimate
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send to specific officer's room
        self.socketio.emit('proximity_alert', alert_data, room=f'user_{officer_id}')
        
        print(f"Sent proximity alert to officer {officer_id} for incident {incident.id}")
    
    def send_pattern_alert(self, pattern_data: dict):
        """
        Send alert when new crime pattern is detected.
        
        Args:
            pattern_data: Pattern detection results
        """
        alert_data = {
            'alert_type': 'pattern_detected',
            'pattern_type': pattern_data.get('pattern_type'),
            'confidence': pattern_data.get('confidence'),
            'incident_count': pattern_data.get('incident_count'),
            'category': pattern_data.get('category'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send to officers and admins
        self.socketio.emit('pattern_detected', alert_data, room='officers')
        self.socketio.emit('pattern_detected', alert_data, room='admins')
        
        print(f"Broadcast pattern alert: {pattern_data.get('pattern_type')}")
    
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


# Global socket service instance
socket_service = SocketService()
```

#### 1.3 Integrate SocketIO with Flask App

**File:** `backend/app/__init__.py`

```python
# Add to imports
from app.services.realtime.socket_service import socket_service

# Modify create_app function
def create_app(config_name: str = "development") -> Flask:
    """Application factory with WebSocket support."""
    app = Flask(__name__)
    
    # ... existing app setup ...
    
    # Initialize SocketIO
    socket_service.init_app(app)
    
    return app

# Replace app.run with socketio.run in wsgi.py
```

**File:** `backend/wsgi.py`

```python
from app import create_app
from app.services.realtime.socket_service import socket_service

app = create_app()

if __name__ == "__main__":
    socket_service.socketio.run(app, debug=True, host='0.0.0.0', port=5000)
```

---

### **Phase 2: Alert Generation Engine (Day 1-2)**

#### 2.1 Create Alert Service

**File:** `backend/app/services/realtime/alert_service.py`

```python
"""
Alert Generation Service
========================
Generates and prioritizes real-time alerts based on incident data.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum

from app.models.models import Incident, User
from app.services.realtime.socket_service import socket_service
from app.services.pattern_detection.pattern_recognizer import PatternRecognizer
from app import db


class AlertPriority(Enum):
    """Alert priority levels."""
    CRITICAL = "critical"  # Immediate threat to life
    HIGH = "high"         # HIGH severity incidents
    MEDIUM = "medium"     # Pattern detection, proximity alerts
    LOW = "low"          # Informational updates


class AlertService:
    """
    Real-time alert generation and management.
    
    Generates alerts based on:
    - Incident severity (HIGH severity triggers immediate alerts)
    - Pattern detection (serial crimes, sprees)
    - Location proximity (nearby officers)
    - Escalation rules (time-based, pattern-based)
    """
    
    def __init__(self):
        self.socket_service = socket_service
        self.pattern_recognizer = PatternRecognizer()
        
        # Alert configuration
        self.alert_rules = {
            'high_severity_broadcast': True,
            'proximity_alert_radius_km': 5.0,
            'pattern_alert_threshold': 0.7,
            'escalation_timeout_minutes': 30
        }
    
    def process_new_incident(self, incident: Incident):
        """
        Process new incident and generate appropriate alerts.
        
        Args:
            incident: Newly created incident
        """
        # Priority 1: HIGH severity incidents
        if incident.severity == 'HIGH':
            self._handle_high_severity_incident(incident)
        
        # Priority 2: Pattern detection
        self._check_for_patterns(incident)
        
        # Priority 3: Proximity alerts for nearby officers
        self._send_proximity_alerts(incident)
        
        # Priority 4: Escalation checks
        self._check_escalation_rules(incident)
    
    def _handle_high_severity_incident(self, incident: Incident):
        """Handle HIGH severity incident with immediate broadcast."""
        # Broadcast to all officers
        self.socket_service.broadcast_urgent_incident(incident)
        
        # Send additional context if available
        if incident.category in ['murder', 'rape', 'robbery']:
            self._send_critical_alert(incident)
    
    def _send_critical_alert(self, incident: Incident):
        """Send critical alert for most severe incidents."""
        critical_alert = {
            'alert_type': 'critical_incident',
            'priority': AlertPriority.CRITICAL.value,
            'incident_id': incident.id,
            'category': incident.category,
            'requires_immediate_response': True,
            'all_units_respond': True,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Broadcast to officers and admins
        self.socket_service.socketio.emit('critical_alert', critical_alert, room='officers')
        self.socket_service.socketio.emit('critical_alert', critical_alert, room='admins')
    
    def _check_for_patterns(self, incident: Incident):
        """Check if incident is part of a larger pattern."""
        try:
            # Get recent incidents for pattern detection
            time_cutoff = datetime.utcnow() - timedelta(days=7)
            recent_incidents = Incident.query.filter(
                Incident.created_at >= time_cutoff
            ).all()
            
            # Run pattern detection
            patterns = self.pattern_recognizer.detect_all_patterns(days_back=7)
            
            # Check if this incident is part of any detected pattern
            for pattern_type, pattern_list in patterns.items():
                for pattern in pattern_list:
                    if incident.id in pattern.get('incident_ids', []):
                        if pattern.get('confidence', 0) >= self.alert_rules['pattern_alert_threshold']:
                            self.socket_service.send_pattern_alert(pattern)
                            break
                            
        except Exception as e:
            print(f"Pattern detection failed: {e}")
    
    def _send_proximity_alerts(self, incident: Incident):
        """Send proximity alerts to nearby officers."""
        if not incident.location:
            return
        
        # Get all active officers with locations
        officers = User.query.filter(
            User.role == 'officer',
            User.location_lat.isnot(None),
            User.location_lng.isnot(None)
        ).all()
        
        from geoalchemy2.shape import to_shape
        incident_point = to_shape(incident.location)
        
        for officer in officers:
            distance_km = self.socket_service._haversine_distance(
                officer.location_lat, officer.location_lng,
                incident_point.y, incident_point.x
            )
            
            if distance_km <= self.alert_rules['proximity_alert_radius_km']:
                self.socket_service.send_proximity_alert(incident, officer.id)
    
    def _check_escalation_rules(self, incident: Incident):
        """Check if incident requires escalation based on rules."""
        # Check for incidents that haven't been responded to
        time_threshold = datetime.utcnow() - timedelta(minutes=self.alert_rules['escalation_timeout_minutes'])
        
        if incident.created_at < time_threshold and incident.status == 'PENDING':
            if incident.severity in ['HIGH', 'MEDIUM']:
                self._send_escalation_alert(incident)
    
    def _send_escalation_alert(self, incident: Incident):
        """Send escalation alert for unresponded incidents."""
        escalation_alert = {
            'alert_type': 'escalation_required',
            'incident_id': incident.id,
            'severity': incident.severity,
            'waiting_time_minutes': int((datetime.utcnow() - incident.created_at).total_seconds() / 60),
            'requires_supervisor_attention': incident.severity == 'HIGH',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send to admins only
        self.socket_service.socketio.emit('escalation_alert', escalation_alert, room='admins')
    
    def send_test_alert(self, user_id: int, message: str):
        """Send test alert for system verification."""
        test_alert = {
            'alert_type': 'test_alert',
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.socket_service.socketio.emit('test_alert', test_alert, room=f'user_{user_id}')
```

#### 2.2 Integrate Alert Service with Incident Creation

**File:** `backend/app/api/v1/routes/incidents.py` (modify existing)

```python
# Add import
from app.services.realtime.alert_service import AlertService

# Initialize alert service
alert_service = AlertService()

# In the incident creation endpoint, after saving incident:
@incidents_bp.post("/", methods=["POST"])
@jwt_required()
def submit_incident():
    # ... existing incident creation logic ...
    
    # After incident is saved to database
    db.session.add(new_incident)
    db.session.commit()
    
    # Generate real-time alerts
    try:
        alert_service.process_new_incident(new_incident)
    except Exception as e:
        # Don't fail incident creation if alerting fails
        print(f"Alert generation failed: {e}")
    
    # ... rest of response logic ...
```

---

### **Phase 3: API Endpoints (Day 2)**

#### 3.1 Create Alert Management API

**File:** `backend/app/api/v1/routes/alerts.py`

```python
"""
Alert Management API Routes
===========================
Endpoints for alert testing, history, and acknowledgment.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

from app import db
from app.models.models import User
from app.services.realtime.alert_service import AlertService
from app.services.realtime.socket_service import socket_service

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.post("/test")
@jwt_required()
def send_test_alert():
    """
    Send a test alert to verify WebSocket connectivity.
    
    Request: { "message": str }
    Response: { "status": "sent", "timestamp": str }
    """
    data = request.get_json()
    message = data.get('message', 'Test alert')
    
    user_id = get_jwt_identity()
    
    try:
        alert_service = AlertService()
        alert_service.send_test_alert(user_id, message)
        
        return jsonify({
            'status': 'sent',
            'user_id': user_id,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@alerts_bp.get("/history")
@jwt_required()
def get_alert_history():
    """
    Get alert history for the current user.
    
    Query params: hours_back (default 24)
    Response: { "alerts": [...], "total_count": int }
    """
    hours_back = request.args.get('hours_back', 24, type=int)
    user_id = get_jwt_identity()
    
    # This would require an Alert model for persistence
    # For now, return placeholder response
    return jsonify({
        'alerts': [],
        'total_count': 0,
        'message': 'Alert history requires Alert model implementation',
        'hours_back': hours_back,
        'user_id': user_id
    }), 200


@alerts_bp.post("/acknowledge")
@jwt_required()
def acknowledge_alert():
    """
    Acknowledge receipt of an alert.
    
    Request: { "alert_id": str, "response": str }
    Response: { "status": "acknowledged", "timestamp": str }
    """
    data = request.get_json()
    alert_id = data.get('alert_id')
    response = data.get('response', 'Acknowledged')
    
    user_id = get_jwt_identity()
    
    # This would require Alert model for persistence
    return jsonify({
        'status': 'acknowledged',
        'alert_id': alert_id,
        'user_id': user_id,
        'response': response,
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@alerts_bp.get("/stats")
@jwt_required()
def get_alert_stats():
    """
    Get alert statistics and system health.
    
    Response: { "alert_stats": {...}, "system_health": {...} }
    """
    # This would require Alert model for real statistics
    return jsonify({
        'alert_stats': {
            'total_alerts_24h': 0,
            'urgent_alerts_24h': 0,
            'avg_response_time_minutes': 0,
            'acknowledgment_rate': 0
        },
        'system_health': {
            'websocket_connected': True,
            'active_officers': 0,
            'system_uptime': '24h'
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200
```

#### 3.2 Register Alerts Blueprint

**File:** `backend/app/__init__.py`

```python
# Add to existing imports
from app.api.v1.routes.alerts import alerts_bp

# Add to blueprint registration
app.register_blueprint(alerts_bp, url_prefix="/api/v1/alerts")
```

---

### **Phase 4: Frontend WebSocket Client (Day 2-3)**

#### 4.1 Create WebSocket Client Service

**File:** `frontend/src/services/websocket.ts`

```typescript
/**
 * WebSocket Client Service
 * ========================
 * Manages WebSocket connection for real-time alerts
 */
import { io, Socket } from 'socket.io-client';

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(token: string) {
    if (this.socket?.connected) {
      console.log('WebSocket already connected');
      return;
    }

    this.socket = io('http://localhost:5000', {
      auth: { token },
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: this.reconnectDelay,
      reconnectionAttempts: this.maxReconnectAttempts
    });

    this.setupEventHandlers();
  }

  private setupEventHandlers() {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.reconnectAttempts++;
      
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached');
      }
    });

    this.socket.on('connection_success', (data) => {
      console.log('Connection successful:', data);
    });

    this.socket.on('urgent_incident', (data) => {
      console.log('Urgent incident received:', data);
      this.handleUrgentIncident(data);
    });

    this.socket.on('proximity_alert', (data) => {
      console.log('Proximity alert received:', data);
      this.handleProximityAlert(data);
    });

    this.socket.on('pattern_detected', (data) => {
      console.log('Pattern detected:', data);
      this.handlePatternAlert(data);
    });

    this.socket.on('critical_alert', (data) => {
      console.log('Critical alert received:', data);
      this.handleCriticalAlert(data);
    });
  }

  private handleUrgentIncident(data: any) {
    // Create browser notification
    if (Notification.permission === 'granted') {
      new Notification('Urgent Incident', {
        body: `${data.category} - ${data.summary}`,
        icon: '/alert-icon.png',
        requireInteraction: true
      });
    }

    // Play alert sound
    this.playAlertSound('urgent');

    // Dispatch custom event for React components
    window.dispatchEvent(new CustomEvent('urgent-incident', { detail: data }));
  }

  private handleProximityAlert(data: any) {
    if (Notification.permission === 'granted') {
      new Notification('Proximity Alert', {
        body: `Incident ${data.distance_km}km away - Est. response: ${data.estimated_response_time_minutes}min`,
        icon: '/proximity-icon.png'
      });
    }

    this.playAlertSound('proximity');
    window.dispatchEvent(new CustomEvent('proximity-alert', { detail: data }));
  }

  private handlePatternAlert(data: any) {
    if (Notification.permission === 'granted') {
      new Notification('Pattern Detected', {
        body: `${data.pattern_type} - ${data.incident_count} incidents - Confidence: ${(data.confidence * 100).toFixed(0)}%`,
        icon: '/pattern-icon.png'
      });
    }

    this.playAlertSound('pattern');
    window.dispatchEvent(new CustomEvent('pattern-alert', { detail: data }));
  }

  private handleCriticalAlert(data: any) {
    if (Notification.permission === 'granted') {
      new Notification('CRITICAL ALERT', {
        body: `All units respond - ${data.category}`,
        icon: '/critical-icon.png',
        requireInteraction: true
      });
    }

    this.playAlertSound('critical');
    window.dispatchEvent(new CustomEvent('critical-alert', { detail: data }));
  }

  private playAlertSound(type: string) {
    const audio = new Audio(`/sounds/${type}-alert.mp3`);
    audio.play().catch(error => console.error('Failed to play sound:', error));
  }

  joinPatrol(patrolId: string) {
    this.socket?.emit('join_patrol', { patrol_id: patrolId });
  }

  leavePatrol(patrolId: string) {
    this.socket?.emit('leave_patrol', { patrol_id: patrolId });
  }

  updateLocation(lat: number, lng: number) {
    this.socket?.emit('update_location', { lat, lng });
  }

  disconnect() {
    this.socket?.disconnect();
    this.socket = null;
  }
}

export const websocketService = new WebSocketService();
```

#### 4.2 Create Real-Time Alerts Component

**File:** `frontend/src/components/alerts/RealTimeAlerts.tsx`

```typescript
"use client";

import { useEffect, useState } from 'react';
import { getToken } from '@/lib/client';
import { websocketService } from '@/services/websocket';

interface Alert {
  alert_type: string;
  [key: string]: any;
}

export default function RealTimeAlerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Request notification permission
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }

    // Connect to WebSocket
    const token = getToken();
    if (token) {
      websocketService.connect(token);
      setIsConnected(true);
    }

    // Listen for custom events
    const handleUrgentIncident = (event: CustomEvent) => {
      setAlerts(prev => [{ ...event.detail, received_at: new Date() }, ...prev]);
    };

    const handleProximityAlert = (event: CustomEvent) => {
      setAlerts(prev => [{ ...event.detail, received_at: new Date() }, ...prev]);
    };

    const handlePatternAlert = (event: CustomEvent) => {
      setAlerts(prev => [{ ...event.detail, received_at: new Date() }, ...prev]);
    };

    window.addEventListener('urgent-incident', handleUrgentIncident as EventListener);
    window.addEventListener('proximity-alert', handleProximityAlert as EventListener);
    window.addEventListener('pattern-alert', handlePatternAlert as EventListener);

    return () => {
      window.removeEventListener('urgent-incident', handleUrgentIncident as EventListener);
      window.removeEventListener('proximity-alert', handleProximityAlert as EventListener);
      window.removeEventListener('pattern-alert', handlePatternAlert as EventListener);
      websocketService.disconnect();
    };
  }, []);

  const getAlertColor = (alertType: string) => {
    switch (alertType) {
      case 'urgent_incident': return 'bg-red-500';
      case 'proximity_alert': return 'bg-orange-500';
      case 'pattern_detected': return 'bg-yellow-500';
      case 'critical_alert': return 'bg-purple-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Real-Time Alerts</h2>
        <div className="flex items-center gap-2">
          <span className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm">{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      {alerts.length === 0 ? (
        <div className="text-gray-500">No recent alerts</div>
      ) : (
        <div className="space-y-2">
          {alerts.slice(0, 10).map((alert, idx) => (
            <div key={idx} className={`p-4 rounded-lg ${getAlertColor(alert.alert_type)} bg-opacity-20`}>
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold capitalize">{alert.alert_type.replace('_', ' ')}</h3>
                  <p className="text-sm mt-1">
                    {alert.summary || alert.message || `${alert.incident_count} incidents detected`}
                  </p>
                  {alert.distance_km && (
                    <p className="text-sm">Distance: {alert.distance_km}km</p>
                  )}
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">
                    {alert.received_at instanceof Date 
                      ? alert.received_at.toLocaleTimeString() 
                      : 'Just now'}
                  </p>
                  {alert.confidence && (
                    <p className="text-sm">
                      Confidence: {(alert.confidence * 100).toFixed(0)}%
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## 📊 Academic Evaluation Framework

### **Research Questions:**
1. What is the latency of real-time alert delivery?
2. How do proximity alerts affect officer response times?
3. What is the optimal alert prioritization strategy?

### **Evaluation Metrics:**
- **Alert Latency:** Time from incident creation to alert delivery
- **Delivery Success Rate:** % of alerts successfully delivered
- **Response Time Improvement:** Reduction in officer response times
- **False Positive Rate:** % of alerts that don't require action

### **Success Criteria:**
- Alert latency < 2 seconds for HIGH severity incidents
- Delivery success rate ≥ 95%
- Response time improvement ≥ 15% for alerted officers
- False positive rate ≤ 10%

---

## 🎯 Acceptance Checklist

### **Backend Requirements:**
- ✅ WebSocket server integrated with Flask
- ✅ Alert service generates appropriate alerts
- ✅ Location-based proximity alerts functional
- ✅ Pattern-based smart escalation working
- ✅ API endpoints for alert management

### **Frontend Requirements:**
- ✅ WebSocket client connects and authenticates
- ✅ Real-time alerts displayed in UI
- ✅ Browser notifications working
- ✅ Alert sounds playing correctly
- ✅ Connection status indicator

### **Testing Requirements:**
- ✅ WebSocket connection testing
- ✅ Alert delivery latency measurement
- ✅ Proximity alert accuracy testing
- ✅ Load testing for concurrent connections

### **Academic Requirements:**
- ✅ Real-time architecture documented
- ✅ Alert prioritization algorithm explained
- ✅ Performance metrics collected
- ✅ Response time impact analyzed

---

## 🚀 Next Steps

After completing Real-Time Alerts:

1. **Move to Priority 5:** Implement Dynamic Patrol Route Rebalancing
2. **Documentation:** Update dissertation with real-time architecture
3. **Testing:** Conduct field testing with actual officers
4. **Optimization:** Tune alert thresholds based on feedback

**Implementation Guide:** `docs/13_DYNAMIC_PATROL_REBALANCING.md`

---

## 📝 Notes for Dissertation

### **Chapter 3 - Methodology Additions:**
- **Section 3.X: Real-Time Alert System Architecture**
  - WebSocket implementation details
  - Alert generation and prioritization algorithms
  - Location-based proximity alert methodology
  - Pattern-based escalation logic

### **Chapter 4 - Results Additions:**
- **Section 4.X: Real-Time System Performance**
  - Alert latency analysis
  - Response time improvement metrics
  - System reliability and delivery success rates
  - User feedback and satisfaction analysis

### **Academic Contributions:**
- Real-time DSS architecture for law enforcement
- Location-based alert prioritization algorithms
- WebSocket integration patterns for critical systems
- Quantitative analysis of real-time alert effectiveness

This feature transforms the system from reactive to proactive while being implementable within 3-4 days.
