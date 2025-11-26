# Phishing Model Monitoring and Drift Detection

A comprehensive demonstration of monitoring machine learning models in production, specifically tailored for phishing detection. This project illustrates how to detect **Data Drift** and **Concept Drift** and implements an automated retraining pipeline.

## 📌 Project Overview

In cybersecurity, attackers constantly evolve their tactics (e.g., using new TLDs, mimicking legitimate URL lengths). A static machine learning model will degrade in performance over time. This project provides a robust framework to:
1.  **Simulate Phishing Traffic**: Generate synthetic data with configurable drift patterns.
2.  **Monitor in Real-Time**: Check incoming data batches for statistical anomalies.
3.  **Detect Drift**: Use Kolmogorov-Smirnov (KS) and Chi-Square tests to identify shifts.
4.  **Auto-Retrain**: Automatically update the model when significant drift is detected.

## 🚀 Features

*   **Synthetic Data Generator**: Creates realistic phishing URL features (URL length, special chars, IP usage, HTTPS).
*   **Drift Detection Engine**:
    *   **Numerical Features**: KS-Test (Kolmogorov-Smirnov).
    *   **Categorical Features**: Chi-Square Test.
*   **Interactive Web Dashboard**: A premium Flask-based dashboard to visualize drift and control simulations.
*   **Automated Pipeline**: Seamless integration of training, monitoring, and retraining.
*   **Detailed Documentation**: In-depth explanation of drift concepts in `docs/`.

## 📂 Project Structure

```
phishing/
├── docs/
│   └── model_monitoring_explanation.md  # Deep dive into concepts & strategies
├── models/
│   ├── phishing_model.pkl               # Trained Random Forest model
│   └── reference_data.csv               # Baseline data for drift comparison
├── src/
│   ├── web/
│   │   ├── static/                      # CSS and JS assets
│   │   ├── templates/                   # HTML templates
│   │   └── app.py                       # Flask application entry point
│   ├── data_generator.py                # Generates synthetic normal & drifted data
│   ├── drift_detector.py                # Statistical tests implementation
│   ├── monitor.py                       # Main production simulation loop
│   ├── retrain.py                       # Retraining logic
│   └── train.py                         # Initial model training script
├── run_demo.py                          # CLI script to run the full demo
├── requirements.txt                     # Python dependencies
└── README.md                            # This file
```

## 🛠️ Installation

1.  **Clone the repository** (if applicable) or navigate to the project folder.
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## ⚡ Usage

### 1. Run the Web Dashboard (Recommended)

Start the Flask application to interactively monitor the model and inject drift:

```bash
python src/web/app.py
```

Then open your browser and navigate to: `http://localhost:5000`

### 2. Quick Start (CLI Demo)

To see the entire system in action via the command line with synthetic data:

```bash
python run_demo.py
```

### 3. Using Real Phishing Data

To use the Kaggle Phishing Site URLs dataset (549,346 URLs):

1. **Download the dataset**:
   - Visit: https://www.kaggle.com/datasets/taruntiwarihp/phishing-site-urls
   - Download `phishing_site_urls.csv`
   - Place it in `data/phishing_site_urls.csv`
   - See `data/DOWNLOAD_INSTRUCTIONS.md` for details

2. **Train with real data**:
   ```bash
   python src/train.py --sample 10000
   ```

3. **Run the dashboard**:
   ```bash
   python src/web/app.py
   ```

### What happens when you run the demo?
1.  **Training**: It trains a baseline Random Forest model and saves it.
2.  **Monitoring (Normal)**: It simulates incoming batches of "normal" traffic. The system reports "Healthy".
3.  **Monitoring (Drift)**: It injects "drifted" data (e.g., attackers changing URL patterns).
4.  **Alert & Retrain**: The system detects the drift (p-value < 0.05), raises an alarm, and automatically retrains the model on the new data.

## 🧠 Key Concepts

### Data Drift (Covariate Shift)
Changes in the distribution of input features.
*   *Example in Demo*: All URLs suddenly become longer (simulating a change in global web standards or attacker tools).

### Concept Drift
Changes in the relationship between inputs and the target label.
*   *Example in Demo*: Attackers start using short URLs (which were previously safe) for phishing.

## 🔧 Extensibility

This project is designed to be a template. You can extend it by:
*   Replacing `data_generator.py` with a real data stream (e.g., Kafka, RabbitMQ).
*   Adding more sophisticated drift detectors (e.g., Adversarial Validation, Population Stability Index).
*   Integrating with alerting tools (Slack, Email, PagerDuty) in `monitor.py`.

## 📄 License
MIT License
