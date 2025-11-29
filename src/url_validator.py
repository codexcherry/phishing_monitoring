"""
URL Validator - Checks if URLs are reachable and valid
"""
import requests
import socket
from urllib.parse import urlparse
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class URLValidator:
    """
    Validates URLs by checking DNS resolution, HTTP reachability, and status codes.
    """
    
    def __init__(self, timeout: int = 5):
        """
        Initialize URL validator.
        
        Args:
            timeout: Timeout in seconds for HTTP requests
        """
        self.timeout = timeout
        
    def validate_url(self, url: str) -> Tuple[bool, Dict, Optional[str]]:
        """
        Validate if a URL is reachable and exists.
        
        Args:
            url: URL to validate
            
        Returns:
            Tuple of (is_valid, result_dict, error_message)
            - is_valid: True if URL is reachable and returns valid status
            - result_dict: Contains 'exists', 'status_code', 'is_reachable', etc.
            - error_message: Error message if validation failed
        """
        result = {
            'exists': False,
            'is_reachable': False,
            'status_code': None,
            'dns_resolved': False,
            'has_ssl': False,
            'error_type': None
        }
        
        try:
            # Parse URL
            parsed = urlparse(url)
            
            # Check if URL has a valid scheme
            if not parsed.scheme:
                # Try adding https://
                url = 'https://' + url
                parsed = urlparse(url)
            
            # Extract hostname
            hostname = parsed.netloc or parsed.path.split('/')[0]
            if not hostname:
                return False, result, "Invalid URL format"
            
            # Step 1: Check DNS resolution
            try:
                socket.gethostbyname(hostname)
                result['dns_resolved'] = True
                logger.info(f"DNS resolved for {hostname}")
            except socket.gaierror:
                result['error_type'] = 'DNS_FAILURE'
                return False, result, f"DNS resolution failed for {hostname}"
            except Exception as e:
                result['error_type'] = 'DNS_ERROR'
                return False, result, f"DNS error: {str(e)}"
            
            # Step 2: Try HTTP/HTTPS request
            try:
                # Try HTTPS first
                response = requests.head(url, timeout=self.timeout, allow_redirects=True, verify=True)
                result['status_code'] = response.status_code
                result['has_ssl'] = url.startswith('https://')
                
                # Check if URL exists (2xx, 3xx are generally OK, 4xx/5xx are problematic)
                if response.status_code in [200, 201, 202, 204]:
                    result['exists'] = True
                    result['is_reachable'] = True
                    logger.info(f"URL {url} is reachable with status {response.status_code}")
                    return True, result, None
                elif response.status_code in [301, 302, 303, 307, 308]:
                    # Redirect - follow it
                    result['is_reachable'] = True
                    result['exists'] = True  # Redirect means URL exists
                    logger.info(f"URL {url} redirects (status {response.status_code})")
                    return True, result, None
                elif response.status_code == 404:
                    result['error_type'] = 'NOT_FOUND'
                    result['is_reachable'] = False
                    return False, result, f"URL not found (404) - {url}"
                elif response.status_code in [403, 401]:
                    result['error_type'] = 'ACCESS_DENIED'
                    result['is_reachable'] = True  # Server exists but access denied
                    result['exists'] = True
                    logger.warning(f"URL {url} exists but access denied (status {response.status_code})")
                    return True, result, None  # URL exists, just access restricted
                elif response.status_code >= 500:
                    result['error_type'] = 'SERVER_ERROR'
                    result['is_reachable'] = False
                    return False, result, f"Server error (status {response.status_code}) - {url}"
                else:
                    result['error_type'] = 'UNKNOWN_STATUS'
                    result['is_reachable'] = True
                    result['exists'] = True
                    return True, result, None
                    
            except requests.exceptions.SSLError as e:
                result['error_type'] = 'SSL_ERROR'
                result['is_reachable'] = False
                # Try HTTP if HTTPS fails
                http_url = url.replace('https://', 'http://')
                try:
                    response = requests.head(http_url, timeout=self.timeout, allow_redirects=True)
                    result['status_code'] = response.status_code
                    result['has_ssl'] = False
                    if response.status_code in [200, 301, 302]:
                        result['exists'] = True
                        result['is_reachable'] = True
                        logger.warning(f"URL {url} works on HTTP but not HTTPS")
                        return True, result, None
                except:
                    pass
                return False, result, f"SSL certificate error - {str(e)}"
                
            except requests.exceptions.Timeout:
                result['error_type'] = 'TIMEOUT'
                result['is_reachable'] = False
                return False, result, f"Request timeout - URL may be unreachable"
                
            except requests.exceptions.ConnectionError as e:
                result['error_type'] = 'CONNECTION_ERROR'
                result['is_reachable'] = False
                return False, result, f"Connection error - URL may not exist: {str(e)}"
                
            except requests.exceptions.RequestException as e:
                result['error_type'] = 'REQUEST_ERROR'
                result['is_reachable'] = False
                return False, result, f"Request failed: {str(e)}"
                
        except Exception as e:
            result['error_type'] = 'UNKNOWN_ERROR'
            return False, result, f"Validation error: {str(e)}"
    
    def is_suspicious_unreachable(self, validation_result: Dict) -> bool:
        """
        Determine if an unreachable URL is suspicious (potential phishing indicator).
        
        Args:
            validation_result: Result dictionary from validate_url
            
        Returns:
            True if the unreachability is suspicious
        """
        if validation_result.get('is_reachable'):
            return False  # URL is reachable, not suspicious
        
        error_type = validation_result.get('error_type')
        suspicious_errors = [
            'DNS_FAILURE',
            'NOT_FOUND',
            'TIMEOUT',
            'CONNECTION_ERROR',
            'SSL_ERROR'
        ]
        
        return error_type in suspicious_errors

