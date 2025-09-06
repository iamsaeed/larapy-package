"""
Maintenance mode middleware for application downtime management.

This middleware allows putting the application into maintenance mode
with custom messages and bypass capabilities for authorized users.
"""

import os
import json
from datetime import datetime
from typing import Callable, Optional, List
from ..middleware import Middleware
from ...http.request import Request
from ...http.response import Response, JsonResponse


class MaintenanceModeMiddleware(Middleware):
    """Middleware to handle maintenance mode."""
    
    def __init__(self, 
                 maintenance_file: str = 'storage/framework/maintenance.json',
                 allowed_ips: Optional[List[str]] = None,
                 allowed_paths: Optional[List[str]] = None,
                 status_code: int = 503):
        """
        Initialize maintenance mode middleware.
        
        Args:
            maintenance_file: Path to maintenance mode file
            allowed_ips: IP addresses that can bypass maintenance mode
            allowed_paths: Paths that are accessible during maintenance
            status_code: HTTP status code to return (503 Service Unavailable)
        """
        self.maintenance_file = maintenance_file
        self.allowed_ips = allowed_ips or []
        self.allowed_paths = allowed_paths or []
        self.status_code = status_code
    
    async def handle(self, request: Request, next_handler: Callable) -> Response:
        """
        Check maintenance mode and handle accordingly.
        
        Args:
            request: The HTTP request
            next_handler: The next middleware in the stack
            
        Returns:
            HTTP response (maintenance page or normal response)
        """
        # Check if maintenance mode is enabled
        if not self._is_maintenance_mode_enabled():
            return await next_handler(request)
        
        # Check if request should bypass maintenance mode
        if self._should_bypass_maintenance(request):
            return await next_handler(request)
        
        # Return maintenance mode response
        return self._maintenance_response(request)
    
    def _is_maintenance_mode_enabled(self) -> bool:
        """Check if maintenance mode is enabled."""
        return os.path.exists(self.maintenance_file)
    
    def _should_bypass_maintenance(self, request: Request) -> bool:
        """Determine if request should bypass maintenance mode."""
        # Check allowed IPs
        if request.ip in self.allowed_ips:
            return True
        
        # Check allowed paths
        for allowed_path in self.allowed_paths:
            if request.path.startswith(allowed_path):
                return True
        
        # Check maintenance bypass token
        maintenance_data = self._get_maintenance_data()
        bypass_secret = maintenance_data.get('secret')
        
        if bypass_secret:
            # Check query parameter
            if request.query_params.get('bypass') == bypass_secret:
                return True
            
            # Check header
            if request.header('X-Maintenance-Bypass') == bypass_secret:
                return True
        
        return False
    
    def _get_maintenance_data(self) -> dict:
        """Get maintenance mode configuration data."""
        try:
            with open(self.maintenance_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _maintenance_response(self, request: Request) -> Response:
        """Create maintenance mode response."""
        maintenance_data = self._get_maintenance_data()
        
        # Get maintenance info
        message = maintenance_data.get('message', 'Application is under maintenance.')
        retry_after = maintenance_data.get('retry_after', 3600)  # 1 hour
        until = maintenance_data.get('until')
        
        # Return JSON for API requests
        accept_header = request.header('accept', '')
        if 'application/json' in accept_header or request.is_ajax():
            response_data = {
                'error': 'Service Unavailable',
                'message': message,
                'maintenance': True
            }
            
            if until:
                response_data['until'] = until
            
            response = JsonResponse(response_data, status=self.status_code)
        else:
            # Return HTML for browser requests
            until_text = ""
            if until:
                try:
                    until_dt = datetime.fromisoformat(until.replace('Z', '+00:00'))
                    until_text = f"<p>Expected to be back: {until_dt.strftime('%B %d, %Y at %I:%M %p UTC')}</p>"
                except ValueError:
                    pass
            
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Under Maintenance</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        margin: 0;
                        padding: 0;
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }}
                    .container {{
                        text-align: center;
                        padding: 2rem;
                        max-width: 600px;
                    }}
                    .maintenance-icon {{
                        font-size: 4rem;
                        margin-bottom: 1rem;
                    }}
                    h1 {{
                        font-size: 2.5rem;
                        margin-bottom: 1rem;
                        font-weight: 300;
                    }}
                    .message {{
                        font-size: 1.2rem;
                        margin-bottom: 2rem;
                        opacity: 0.9;
                    }}
                    .info {{
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 8px;
                        padding: 1rem;
                        margin-bottom: 2rem;
                    }}
                    .back-link {{
                        color: white;
                        text-decoration: none;
                        border: 2px solid white;
                        padding: 0.5rem 1rem;
                        border-radius: 4px;
                        transition: all 0.3s;
                    }}
                    .back-link:hover {{
                        background: white;
                        color: #667eea;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="maintenance-icon">🔧</div>
                    <h1>Under Maintenance</h1>
                    <div class="message">{message}</div>
                    <div class="info">
                        <p>We're currently performing scheduled maintenance to improve your experience.</p>
                        {until_text}
                        <p>Please check back shortly.</p>
                    </div>
                    <a href="mailto:support@example.com" class="back-link">Contact Support</a>
                </div>
            </body>
            </html>
            """
            
            response = Response(html_content, status=self.status_code)
        
        # Add retry-after header
        response.header('Retry-After', str(retry_after))
        
        return response


class MaintenanceManager:
    """Helper class to manage maintenance mode."""
    
    def __init__(self, maintenance_file: str = 'storage/framework/maintenance.json'):
        self.maintenance_file = maintenance_file
    
    def enable(self, message: str = None, until: str = None, 
              retry_after: int = 3600, secret: str = None) -> bool:
        """
        Enable maintenance mode.
        
        Args:
            message: Custom maintenance message
            until: ISO datetime when maintenance will end
            retry_after: Seconds to wait before retrying
            secret: Secret token to bypass maintenance mode
            
        Returns:
            True if maintenance mode was enabled successfully
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.maintenance_file), exist_ok=True)
            
            # Prepare maintenance data
            maintenance_data = {
                'enabled': True,
                'enabled_at': datetime.utcnow().isoformat() + 'Z',
                'message': message or 'Application is under maintenance.',
                'retry_after': retry_after
            }
            
            if until:
                maintenance_data['until'] = until
            
            if secret:
                maintenance_data['secret'] = secret
            
            # Write maintenance file
            with open(self.maintenance_file, 'w') as f:
                json.dump(maintenance_data, f, indent=2)
            
            return True
            
        except Exception:
            return False
    
    def disable(self) -> bool:
        """
        Disable maintenance mode.
        
        Returns:
            True if maintenance mode was disabled successfully
        """
        try:
            if os.path.exists(self.maintenance_file):
                os.remove(self.maintenance_file)
            return True
        except Exception:
            return False
    
    def is_enabled(self) -> bool:
        """Check if maintenance mode is currently enabled."""
        return os.path.exists(self.maintenance_file)
    
    def get_status(self) -> dict:
        """Get current maintenance mode status."""
        if not self.is_enabled():
            return {'enabled': False}
        
        try:
            with open(self.maintenance_file, 'r') as f:
                data = json.load(f)
                return {'enabled': True, **data}
        except Exception:
            return {'enabled': True, 'error': 'Could not read maintenance file'}


