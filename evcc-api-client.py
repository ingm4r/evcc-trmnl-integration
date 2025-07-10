#!/usr/bin/env python3
"""
EVCC API to TRMNL Integration Script
A standalone Python script for fetching EVCC data via API
and sending data to TRMNL without requiring Node-RED or MQTT.
"""

import json
import time
import logging
import argparse
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import signal
import sys
import threading
import os
import re
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ChargingPoint:
    """Data class for charging point information"""
    name: str
    status: str
    power: float
    vehicle: str
    soc: Optional[int] = None
    range: Optional[int] = None
    last_updated: str = ""

@dataclass
class SystemData:
    """Data class for system-wide information"""
    grid_power: float = 0.0
    solar_power: float = 0.0
    home_power: float = 0.0
    battery_power: float = 0.0
    battery_soc: Optional[int] = None

class EVCCAPIClient:
    """API client for EVCC data fetching"""
    
    def __init__(self, evcc_url: str, trmnl_url: str = "", trmnl_mac: str = "",
                 trmnl_api_key: str = "", poll_interval: int = 300, session_timeout: int = 30):
        self.evcc_url = evcc_url.rstrip('/')
        self.trmnl_url = trmnl_url.rstrip('/')
        self.trmnl_mac = trmnl_mac
        self.trmnl_api_key = trmnl_api_key
        self.poll_interval = poll_interval
        self.session_timeout = session_timeout
        
        # HTTP session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'EVCC-TRMNL-API-Client/1.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # Data storage
        self.charging_points: List[ChargingPoint] = []
        self.system_data = SystemData()
        
        # Rate limiting
        self.last_sent_time = 0
        self.min_send_interval = 300  # 5 minutes
        self.last_sent_data = None
        
        # Threading and control
        self.running = False
        self.polling_thread = None
        
        # Statistics
        self.stats = {
            'api_calls': 0,
            'api_successes': 0,
            'api_errors': 0,
            'data_sent': 0,
            'http_errors': 0,
            'last_success': None,
            'last_error': None
        }
    
    def fetch_api_data(self) -> Optional[Dict[str, Any]]:
        """Fetch data from EVCC API endpoint"""
        api_url = f"{self.evcc_url}/api/state"
        
        try:
            logger.debug(f"Fetching data from {api_url}")
            response = self.session.get(api_url, timeout=self.session_timeout)
            response.raise_for_status()
            
            self.stats['api_calls'] += 1
            
            # Parse JSON response
            data = response.json()
            logger.debug(f"Fetched API data: {len(str(data))} chars")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed for {api_url}: {e}")
            self.stats['http_errors'] += 1
            self.stats['last_error'] = datetime.now()
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            self.stats['api_errors'] += 1
            self.stats['last_error'] = datetime.now()
            return None
    
    def parse_evcc_data(self, data: Dict[str, Any]) -> bool:
        """Parse EVCC API data to extract charging information"""
        try:
            # Reset data
            self.charging_points = []
            self.system_data = SystemData()
            
            # EVCC API returns data nested under 'result' key
            result = data.get('result', {})
            if not result:
                logger.error("No 'result' key found in API response")
                return False
            
            # Extract system-wide data from correct structure
            # Grid power from result.grid.power
            grid = result.get('grid', {})
            self.system_data.grid_power = grid.get('power', 0.0)
            
            # Home power from result.homePower
            self.system_data.home_power = result.get('homePower', 0.0)
            
            # PV power from result.pv[0].power
            pv_array = result.get('pv', [])
            if pv_array and len(pv_array) > 0:
                self.system_data.solar_power = pv_array[0].get('power', 0.0)
            else:
                self.system_data.solar_power = 0.0
            
            # Extract battery data if available
            battery_array = result.get('battery', [])
            if battery_array and len(battery_array) > 0:
                battery = battery_array[0]
                self.system_data.battery_power = battery.get('power', 0.0)
                self.system_data.battery_soc = battery.get('soc')
            
            logger.info(f"System data - Grid: {self.system_data.grid_power}W, "
                       f"Solar: {self.system_data.solar_power}W, "
                       f"Home: {self.system_data.home_power}W")
            
            # Extract vehicles data for title lookup
            vehicles = result.get('vehicles', {})
            
            # Extract loadpoint data from result.loadpoints
            loadpoints = result.get('loadpoints', [])
            for i, loadpoint in enumerate(loadpoints):
                title = loadpoint.get('title', f'Loadpoint {i+1}')
                charge_power = loadpoint.get('chargePower', 0.0)
                
                # Default names for known setup
                if i == 0 and title == f'Loadpoint {i+1}':
                    title = "Garage"
                elif i == 1 and title == f'Loadpoint {i+1}':
                    title = "Stellplatz"
                
                # Determine status
                status = self.determine_status_from_loadpoint(loadpoint)
                
                # Extract vehicle information using vehicles data
                vehicle = self.extract_vehicle_info(loadpoint, vehicles)
                
                # Extract SOC and range
                soc = loadpoint.get('vehicleSoc')
                vehicle_range = loadpoint.get('vehicleRange')
                
                point = ChargingPoint(
                    name=title,
                    status=status,
                    power=charge_power,
                    vehicle=vehicle,
                    soc=soc,
                    range=vehicle_range,
                    last_updated=datetime.now().isoformat()
                )
                
                self.charging_points.append(point)
                logger.info(f"Loadpoint {title}: {status}, {charge_power}W, {vehicle}")
            
            self.stats['api_successes'] += 1
            return True
            
        except Exception as e:
            logger.error(f"API data parsing failed: {e}")
            logger.error(f"API data structure: {data}")
            self.stats['api_errors'] += 1
            self.stats['last_error'] = datetime.now()
            return False
    
    def determine_status_from_loadpoint(self, loadpoint: Dict[str, Any]) -> str:
        """Determine charging status from loadpoint data"""
        if not loadpoint.get('connected', False):
            return 'idle'
        if loadpoint.get('charging', False):
            return 'charging'
        if loadpoint.get('connected', False):
            return 'connected'
        return 'idle'
    
    def extract_vehicle_info(self, loadpoint: Dict[str, Any], vehicles: Dict[str, Any]) -> str:
        """Extract vehicle information from loadpoint data and vehicles list"""
        # First try to get vehicle name from loadpoint
        vehicle_name = loadpoint.get('vehicleName')
        
        # If we have a vehicle name, look up its title in the vehicles dictionary
        if vehicle_name and vehicle_name in vehicles:
            vehicle_title = vehicles[vehicle_name].get('title')
            if vehicle_title:
                return vehicle_title
        
        # Fallback to vehicleTitle or vehicleName from loadpoint
        vehicle = loadpoint.get('vehicleTitle') or loadpoint.get('vehicleName')
        if vehicle:
            return vehicle
        
        if loadpoint.get('connected', False):
            return "Connected"
        
        return "None"
    
    def load_html_template(self) -> str:
        """Load HTML template from file"""
        template_path = os.path.join(os.path.dirname(__file__), 'evcc-template.html')
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Template file not found: {template_path}")
            return self.get_fallback_template()
    
    def get_fallback_template(self) -> str:
        """Fallback template if file is not found"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>EVCC Status</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .point { border: 1px solid black; padding: 10px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>EV Charging - {{site_title}}</h1>
    {{#each charging_points}}
    <div class="point">
        <h3>{{name}}</h3>
        <p>Status: {{status_text}} ({{power}}W)</p>
        <p>Vehicle: {{vehicle}}</p>
    </div>
    {{/each}}
    <p>Grid: {{grid_power}}W | Solar: {{solar_power}}W | Home: {{home_power}}W</p>
    <p>Last updated: {{last_update}}</p>
</body>
</html>"""
    
    def format_trmnl_html(self) -> str:
        """Format data as HTML for TRMNL display using template"""
        template = self.load_html_template()
        
        # Prepare charging points data
        charging_points_data = []
        for point in self.charging_points:
            point_data = asdict(point)
            # Add template-specific fields
            point_data['status_icon'] = self.get_status_symbol(point.status)
            point_data['status_text'] = point.status.upper()
            charging_points_data.append(point_data)
        
        # If no charging points found, create defaults
        if not charging_points_data:
            charging_points_data = [
                {
                    'name': 'Garage',
                    'status': 'error',
                    'status_icon': '❌',
                    'status_text': 'ERROR',
                    'power': 0,
                    'vehicle': 'No Data',
                    'soc': None,
                    'range': None,
                    'last_updated': datetime.now().isoformat()
                },
                {
                    'name': 'Stellplatz',
                    'status': 'error',
                    'status_icon': '❌',
                    'status_text': 'ERROR',
                    'power': 0,
                    'vehicle': 'No Data',
                    'soc': None,
                    'range': None,
                    'last_updated': datetime.now().isoformat()
                }
            ]
        
        # Prepare template variables
        template_vars = {
            'site_title': self.evcc_url.replace('http://', '').replace('https://', '').split('/')[0],
            'system_offline': not bool(self.charging_points),
            'charging_points': charging_points_data,
            'grid_power': f"{self.system_data.grid_power:.0f}",
            'grid_class': 'negative' if self.system_data.grid_power < 0 else 'positive',
            'solar_power': f"{self.system_data.solar_power:.0f}",
            'home_power': f"{self.system_data.home_power:.0f}",
            'battery_power': f"{self.system_data.battery_power:.0f}" if self.system_data.battery_power != 0 else None,
            'battery_class': 'negative' if self.system_data.battery_power < 0 else 'positive',
            'battery_soc': self.system_data.battery_soc,
            'last_update': datetime.now().strftime("%H:%M, %d.%m.%Y")
        }
        
        # Simple template substitution (since we don't have a full template engine)
        html_content = self.substitute_template_vars(template, template_vars)
        
        return html_content
    
    def substitute_template_vars(self, template: str, variables: Dict[str, Any]) -> str:
        """Simple template variable substitution"""
        result = template
        
        # Handle simple variables {{variable}}
        for key, value in variables.items():
            if value is not None:
                if key in ['charging_points']:
                    continue  # Handle these separately
                pattern = "{{" + key + "}}"
                result = result.replace(pattern, str(value))
            else:
                # Remove variables that are None/empty
                pattern = "{{" + key + "}}"
                result = result.replace(pattern, "")
        
        # Handle charging points iteration {{#each charging_points}}
        charging_points_section = self.extract_section(result, '{{#each charging_points}}', '{{/each}}')
        if charging_points_section:
            points_html = ""
            for point in variables.get('charging_points', []):
                point_html = charging_points_section
                for key, value in point.items():
                    if value is not None:
                        point_html = point_html.replace("{{" + key + "}}", str(value))
                    else:
                        # Remove sections with null values
                        point_html = self.remove_conditional_sections(point_html, key)
                points_html += point_html
            
            # Replace the entire section
            start_tag = '{{#each charging_points}}'
            end_tag = '{{/each}}'
            start_idx = result.find(start_tag)
            end_idx = result.find(end_tag) + len(end_tag)
            if start_idx >= 0 and end_idx > start_idx:
                result = result[:start_idx] + points_html + result[end_idx:]
        
        # Handle conditional sections {{#if condition}}
        result = self.handle_conditional_sections(result, variables)
        
        # Clean up any remaining template syntax
        result = re.sub(r'\{\{[^}]*\}\}', '', result)
        
        return result
    
    def extract_section(self, text: str, start_tag: str, end_tag: str) -> Optional[str]:
        """Extract content between template tags"""
        start_idx = text.find(start_tag)
        end_idx = text.find(end_tag)
        if start_idx >= 0 and end_idx > start_idx:
            return text[start_idx + len(start_tag):end_idx]
        return None
    
    def remove_conditional_sections(self, html: str, key: str) -> str:
        """Remove HTML sections that depend on null values"""
        patterns = [
            f'{{{{#if {key}}}}}.*?{{{{/if}}}}',
            f'<[^>]*>{{{{#{key}}}}}.*?</[^>]*>'
        ]
        for pattern in patterns:
            html = re.sub(pattern, '', html, flags=re.DOTALL)
        return html
    
    def handle_conditional_sections(self, template: str, variables: Dict[str, Any]) -> str:
        """Handle {{#if condition}} sections"""
        # Handle {{#if system_offline}}
        if variables.get('system_offline'):
            template = re.sub(r'\{\{#if system_offline\}\}(.*?)\{\{/if\}\}', r'\1', template, flags=re.DOTALL)
        else:
            template = re.sub(r'\{\{#if system_offline\}\}.*?\{\{/if\}\}', '', template, flags=re.DOTALL)
        
        # Handle other conditional sections
        for key, value in variables.items():
            if isinstance(value, bool):
                if value:
                    template = re.sub(f'{{{{#if {key}}}}}(.*?){{{{/if}}}}', r'\1', template, flags=re.DOTALL)
                else:
                    template = re.sub(f'{{{{#if {key}}}}}.*?{{{{/if}}}}', '', template, flags=re.DOTALL)
            elif value is not None:
                template = re.sub(f'{{{{#if {key}}}}}(.*?){{{{/if}}}}', r'\1', template, flags=re.DOTALL)
            else:
                template = re.sub(f'{{{{#if {key}}}}}.*?{{{{/if}}}}', '', template, flags=re.DOTALL)
        
        return template
    
    def format_trmnl_json(self) -> Dict[str, Any]:
        """Format data as JSON for TRMNL /api/screens endpoint"""
        # Get HTML content using the template
        html_content = self.format_trmnl_html()
        
        # Return JSON data structure for TRMNL screens API following the required format
        return {
            'image': {
                'content': html_content,
                'file_name': 'evcc-status.png'
            }
        }
    
    def get_status_symbol(self, status: str) -> str:
        """Get emoji symbol for status"""
        symbols = {
            'charging': '⚡',
            'connected': '🔌',
            'idle': '⏸️',
            'error': '❌'
        }
        return symbols.get(status, '❓')
    
    def should_send_update(self) -> bool:
        """Determine if we should send an update to TRMNL"""
        now = time.time()
        
        # Rate limiting check
        if now - self.last_sent_time < self.min_send_interval:
            return False
        
        # Check for significant changes
        current_data = self.format_trmnl_html()
        if self.last_sent_data and not self.has_significant_change(self.last_sent_data, current_data):
            return False
        
        return True
    
    def has_significant_change(self, old_data: str, new_data: str) -> bool:
        """Check if there are significant changes worth sending"""
        # For HTML comparison, we'll check if key data points have changed
        # This is a simplified approach - in production you might want more sophisticated comparison
        
        # Simple approach: if HTML content is different enough, consider it significant
        if not old_data or not new_data:
            return True
        
        # Check for power value changes (look for differences in displayed power)
        import re
        
        # Extract power values from HTML
        old_powers = re.findall(r'(\d+)W', old_data)
        new_powers = re.findall(r'(\d+)W', new_data)
        
        if old_powers != new_powers:
            # Check if any power change is > 100W
            if len(old_powers) == len(new_powers):
                for i in range(len(old_powers)):
                    if abs(int(old_powers[i]) - int(new_powers[i])) > 100:
                        return True
            else:
                return True
        
        # Check for status changes (connected/charging/idle/error)
        old_statuses = re.findall(r'(CONNECTED|CHARGING|IDLE|ERROR)', old_data)
        new_statuses = re.findall(r'(CONNECTED|CHARGING|IDLE|ERROR)', new_data)
        
        if old_statuses != new_statuses:
            return True
        
        # Check for vehicle name changes
        old_vehicles = re.findall(r'Vehicle: ([^<]+)', old_data)
        new_vehicles = re.findall(r'Vehicle: ([^<]+)', new_data)
        
        if old_vehicles != new_vehicles:
            return True
        
        # If no significant changes detected
        return False
    
    def send_to_trmnl(self, force: bool = False) -> bool:
        """Send data to TRMNL using BYOS API"""
        if not self.trmnl_url:
            logger.warning("TRMNL URL not configured")
            return False
        
        if not force and not self.should_send_update():
            logger.debug("No significant changes, skipping TRMNL update")
            return False
        
        try:
            # Try different endpoint configurations
            endpoint_configs = [
                ('/api/screens', 'POST', 'json'),    # Primary: Screens endpoint with JSON POST
                ('/api/display', 'GET', 'html'),     # Fallback: GET for /api/display
                ('/api/display', 'POST', 'html'),    # Fallback: POST as alternative
            ]
            
            for endpoint, method, format_type in endpoint_configs:
                if self.try_trmnl_endpoint(endpoint, method, format_type, force):
                    return True
            
            logger.error("Failed to send data to any TRMNL endpoint")
            return False
                
        except Exception as e:
            logger.error(f"Error sending data to TRMNL: {e}")
            return False
    
    def try_trmnl_endpoint(self, endpoint: str, method: str = 'POST', format_type: str = 'html', force: bool = False) -> bool:
        """Try sending data to a specific TRMNL endpoint"""
        try:
            url = f"{self.trmnl_url}{endpoint}"
            
            # TRMNL BYOS API headers
            headers = {
                'User-Agent': 'EVCC-TRMNL-Client/1.0'
            }
            
            # Add API key if available (for /api/screens)
            if self.trmnl_api_key:
                headers['Access-Token'] = self.trmnl_api_key
                logger.debug(f"Using API key: {self.trmnl_api_key[:8]}...")
            
            # Add MAC address if available (for /api/display)
            if self.trmnl_mac and endpoint == '/api/display':
                headers['ID'] = self.trmnl_mac
                logger.debug(f"Using MAC address: {self.trmnl_mac}")
            
            logger.debug(f"Sending to TRMNL endpoint: {url} via {method} ({format_type})")
            logger.debug(f"Headers: {list(headers.keys())}")
            
            # Prepare content based on format type
            if format_type == 'json':
                # JSON format for /api/screens
                content_data = self.format_trmnl_json()
                headers['Content-Type'] = 'application/json'
                data = json.dumps(content_data)
            else:
                # HTML format
                content_data = self.format_trmnl_html()
                headers['Content-Type'] = 'text/html'
                data = content_data
            
            # Choose request method
            if method.upper() == 'GET':
                # For GET requests, no data payload
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=30,
                    verify=False  # TRMNL BYOS uses self-signed certificates
                )
            else:
                # For POST requests, send content
                response = requests.post(
                    url,
                    data=data,
                    headers=headers,
                    timeout=30,
                    verify=False  # TRMNL BYOS uses self-signed certificates
                )
            
            if response.status_code == 200:
                logger.info(f"Successfully sent data to TRMNL via {method} {endpoint}")
                self.stats['data_sent'] += 1
                self.stats['last_success'] = datetime.now()
                self.last_sent_time = time.time()
                self.last_sent_data = content_data
                return True
            else:
                logger.debug(f"Endpoint {method} {endpoint} failed with status {response.status_code}")
                if response.status_code not in [404, 405]:  # Don't log 404s/405s as errors since we're trying multiple endpoints/methods
                    logger.debug(f"Response: {response.text[:200]}...")
                return False
                
        except Exception as e:
            logger.debug(f"Endpoint {endpoint} error: {e}")
            return False
    
    def send_test_data(self) -> bool:
        """Send test data to TRMNL for debugging"""
        if not self.trmnl_url:
            logger.error("TRMNL URL not configured")
            print("Error: TRMNL URL not configured")
            return False
        
        # Create test charging points
        test_points = [
            ChargingPoint(
                name='Garage',
                status='charging',
                power=7200,
                vehicle='Test Vehicle (API)',
                soc=65,
                range=280,
                last_updated=datetime.now().isoformat()
            ),
            ChargingPoint(
                name='Stellplatz',
                status='idle',
                power=0,
                vehicle='None',
                soc=None,
                range=None,
                last_updated=datetime.now().isoformat()
            )
        ]
        
        # Temporarily set test data
        original_points = self.charging_points
        original_system = self.system_data
        
        self.charging_points = test_points
        self.system_data = SystemData(
            grid_power=2500,
            solar_power=4800,
            home_power=1800,
            battery_power=-1200,
            battery_soc=85
        )
        
        try:
            success = self.send_to_trmnl(force=True)
            if success:
                print("Test data sent successfully to TRMNL!")
            else:
                print("Failed to send test data to TRMNL")
            return success
        finally:
            # Restore original data
            self.charging_points = original_points
            self.system_data = original_system
    
    def poll_once(self) -> bool:
        """Poll EVCC once and process data"""
        logger.info("Polling EVCC API...")
        
        # Fetch API data
        api_data = self.fetch_api_data()
        if not api_data:
            logger.error("Failed to fetch API data")
            return False
        
        # Parse API data
        if not self.parse_evcc_data(api_data):
            logger.error("Failed to parse API data")
            return False
        
        logger.info(f"Parsed data: {len(self.charging_points)} charging points")
        
        # Send to TRMNL
        return self.send_to_trmnl()
    
    def start_polling(self):
        """Start continuous polling"""
        self.running = True
        
        def polling_loop():
            while self.running:
                try:
                    self.poll_once()
                except Exception as e:
                    logger.error(f"Polling error: {e}")
                
                # Wait for next poll
                for _ in range(self.poll_interval):
                    if not self.running:
                        break
                    time.sleep(1)
        
        self.polling_thread = threading.Thread(target=polling_loop)
        self.polling_thread.start()
        logger.info(f"Started polling every {self.poll_interval} seconds")
    
    def stop_polling(self):
        """Stop polling"""
        self.running = False
        if self.polling_thread:
            self.polling_thread.join()
        logger.info("Stopped polling")
    
    def print_stats(self):
        """Print current statistics"""
        print("\n=== EVCC API Client Statistics ===")
        print(f"API calls: {self.stats['api_calls']}")
        print(f"API successes: {self.stats['api_successes']}")
        print(f"API errors: {self.stats['api_errors']}")
        print(f"HTTP errors: {self.stats['http_errors']}")
        print(f"Data sent to TRMNL: {self.stats['data_sent']}")
        print(f"Last success: {self.stats['last_success']}")
        print(f"Last error: {self.stats['last_error']}")
        print(f"Running: {self.running}")
        
        print("\n=== Current Data ===")
        for point in self.charging_points:
            print(f"{point.name}: {point.status}, {point.power}W, {point.vehicle}")
        
        print(f"System: grid={self.system_data.grid_power}W, "
              f"solar={self.system_data.solar_power}W, "
              f"home={self.system_data.home_power}W, "
              f"battery={self.system_data.battery_power}W")
    
    def print_raw_data(self):
        """Print raw API data for debugging"""
        api_data = self.fetch_api_data()
        if api_data:
            print("\n=== Raw EVCC API Data ===")
            print(json.dumps(api_data, indent=2))
        else:
            print("Failed to fetch API data")
    
    def run_interactive(self):
        """Run in interactive mode with command prompt"""
        print("EVCC API Client - Interactive Mode")
        print("Commands: stats, test, poll, send, start, stop, raw, html, quit")
        
        while True:
            try:
                cmd = input("\n> ").strip().lower()
                
                if cmd == 'stats':
                    self.print_stats()
                elif cmd == 'test':
                    self.send_test_data()
                elif cmd == 'poll':
                    self.poll_once()
                elif cmd == 'send':
                    self.send_to_trmnl(force=True)
                elif cmd == 'start':
                    if not self.running:
                        self.start_polling()
                    else:
                        print("Already running")
                elif cmd == 'stop':
                    if self.running:
                        self.stop_polling()
                    else:
                        print("Not running")
                elif cmd == 'raw':
                    self.print_raw_data()
                elif cmd == 'html':
                    api_data = self.fetch_api_data()
                    if api_data and self.parse_evcc_data(api_data):
                        html = self.format_trmnl_html()
                        print("\n=== Generated HTML for TRMNL ===")
                        print(html[:500] + "..." if len(html) > 500 else html)
                    else:
                        print("Failed to fetch or parse EVCC data")
                elif cmd == 'quit':
                    break
                else:
                    print("Unknown command. Use: stats, test, poll, send, start, stop, raw, html, quit")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Interactive error: {e}")
        
        if self.running:
            self.stop_polling()
        print("Goodbye!")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    sys.exit(0)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='EVCC API to TRMNL Integration')
    parser.add_argument('--evcc-url', default='http://your-evcc-host',
                        help='EVCC web interface URL (e.g., http://evcc.local or http://192.168.1.100)')
    parser.add_argument('--trmnl-url', default='http://your-trmnl-host:2300',
                        help='TRMNL BYOS server URL (e.g., http://trmnl.local:2300)')
    parser.add_argument('--trmnl-mac', default='AA:BB:CC:DD:EE:FF',
                        help='TRMNL device MAC address (find in TRMNL app)')
    parser.add_argument('--trmnl-api-key', default='your-trmnl-api-key-here',
                        help='TRMNL API key for authentication (from TRMNL app)')
    parser.add_argument('--poll-interval', type=int, default=300,
                        help='Polling interval in seconds')
    parser.add_argument('--session-timeout', type=int, default=30,
                        help='HTTP session timeout in seconds')
    parser.add_argument('--test-only', action='store_true',
                        help='Send test data and exit')
    parser.add_argument('--poll-once', action='store_true',
                        help='Poll once and exit')
    parser.add_argument('--show-raw', action='store_true',
                        help='Show raw API data and exit')
    parser.add_argument('--show-html', action='store_true',
                        help='Show generated HTML and exit')
    parser.add_argument('--interactive', action='store_true',
                        help='Run in interactive mode')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create client
    client = EVCCAPIClient(
        evcc_url=args.evcc_url,
        trmnl_url=args.trmnl_url,
        trmnl_mac=args.trmnl_mac,
        trmnl_api_key=args.trmnl_api_key,
        poll_interval=args.poll_interval,
        session_timeout=args.session_timeout
    )
    
    if args.test_only:
        print("Sending test data to TRMNL...")
        client.send_test_data()
        return
    
    if args.show_raw:
        print("Fetching raw EVCC API data...")
        client.print_raw_data()
        return
    
    if args.show_html:
        print("Generating HTML for TRMNL...")
        # First fetch and parse data
        api_data = client.fetch_api_data()
        if api_data and client.parse_evcc_data(api_data):
            html = client.format_trmnl_html()
            print(html)
        else:
            print("Failed to fetch or parse EVCC data")
        return
    
    if args.poll_once:
        print("Polling EVCC once...")
        success = client.poll_once()
        if success:
            print("Successfully polled and sent data")
        else:
            print("Failed to poll or send data")
        return
    
    try:
        if args.interactive:
            client.run_interactive()
        else:
            client.start_polling()
            print("EVCC API Client running. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        client.stop_polling()

if __name__ == "__main__":
    main()