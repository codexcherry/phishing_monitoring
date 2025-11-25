import pandas as pd

try:
    df = pd.read_csv(r"C:\Users\ASUS\Downloads\cybersecurity_extraction.csv", sep=';', on_bad_lines='skip')
    print("Columns:", df.columns.tolist())
    print("\nFirst 5 rows (id, threat_status, stats_malicious):")
    print(df[['id', 'threat_status', 'stats_malicious']].head())
    print("\nValue counts for 'threat_status':")
    print(df['threat_status'].value_counts())
except Exception as e:
    print(f"Error: {e}")