# CLI integration helper
def create_maintenance_commands():
    """Create maintenance mode CLI commands."""
    import click
    
    @click.group()
    def maintenance():
        """Maintenance mode management commands."""
        pass
    
    @maintenance.command('enable')
    @click.option('--message', help='Custom maintenance message')
    @click.option('--until', help='ISO datetime when maintenance will end')
    @click.option('--retry-after', default=3600, help='Seconds to wait before retrying')
    @click.option('--secret', help='Secret token to bypass maintenance mode')
    def enable_maintenance(message, until, retry_after, secret):
        """Enable maintenance mode."""
        manager = MaintenanceManager()
        if manager.enable(message, until, retry_after, secret):
            click.echo("✅ Maintenance mode enabled.")
        else:
            click.echo("❌ Failed to enable maintenance mode.")
    
    @maintenance.command('disable')
    def disable_maintenance():
        """Disable maintenance mode."""
        manager = MaintenanceManager()
        if manager.disable():
            click.echo("✅ Maintenance mode disabled.")
        else:
            click.echo("❌ Failed to disable maintenance mode.")
    
    @maintenance.command('status')
    def maintenance_status():
        """Show maintenance mode status."""
        manager = MaintenanceManager()
        status = manager.get_status()
        
        if status['enabled']:
            click.echo("🔧 Maintenance mode is ENABLED")
            if 'message' in status:
                click.echo(f"   Message: {status['message']}")
            if 'until' in status:
                click.echo(f"   Until: {status['until']}")
        else:
            click.echo("✅ Maintenance mode is DISABLED")
    
    return maintenance