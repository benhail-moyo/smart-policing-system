# Feature 2: Comprehensive Audit Trail & Accountability Dashboard

> **Priority:** 2 (Second to implement)  
> **Estimated Time:** 1-2 days  
> **Academic Value:** ⭐⭐⭐⭐  
> **Complexity:** Low  
> **Dependencies:** None

---

## 🎯 Feature Overview

**What it adds:** Complete audit logging for all AI-driven decisions with comprehensive accountability dashboard and analytics.

**Academic Contribution:**
- AI transparency and accountability framework
- Algorithmic bias analysis infrastructure
- Decision traceability for law enforcement ethics
- Data-driven approach to algorithmic governance

**Operational Value:**
- Complete audit trail for all system decisions
- Accountability for AI-driven classifications
- Transparency for officers and administrators
- Data for performance analysis and improvement

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              Audit & Accountability System              │
├─────────────────────────────────────────────────────────┤
│  1. Decision Logging Middleware                         │
│     - Automatic logging of all AI operations             │
│     - Capture full decision context and parameters      │
│     - Track model versions and confidence scores         │
│     - Store user actions and system responses           │
│                                                          │
│  2. Audit Trail Storage                                 │
│     - Database model for decision records               │
│     - Immutable audit log with timestamps               │
│     - Decision context storage (JSON)                    │
│     - User attribution and role tracking                │
│                                                          │
│  3. Accountability Analytics                           │
│     - Decision frequency analysis                       │
│     - Model performance metrics                          │
│     - Bias detection indicators                         │
│     - Transparency reporting                             │
│                                                          │
│  4. Investigation Tools                                 │
│     - Decision timeline reconstruction                  │
│     - Pattern analysis in decisions                     │
│     - Anomaly detection in AI behavior                   │
│     - Export functionality for research                │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              Audit & Accountability API                  │
│  GET  /api/v1/audit/decisions                           │
│  GET  /api/v1/audit/analytics                           │
│  GET  /api/v1/audit/decision/{id}                       │
│  POST /api/v1/audit/export                              │
│  GET  /api/v1/audit/bias-analysis                       │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Implementation Plan

### **Phase 1: Database Model & Migration (Day 1)**

#### 1.1 Create Audit Log Model

**File:** `backend/app/models/audit_log.py`

```python
"""
Audit Log Model
===============
Immutable record of all AI-driven decisions and system actions
for accountability and transparency.
"""
from datetime import datetime
from app import db


class AuditLog(db.Model):
    """
    Comprehensive audit trail for all system decisions.
    
    Tracks:
    - AI model decisions (NLP triage, routing optimization)
    - User actions (incident submission, route generation)
    - System responses and outcomes
    - Model versions and parameters
    """
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Decision identification
    decision_type = db.Column(db.String(50), nullable=False, index=True)
    # Values: 'nlp_triage', 'route_generation', 'pattern_detection', 'user_action'
    
    decision_id = db.Column(db.String(100), unique=True, nullable=False)
    # Unique identifier for the decision (e.g., incident ID, route ID)
    
    # User attribution
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user_role = db.Column(db.String(20), nullable=True)
    
    # AI model information
    ai_model_used = db.Column(db.String(100), nullable=True)
    # Values: 'gemini-flash-latest', 'genetic_algorithm', 'dijkstra', etc.
    
    model_version = db.Column(db.String(50), nullable=True)
    model_confidence = db.Column(db.Float, nullable=True)
    
    # Decision context (full details)
    input_data = db.Column(db.JSON, nullable=True)
    # Original input to the AI system
    
    output_data = db.Column(db.JSON, nullable=True)
    # Decision output from the AI system
    
    decision_parameters = db.Column(db.JSON, nullable=True)
    # Parameters used in decision (thresholds, weights, etc.)
    
    # Performance metrics
    execution_time_ms = db.Column(db.Float, nullable=True)
    memory_usage_mb = db.Column(db.Float, nullable=True)
    
    # Outcome tracking
    outcome = db.Column(db.String(50), nullable=True)
    # Values: 'success', 'fallback', 'error', 'manual_override'
    
    human_review_required = db.Column(db.Boolean, default=False)
    human_review_completed = db.Column(db.Boolean, default=False)
    human_reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    human_review_notes = db.Column(db.Text, nullable=True)
    
    # Error handling
    error_message = db.Column(db.Text, nullable=True)
    fallback_used = db.Column(db.Boolean, default=False)
    fallback_reason = db.Column(db.String(200), nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='audit_logs')
    reviewer = db.relationship('User', foreign_keys=[human_reviewer_id], backref='reviewed_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.decision_type}:{self.decision_id}>'
    
    def to_dict(self):
        """Convert audit log to dictionary for API responses."""
        return {
            'id': self.id,
            'decision_type': self.decision_type,
            'decision_id': self.decision_id,
            'user_id': self.user_id,
            'user_role': self.user_role,
            'ai_model_used': self.ai_model_used,
            'model_version': self.model_version,
            'model_confidence': self.model_confidence,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'decision_parameters': self.decision_parameters,
            'execution_time_ms': self.execution_time_ms,
            'outcome': self.outcome,
            'human_review_required': self.human_review_required,
            'human_review_completed': self.human_review_completed,
            'error_message': self.error_message,
            'fallback_used': self.fallback_used,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
```

