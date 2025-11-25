import numpy as np
import pandas as pd
import os

class PhishingDataGenerator:
    def __init__(self, random_state=42, real_data_path=None):
        self.rng = np.random.default_rng(random_state)
        # Check for user provided dataset first
        if os.path.exists('data/cybersecurity_extraction.csv'):
            self.real_data_path = 'data/cybersecurity_extraction.csv'
        else:
            self.real_data_path = real_data_path or 'data/phishing_site_urls.csv'
        
        self.real_data = None
        
        # Try to load real data if available
        if os.path.exists(self.real_data_path):
            try:
                from src.feature_extractor import URLFeatureExtractor
                print(f"Loading real data from {self.real_data_path}...")
                extractor = URLFeatureExtractor()
                self.real_data = extractor.process_dataset(self.real_data_path)
                print(f"Loaded {len(self.real_data)} real URLs")
            except Exception as e:
                print(f"Could not load real data: {e}")
                self.real_data = None

    def generate_data(self, n_samples=1000, drift_type=None, use_real_data=False):
        """
        Generates phishing dataset (synthetic or real).
        
        Args:
            n_samples: Number of samples to generate/sample
            drift_type: Type of drift to inject ('data_drift', 'concept_drift', or None)
            use_real_data: If True and real data is available, sample from it
        
        Features:
        - url_length: Length of the URL.
        - num_special_chars: Count of special characters like @, -, _.
        - has_ip_address: Binary (0 or 1).
        - https_token: Binary (0 or 1).
        - is_phishing: Target variable (0: Legitimate, 1: Phishing).
        """
        
        if use_real_data and self.real_data is not None:
            # Sample from real data
            if n_samples >= len(self.real_data):
                return self.real_data.copy()
            else:
                return self.real_data.sample(n=n_samples, random_state=self.rng.integers(0, 10000))
        
        # Generate synthetic data
        # Base distributions for Legitimate (0) and Phishing (1)
        # Legitimate: shorter URLs, fewer special chars, rarely IP, usually HTTPS
        # Phishing: longer URLs, more special chars, sometimes IP, sometimes HTTPS (mimicry)
        
        y = self.rng.choice([0, 1], size=n_samples, p=[0.7, 0.3]) # 30% phishing rate
        
        url_length = np.zeros(n_samples)
        num_special_chars = np.zeros(n_samples)
        has_ip_address = np.zeros(n_samples)
        https_token = np.zeros(n_samples)
        
        for i in range(n_samples):
            if y[i] == 0: # Legitimate
                url_length[i] = self.rng.normal(loc=25, scale=5)
                num_special_chars[i] = self.rng.poisson(lam=1)
                has_ip_address[i] = 0 if self.rng.random() > 0.01 else 1
                https_token[i] = 1 if self.rng.random() > 0.1 else 0 # Most have HTTPS
            else: # Phishing
                url_length[i] = self.rng.normal(loc=60, scale=15)
                num_special_chars[i] = self.rng.poisson(lam=4)
                has_ip_address[i] = 1 if self.rng.random() > 0.3 else 0
                https_token[i] = 1 if self.rng.random() > 0.6 else 0 # Less likely to have valid HTTPS initially

        # Apply Drift if requested
        if drift_type == 'concept_drift':
            # Concept Drift: Relationship changes. 
            # E.g., Attackers start using short URLs (mimicking legit) but still phishing.
            # We modify the features for phishing class to look more like legitimate.
            mask_phishing = (y == 1)
            # Attackers use shorter URLs
            url_length[mask_phishing] = self.rng.normal(loc=30, scale=8, size=mask_phishing.sum())
            
        elif drift_type == 'data_drift':
            # Data Drift: Input distribution changes globally.
            # E.g., A new TLD becomes popular for EVERYONE, or URL shorteners become standard.
            # Let's say ALL URLs get longer on average.
            url_length = url_length + 20
            
        # Create DataFrame
        df = pd.DataFrame({
            'url_length': url_length,
            'num_special_chars': num_special_chars,
            'has_ip_address': has_ip_address,
            'https_token': https_token,
            'is_phishing': y
        })
        
        return df
