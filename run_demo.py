import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.train import train_model
from src.monitor import run_monitoring_loop

def main():
    print("=== Step 1: Initial Model Training ===")
    train_model()
    
    print("\n=== Step 2: Start Monitoring Loop ===")
    print("This will simulate normal traffic, then drifted traffic, and trigger retraining.")
    run_monitoring_loop()
    
    print("\n=== Demo Completed ===")

if __name__ == "__main__":
    main()
