# Feature 3: AI-Powered Predictive Crime Hotspots

> **Priority:** 3 (Third to implement)  
> **Estimated Time:** 2-3 days  
> **Academic Value:** ⭐⭐⭐⭐⭐  
> **Complexity:** Medium-High  
> **Dependencies:** Phase 1 features (for enhanced data)

---

## 🎯 Feature Overview

**What it adds:** Machine learning model that predicts where crime is likely to occur in the next 7 days based on historical patterns, temporal trends, and spatial clustering.

**Academic Contribution:**
- Spatiotemporal predictive modeling for crime
- Time-series analysis of incident patterns
- ML model evaluation framework for law enforcement
- Comparative analysis of prediction algorithms

**Operational Value:**
- Proactive resource allocation based on predictions
- Early warning for emerging crime trends
- Data-driven patrol planning
- Risk assessment for geographic areas

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              Predictive Hotspot System                    │
├─────────────────────────────────────────────────────────┤
│  1. Feature Engineering Pipeline                        │
│     - Spatial features (location density, nearby incidents)│
│     - Temporal features (hour, day of week, seasonality) │
│     - Contextual features (weather, events, land use)     │
│     - Historical crime rates (trend analysis)            │
│                                                          │
│  2. ML Model Training Framework                         │
│     - Random Forest for baseline prediction              │
│     - Gradient Boosting for improved accuracy            │
│     - Time-series models for temporal patterns           │
│     - Ensemble methods for robust predictions            │
│                                                          │
│  3. Prediction Generation System                         │
│     - Grid-based prediction over Harare                   │
│     - Confidence intervals for predictions                │
│     - Risk categorization (LOW/MEDIUM/HIGH)              │
│     - Time-horizon predictions (1, 3, 7 days)            │
│                                                          │
│  4. Model Evaluation & Monitoring                       │
│     - Accuracy metrics (precision, recall, F1)           │
│     - Spatial prediction accuracy analysis               │
│     - Temporal drift detection                           │
│     - Model retraining scheduling                        │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              Predictive Hotspot API                       │
│  POST /api/v1/predictive/train-model                     │
│  GET  /api/v1/predictive/hotspots                       │
│  GET  /api/v1/predictive/accuracy                       │
│  POST /api/v1/predictive/evaluate-model                  │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Implementation Plan

### **Phase 1: Feature Engineering (Day 1)**

#### 1.1 Create Predictive Service Structure

**File:** `backend/app/services/predictive/__init__.py`

```python
"""
Predictive Hotspot Service — Crime-Watch
========================================
Machine learning-based crime prediction using spatiotemporal analysis.

Academic Context:
- Random Forest baseline with spatial-temporal features
- Gradient Boosting for improved accuracy
- Time-series analysis for seasonal patterns
- Ensemble methods for robust predictions
"""
from .feature_engineering import FeatureEngineer
from .model_trainer import ModelTrainer
from .prediction_generator import PredictionGenerator

__all__ = ['FeatureEngineer', 'ModelTrainer', 'PredictionGenerator']
```

#### 1.2 Implement Feature Engineering

**File:** `backend/app/services/predictive/feature_engineering.py`

