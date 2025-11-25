# Kaggle Dataset Download Instructions

## Dataset: Phishing Site URLs

**Source**: https://www.kaggle.com/datasets/taruntiwarihp/phishing-site-urls

### Option 1: Manual Download (Recommended)
1. Go to: https://www.kaggle.com/datasets/taruntiwarihp/phishing-site-urls
2. Click "Download" (requires free Kaggle account)
3. Extract `phishing_site_urls.csv` from the downloaded ZIP
4. Place it in `d:/CLi/phishing/data/phishing_site_urls.csv`

### Option 2: Using Kaggle API
```bash
# Install Kaggle CLI
pip install kaggle

# Configure API credentials (get from kaggle.com/account)
# Place kaggle.json in ~/.kaggle/ or C:\Users\<username>\.kaggle\

# Download dataset
kaggle datasets download -d taruntiwarihp/phishing-site-urls -p d:/CLi/phishing/data/

# Unzip
cd d:/CLi/phishing/data/
unzip phishing-site-urls.zip
```

### Dataset Structure
- **Rows**: 549,346 URLs
- **Columns**:
  - `URL`: The actual URL string
  - `Label`: "good" (legitimate) or "bad" (phishing)

### After Download
Run the training script to process the dataset:
```bash
python src/train.py
```
