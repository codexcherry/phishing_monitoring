import pandas as pd
import joblib
import time
import sys
import os

# Ensure src is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_generator import PhishingDataGenerator
from src.drift_detector import DriftDetector
from src.retrain import retrain_model

class ModelMonitor:
    def __init__(self, reference_data_path='models/reference_data.csv'):
        self.reference_data_path = reference_data_path
        self.load_reference_data()
        self.generator = PhishingDataGenerator(random_state=None) # Random state None for real randomness

    def load_reference_data(self):
        try:
            self.reference_data = pd.read_csv(self.reference_data_path)
            self.detector = DriftDetector(self.reference_data)
            return True
        except FileNotFoundError:
            print("Error: Reference data not found.")
            self.reference_data = None
            self.detector = None
            return False

    def process_batch(self, batch_size=500, drift_type=None):
        """
        Generates a batch, checks for drift, and retrains if necessary.
        Returns a dictionary with results for the UI.
        """
        if self.detector is None:
            if not self.load_reference_data():
                return {'error': 'Reference data not found. Train model first.'}

        # Generate data
        new_data = self.generator.generate_data(n_samples=batch_size, drift_type=drift_type)
        features_only = new_data.drop(columns=['is_phishing'])
        
        # Detect Drift
        drift_detected, report = self.detector.detect_drift(features_only)
        
        result = {
            'data': new_data,
            'drift_detected': drift_detected,
            'drift_report': report,
            'retrained': False
        }

        if drift_detected:
            # Trigger Retraining
            retrain_model(new_data)
            # Reload reference data
            self.load_reference_data()
            result['retrained'] = True
            
        return result

def run_monitoring_loop():
    # Legacy CLI support
    monitor = ModelMonitor()
    if monitor.detector is None:
        return

    batches = [
        ('Normal Batch 1', None),
        ('Normal Batch 2', None),
        ('Drifted Batch (Data Drift)', 'data_drift'),
        ('Drifted Batch (Concept Drift)', 'concept_drift')
    ]
    
    for batch_name, drift_type in batches:
        print(f"\n--- Processing {batch_name} ---")
        result = monitor.process_batch(drift_type=drift_type)
        
        if 'error' in result:
            print(result['error'])
            break
            
        if result['drift_detected']:
            print(f"ALARM: Drift Detected in {batch_name}!")
            for feature, res in result['drift_report'].items():
                if res['drift_detected']:
                    print(f"  - Feature '{feature}' drifted ({res['test']} p-value: {res['p_value']:.4f})")
            
            if result['retrained']:
                print("Triggered automated retraining... Model updated.")
        else:
            print("Status: Healthy. No significant drift detected.")
            
        time.sleep(1)

if __name__ == "__main__":
    run_monitoring_loop()
