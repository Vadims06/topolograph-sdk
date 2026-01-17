"""Core HTTP client for Topolograph API."""

import os
import requests
from typing import Optional, Dict, Any
from urllib.parse import urljoin

from .exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
)
from .resources.graph import GraphsManager
from .upload.uploader import Uploader


class Topolograph:
    """Main client class for interacting with the Topolograph API.
    
    Authentication priority:
    1. Explicit token parameter
    2. TOPOLOGRAPH_TOKEN environment variable
    3. Optional basic auth (username/password)
    """
    
    def __init__(
        self,
        url: str,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize the Topolograph client.
        
        Args:
            url: Base URL of the Topolograph API (e.g., "http://localhost:8080")
            token: Optional API token for bearer authentication
            username: Optional username for basic authentication
            password: Optional password for basic authentication
        """
        # Ensure URL doesn't end with trailing slash
        self.base_url = url.rstrip('/')
        self.api_base = urljoin(self.base_url, '/api')
        
        # Determine authentication method
        self.token = token or os.environ.get('TOPOLOGRAPH_TOKEN')
        self.username = username
        self.password = password
        
        # Create session for connection pooling
        self.session = requests.Session()
        
        # Set up authentication
        if self.token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
        elif self.username and self.password:
            self.session.auth = (self.username, self.password)
        elif not self.token and not (self.username and self.password):
            # No authentication provided - API may still work for some endpoints
            pass
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
        
        # Initialize resource managers
        self._graphs_manager = None
        self._uploader = None
    
    @property
    def graphs(self) -> GraphsManager:
        """Get graphs resource manager."""
        if self._graphs_manager is None:
            self._graphs_manager = GraphsManager(self)
        return self._graphs_manager
    
    @property
    def uploader(self) -> Uploader:
        """Get uploader for LSDB data."""
        if self._uploader is None:
            self._uploader = Uploader(self)
        return self._uploader
    
    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> requests.Response:
        """Internal request handler with error handling.
        
        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint (e.g., '/graph/')
            **kwargs: Additional arguments to pass to requests
        
        Returns:
            Response object
            
        Raises:
            AuthenticationError: If authentication fails (401)
            NotFoundError: If resource not found (404)
            ValidationError: If request validation fails (400, 405)
            APIError: For other API errors
        """
        # Construct URL properly - ensure /api is preserved
        endpoint = endpoint.lstrip('/')
        if self.api_base.endswith('/'):
            url = self.api_base + endpoint
        else:
            url = self.api_base + '/' + endpoint
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Handle different error status codes
            if response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Check your token or credentials.",
                    status_code=401,
                    response=response
                )
            elif response.status_code == 404:
                raise NotFoundError(
                    f"Resource not found: {endpoint}",
                    status_code=404,
                    response=response
                )
            elif response.status_code in (400, 405):
                error_msg = "Invalid request"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg = error_data['error']
                except:
                    error_msg = response.text or error_msg
                raise ValidationError(
                    error_msg,
                    status_code=response.status_code,
                    response=response
                )
            elif not response.ok:
                error_msg = f"API request failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg = error_data['error']
                except:
                    error_msg = response.text or error_msg
                raise APIError(
                    error_msg,
                    status_code=response.status_code,
                    response=response
                )
            
            return response
            
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a GET request.
        
        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments to pass to requests.get
        
        Returns:
            Response object
        """
        return self._request('GET', endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a POST request.
        
        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments to pass to requests.post
        
        Returns:
            Response object
        """
        return self._request('POST', endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a DELETE request.
        
        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments to pass to requests.delete
        
        Returns:
            Response object
        """
        return self._request('DELETE', endpoint, **kwargs)
