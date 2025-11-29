# Phishing URL Detection System

A real-time phishing detection system that combines machine learning, SERQ API reputation checking, and URL validation to identify malicious URLs with high accuracy.

## Features

- **Real-time URL Checking**: Check any URL instantly for phishing threats
- **SERQ API Integration**: 100% accurate reputation verification for known URLs
- **URL Validation**: Detects unreachable or non-existent URLs (highly suspicious)
- **Machine Learning Model**: Random Forest classifier for unknown URLs
- **Interactive Dashboard**: Web-based interface for easy URL checking
- **Drift Detection**: Monitors model performance and auto-retrains when needed

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Train the Model (First Time)

```bash
python src/train.py
```

### 3. Run the Web Application

```bash
python src/web/app.py
```

Open your browser and go to: `http://localhost:5000`

## How It Works

When you check a URL, the system follows this process:

1. **URL Validation**: Checks if the URL exists and is reachable
   - If unreachable → Flags as suspicious (95% phishing probability)

2. **SERQ API Check**: Queries SERQ API for reputation data
   - If verified legitimate → 100% safe
   - If verified malicious → 100% phishing

3. **ML Model Prediction**: Uses trained Random Forest model
   - Analyzes URL features (length, special chars, TLD, etc.)
   - Returns phishing probability

## Project Structure

```
phishing_monitoring/
├── models/              # Trained model and reference data
├── data/                # Training datasets (optional)
├── docs/                # Documentation
├── src/
│   ├── web/            # Flask web application
│   │   ├── app.py      # Main web server
│   │   ├── static/     # CSS and JavaScript
│   │   └── templates/ # HTML templates
│   ├── feature_extractor.py  # URL feature extraction
│   ├── serq_api.py     # SERQ API integration
│   ├── url_validator.py # URL validation
│   ├── train.py        # Model training
│   ├── monitor.py      # Drift detection
│   └── retrain.py      # Model retraining
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Configuration

### SERQ API Key

The SERQ API key is configured in `src/web/app.py`. You can also set it via environment variable:

```bash
export SERQ_API_KEY="your_api_key_here"
```

## Documentation

- [SERQ API Integration Guide](docs/SERQ_API_INTEGRATION.md) - Detailed SERQ API setup and usage
- [Model Monitoring Explanation](docs/model_monitoring_explanation.md) - Drift detection concepts

## Requirements

- Python 3.8+
- Flask
- scikit-learn
- pandas
- requests
- numpy
- scipy

## License

MIT License
