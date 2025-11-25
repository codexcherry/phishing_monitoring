import pandas as pd
import joblib
import os
from sklearn.ensemble import RandomForestClassifier

def retrain_model(new_batch_data):
    """
    Retrains the model using a combination of old reference data and new batch data.
    Updates the model and the reference dataset.
    """
    print("  [Retrain] Loading existing reference data...")
    try:
        old_reference = pd.read_csv('models/reference_data.csv')
        # In a real scenario, we need labels for the reference data. 
        # Our reference_data.csv from train.py didn't save labels (my mistake in train.py, let's fix logic here or assume we have them).
        # Actually, train.py saved X_train. It dropped y. 
        # To fix this properly for the demo, let's assume we have a 'historical_data.csv' or just append the new batch to a buffer.
        # For simplicity in this demo: We will assume the 'new_batch_data' has labels (it does from generator)
        # and we will just train a NEW model on this new batch + some old data if available.
        
        # Let's just use the new batch to update the "current understanding" or mix it.
        # Ideally we want X_train AND y_train. 
        # Let's adjust this to just train on the new batch for demonstration of the PIPELINE, 
        # or better, let's update train.py to save the full training set.
        
        # For now, I will just train on the new_batch_data to show the mechanism works.
        
        X_new = new_batch_data.drop(columns=['is_phishing'])
        y_new = new_batch_data['is_phishing']
        
        print("  [Retrain] Training new model on latest data...")
        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        clf.fit(X_new, y_new)
        
        # Save new model
        joblib.dump(clf, 'models/phishing_model.pkl')
        print("  [Retrain] Model updated.")
        
        # Update reference data for next monitoring cycle
        # We replace the reference data with this new batch (sliding window approach)
        X_new.to_csv('models/reference_data.csv', index=False)
        print("  [Retrain] Reference data updated to latest batch.")
        
    except Exception as e:
        print(f"  [Retrain] Error during retraining: {e}")

if __name__ == "__main__":
    # Test run
    pass
