import re
import pandas as pd
from urllib.parse import urlparse

class URLFeatureExtractor:
    """
    Extracts features from raw URLs for phishing detection.
    """
    
    def __init__(self):
        # Regex pattern to detect IP addresses in URLs
        self.ip_pattern = re.compile(
            r'(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}'
            r'([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])'
        )
        
        self.suspicious_tlds = ['.top', '.xyz', '.info', '.club', '.live', '.online', '.site', '.cn', '.ru']
        self.suspicious_keywords = ['login', 'secure', 'account', 'update', 'verify', 'signin', 'banking', 'confirm', 'wallet']
        
    def extract_features(self, url):
        """
        Extract features from a single URL.
        
        Returns:
            dict: Dictionary of features
        """
        features = {}
        
        # 1. URL Length
        features['url_length'] = len(url)
        
        # 2. Number of Special Characters
        special_chars = ['@', '-', '_', '.', '?', '=', '&', '!', '#', '%', '+', '$', ',', '//']
        features['num_special_chars'] = sum(url.count(char) for char in special_chars)
        
        # 3. Has IP Address
        features['has_ip_address'] = 1 if self.ip_pattern.search(url) else 0
        
        # 4. HTTPS Token
        features['https_token'] = 1 if url.startswith('https://') else 0
        
        # 5. Suspicious TLD
        parsed = urlparse(url)
        hostname = parsed.netloc if parsed.netloc else parsed.path
        if '/' in hostname:
            hostname = hostname.split('/')[0]
        features['is_suspicious_tld'] = 1 if any(hostname.endswith(tld) for tld in self.suspicious_tlds) else 0
        
        # 6. Suspicious Keywords
        features['has_suspicious_keyword'] = 1 if any(keyword in url.lower() for keyword in self.suspicious_keywords) else 0
        
        return features
    
    def extract_features_batch(self, urls):
        """
        Extract features from a list of URLs.
        
        Args:
            urls: List of URL strings
            
        Returns:
            pd.DataFrame: DataFrame with extracted features
        """
        features_list = [self.extract_features(url) for url in urls]
        return pd.DataFrame(features_list)
    
    def process_dataset(self, csv_path, label_column='Label', url_column='URL', sample_size=None):
        """
        Load and process a phishing dataset CSV.
        
        Args:
            csv_path: Path to CSV file
            label_column: Name of the label column
            url_column: Name of the URL column
            sample_size: Optional number of rows to sample
            
        Returns:
            pd.DataFrame: DataFrame with features and labels
        """
        # Determine separator based on extension or content
        # For the user provided dataset, it uses ';'
        try:
            df = pd.read_csv(csv_path)
            if len(df.columns) < 2: # Likely wrong separator
                df = pd.read_csv(csv_path, sep=';', on_bad_lines='skip')
        except:
            df = pd.read_csv(csv_path, sep=';', on_bad_lines='skip')
            
        # Handle column renaming if needed for specific datasets
        if 'id' in df.columns and 'threat_status' in df.columns:
            url_column = 'id'
            label_column = 'threat_status'
        
        # Sample if requested
        if sample_size and sample_size < len(df):
            df = df.sample(n=sample_size, random_state=42)
        
        # Extract features
        features_df = self.extract_features_batch(df[url_column].values)
        
        # Convert labels
        # 'good'/'whitelist' -> 0
        # 'bad'/'malicious' -> 1
        if label_column in df.columns:
            labels = df[label_column].astype(str).str.lower().map({
                'good': 0, 'whitelist': 0, '0': 0,
                'bad': 1, 'malicious': 1, '1': 1
            })
            # Fill NaN if mapping failed for some rows
            labels = labels.fillna(0).astype(int)
            features_df['is_phishing'] = labels.values
        
        return features_df

if __name__ == "__main__":
    # Test with sample URLs
    extractor = URLFeatureExtractor()
    
    test_urls = [
        "https://www.google.com",
        "http://192.168.1.1/login",
        "http://suspicious-site-with-many-dashes-and-special-chars.com/login?user=admin&pass=123"
    ]
    
    for url in test_urls:
        features = extractor.extract_features(url)
        print(f"\nURL: {url}")
        print(f"Features: {features}")