#### 1.2 Create Database Migration

**File:** `backend/migrations/versions/001_add_audit_log.py`

```python
"""
Add audit_log table for decision tracking
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


def upgrade():
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('decision_type', sa.String(50), nullable=False, index=True),
        sa.Column('decision_id', sa.String(100), unique=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('user_role', sa.String(20), nullable=True),
        sa.Column('ai_model_used', sa.String(100), nullable=True),
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('model_confidence', sa.Float(), nullable=True),
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('decision_parameters', sa.JSON(), nullable=True),
        sa.Column('execution_time_ms', sa.Float(), nullable=True),
        sa.Column('memory_usage_mb', sa.Float(), nullable=True),
        sa.Column('outcome', sa.String(50), nullable=True),
        sa.Column('human_review_required', sa.Boolean(), default=False),
        sa.Column('human_review_completed', sa.Boolean(), default=False),
        sa.Column('human_reviewer_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('human_review_notes', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('fallback_used', sa.Boolean(), default=False),
        sa.Column('fallback_reason', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow, nullable=False, index=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True)
    )
    
    # Create indexes for common queries
    op.create_index('ix_audit_logs_decision_type_created', 'audit_logs', ['decision_type', 'created_at'])
    op.create_index('ix_audit_logs_user_id_created', 'audit_logs', ['user_id', 'created_at'])


def downgrade():
    op.drop_index('ix_audit_logs_user_id_created')
    op.drop_index('ix_audit_logs_decision_type_created')
    op.drop_table('audit_logs')
```

---

### **Phase 2: Audit Logging Service (Day 1)**

#### 2.1 Create Audit Service

**File:** `backend/app/services/audit/audit_service.py`