```python
"""
Feature Engineering for Crime Prediction
=========================================
Extracts spatial, temporal, and contextual features from incident data
for machine learning models.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from sklearn.preprocessing import StandardScaler
from geoalchemy2.shape import to_shape

from app.models.models import Incident
from app import db


class FeatureEngineer:
    """
    Extract and engineer features for crime prediction models.
    
    Features include:
    - Spatial: location density, nearby incidents, distance to hotspots
    - Temporal: hour of day, day of week, seasonal patterns
    - Contextual: historical crime rates, trend analysis
    - Environmental: (future integration with weather data)
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_names = []
        
        # Harare geographic bounds for normalization
        self.lat_bounds = (-17.95, -17.70)
        self.lng_bounds = (30.95, 31.20)
    
    def extract_features_from_incident(self, incident: Incident) -> Dict[str, float]:
        """
        Extract comprehensive features from a single incident.
        
        Returns:
            Dictionary of feature names to values
        """
        features = {}
        
        # Temporal features
        features.update(self._extract_temporal_features(incident.created_at))
        
        # Spatial features
        if incident.location:
            features.update(self._extract_spatial_features(incident.location))
        
        # Contextual features
        features.update(self._extract_contextual_features(incident))
        
        # Category-specific features
        features.update(self._extract_category_features(incident))
        
        return features
    
    def _extract_temporal_features(self, timestamp: datetime) -> Dict[str, float]:
        """Extract temporal features from timestamp."""
        features = {}
        
        # Basic time features
        features['hour'] = timestamp.hour / 24.0  # Normalized 0-1
        features['day_of_week'] = timestamp.weekday() / 6.0  # Normalized 0-1
        features['day_of_month'] = timestamp.day / 31.0  # Normalized 0-1
        features['month'] = timestamp.month / 12.0  # Normalized 0-1
        
        # Cyclical encoding for periodic features
        features['hour_sin'] = np.sin(2 * np.pi * timestamp.hour / 24)
        features['hour_cos'] = np.cos(2 * np.pi * timestamp.hour / 24)
        features['day_sin'] = np.sin(2 * np.pi * timestamp.weekday() / 7)
        features['day_cos'] = np.cos(2 * np.pi * timestamp.weekday() / 7)
        
        # Time period indicators
        features['is_weekend'] = 1.0 if timestamp.weekday() >= 5 else 0.0
        features['is_night'] = 1.0 if timestamp.hour < 6 or timestamp.hour >= 22 else 0.0
        features['is_rush_hour'] = 1.0 if 7 <= timestamp.hour <= 9 or 16 <= timestamp.hour <= 18 else 0.0
        
        return features
    
    def _extract_spatial_features(self, location) -> Dict[str, float]:
        """Extract spatial features from location."""
        features = {}
        
        point = to_shape(location)
        lat, lng = point.y, point.x
        
        # Normalize coordinates to 0-1 range
        norm_lat = (lat - self.lat_bounds[0]) / (self.lat_bounds[1] - self.lat_bounds[0])
        norm_lng = (lng - self.lng_bounds[0]) / (self.lng_bounds[1] - self.lng_bounds[0])
        
        features['lat_normalized'] = np.clip(norm_lat, 0, 1)
        features['lng_normalized'] = np.clip(norm_lng, 0, 1)
        
        # Grid-based features (divide Harare into 10x10 grid)
        grid_size = 10
        lat_grid = int(norm_lat * grid_size)
        lng_grid = int(norm_lng * grid_size)
        features['grid_lat'] = lat_grid / grid_size
        features['grid_lng'] = lng_grid / grid_size
        
        return features
    
    def _extract_contextual_features(self, incident: Incident) -> Dict[str, float]:
        """Extract contextual features based on historical data."""
        features = {}
        
        # Historical crime rate in area (past 30 days)
        time_cutoff = datetime.utcnow() - timedelta(days=30)
        
        if incident.location:
            point = to_shape(incident.location)
            nearby_incidents = Incident.query.filter(
                Incident.created_at >= time_cutoff,
                Incident.location.isnot(None)
            ).all()
            
            # Count incidents within 2km
            nearby_count = 0
            for nearby in nearby_incidents:
                if nearby.location:
                    nearby_point = to_shape(nearby.location)
                    distance = self._haversine_distance(
                        point.y, point.x,
                        nearby_point.y, nearby_point.x
                    )
                    if distance <= 2.0:  # 2km radius
                        nearby_count += 1
            
            features['nearby_incident_count_30d'] = nearby_count / 10.0  # Normalized
            
            # Severity-based nearby count
            high_severity_nearby = 0
            for nearby in nearby_incidents:
                if nearby.location and nearby.severity == 'HIGH':
                    nearby_point = to_shape(nearby.location)
                    distance = self._haversine_distance(
                        point.y, point.x,
                        nearby_point.y, nearby_point.x
                    )
                    if distance <= 2.0:
                        high_severity_nearby += 1
            
            features['high_severity_nearby_30d'] = high_severity_nearby / 5.0  # Normalized
        
        # Historical trend (7 days vs 30 days)
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        if incident.location:
            point = to_shape(incident.location)
            recent_incidents = Incident.query.filter(
                Incident.created_at >= recent_cutoff,
                Incident.location.isnot(None)
            ).all()
            
            recent_count = 0
            for recent in recent_incidents:
                if recent.location:
                    recent_point = to_shape(recent.location)
                    distance = self._haversine_distance(
                        point.y, point.x,
                        recent_point.y, recent_point.x
                    )
                    if distance <= 2.0:
                        recent_count += 1
            
            features['recent_trend_ratio'] = (recent_count / max(nearby_count, 1)) if nearby_count > 0 else 0
        
        return features
    
    def _extract_category_features(self, incident: Incident) -> Dict[str, float]:
        """Extract category-specific features."""
        features = {}
        
        # One-hot encoding for major categories
        major_categories = ['robbery', 'assault', 'theft', 'burglary', 'drug_offence']
        for category in major_categories:
            features[f'category_{category}'] = 1.0 if incident.category == category else 0.0
        
        # Severity encoding
        severity_encoding = {'HIGH': 1.0, 'MEDIUM': 0.5, 'LOW': 0.0}
        features['severity_encoded'] = severity_encoding.get(incident.severity, 0.0)
        
        return features
    
    def create_training_dataset(self, days_back: int = 90) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create a complete training dataset from historical incidents.
        
        Returns:
            X (features), y (labels - whether crime occurred in next 7 days)
        """
        time_cutoff = datetime.utcnow() - timedelta(days=days_back)
        incidents = Incident.query.filter(
            Incident.created_at >= time_cutoff,
            Incident.location.isnot(None)
        ).all()
        
        features_list = []
        labels = []
        
        for incident in incidents:
            # Extract features
            features = self.extract_features_from_incident(incident)
            features_list.append(features)
            
            # Create label: did similar crime occur in this area in next 7 days?
            label = self._create_prediction_label(incident)
            labels.append(label)
        
        # Convert to arrays
        X = pd.DataFrame(features_list).fillna(0).values
        y = np.array(labels)
        
        # Store feature names
        self.feature_names = list(features_list[0].keys()) if features_list else []
        
        return X, y
    
    def _create_prediction_label(self, incident: Incident) -> int:
        """
        Create prediction label for training.
        
        Label = 1 if similar crime occurred in same area within 7 days after this incident
        Label = 0 otherwise
        """
        # Look ahead 7 days from this incident
        time_window_start = incident.created_at + timedelta(days=1)
        time_window_end = incident.created_at + timedelta(days=7)
        
        if not incident.location:
            return 0
        
        point = to_shape(incident.location)
        
        # Check for similar incidents in future time window
        future_incidents = Incident.query.filter(
            Incident.created_at >= time_window_start,
            Incident.created_at <= time_window_end,
            Incident.category == incident.category,
            Incident.location.isnot(None)
        ).all()
        
        for future in future_incidents:
            if future.location:
                future_point = to_shape(future.location)
                distance = self._haversine_distance(
                    point.y, point.x,
                    future_point.y, future_point.x
                )
                if distance <= 1.0:  # 1km radius
                    return 1
        
        return 0
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate Haversine distance between two points in kilometers."""
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        return R * c
    
    def normalize_features(self, X: np.ndarray) -> np.ndarray:
        """Normalize features using StandardScaler."""
        return self.scaler.fit_transform(X)
```

