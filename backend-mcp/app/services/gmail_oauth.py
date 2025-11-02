"""
Gmail OAuth Integration
Handles OAuth 2.0 flow for Gmail access with user consent
"""

from typing import Dict, Any, Optional
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.utils.logger import get_logger
import base64
from email.mime.text import MIMEText

logger = get_logger(__name__)


# Singleton instance to persist credentials across requests
_gmail_oauth_instance = None


def get_gmail_oauth_service():
    """Get singleton Gmail OAuth service"""
    global _gmail_oauth_instance
    if _gmail_oauth_instance is None:
        _gmail_oauth_instance = GmailOAuthService()
    return _gmail_oauth_instance


class GmailOAuthService:
    """
    Manages Gmail OAuth 2.0 authentication and API access
    """
    
    # OAuth scopes - what we're asking permission for
    # Note: gmail.readonly allows full search, gmail.metadata is too restrictive
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',  # Read emails with search
    ]
    
    def _get_client_config(self):
        """Get OAuth client configuration from environment"""
        from app.config import get_settings
        settings = get_settings()
        
        return {
            "web": {  # Changed from "installed" to "web" for web apps
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8080/oauth/callback"],
                "javascript_origins": ["http://localhost:3000", "http://localhost:8080"]
            }
        }
    
    def __init__(self):
        """Initialize OAuth service"""
        self.credentials_cache: Dict[str, Credentials] = {}
    
    def get_authorization_url(self, state: str) -> str:
        """
        Generate OAuth authorization URL for user to grant consent
        
        Args:
            state: Session state for security
            
        Returns:
            URL to redirect user to for Gmail authorization
        """
        try:
            client_config = self._get_client_config()
            
            flow = Flow.from_client_config(
                client_config,
                scopes=self.SCOPES,
                redirect_uri="http://localhost:8080/oauth/callback"
            )
            
            # Generate authorization URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=state,
                prompt='consent'
            )
            
            logger.info("gmail_auth_url_generated", state=state)
            
            return auth_url
            
        except Exception as e:
            logger.error("gmail_auth_url_failed", error=str(e))
            return ""
    
    def handle_oauth_callback(self, code: str, state: str) -> Optional[Credentials]:
        """
        Handle OAuth callback and exchange code for credentials
        
        Args:
            code: Authorization code from Google
            state: State parameter for verification
            
        Returns:
            Google OAuth credentials
        """
        try:
            client_config = self._get_client_config()
            
            # Try with current scopes first
            try:
                flow = Flow.from_client_config(
                    client_config,
                    scopes=self.SCOPES,
                    redirect_uri="http://localhost:8080/oauth/callback"
                )
                
                # Exchange code for credentials
                flow.fetch_token(code=code)
                credentials = flow.credentials
            
            except Exception as scope_error:
                # If scope mismatch (user authorized more scopes than we requested), that's OK
                # Just accept the credentials anyway
                logger.warning("gmail_scope_mismatch_accepting_anyway", error=str(scope_error))
                
                # Try again accepting any scopes
                flow = Flow.from_client_config(
                    client_config,
                    scopes=['https://www.googleapis.com/auth/gmail.readonly', 
                           'https://www.googleapis.com/auth/gmail.metadata'],  # Accept both
                    redirect_uri="http://localhost:8080/oauth/callback"
                )
                
                flow.fetch_token(code=code)
                credentials = flow.credentials
            
            # Cache credentials for this session
            self.credentials_cache[state] = credentials
            
            logger.info("gmail_oauth_success", state=state)
            
            return credentials
            
        except Exception as e:
            logger.error("gmail_oauth_callback_failed", error=str(e))
            return None
    
    def search_emails(
        self,
        credentials: Credentials,
        query: str,
        max_results: int = 50
    ) -> list:
        """
        Search Gmail for emails matching query
        
        Args:
            credentials: OAuth credentials
            query: Gmail search query (e.g., "booking confirmation")
            max_results: Maximum emails to return
            
        Returns:
            List of email messages
        """
        try:
            service = build('gmail', 'v1', credentials=credentials)
            
            # Search for messages
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            logger.info("gmail_search_success", query=query, count=len(messages))
            
            return messages
            
        except HttpError as e:
            logger.error("gmail_search_failed", error=str(e))
            return []
    
    def get_email_content(
        self,
        credentials: Credentials,
        message_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get full email content
        
        Args:
            credentials: OAuth credentials
            message_id: Gmail message ID
            
        Returns:
            Email details (subject, body, date, etc.)
        """
        try:
            service = build('gmail', 'v1', credentials=credentials)
            
            # Get message
            message = service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = message.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract body
            body = self._extract_body(message.get('payload', {}))
            
            return {
                'id': message_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body
            }
            
        except HttpError as e:
            logger.error("gmail_get_content_failed", error=str(e), message_id=message_id)
            return None
    
    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8')
            # If no plain text, try first part
            if payload['parts']:
                data = payload['parts'][0]['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
        elif 'body' in payload and 'data' in payload['body']:
            # Simple message
            data = payload['body']['data']
            return base64.urlsafe_b64decode(data).decode('utf-8')
        
        return ""