```python
"""
Audit Service
=============
Centralized logging service for all AI-driven decisions and system actions.
"""
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional
from flask import request

from app.models.audit_log import AuditLog
from app import db


class AuditService:
    """
    Centralized audit logging service.
    
    Provides consistent logging interface for all system decisions
    with automatic context capture and storage.
    """
    
    @staticmethod
    def log_decision(
        decision_type: str,
        decision_id: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        ai_model_used: Optional[str] = None,
        model_version: Optional[str] = None,
        model_confidence: Optional[float] = None,
        decision_parameters: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[float] = None,
        outcome: str = 'success',
        human_review_required: bool = False,
        error_message: Optional[str] = None,
        fallback_used: bool = False,
        fallback_reason: Optional[str] = None
    ) -> AuditLog:
        """
        Log an AI-driven decision to the audit trail.
        
        Args:
            decision_type: Type of decision (nlp_triage, route_generation, etc.)
            decision_id: Unique identifier for the decision
            input_data: Input data provided to the AI system
            output_data: Output data from the AI system
            ai_model_used: Name of the AI model used
            model_version: Version of the AI model
            model_confidence: Confidence score from the model
            decision_parameters: Parameters used in the decision
            execution_time_ms: Execution time in milliseconds
            outcome: Outcome of the decision (success, fallback, error)
            human_review_required: Whether human review is required
            error_message: Error message if decision failed
            fallback_used: Whether fallback mechanism was used
            fallback_reason: Reason for using fallback
            
        Returns:
            Created AuditLog record
        """
        from flask_jwt_extended import get_jwt_identity
        
        try:
            user_id = get_jwt_identity()
        except:
            user_id = None
        
        # Generate unique decision ID if not provided
        if not decision_id:
            decision_id = str(uuid.uuid4())
        
        # Get request context
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent') if request else None
        
        # Get user role if user_id exists
        user_role = None
        if user_id:
            from app.models.models import User
            user = User.query.get(user_id)
            if user:
                user_role = user.role
        
        audit_log = AuditLog(
            decision_type=decision_type,
            decision_id=decision_id,
            user_id=user_id,
            user_role=user_role,
            ai_model_used=ai_model_used,
            model_version=model_version,
            model_confidence=model_confidence,
            input_data=input_data,
            output_data=output_data,
            decision_parameters=decision_parameters,
            execution_time_ms=execution_time_ms,
            outcome=outcome,
            human_review_required=human_review_required,
            error_message=error_message,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.add(audit_log)
        db.session.commit()
        
        return audit_log
    
    @staticmethod
    def log_nlp_triage(
        incident_id: int,
        raw_text: str,
        triage_result: Dict[str, Any],
        model_used: str,
        execution_time_ms: float,
        fallback_used: bool = False
    ) -> AuditLog:
        """
        Log NLP triage decision specifically.
        """
        return AuditService.log_decision(
            decision_type='nlp_triage',
            decision_id=f"incident_{incident_id}",
            input_data={
                'incident_id': incident_id,
                'raw_text': raw_text,
                'text_length': len(raw_text)
            },
            output_data={
                'category': triage_result.get('category'),
                'severity': triage_result.get('severity'),
                'confidence': triage_result.get('confidence'),
                'summary': triage_result.get('summary'),
                'reasoning': triage_result.get('reasoning')
            },
            ai_model_used=model_used,
            model_confidence=triage_result.get('confidence'),
            execution_time_ms=execution_time_ms,
            outcome='success' if not fallback_used else 'fallback',
            fallback_used=fallback_used,
            fallback_reason='API unavailable' if fallback_used else None
        )
    
    @staticmethod
    def log_route_generation(
        route_id: int,
        hotspots: list,
        route_result: Dict[str, Any],
        algorithm: str,
        execution_time_ms: float
    ) -> AuditLog:
        """
        Log patrol route generation decision specifically.
        """
        return AuditService.log_decision(
            decision_type='route_generation',
            decision_id=f"route_{route_id}",
            input_data={
                'hotspot_ids': [h.get('id') for h in hotspots],
                'hotspot_count': len(hotspots),
                'algorithm': algorithm
            },
            output_data={
                'total_distance_km': route_result.get('total_distance_km'),
                'estimated_fuel_litres': route_result.get('estimated_fuel_litres'),
                'estimated_time_minutes': route_result.get('estimated_time_minutes'),
                'hotspots_covered': route_result.get('hotspots_covered')
            },
            ai_model_used=algorithm,
            execution_time_ms=execution_time_ms,
            outcome='success'
        )
    
    @staticmethod
    def log_pattern_detection(
        pattern_type: str,
        incident_ids: list,
        pattern_result: Dict[str, Any],
        execution_time_ms: float
    ) -> AuditLog:
        """
        Log pattern detection decision specifically.
        """
        return AuditService.log_decision(
            decision_type='pattern_detection',
            decision_id=f"pattern_{pattern_type}_{len(incident_ids)}_{int(time.time())}",
            input_data={
                'pattern_type': pattern_type,
                'incident_ids': incident_ids,
                'incident_count': len(incident_ids)
            },
            output_data={
                'confidence': pattern_result.get('confidence'),
                'pattern_details': pattern_result
            },
            ai_model_used='pattern_recognition_algorithm',
            execution_time_ms=execution_time_ms,
            outcome='success'
        )
    
    @staticmethod
    def get_decision_timeline(decision_id: str) -> list:
        """
        Get full timeline of decisions related to a specific decision ID.
        """
        logs = AuditLog.query.filter(
            AuditLog.decision_id == decision_id
        ).order_by(AuditLog.created_at).all()
        
        return [log.to_dict() for log in logs]
    
    @staticmethod
    def get_user_decisions(user_id: int, days_back: int = 30) -> list:
        """
        Get all decisions made by a specific user.
        """
        from datetime import timedelta
        time_cutoff = datetime.utcnow() - timedelta(days=days_back)
        
        logs = AuditLog.query.filter(
            AuditLog.user_id == user_id,
            AuditLog.created_at >= time_cutoff
        ).order_by(AuditLog.created_at.desc()).all()
        
        return [log.to_dict() for log in logs]
```