---

### **Phase 2: ML Model Training (Day 1-2)**

#### 2.1 Implement Model Trainer

**File:** `backend/app/services/predictive/model_trainer.py`

```python
"""
ML Model Training for Crime Prediction
======================================
Train and evaluate machine learning models for crime prediction.
"""
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import joblib
import json

from app.services.predictive.feature_engineering import FeatureEngineer


class ModelTrainer:
    """
    Train and evaluate ML models for crime prediction.
    
    Supports multiple algorithms:
    - Random Forest (baseline)
    - Gradient Boosting (improved accuracy)
    - Ensemble methods (robust predictions)
    """
    
    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.models = {}
        self.model_performance = {}
        
    def train_models(self, days_back: int = 90) -> Dict[str, Dict]:
        """
        Train multiple models and compare performance.
        
        Args:
            days_back: Historical data period for training
            
        Returns:
            Dictionary of model performance metrics
        """
        # Create training dataset
        X, y = self.feature_engineer.create_training_dataset(days_back)
        
        if len(X) == 0:
            raise ValueError("No training data available")
        
        # Normalize features
        X_normalized = self.feature_engineer.normalize_features(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_normalized, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train multiple models
        models_to_train = {
            'random_forest': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        }
        
        results = {}
        
        for model_name, model in models_to_train.items():
            print(f"Training {model_name}...")
            
            # Train model
            model.fit(X_train, y_train)
            
            # Evaluate
            performance = self._evaluate_model(model, X_test, y_test)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='f1')
            
            results[model_name] = {
                'test_performance': performance,
                'cv_mean_f1': cv_scores.mean(),
                'cv_std_f1': cv_scores.std(),
                'feature_importance': self._get_feature_importance(model, model_name)
            }
            
            # Store model
            self.models[model_name] = model
            self.model_performance[model_name] = performance
            
            print(f"{model_name} - F1: {performance['f1']:.3f}, AUC: {performance['auc']:.3f}")
        
        # Select best model
        best_model = max(results.keys(), key=lambda k: results[k]['test_performance']['f1'])
        print(f"\nBest model: {best_model}")
        
        # Save best model
        self._save_model(self.models[best_model], best_model)
        
        return results
    
    def _evaluate_model(self, model, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """Evaluate model performance."""
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1': f1_score(y_test, y_pred, zero_division=0)
        }
        
        if y_pred_proba is not None:
            metrics['auc'] = roc_auc_score(y_test, y_pred_proba)
        else:
            metrics['auc'] = 0.0
        
        return metrics
    
    def _get_feature_importance(self, model, model_name: str) -> Dict[str, float]:
        """Get feature importance from model."""
        if hasattr(model, 'feature_importances_'):
            importance_dict = dict(zip(
                self.feature_engineer.feature_names,
                model.feature_importances_
            ))
            # Sort by importance
            return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
        return {}
    
    def _save_model(self, model, model_name: str):
        """Save trained model to disk."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"ml/predictive/models/{model_name}_{timestamp}.joblib"
        
        try:
            joblib.dump(model, filename)
            print(f"Model saved to {filename}")
        except Exception as e:
            print(f"Failed to save model: {e}")
    
    def load_model(self, model_path: str):
        """Load a trained model from disk."""
        try:
            model = joblib.load(model_path)
            return model
        except Exception as e:
            print(f"Failed to load model: {e}")
            return None
    
    def get_prediction_for_location(
        self, 
        lat: float, 
        lng: float, 
        model_name: str = 'random_forest'
    ) -> Dict[str, float]:
        """
        Get crime probability prediction for a specific location.
        
        Args:
            lat: Latitude
            lng: Longitude
            model_name: Name of model to use
            
        Returns:
            Dictionary with prediction and confidence
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not trained")
        
        model = self.models[model_name]
        
        # Create features for this location
        # This is a simplified version - would need proper incident context
        features = {
            'hour': datetime.utcnow().hour / 24.0,
            'day_of_week': datetime.utcnow().weekday() / 6.0,
            'lat_normalized': (lat - self.feature_engineer.lat_bounds[0]) / 
                            (self.feature_engineer.lat_bounds[1] - self.feature_engineer.lat_bounds[0]),
            'lng_normalized': (lng - self.feature_engineer.lng_bounds[0]) / 
                            (self.feature_engineer.lng_bounds[1] - self.feature_engineer.lng_bounds[0]),
            # Add other features as needed
        }
        
        # Ensure all expected features are present
        feature_vector = []
        for feature_name in self.feature_engineer.feature_names:
            feature_vector.append(features.get(feature_name, 0.0))
        
        # Normalize and predict
        X = np.array([feature_vector])
        X_normalized = self.feature_engineer.scaler.transform(X)
        
        prediction_proba = model.predict_proba(X_normalized)[0]
        
        return {
            'crime_probability': prediction_proba[1],  # Probability of class 1 (crime)
            'confidence': max(prediction_proba),  # Model confidence
            'risk_level': self._categorize_risk(prediction_proba[1])
        }
    
    def _categorize_risk(self, probability: float) -> str:
        """Categorize probability into risk levels."""
        if probability >= 0.7:
            return 'HIGH'
        elif probability >= 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'
```

