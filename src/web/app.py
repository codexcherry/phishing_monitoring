from flask import Flask, render_template, jsonify, request
import pandas as pd
import json
import os
import sys

# Add parent directory to path to import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.monitor import ModelMonitor
from src.feature_extractor import URLFeatureExtractor
from src.serq_api import SERQAPIClient
from src.url_validator import URLValidator
import joblib
import numpy as np

app = Flask(__name__)

# Get the project root directory (two levels up from src/web)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

# Initialize Monitor with absolute path
# Initialize Monitor with absolute path
reference_data_path = os.path.join(PROJECT_ROOT, 'models', 'reference_data.csv')
monitor = ModelMonitor(reference_data_path=reference_data_path)

# Load Model
model_path = os.path.join(PROJECT_ROOT, 'models', 'phishing_model.pkl')
try:
    phishing_model = joblib.load(model_path)
    print(f"Model loaded from {model_path}")
except Exception as e:
    print(f"Error loading model: {e}")
    phishing_model = None

# Initialize Feature Extractor
extractor = URLFeatureExtractor()

# Initialize SERQ API Client
# SERQ API key - can be set via environment variable SERQ_API_KEY or passed here
SERQ_API_KEY = os.getenv('SERQ_API_KEY', '775bf88d18658f9e3b81d9766ee63b77e7dc88ad9f873519751d25c180558ae2')
serq_client = SERQAPIClient(api_key=SERQ_API_KEY)

# Initialize URL Validator
url_validator = URLValidator(timeout=5)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    """Returns current model statistics."""
    stats = {
        'model_status': 'Active',
        'reference_data_size': len(monitor.reference_data) if monitor.reference_data is not None else 0,
        'features': list(monitor.reference_data.columns) if monitor.reference_data is not None else []
    }
    return jsonify(stats)

@app.route('/api/process_batch', methods=['POST'])
def process_batch():
    """Processes a new batch of data."""
    data = request.json
    batch_size = int(data.get('batch_size', 500))
    drift_type = data.get('drift_type') # None, 'data_drift', 'concept_drift'
    
    if drift_type == 'none':
        drift_type = None
        
    result = monitor.process_batch(batch_size=batch_size, drift_type=drift_type)
    
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
        
    # Convert result to JSON-friendly format
    # Ensure numpy types are converted to native Python types
    response = {
        'drift_detected': bool(result['drift_detected']),
        'retrained': bool(result['retrained']),
        'drift_report': result['drift_report'],
        'timestamp': pd.Timestamp.now().strftime("%H:%M:%S"),
        # Sample data for visualization (first 100 rows)
        'batch_data': result['data'].head(100).to_dict(orient='records'),
        'reference_data_sample': monitor.reference_data.sample(min(100, len(monitor.reference_data))).to_dict(orient='records')
    }
    
    # Deep clean the response to ensure no numpy types remain
    def clean_numpy(obj):
        if isinstance(obj, (pd.Timestamp, pd.Timedelta)):
            return str(obj)
        if hasattr(obj, 'item'): # Numpy scalar
            return obj.item()
        if isinstance(obj, dict):
            return {k: clean_numpy(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [clean_numpy(v) for v in obj]
        return obj
        
    response = clean_numpy(response)
    
    response = clean_numpy(response)
    
    return jsonify(response)

@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Predicts if a URL is phishing or legitimate.
    Uses SERQ API for real-time reputation checking first, then falls back to model prediction.
    """
    if phishing_model is None:
        return jsonify({'error': 'Model not loaded'}), 500
        
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
        
    try:
        # Step 0: Validate URL - check if it exists and is reachable
        url_valid, validation_result, validation_error = url_validator.validate_url(url)
        
        # If URL is unreachable, flag it as suspicious
        if not url_valid:
            is_suspicious_unreachable = url_validator.is_suspicious_unreachable(validation_result)
            error_type = validation_result.get('error_type', 'UNKNOWN')
            
            # Extract features for analysis
            features = extractor.extract_features(url)
            
            # If unreachable, treat as highly suspicious (potential phishing)
            result = {
                'url': url,
                'is_phishing': True,  # Unreachable URLs are suspicious
                'probability': 0.95,  # High probability of phishing if unreachable
                'url_unreachable': True,
                'url_validation_error': validation_error,
                'url_error_type': error_type,
                'url_exists': False,
                'url_is_reachable': False,
                'method': 'URL Validation (Unreachable)',
                'alert': f'⚠️ URL is unreachable: {validation_error}',
                'features': features
            }
            return jsonify(result)
        
        # URL is reachable, continue with normal checks
        # Step 1: Check with SERQ API first for real-time reputation
        serq_success, serq_result, serq_error = serq_client.check_url(url)
        
        # If SERQ API confirms it's legitimate (known good), return 100% confidence
        if serq_success and serq_result and serq_result.get('is_legitimate') is True:
            # SERQ confirmed it's legitimate - 100% confidence it's safe
            result = {
                'url': url,
                'is_phishing': False,
                'probability': 0.0,  # 0% phishing = 100% safe
                'serq_verified': True,
                'serq_legitimate': True,
                'serq_confidence': serq_result.get('confidence', 1.0),
                'method': 'SERQ API (Verified Legitimate)',
                'url_exists': validation_result.get('exists', True),
                'url_is_reachable': validation_result.get('is_reachable', True),
                'features': extractor.extract_features(url)
            }
            return jsonify(result)
        
        # If SERQ API confirms it's malicious, return 100% phishing
        if serq_success and serq_result and serq_result.get('is_malicious') is True:
            result = {
                'url': url,
                'is_phishing': True,
                'probability': 1.0,  # 100% phishing
                'serq_verified': True,
                'serq_malicious': True,
                'serq_confidence': serq_result.get('confidence', 1.0),
                'method': 'SERQ API (Verified Malicious)',
                'url_exists': validation_result.get('exists', True),
                'url_is_reachable': validation_result.get('is_reachable', True),
                'features': extractor.extract_features(url)
            }
            return jsonify(result)
        
        # Step 2: If SERQ didn't provide definitive answer, use model prediction
        # Extract features
        features = extractor.extract_features(url)
        
        # Convert to DataFrame for prediction (expected by model)
        features_df = pd.DataFrame([features])
        
        # Predict using model
        prediction = phishing_model.predict(features_df)[0]
        probability = phishing_model.predict_proba(features_df)[0][1]  # Probability of class 1 (Phishing)
        
        # Determine method used
        method = 'ML Model'
        if serq_success and serq_result:
            method = 'ML Model (SERQ inconclusive)'
        elif not serq_success:
            method = f'ML Model (SERQ unavailable: {serq_error})'
        
        result = {
            'url': url,
            'is_phishing': bool(prediction),
            'probability': float(probability),
            'method': method,
            'serq_checked': serq_success,
            'serq_error': serq_error if not serq_success else None,
            'url_exists': validation_result.get('exists', True),
            'url_is_reachable': validation_result.get('is_reachable', True),
            'url_status_code': validation_result.get('status_code'),
            'features': features
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run on 0.0.0.0 to make accessible from outside
    app.run(debug=True, host='0.0.0.0', port=5000)