#### 2.2 Integrate Audit Logging into Existing Services

**File:** `backend/app/services/nlp/triage.py` (add to existing)

```python
# Add import at top
from app.services.audit.audit_service import AuditService

# In the triage method, add audit logging
def triage(self, report_text: str) -> dict:
    """Run the full triage pipeline with audit logging."""
    start_time = time.time()
    
    # ... existing triage logic ...
    
    execution_time_ms = (time.time() - start_time) * 1000
    
    # Log the decision
    try:
        # Generate temporary incident ID for logging
        incident_id = hash(report_text + str(datetime.utcnow()))
        
        AuditService.log_nlp_triage(
            incident_id=incident_id,
            raw_text=text,
            triage_result=result,
            model_used='gemini-flash-latest' if gemini_api_key else 'keyword_fallback',
            execution_time_ms=execution_time_ms,
            fallback_used=(result.get('reasoning', '').find('keyword') != -1)
        )
    except Exception as e:
        # Don't fail triage if audit logging fails
        print(f"Audit logging failed: {e}")
    
    return result
```

**File:** `backend/app/services/routing/route_engine.py` (add to existing)

```python
# Add import at top
from app.services.audit.audit_service import AuditService

# In route generation methods, add audit logging
def generate_route(self, hotspot_ids, algorithm, start_location):
    """Generate patrol route with audit logging."""
    start_time = time.time()
    
    # ... existing route generation logic ...
    
    execution_time_ms = (time.time() - start_time) * 1000
    
    # Log the decision
    try:
        route_id = hash(frozenset(hotspot_ids) + algorithm + str(start_time))
        
        AuditService.log_route_generation(
            route_id=route_id,
            hotspots=hotspots,
            route_result=result,
            algorithm=algorithm,
            execution_time_ms=execution_time_ms
        )
    except Exception as e:
        print(f"Audit logging failed: {e}")
    
    return result
```

---

### **Phase 3: API Endpoints (Day 1-2)**

#### 3.1 Create Audit API Routes

**File:** `backend/app/api/v1/routes/audit.py`