---

### **Phase 3: Prediction Generation (Day 2)**

#### 3.1 Implement Prediction Generator

**File:** `backend/app/services/predictive/prediction_generator.py`

```python
"""
Prediction Generation System
===========================
Generate crime probability predictions across geographic grid.
"""
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.services.predictive.model_trainer import ModelTrainer
from app.services.predictive.feature_engineering import FeatureEngineer


class PredictionGenerator:
    """
    Generate crime probability predictions across geographic areas.
    
    Creates a grid-based prediction surface for Harare with
    confidence intervals and risk categorization.
    """
    
    def __init__(self):
        self.model_trainer = ModelTrainer()
        self.feature_engineer = FeatureEngineer()
        
        # Harare bounds
        self.lat_bounds = (-17.95, -17.70)
        self.lng_bounds = (30.95, 31.20)
        
        # Grid resolution
        self.grid_resolution = 0.01  # ~1km resolution
        
    def generate_predictive_hotspots(
        self, 
        days_ahead: int = 7,
        model_name: str = 'random_forest'
    ) -> List[Dict]:
        """
        Generate predictive hotspots for the specified time horizon.
        
        Args:
            days_ahead: Prediction horizon (1, 3, or 7 days)
            model_name: ML model to use for predictions
            
        Returns:
            List of predicted hotspot areas with risk levels
        """
        # Ensure model is trained
        if model_name not in self.model_trainer.models:
            print(f"Model {model_name} not trained, training now...")
            self.model_trainer.train_models()
        
        # Create prediction grid
        grid_points = self._create_prediction_grid()
        
        # Generate predictions for each grid point
        predictions = []
        for lat, lng in grid_points:
            prediction = self.model_trainer.get_prediction_for_location(lat, lng, model_name)
            
            if prediction['crime_probability'] > 0.3:  # Only include significant predictions
                predictions.append({
                    'lat': lat,
                    'lng': lng,
                    'crime_probability': prediction['crime_probability'],
                    'risk_level': prediction['risk_level'],
                    'confidence': prediction['confidence'],
                    'prediction_date': datetime.utcnow().isoformat(),
                    'days_ahead': days_ahead
                })
        
        # Cluster predictions into hotspot areas
        hotspots = self._cluster_predictions(predictions)
        
        return hotspots
    
    def _create_prediction_grid(self) -> List[Tuple[float, float]]:
        """Create a grid of points covering Harare for prediction."""
        points = []
        
        lat_steps = int((self.lat_bounds[1] - self.lat_bounds[0]) / self.grid_resolution)
        lng_steps = int((self.lng_bounds[1] - self.lng_bounds[0]) / self.grid_resolution)
        
        for i in range(lat_steps):
            for j in range(lng_steps):
                lat = self.lat_bounds[0] + i * self.grid_resolution
                lng = self.lng_bounds[0] + j * self.grid_resolution
                points.append((lat, lng))
        
        return points
    
    def _cluster_predictions(self, predictions: List[Dict]) -> List[Dict]:
        """
        Cluster individual predictions into hotspot areas.
        
        Uses simple spatial clustering to group nearby high-risk predictions.
        """
        if not predictions:
            return []
        
        # Sort by probability
        predictions.sort(key=lambda x: x['crime_probability'], reverse=True)
        
        # Simple clustering: group nearby high-risk predictions
        hotspots = []
        used_indices = set()
        
        for i, pred in enumerate(predictions):
            if i in used_indices:
                continue
            
            # Only start clusters with high probability points
            if pred['crime_probability'] < 0.5:
                continue
            
            # Find nearby predictions
            cluster = [pred]
            used_indices.add(i)
            
            for j, other_pred in enumerate(predictions):
                if j in used_indices:
                    continue
                
                distance = self._haversine_distance(
                    pred['lat'], pred['lng'],
                    other_pred['lat'], other_pred['lng']
                )
                
                if distance <= 1.5:  # 1.5km clustering radius
                    cluster.append(other_pred)
                    used_indices.add(j)
            
            if len(cluster) >= 2:  # Minimum cluster size
                hotspot = self._create_hotspot_from_cluster(cluster)
                hotspots.append(hotspot)
        
        return hotspots
    
    def _create_hotspot_from_cluster(self, cluster: List[Dict]) -> Dict:
        """Create a hotspot object from a cluster of predictions."""
        # Calculate centroid
        avg_lat = sum(p['lat'] for p in cluster) / len(cluster)
        avg_lng = sum(p['lng'] for p in cluster) / len(cluster)
        
        # Calculate average probability
        avg_probability = sum(p['crime_probability'] for p in cluster) / len(cluster)
        
        # Determine risk level
        if avg_probability >= 0.7:
            risk_level = 'HIGH'
        elif avg_probability >= 0.4:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'centroid': {'lat': avg_lat, 'lng': avg_lng},
            'crime_probability': avg_probability,
            'risk_level': risk_level,
            'prediction_count': len(cluster),
            'confidence': sum(p['confidence'] for p in cluster) / len(cluster),
            'prediction_date': cluster[0]['prediction_date'],
            'days_ahead': cluster[0]['days_ahead'],
            'boundary_radius_km': self._calculate_cluster_radius(cluster, avg_lat, avg_lng)
        }
    
    def _calculate_cluster_radius(self, cluster: List[Dict], center_lat: float, center_lng: float) -> float:
        """Calculate the radius of the cluster."""
        max_distance = 0
        for pred in cluster:
            distance = self._haversine_distance(
                center_lat, center_lng,
                pred['lat'], pred['lng']
            )
            max_distance = max(max_distance, distance)
        return max_distance
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate Haversine distance between two points in kilometers."""
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        return R * c
```

