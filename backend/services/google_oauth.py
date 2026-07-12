import os
import requests
from typing import Optional, Dict, Any
import logging
from urllib.parse import urlencode
import secrets

logger = logging.getLogger(__name__)

class GoogleOAuthService:
    def __init__(self):
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
        
        # Google OAuth URLs
        self.auth_url = "https://accounts.google.com/o/oauth2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        
    def is_configured(self) -> bool:
        """Check if Google OAuth is properly configured"""
        return bool(self.client_id and self.client_secret and self.redirect_uri)
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate Google OAuth authorization URL"""
        if not self.is_configured():
            raise ValueError("Google OAuth not configured")
        
        if not state:
            state = secrets.token_urlsafe(32)
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'openid email profile',
            'response_type': 'code',
            'access_type': 'offline',
            'state': state,
            'prompt': 'consent'
        }
        
        return f"{self.auth_url}?{urlencode(params)}"
    
    def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token"""
        if not self.is_configured():
            raise ValueError("Google OAuth not configured")
        
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri,
            }
            
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to exchange code for token: {str(e)}")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Google"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(self.userinfo_url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get user info: {str(e)}")
            return None

# Global instance
google_oauth = GoogleOAuthService()