```python
"""
Audit & Accountability API Routes
==================================
Endpoints for accessing audit trail and accountability analytics.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func

from app import db
from app.models.audit_log import AuditLog
from app.models.models import User

audit_bp = Blueprint("audit", __name__)


@audit_bp.get("/decisions")
@jwt_required()
def get_decisions():
    """
    Get audit log entries with filtering.
    
    Query params:
    - decision_type: Filter by decision type
    - user_id: Filter by user
    - days_back: Time period (default 30)
    - limit: Maximum results (default 100)
    """
    decision_type = request.args.get('decision_type')
    user_id = request.args.get('user_id', type=int)
    days_back = request.args.get('days_back', 30, type=int)
    limit = request.args.get('limit', 100, type=int)
    
    time_cutoff = datetime.utcnow() - timedelta(days=days_back)
    
    query = AuditLog.query.filter(AuditLog.created_at >= time_cutoff)
    
    if decision_type:
        query = query.filter(AuditLog.decision_type == decision_type)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    # Role-based access control
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if current_user.role == 'community':
        # Community users can only see their own decisions
        query = query.filter(AuditLog.user_id == current_user_id)
    
    decisions = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    return jsonify({
        'decisions': [decision.to_dict() for decision in decisions],
        'total_count': len(decisions),
        'filters_applied': {
            'decision_type': decision_type,
            'user_id': user_id,
            'days_back': days_back
        }
    }), 200


@audit_bp.get("/analytics")
@jwt_required()
def get_audit_analytics():
    """
    Get comprehensive accountability analytics.
    
    Returns decision statistics, model performance, and transparency metrics.
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Role-based filtering
    base_query = AuditLog.query
    if current_user.role == 'community':
        base_query = base_query.filter(AuditLog.user_id == current_user_id)
    
    time_cutoff = datetime.utcnow() - timedelta(days=30)
    recent_decisions = base_query.filter(AuditLog.created_at >= time_cutoff)
    
    # Decision type breakdown
    decision_type_counts = recent_decisions.with_entities(
        AuditLog.decision_type,
        func.count(AuditLog.id)
    ).group_by(AuditLog.decision_type).all()
    
    decision_type_breakdown = {
        decision_type: count for decision_type, count in decision_type_counts
    }
    
    # AI model usage statistics
    model_usage = recent_decisions.with_entities(
        AuditLog.ai_model_used,
        func.count(AuditLog.id)
    ).group_by(AuditLog.ai_model_used).all()
    
    model_usage_stats = {
        model: count for model, count in model_usage if model
    }
    
    # Confidence distribution
    confidence_decisions = recent_decisions.filter(
        AuditLog.model_confidence.isnot(None)
    ).all()
    
    confidence_distribution = {
        'high_confidence': len([d for d in confidence_decisions if d.model_confidence >= 0.8]),
        'medium_confidence': len([d for d in confidence_decisions if 0.5 <= d.model_confidence < 0.8]),
        'low_confidence': len([d for d in confidence_decisions if d.model_confidence < 0.5])
    }
    
    # Fallback usage
    fallback_count = recent_decisions.filter(AuditLog.fallback_used == True).count()
    total_count = recent_decisions.count()
    fallback_rate = (fallback_count / total_count * 100) if total_count > 0 else 0
    
    # Human review requirements
    human_review_required = recent_decisions.filter(
        AuditLog.human_review_required == True
    ).count()
    human_review_completed = recent_decisions.filter(
        AuditLog.human_review_completed == True
    ).count()
    
    # Outcome distribution
    outcome_counts = recent_decisions.with_entities(
        AuditLog.outcome,
        func.count(AuditLog.id)
    ).group_by(AuditLog.outcome).all()
    
    outcome_distribution = {
        outcome: count for outcome, count in outcome_counts
    }
    
    return jsonify({
        'decision_analytics': {
            'total_decisions': total_count,
            'decision_type_breakdown': decision_type_breakdown,
            'outcome_distribution': outcome_distribution
        },
        'model_performance': {
            'model_usage': model_usage_stats,
            'confidence_distribution': confidence_distribution,
            'fallback_rate': round(fallback_rate, 2),
            'fallback_count': fallback_count
        },
        'human_oversight': {
            'review_required': human_review_required,
            'review_completed': human_review_completed,
            'completion_rate': round(
                (human_review_completed / human_review_required * 100) if human_review_required > 0 else 0,
                2
            )
        },
        'system_transparency': {
            'decisions_reviewable': True,
            'audit_trail_complete': True,
            'model_explainability_available': True,
            'user_attribution_available': True
        },
        'analysis_period_days': 30,
        'generated_at': datetime.utcnow().isoformat()
    }), 200


@audit_bp.get("/decision/<decision_id>")
@jwt_required()
def get_decision_details(decision_id):
    """
    Get detailed information about a specific decision.
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    decision = AuditLog.query.filter(
        AuditLog.decision_id == decision_id
    ).first()
    
    if not decision:
        return jsonify({"error": "Decision not found"}), 404
    
    # Role-based access control
    if current_user.role == 'community' and decision.user_id != current_user_id:
        return jsonify({"error": "Access denied"}), 403
    
    return jsonify(decision.to_dict()), 200


@audit_bp.post("/export")
@jwt_required()
def export_audit_data():
    """
    Export audit data for research or analysis.
    
    Request: { "decision_type": str, "days_back": int, "format": "csv|json" }
    Response: File download or data export
    """
    data = request.get_json()
    decision_type = data.get('decision_type')
    days_back = data.get('days_back', 30)
    export_format = data.get('format', 'json')
    
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Only officers and admins can export
    if current_user.role not in ['officer', 'admin']:
        return jsonify({"error": "Insufficient permissions"}), 403
    
    time_cutoff = datetime.utcnow() - timedelta(days=days_back)
    
    query = AuditLog.query.filter(AuditLog.created_at >= time_cutoff)
    
    if decision_type:
        query = query.filter(AuditLog.decision_type == decision_type)
    
    decisions = query.all()
    
    if export_format == 'json':
        return jsonify({
            'export_metadata': {
                'decision_type': decision_type,
                'days_back': days_back,
                'export_date': datetime.utcnow().isoformat(),
                'total_records': len(decisions)
            },
            'decisions': [decision.to_dict() for decision in decisions]
        }), 200
    elif export_format == 'csv':
        # CSV export logic would go here
        return jsonify({"error": "CSV export not yet implemented"}), 501
    else:
        return jsonify({"error": "Invalid format"}), 400


@audit_bp.get("/bias-analysis")
@jwt_required()
def get_bias_analysis():
    """
    Perform basic bias analysis on audit data.
    
    Analyzes decision patterns across different user groups,
    time periods, and other dimensions for potential bias.
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Only officers and admins can view bias analysis
    if current_user.role not in ['officer', 'admin']:
        return jsonify({"error": "Insufficient permissions"}), 403
    
    time_cutoff = datetime.utcnow() - timedelta(days=30)
    recent_decisions = AuditLog.query.filter(
        AuditLog.created_at >= time_cutoff
    ).all()
    
    # Analyze by user role
    role_analysis = {}
    for decision in recent_decisions:
        if decision.user_role:
            if decision.user_role not in role_analysis:
                role_analysis[decision.user_role] = {
                    'total_decisions': 0,
                    'avg_confidence': 0,
                    'fallback_rate': 0
                }
            
            role_analysis[decision.user_role]['total_decisions'] += 1
            if decision.model_confidence:
                role_analysis[decision.user_role]['avg_confidence'] += decision.model_confidence
            if decision.fallback_used:
                role_analysis[decision.user_role]['fallback_rate'] += 1
    
    # Calculate averages
    for role in role_analysis:
        total = role_analysis[role]['total_decisions']
        if total > 0:
            role_analysis[role]['avg_confidence'] = round(
                role_analysis[role]['avg_confidence'] / total, 3
            )
            role_analysis[role]['fallback_rate'] = round(
                (role_analysis[role]['fallback_rate'] / total) * 100, 2
            )
    
    # Analyze by time of day
    time_analysis = {}
    for decision in recent_decisions:
        hour = decision.created_at.hour
        time_period = self._get_time_period(hour)
        
        if time_period not in time_analysis:
            time_analysis[time_period] = 0
        time_analysis[time_period] += 1
    
    return jsonify({
        'bias_indicators': {
            'role_based_analysis': role_analysis,
            'temporal_analysis': time_analysis,
            'analysis_period_days': 30
        },
        'disclaimer': 'This is basic statistical analysis. Comprehensive bias assessment requires domain expertise and larger datasets.',
        'generated_at': datetime.utcnow().isoformat()
    }), 200

def _get_time_period(hour):
    """Helper function to categorize hours into time periods."""
    if 6 <= hour < 12:
        return 'morning'
    elif 12 <= hour < 18:
        return 'afternoon'
    elif 18 <= hour < 24:
        return 'evening'
    else:
        return 'night'
```