---

### **Phase 4: API Integration (Day 2-3)**

#### 4.1 Create Predictive API Routes

**File:** `backend/app/api/v1/routes/predictive.py`

```python
"""
Predictive Hotspot API Routes
=============================
Endpoints for ML-based crime prediction.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.predictive.model_trainer import ModelTrainer
from app.services.predictive.prediction_generator import PredictionGenerator

predictive_bp = Blueprint("predictive", __name__)


@predictive_bp.post("/train-model")
@jwt_required()
def train_prediction_model():
    """
    Train ML models for crime prediction.
    
    Request: { "days_back": int }
    Response: { "training_results": {...}, "best_model": str }
    """
    from flask_jwt_extended import get_jwt_identity
    current_user_id = get_jwt_identity()
    
    # Only officers and admins can train models
    # (Add role check here)
    
    data = request.get_json()
    days_back = data.get('days_back', 90)
    
    try:
        trainer = ModelTrainer()
        results = trainer.train_models(days_back)
        
        best_model = max(results.keys(), key=lambda k: results[k]['test_performance']['f1'])
        
        return jsonify({
            'training_results': results,
            'best_model': best_model,
            'training_data_days': days_back,
            'trained_by': current_user_id,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@predictive_bp.get("/hotspots")
@jwt_required()
def get_predictive_hotspots():
    """
    Get predicted crime hotspots for specified time horizon.
    
    Query params: days_ahead (default 7), model (default random_forest)
    Response: { "hotspots": [...], "prediction_metadata": {...} }
    """
    days_ahead = request.args.get('days_ahead', 7, type=int)
    model_name = request.args.get('model', 'random_forest')
    
    try:
        generator = PredictionGenerator()
        hotspots = generator.generate_predictive_hotspots(days_ahead, model_name)
        
        return jsonify({
            'hotspots': hotspots,
            'prediction_metadata': {
                'days_ahead': days_ahead,
                'model_used': model_name,
                'total_hotspots': len(hotspots),
                'high_risk_count': len([h for h in hotspots if h['risk_level'] == 'HIGH']),
                'medium_risk_count': len([h for h in hotspots if h['risk_level'] == 'MEDIUM']),
                'low_risk_count': len([h for h in hotspots if h['risk_level'] == 'LOW'])
            },
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@predictive_bp.get("/accuracy")
@jwt_required()
def get_model_accuracy():
    """
    Get accuracy metrics for trained prediction models.
    
    Response: { "model_performance": {...}, "comparison": {...} }
    """
    try:
        trainer = ModelTrainer()
        
        if not trainer.model_performance:
            return jsonify({'error': 'No models trained yet'}), 400
        
        return jsonify({
            'model_performance': trainer.model_performance,
            'best_model': max(trainer.model_performance.keys(), 
                           key=lambda k: trainer.model_performance[k]['f1']),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@predictive_bp.post("/evaluate-model")
@jwt_required()
def evaluate_model():
    """
    Evaluate a specific model on test data.
    
    Request: { "model_name": str, "test_data_days": int }
    Response: { "evaluation_results": {...} }
    """
    data = request.get_json()
    model_name = data.get('model_name', 'random_forest')
    test_data_days = data.get('test_data_days', 30)
    
    try:
        trainer = ModelTrainer()
        
        # This would implement proper evaluation on held-out test set
        # For now, return cached performance metrics
        
        if model_name not in trainer.model_performance:
            return jsonify({'error': f'Model {model_name} not found'}), 404
        
        return jsonify({
            'model_name': model_name,
            'evaluation_results': trainer.model_performance[model_name],
            'test_data_period_days': test_data_days,
            'evaluated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

#### 4.2 Register Predictive Blueprint

**File:** `backend/app/__init__.py`

```python
# Add to existing imports
from app.api.v1.routes.predictive import predictive_bp

