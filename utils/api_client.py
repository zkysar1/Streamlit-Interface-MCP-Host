import requests
import json
from typing import Dict, Any, Optional, Generator, Tuple
import time
from datetime import datetime

class MCPApiClient:
    """Centralized API client for all Agents-MCP-Host endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:8080/host/v1"):
        self.base_url = base_url
        self.timeout = 300  # 5 minutes to allow for long OpenAI responses
        self.session = requests.Session()
    
    def close(self):
        """Close the requests session"""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Backend server not running. Please start Agents-MCP-Host on port 8080.")
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = e.response.json().get('error', str(e))
            except:
                error_detail = str(e)
            raise Exception(f"Backend error: {error_detail}")
        except requests.exceptions.Timeout:
            raise TimeoutError("Request timed out. The backend took too long to respond.")
    
    # Health and Status Endpoints
    def get_health(self) -> Dict[str, Any]:
        """Get health status of the system"""
        response = self._make_request('GET', '/health')
        return response.json()
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        response = self._make_request('GET', '/status')
        return response.json()
    
    def get_hosts_status(self) -> Dict[str, Any]:
        """Get status of all available hosts"""
        response = self._make_request('GET', '/hosts/status')
        return response.json()
    
    # Session Management Endpoints
    def interrupt_session(self, session_id: str, reason: str = "User requested", graceful: bool = True) -> Dict[str, Any]:
        """Interrupt an active session"""
        payload = {
            "reason": reason,
            "graceful": graceful
        }
        response = self._make_request('POST', f'/conversations/{session_id}/interrupt', json=payload)
        return response.json()
    
    def cancel_session(self, session_id: str) -> Dict[str, Any]:
        """Cancel/delete a session"""
        response = self._make_request('DELETE', f'/conversations/{session_id}')
        return response.json()
    
    def submit_feedback(self, session_id: str, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Submit feedback for a session"""
        response = self._make_request('POST', f'/conversations/{session_id}/feedback', json=feedback)
        return response.json()
    
    # MCP Endpoints
    def get_mcp_status(self) -> Dict[str, Any]:
        """Get MCP system status"""
        response = self._make_request('GET', '/mcp/status')
        return response.json()
    
    def get_mcp_tools(self) -> Dict[str, Any]:
        """Get list of available MCP tools"""
        response = self._make_request('GET', '/mcp/tools')
        return response.json()
    
    def get_mcp_clients(self) -> Dict[str, Any]:
        """Get list of connected MCP clients"""
        response = self._make_request('GET', '/mcp/clients')
        return response.json()
    
    # Streaming Conversation
    def send_conversation_streaming(self, messages: list, host: str = "oracledbanswerer", 
                                  options: Optional[Dict] = None) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
        """
        Send conversation with SSE streaming
        Yields tuples of (event_type, data)
        """
        url = f"{self.base_url}/conversations"
        payload = {
            "messages": messages,
            "host": host,
            "streaming": True,
            "options": options or {}
        }
        headers = {
            "Accept": "text/event-stream",
            "Content-Type": "application/json"
        }
        
        response = None
        try:
            response = self.session.post(url, json=payload, headers=headers, stream=True, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse SSE stream
            current_event = None
            current_data = []
            
            for line in response.iter_lines():
                if not line:
                    # Empty line signals end of an event
                    if current_event and current_data:
                        data_str = '\n'.join(current_data)
                        try:
                            data = json.loads(data_str)
                            yield (current_event, data)
                            
                            # Exit on final response or error
                            if current_event in ('final', 'error', 'complete'):
                                return
                        except json.JSONDecodeError as e:
                            yield ('parse_error', {
                                'error': str(e),
                                'raw_data': data_str[:200]
                            })
                        
                        current_event = None
                        current_data = []
                    continue
                
                # Decode the line
                line = line.decode('utf-8') if isinstance(line, bytes) else line
                
                # Parse SSE format
                if line.startswith('event: '):
                    current_event = line[7:].strip()
                elif line.startswith('data: '):
                    current_data.append(line[6:])
                    
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Backend server not running. Please start Agents-MCP-Host on port 8080.")
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = e.response.json().get('error', str(e))
            except:
                error_detail = str(e)
            raise Exception(f"Backend error: {error_detail}")
        except requests.exceptions.Timeout:
            raise TimeoutError("Request timed out. The backend took too long to respond.")
        finally:
            # Always close the response if it was opened
            if response:
                response.close()
    
    # Helper methods
    
    def format_timestamp(self, timestamp: int) -> str:
        """Format timestamp to readable string"""
        try:
            # Handle negative or zero timestamps
            if timestamp <= 0:
                return "N/A"
            return datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
        except (OSError, ValueError):
            # Handle timestamps outside valid range
            return "Invalid timestamp"
    
    def calculate_uptime(self, uptime_ms: int) -> str:
        """Convert uptime in milliseconds to readable format"""
        seconds = uptime_ms // 1000
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"