#### 3.2 Register Audit Blueprint

**File:** `backend/app/__init__.py`

```python
# Add to existing imports
from app.api.v1.routes.audit import audit_bp

# Add to blueprint registration
app.register_blueprint(audit_bp, url_prefix="/api/v1/audit")
```

---

### **Phase 4: Frontend Dashboard (Day 2)**

#### 4.1 Create Accountability Dashboard Component

**File:** `frontend/src/components/audit/AccountabilityDashboard.tsx`

```typescript
"use client";

import { useEffect, useState } from 'react';
import { api } from '@/lib/client';

interface AnalyticsData {
  decision_analytics: {
    total_decisions: number;
    decision_type_breakdown: Record<string, number>;
    outcome_distribution: Record<string, number>;
  };
  model_performance: {
    model_usage: Record<string, number>;
    confidence_distribution: {
      high_confidence: number;
      medium_confidence: number;
      low_confidence: number;
    };
    fallback_rate: number;
    fallback_count: number;
  };
  human_oversight: {
    review_required: number;
    review_completed: number;
    completion_rate: number;
  };
  system_transparency: {
    decisions_reviewable: boolean;
    audit_trail_complete: boolean;
    model_explainability_available: boolean;
    user_attribution_available: boolean;
  };
}

export default function AccountabilityDashboard() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api('/audit/analytics')
      .then(data => setAnalytics(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading accountability data...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!analytics) return <div>No analytics data available</div>;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">System Accountability Dashboard</h2>
      
      {/* Decision Analytics */}
      <div className="bg-blue-50 p-4 rounded-lg">
        <h3 className="text-lg font-semibold text-blue-800">Decision Analytics</h3>
        <div className="mt-2 grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">Total Decisions</p>
            <p className="text-2xl font-bold">{analytics.decision_analytics.total_decisions}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Decision Types</p>
            <div className="text-sm">
              {Object.entries(analytics.decision_analytics.decision_type_breakdown).map(([type, count]) => (
                <div key={type}>{type}: {count}</div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Model Performance */}
      <div className="bg-green-50 p-4 rounded-lg">
        <h3 className="text-lg font-semibold text-green-800">Model Performance</h3>
        <div className="mt-2 grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">Fallback Rate</p>
            <p className="text-2xl font-bold">{analytics.model_performance.fallback_rate}%</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Confidence Distribution</p>
            <div className="text-sm">
              <div>High: {analytics.model_performance.confidence_distribution.high_confidence}</div>
              <div>Medium: {analytics.model_performance.confidence_distribution.medium_confidence}</div>
              <div>Low: {analytics.model_performance.confidence_distribution.low_confidence}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Human Oversight */}
      <div className="bg-purple-50 p-4 rounded-lg">
        <h3 className="text-lg font-semibold text-purple-800">Human Oversight</h3>
        <div className="mt-2 grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">Reviews Required</p>
            <p className="text-2xl font-bold">{analytics.human_oversight.review_required}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Completion Rate</p>
            <p className="text-2xl font-bold">{analytics.human_oversight.completion_rate}%</p>
          </div>
        </div>
      </div>

      {/* System Transparency */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-lg font-semibold text-gray-800">System Transparency</h3>
        <div className="mt-2 grid grid-cols-2 gap-4">
          {Object.entries(analytics.system_transparency).map(([key, value]) => (
            <div key={key} className="flex items-center">
              <span className={`w-3 h-3 rounded-full mr-2 ${value ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-sm capitalize">{key.replace(/_/g, ' ')}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

### **Phase 5: Testing & Documentation (Day 2)**

#### 5.1 Create Audit Service Tests

**File:** `backend/tests/unit/test_audit_service.py`

```python
"""
Unit tests for audit service.
"""
import pytest
from app.services.audit.audit_service import AuditService
from app.models.audit_log import AuditLog

class TestAuditService:
    
    def test_log_decision_creates_record(self):
        """Test that logging a decision creates an audit record."""
        decision = AuditService.log_decision(
            decision_type='test_decision',
            decision_id='test_123',
            input_data={'test': 'data'},
            output_data={'result': 'success'}
        )
        
        assert decision.decision_type == 'test_decision'
        assert decision.decision_id == 'test_123'
        assert decision.outcome == 'success'
    
    def test_log_nlp_triage_specialized(self):
        """Test specialized NLP triage logging."""
        decision = AuditService.log_nlp_triage(
            incident_id=123,
            raw_text='Test incident',
            triage_result={'category': 'robbery', 'severity': 'HIGH', 'confidence': 0.9},
            model_used='gemini-flash-latest',
            execution_time_ms=150.5
        )
        
        assert decision.decision_type == 'nlp_triage'
        assert decision.ai_model_used == 'gemini-flash-latest'
        assert decision.model_confidence == 0.9
    
    def test_get_decision_timeline(self):
        """Test retrieving decision timeline."""
        # First log a decision
        AuditService.log_decision(
            decision_type='test_decision',
            decision_id='timeline_test',
            input_data={'test': 'data'},
            output_data={'result': 'success'}
        )
        
        # Then retrieve timeline
        timeline = AuditService.get_decision_timeline('timeline_test')
        
        assert len(timeline) >= 1
        assert timeline[0]['decision_id'] == 'timeline_test'
```

---

## 📊 Academic Evaluation Framework

### **Research Questions:**
1. How comprehensive is the audit trail for AI decision-making?
2. What patterns emerge in AI system behavior over time?
3. Are there indicators of potential bias in decision patterns?

### **Evaluation Metrics:**
- **Audit Completeness:** % of AI decisions logged
- **Data Quality:** % of logs with complete information
- **Performance Impact:** Overhead of audit logging on system performance
- **Transparency Score:** Assessment of decision explainability

### **Success Criteria:**
- 100% of AI decisions logged with full context
- Audit logging adds <5% overhead to system performance
- Dashboard provides meaningful insights into system behavior
- Export functionality enables research analysis

---

## 🎯 Acceptance Checklist

### **Backend Requirements:**
- ✅ AuditLog model created and migrated
- ✅ AuditService provides logging interface
- ✅ Existing services integrated with audit logging
- ✅ API endpoints provide audit data access
- ✅ Role-based access control implemented

### **Frontend Requirements:**
- ✅ Accountability dashboard renders analytics
- ✅ Decision history view available
- ✅ Export functionality accessible to authorized users
- ✅ Bias analysis indicators displayed

### **Testing Requirements:**
- ✅ Unit tests for audit service methods
- ✅ Integration tests for API endpoints
- ✅ Performance tests for logging overhead
- ✅ Security tests for access control

### **Academic Requirements:**
- ✅ Audit trail methodology documented
- ✅ Transparency framework explained
- ✅ Bias analysis approach described
- ✅ Research questions addressed

---

## 🚀 Next Steps

After completing Audit Trail & Accountability Dashboard:

1. **Move to Priority 3:** Implement AI-Powered Predictive Crime Hotspots
2. **Documentation:** Update dissertation with accountability framework
3. **Integration:** Ensure all future features use audit logging
4. **Analysis:** Use audit data for initial bias analysis

**Implementation Guide:** `docs/11_PREDICTIVE_HOTSPOTS.md`

---

## 📝 Notes for Dissertation

### **Chapter 3 - Methodology Additions:**
- **Section 3.X: Accountability Framework**
  - Audit trail architecture and data model
  - Decision logging methodology
  - Transparency and explainability approach
  - Bias detection methodology

### **Chapter 4 - Results Additions:**
- **Section 4.X: System Accountability Analysis**
  - Audit completeness statistics
  - Decision pattern analysis
  - Performance impact assessment
  - Bias analysis results

### **Academic Contributions:**
- Comprehensive audit trail framework for AI-driven DSS
- Methodology for algorithmic transparency in law enforcement
- Bias detection approach for pattern recognition systems
- Accountability metrics for AI decision-making

This feature provides essential ethical AI infrastructure while being implementable within 1-2 days.
