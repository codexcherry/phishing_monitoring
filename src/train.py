import pandas as pd
import joblib
import os
import sys

# Ensure src is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from src.data_generator import PhishingDataGenerator

# Try to import feature_extractor for real data
try:
    from src.feature_extractor import URLFeatureExtractor
    REAL_DATA_AVAILABLE = True
except ImportError:
    REAL_DATA_AVAILABLE = False

def train_model(use_real_data=True, sample_size=10000):
    """
    Train the phishing detection model.
    
    Args:
        use_real_data: If True, use Kaggle dataset. If False, use synthetic data.
        sample_size: Number of samples to use from the dataset.
    """
    
    if use_real_data and REAL_DATA_AVAILABLE:
        print("Loading real phishing dataset from Kaggle...")
        
        # Check if dataset exists
        dataset_path = 'data/phishing_site_urls.csv'
        if os.path.exists('data/cybersecurity_extraction.csv'):
            dataset_path = 'data/cybersecurity_extraction.csv'
            
        if not os.path.exists(dataset_path):
            print(f"\nERROR: Dataset not found at {dataset_path}")
            print("Please download the dataset from Kaggle:")
            print("https://www.kaggle.com/datasets/taruntiwarihp/phishing-site-urls")
            print("\nSee data/DOWNLOAD_INSTRUCTIONS.md for details.")
            print("\nFalling back to synthetic data...")
            use_real_data = False
        else:
            # Extract features from real URLs
            extractor = URLFeatureExtractor()
            df = extractor.process_dataset(
                dataset_path, 
                sample_size=sample_size,
                label_column='Label', # Default, will be overridden by process_dataset logic for specific file
                url_column='URL'
            )
            print(f"Loaded {len(df)} URLs from {dataset_path}")
    
    if not use_real_data or not REAL_DATA_AVAILABLE:
        print("Generating synthetic training data...")
        gen = PhishingDataGenerator(random_state=42)
        df = gen.generate_data(n_samples=sample_size)
    
    X = df.drop(columns=['is_phishing'])
    y = df['is_phishing']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Random Forest Classifier...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    
    y_pred = clf.predict(X_test)
    print("\nModel Performance:")
    print(classification_report(y_test, y_pred))
    
    # Save artifacts
    if not os.path.exists('models'):
        os.makedirs('models')
        
    joblib.dump(clf, 'models/phishing_model.pkl')
    # Save X_train as reference data for drift detection
    X_train.to_csv('models/reference_data.csv', index=False)
    
    print("\nModel and reference data saved to 'models/' directory.")
    
    # Save metadata
    metadata = {
        'data_source': 'real' if use_real_data else 'synthetic',
        'sample_size': len(df),
        'train_size': len(X_train),
        'test_size': len(X_test),
        'test_accuracy': accuracy_score(y_test, y_pred)
    }
    
    import json
    with open('models/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nMetadata: {metadata}")

if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    use_real = '--synthetic' not in sys.argv
    sample_size = 10000
    
    if '--sample' in sys.argv:
        idx = sys.argv.index('--sample')
        if idx + 1 < len(sys.argv):
            sample_size = int(sys.argv[idx + 1])
    
    train_model(use_real_data=use_real, sample_size=sample_size)
