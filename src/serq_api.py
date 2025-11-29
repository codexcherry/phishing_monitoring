"""
SERQ API Integration for Real-time URL Reputation Checking
"""
import requests
import os
import logging
from typing import Dict, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SERQAPIClient:
    """
    Client for SERQ API to check URL reputation in real-time.
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize SERQ API client.
        
        Args:
            api_key: SERQ API key. If None, will try to get from environment variable SERQ_API_KEY
            base_url: Base URL for SERQ API. If None, will try to get from environment variable SERQ_API_BASE_URL
        """
        self.api_key = api_key or os.getenv('SERQ_API_KEY', '')
        self.base_url = base_url or os.getenv('SERQ_API_BASE_URL', 'https://api.serq.io/v1')
        self.timeout = 10  # seconds
        
    def check_url(self, url: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Check URL reputation using SERQ API.
        
        Args:
            url: URL to check
            
        Returns:
            Tuple of (success, result_dict, error_message)
            - success: True if API call succeeded
            - result_dict: Contains 'is_legitimate', 'is_malicious', 'confidence', etc.
            - error_message: Error message if API call failed
        """
        if not self.api_key:
            logger.warning("SERQ API key not configured")
            return False, None, "SERQ API key not configured"
        
        logger.info(f"Checking URL with SERQ API: {url}")
        
        try:
            # Try different common API patterns
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'X-API-Key': self.api_key  # Alternative header format
            }
            
            # Pattern 1: POST with URL in body
            payload = {'url': url}
            
            # Try multiple endpoint patterns
            endpoints = [
                f'{self.base_url}/check',
                f'{self.base_url}/url/check',
                f'{self.base_url}/reputation',
                f'{self.base_url}/scan'
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.post(
                        endpoint,
                        json=payload,
                        headers=headers,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"SERQ API response from {endpoint}: {data}")
                        return self._parse_response(data)
                    elif response.status_code == 404:
                        continue  # Try next endpoint
                    else:
                        # Try GET request pattern
                        try:
                            response = requests.get(
                                f"{endpoint}?url={url}",
                                headers=headers,
                                timeout=self.timeout
                            )
                            if response.status_code == 200:
                                data = response.json()
                                logger.info(f"SERQ API response from {endpoint} (GET): {data}")
                                return self._parse_response(data)
                        except:
                            continue
                            
                except requests.exceptions.RequestException:
                    continue
            
            # If all endpoints failed, try alternative API format
            # Some APIs use different authentication
            alt_headers = {
                'apikey': self.api_key,
                'Content-Type': 'application/json'
            }
            
            for endpoint in endpoints:
                try:
                    response = requests.post(
                        endpoint,
                        json=payload,
                        headers=alt_headers,
                        timeout=self.timeout
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return self._parse_response(data)
                except:
                    continue
            
            return False, None, f"All API endpoints failed. Last status: {response.status_code if 'response' in locals() else 'N/A'}"
            
        except Exception as e:
            return False, None, f"SERQ API error: {str(e)}"
    
    def _parse_response(self, data: Dict) -> Tuple[bool, Dict, Optional[str]]:
        """
        Parse SERQ API response to extract reputation information.
        
        Handles various response formats:
        - { "is_legitimate": true, "confidence": 0.95 }
        - { "status": "safe", "reputation": "good" }
        - { "malicious": false, "verified": true }
        - { "result": "legitimate", "score": 0.9 }
        """
        try:
            result = {
                'is_legitimate': None,
                'is_malicious': None,
                'confidence': None,
                'verified': False,
                'raw_response': data
            }
            
            # Try to extract is_legitimate/is_malicious from various formats
            if 'is_legitimate' in data:
                result['is_legitimate'] = bool(data['is_legitimate'])
                result['confidence'] = float(data.get('confidence', 1.0))
            elif 'is_malicious' in data:
                result['is_malicious'] = bool(data['is_malicious'])
                result['is_legitimate'] = not result['is_malicious']
                result['confidence'] = float(data.get('confidence', 1.0))
            elif 'status' in data:
                status = str(data['status']).lower()
                result['is_legitimate'] = status in ['safe', 'legitimate', 'good', 'clean', 'verified']
                result['is_malicious'] = status in ['malicious', 'phishing', 'unsafe', 'bad', 'blocked']
                result['confidence'] = float(data.get('confidence', data.get('score', 1.0)))
            elif 'reputation' in data:
                rep = str(data['reputation']).lower()
                result['is_legitimate'] = rep in ['good', 'safe', 'legitimate', 'trusted']
                result['is_malicious'] = rep in ['bad', 'malicious', 'suspicious', 'phishing']
                result['confidence'] = float(data.get('confidence', data.get('score', 0.9)))
            elif 'result' in data:
                res = str(data['result']).lower()
                result['is_legitimate'] = res in ['legitimate', 'safe', 'good', 'clean']
                result['is_malicious'] = res in ['malicious', 'phishing', 'unsafe']
                result['confidence'] = float(data.get('score', data.get('confidence', 0.9)))
            elif 'malicious' in data:
                result['is_malicious'] = bool(data['malicious'])
                result['is_legitimate'] = not result['is_malicious']
                result['confidence'] = float(data.get('confidence', data.get('score', 1.0)))
            elif 'verified' in data and data['verified']:
                # If verified as legitimate, trust it
                result['is_legitimate'] = True
                result['verified'] = True
                result['confidence'] = 1.0
            else:
                # Unknown format, return None to use model prediction
                return True, result, None
            
            # If we got a definitive answer, mark as verified
            if result['is_legitimate'] is not None:
                result['verified'] = True
                if result['confidence'] is None:
                    result['confidence'] = 1.0  # 100% confidence if SERQ confirms
            
            return True, result, None
            
        except Exception as e:
            return False, None, f"Error parsing SERQ response: {str(e)}"