# Add to blueprint registration
app.register_blueprint(predictive_bp, url_prefix="/api/v1/predictive")
```

---

### **Phase 5: Frontend Integration (Day 3)**

#### 5.1 Create Predictive Hotspots Component

**File:** `frontend/src/components/predictive/PredictiveHotspots.tsx`

```typescript
"use client";

import { useEffect, useState } from 'react';
import { api } from '@/lib/client';

interface PredictiveHotspot {
  centroid: { lat: number; lng: number };
  crime_probability: number;
  risk_level: string;
  prediction_count: number;
  confidence: number;
  boundary_radius_km: number;
}

export default function PredictiveHotspots() {
  const [hotspots, setHotspots] = useState<PredictiveHotspot[]>([]);
  const [loading, setLoading] = useState(true);
  const [daysAhead, setDaysAhead] = useState(7);

  useEffect(() => {
    loadPredictiveHotspots();
  }, [daysAhead]);

  const loadPredictiveHotspots = async () => {
    try {
      setLoading(true);
      const data = await api(`/predictive/hotspots?days_ahead=${daysAhead}`);
      setHotspots(data.hotspots);
    } catch (error) {
      console.error('Failed to load predictive hotspots:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'HIGH': return 'bg-red-500';
      case 'MEDIUM': return 'bg-orange-500';
      case 'LOW': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Predictive Crime Hotspots</h2>
        <select 
          value={daysAhead}
          onChange={(e) => setDaysAhead(Number(e.target.value))}
          className="border rounded px-3 py-2"
        >
          <option value={1}>1 Day Ahead</option>
          <option value={3}>3 Days Ahead</option>
          <option value={7}>7 Days Ahead</option>
        </select>
      </div>

      {loading ? (
        <div>Loading predictions...</div>
      ) : hotspots.length === 0 ? (
        <div>No high-risk predictions for this time period</div>
      ) : (
        <div className="grid gap-4">
          {hotspots.map((hotspot, idx) => (
            <div key={idx} className={`p-4 rounded-lg ${getRiskColor(hotspot.risk_level)} bg-opacity-20`}>
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold">{hotspot.risk_level} RISK AREA</h3>
                  <p className="text-sm">
                    Location: {hotspot.centroid.lat.toFixed(4)}, {hotspot.centroid.lng.toFixed(4)}
                  </p>
                  <p className="text-sm">
                    Probability: {(hotspot.crime_probability * 100).toFixed(1)}%
                  </p>
                  <p className="text-sm">
                    Confidence: {(hotspot.confidence * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm">{hotspot.prediction_count} predictions</p>
                  <p className="text-sm">Radius: {hotspot.boundary_radius_km.toFixed(1)}km</p>
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
1. How accurately can ML models predict future crime locations?
2. Which algorithm performs best for crime prediction in this context?
3. What is the optimal prediction horizon for operational use?

### **Evaluation Metrics:**
- **Prediction Accuracy:** Overall accuracy of crime occurrence predictions
- **Precision/Recall:** For high-risk predictions
- **Spatial Accuracy:** How close are predictions to actual crime locations
- **Temporal Accuracy:** How well do predictions match actual timing

### **Success Criteria:**
- Model accuracy ≥ 65% for 7-day predictions
- High-risk predictions have precision ≥ 70%
- Spatial prediction error < 2km on average
- Model training time < 5 minutes for 90 days of data

---

## 🎯 Acceptance Checklist

### **Backend Requirements:**
- ✅ Feature engineering pipeline extracts comprehensive features
- ✅ ML models train successfully and achieve target accuracy
- ✅ Prediction generation creates valid hotspot areas
- ✅ API endpoints provide prediction data
- ✅ Model persistence saves trained models

### **Frontend Requirements:**
- ✅ Predictive hotspots displayed on map
- ✅ Risk levels color-coded appropriately
- ✅ Time horizon selection available
- ✅ Prediction confidence displayed

### **Testing Requirements:**
- ✅ Unit tests for feature engineering
- ✅ Model evaluation on test dataset
- ✅ Prediction validation against historical data
- ✅ Performance benchmarks for training/inference

### **Academic Requirements:**
- ✅ ML methodology documented
- ✅ Feature engineering explained
- ✅ Model comparison results collected
- ✅ Prediction accuracy evaluated

---

## 🚀 Next Steps

After completing Predictive Crime Hotspots:

1. **Move to Priority 4:** Implement Real-Time Incident Severity Alerts with WebSockets
2. **Documentation:** Update dissertation with predictive modeling methodology
3. **Validation:** Test predictions against actual crime data
4. **Refinement:** Tune model parameters based on results

**Implementation Guide:** `docs/12_REALTIME_ALERTS.md`

---

## 📝 Notes for Dissertation

### **Chapter 3 - Methodology Additions:**
- **Section 3.X: Predictive Modeling Methodology**
  - Feature engineering approach and rationale
  - ML algorithm selection and comparison
  - Training dataset creation and validation
  - Prediction generation methodology

### **Chapter 4 - Results Additions:**
- **Section 4.X: Predictive Model Results**
  - Model comparison table (Random Forest vs Gradient Boosting)
  - Feature importance analysis
  - Prediction accuracy by time horizon
  - Spatial prediction accuracy analysis

### **Academic Contributions:**
- Novel spatiotemporal feature engineering for crime prediction
- Comparative analysis of ML algorithms for crime forecasting
- Practical prediction system for law enforcement DSS
- Evaluation framework for predictive policing systems

This feature provides strong technical contribution while being implementable within 2-3 days.
