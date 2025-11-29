# SERQ API Integration & URL Validation Guide

This document explains how to use the SERQ API integration and URL validation for real-time URL reputation checking.

## Overview

The phishing detection system now has a multi-layered approach for URL checking:

1. **URL Validation (First Check)**: The system validates if the URL exists and is reachable
   - If URL is **unreachable** (DNS failure, 404, timeout, etc.) → **ALERT**: Highly suspicious, flagged as potential phishing
   - If URL is **reachable** → Continue to next checks
   
2. **SERQ API Check (Second Check)**: The system checks with SERQ API for real-time reputation
   - If SERQ confirms the URL is **legitimate** (known good), it returns **100% confidence** that it's safe
   - If SERQ confirms the URL is **malicious**, it returns **100% confidence** that it's phishing
   
3. **ML Model Prediction (Fallback)**: If SERQ doesn't provide a definitive answer, the system uses the ML model prediction

## Configuration

### Setting the API Key

The SERQ API key can be configured in two ways:

#### Option 1: Environment Variable (Recommended)
```bash
# Windows PowerShell
$env:SERQ_API_KEY="775bf88d18658f9e3b81d9766ee63b77e7dc88ad9f873519751d25c180558ae2"

# Windows CMD
set SERQ_API_KEY=775bf88d18658f9e3b81d9766ee63b77e7dc88ad9f873519751d25c180558ae2

# Linux/Mac
export SERQ_API_KEY="775bf88d18658f9e3b81d9766ee63b77e7dc88ad9f873519751d25c180558ae2"
```

#### Option 2: Hardcoded in app.py
The API key is already set in `src/web/app.py` as a fallback:
```python
SERQ_API_KEY = os.getenv('SERQ_API_KEY', '775bf88d18658f9e3b81d9766ee63b77e7dc88ad9f873519751d25c180558ae2')
```

### Custom API Endpoint

If your SERQ API uses a different endpoint, set the `SERQ_API_BASE_URL` environment variable:
```bash
export SERQ_API_BASE_URL="https://your-custom-api-endpoint.com/v1"
```

## How It Works

### API Request Flow

1. When a URL is submitted via the `/api/predict` endpoint:
   
   **Step 0: URL Validation**
   - The system first validates if the URL is reachable
   - Checks DNS resolution, HTTP connectivity, and status codes
   - **If unreachable**: Immediately flags as suspicious (95% phishing probability) and shows alert
   - **If reachable**: Continues to next step
   
   **Step 1: SERQ API Check** (if URL is reachable)
   - The system calls SERQ API with the URL
   - SERQ API checks the URL against its reputation database

2. Response Handling:
   - **If URL is unreachable**: Returns `is_phishing: true, probability: 0.95` with alert message
   - **If SERQ confirms legitimate**: Returns `is_phishing: false, probability: 0.0` (100% safe)
   - **If SERQ confirms malicious**: Returns `is_phishing: true, probability: 1.0` (100% phishing)
   - **If SERQ is inconclusive or unavailable**: Falls back to ML model prediction

### URL Validation Checks

The system performs the following validation checks:
- **DNS Resolution**: Verifies the domain name can be resolved
- **HTTP/HTTPS Connectivity**: Checks if the server responds
- **Status Codes**: 
  - `200-204`: URL exists and is accessible
  - `301-308`: URL redirects (exists)
  - `404`: URL not found (suspicious)
  - `403/401`: Access denied (exists but restricted)
  - `500+`: Server errors (suspicious)
- **SSL Certificate**: Validates HTTPS certificates
- **Connection Timeout**: Detects if server doesn't respond

**Suspicious Unreachable Errors:**
- DNS failure (domain doesn't exist)
- 404 Not Found
- Connection timeout
- Connection errors
- SSL certificate errors

### Response Format

**For Unreachable URLs:**
```json
{
  "url": "https://nonexistent-site.com",
  "is_phishing": true,
  "probability": 0.95,
  "url_unreachable": true,
  "url_validation_error": "DNS resolution failed for nonexistent-site.com",
  "url_error_type": "DNS_FAILURE",
  "url_exists": false,
  "url_is_reachable": false,
  "method": "URL Validation (Unreachable)",
  "alert": "⚠️ URL is unreachable: DNS resolution failed...",
  "features": {...}
}
```

**For SERQ Verified URLs:**
```json
{
  "url": "https://example.com",
  "is_phishing": false,
  "probability": 0.0,
  "serq_verified": true,
  "serq_legitimate": true,
  "serq_confidence": 1.0,
  "method": "SERQ API (Verified Legitimate)",
  "url_exists": true,
  "url_is_reachable": true,
  "features": {...}
}
```

**For ML Model Predictions:**
```json
{
  "url": "https://example.com",
  "is_phishing": false,
  "probability": 0.15,
  "method": "ML Model",
  "url_exists": true,
  "url_is_reachable": true,
  "url_status_code": 200,
  "features": {...}
}
```

## API Endpoint Patterns

The SERQ client tries multiple common API patterns:
- `POST /v1/check`
- `POST /v1/url/check`
- `POST /v1/reputation`
- `POST /v1/scan`
- `GET /v1/check?url=...`

If your SERQ API uses a different format, you may need to update `src/serq_api.py` to match your API's specific requirements.

## Response Parsing

The client handles various response formats:
- `{"is_legitimate": true, "confidence": 0.95}`
- `{"status": "safe", "reputation": "good"}`
- `{"malicious": false, "verified": true}`
- `{"result": "legitimate", "score": 0.9}`

## Testing

To test the integration:

1. Start the Flask server:
   ```bash
   python src/web/app.py
   ```

2. Use the web interface or make a POST request:
   ```bash
   curl -X POST http://localhost:5000/api/predict \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com"}'
   ```

3. Check the response for `serq_verified` field to see if SERQ API was used

## Troubleshooting

### SERQ API Not Responding

If SERQ API is unavailable or returns errors:
- The system automatically falls back to ML model prediction
- Check the `serq_error` field in the response for details
- Verify your API key is correct
- Check network connectivity

### API Key Issues

- Ensure the API key is set correctly
- Check that the API key has proper permissions
- Verify the API key format matches SERQ's requirements

### Custom API Format

If your SERQ API uses a different format:
1. Update `src/serq_api.py` in the `_parse_response()` method
2. Add your API's specific response format handling
3. Update the endpoint URLs if needed

## Benefits

- **100% Accuracy for Known URLs**: URLs verified by SERQ get 100% confidence
- **Real-time Updates**: SERQ database is updated in real-time
- **Fallback Protection**: ML model still works if SERQ is unavailable
- **Hybrid Approach**: Combines real-time reputation with ML-based detection

