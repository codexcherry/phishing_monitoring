from flask import Flask, render_template, jsonify, request
import pandas as pd
import json
import os
import sys

# Add parent directory to path to import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.monitor import ModelMonitor
from src.feature_extractor import URLFeatureExtractor
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
    """Predicts if a URL is phishing or legitimate."""
    if phishing_model is None:
        return jsonify({'error': 'Model not loaded'}), 500
        
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
        
    try:
        # Extract features
        features = extractor.extract_features(url)
        
        # Convert to DataFrame for prediction (expected by model)
        features_df = pd.DataFrame([features])
        
        # Predict
        prediction = phishing_model.predict(features_df)[0]
        probability = phishing_model.predict_proba(features_df)[0][1] # Probability of class 1 (Phishing)
        
        result = {
            'url': url,
            'is_phishing': bool(prediction),
            'probability': float(probability),
            'features': features
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run on 0.0.0.0 to make accessible from outside
    app.run(debug=True, host='0.0.0.0', port=5000)
