# CLAUDE.md - Development Context and Guidelines

## Project Overview

**EVCC to TRMNL Integration** - A comprehensive solution for displaying electric vehicle charging data from EVCC (Electric Vehicle Charge Controller) on TRMNL e-ink displays.

### Key Components
- **evcc-api-client.py**: Main Python integration script with configurable dummy defaults
- **evcc-template.html**: E-ink optimized HTML template  
- **evcc-trmnl-automated-flow.json**: Node-RED flow using external Python script
- **evcc-trmnl-native-flow.json**: Self-contained Node-RED flow (no external dependencies)
- **run-examples.sh**: Interactive testing and setup script
- **README.md**: Complete user documentation

## Architecture & Data Flow

### EVCC API Structure
```
/api/state endpoint returns:
{
  "result": {
    "grid": { "power": -200 },           // Negative = feed-in to grid
    "pv": [{ "power": 8500 }],           // Solar generation
    "homePower": 1200,                   // Home consumption
    "battery": [{ "power": -1200, "soc": 85 }], // Optional battery
    "loadpoints": [{                     // Charging points
      "title": "Garage",
      "chargePower": 7400,
      "connected": true,
      "charging": true,
      "vehicleName": "tesla",
      "vehicleSoc": 0.85,                // Decimal (0.85 = 85%)
      "vehicleRange": 420
    }],
    "vehicles": {                        // Vehicle name lookup
      "tesla": { "title": "Tesla Model 3" },
      "bmw": { "title": "BMW i3" }
    }
  }
}
```

### TRMNL API Format
```
POST /api/screens
Headers: Access-Token: {api_key}
{
  "image": {
    "content": "<html>...</html>",
    "file_name": "evcc-status.png"
  }
}
```

## Critical Implementation Details

### Data Processing Pipeline
1. **Fetch** EVCC API data from `/api/state`
2. **Parse** nested JSON structure under `result` key
3. **Transform** data (vehicle lookup, SOC percentage conversion, etc.)
4. **Generate** HTML using template or manual substitution
5. **Send** to TRMNL with proper headers and rate limiting

### Key Data Transformations
- **Vehicle Names**: `loadpoint.vehicleName` → lookup in `vehicles` dictionary → get `title`
- **SOC Conversion**: If `< 1`, multiply by 100 and format to 3 decimals (e.g., `0.46288` → `"46.288"`)
- **Negative Grid Power**: Must preserve minus sign for feed-in scenarios
- **Power Rounding**: Use `Math.round()` in JS, `f"{value:.0f}"` in Python

### Rate Limiting
- TRMNL accepts maximum 1 update per 5 minutes
- Implement rate limiting in both Python and Node-RED flows
- Store `last_sent_time` globally in Node-RED

## Technical Architecture

### Python Script (`evcc-api-client.py`)
```python
# Key Classes
- EVCCAPIClient: Main integration class
- ChargingPoint: Data class for loadpoint info  
- SystemData: Data class for system-wide power data

# Key Methods
- fetch_api_data(): HTTP GET to EVCC API
- parse_evcc_data(): Extract and transform data
- format_trmnl_html(): Generate HTML using template
- send_to_trmnl(): POST to TRMNL API with rate limiting

# Template System
- load_html_template(): Load from evcc-template.html
- substitute_template_vars(): Custom variable substitution
- Handles {{variable}}, {{#each}}, {{#if}} syntax
```

### Node-RED Native Flow
```javascript
// Node Structure
1. Configuration Inject → Set Global Variables
2. Manual/Timer Triggers → Set EVCC URL Function
3. HTTP Request → Fetch EVCC API
4. Parse EVCC Data Function → Transform data
5. Generate HTML Function → Manual HTML generation
6. Create TRMNL Payload Function → Format for API
7. Rate Limit Check Function → 5-minute limiting
8. HTTP Request → Send to TRMNL

// Critical Functions
- Parse EVCC Data: Complex data extraction and transformation
- Generate HTML: Manual template literal substitution
- Rate Limit Check: Global variable tracking
```

### Configuration Management
- **Python**: All via command-line arguments with dummy defaults
- **Node-RED**: Global variables set via Configuration inject node
- **No hardcoded values**: Everything configurable for public release

## Common Issues & Solutions

### Template Variable Substitution
**Problem**: Node-RED template node doesn't process Mustache syntax correctly
**Solution**: Replaced with manual JavaScript template literal generation

### Negative Grid Power Display  
**Problem**: Minus sign not displayed for feed-in scenarios
**Solution**: Ensure `Math.round()` and `f-string` formatting preserve signs

### Vehicle Name Resolution
**Problem**: Shows vehicle IDs instead of friendly names
**Solution**: Lookup `loadpoint.vehicleName` in `vehicles` dictionary

### SOC Percentage Display
**Problem**: Decimal values (0.46288) instead of percentages
**Solution**: Detect values < 1, multiply by 100, format to 3 decimals

### TRMNL API Format
**Problem**: Incorrect API payload structure
**Solution**: Use `{"image": {"content": "html", "file_name": "name.png"}}`

## Testing & Debugging

### Test Commands
```bash
# Python script testing
python3 evcc-api-client.py --test-only --verbose
python3 evcc-api-client.py --show-raw
python3 evcc-api-client.py --show-html
python3 evcc-api-client.py --interactive

# Node-RED testing  
./run-examples.sh
# Options: 7 (api-test), 12 (flow-test), 13 (native-flow)
```

### Debug Points
- **Raw EVCC Data**: Verify API structure hasn't changed
- **Parsed System Data**: Check data extraction
- **Vehicle Lookup**: Ensure vehicle names resolve correctly
- **Template Data**: Verify all variables populated
- **Final HTML**: Check template substitution worked
- **TRMNL Response**: Verify HTTP 200 and display update

### Common Debug Logs
```javascript
// Node-RED Debug Logs
node.log('Raw EVCC data: ' + JSON.stringify(data, null, 2));
node.log('Grid power raw: ' + systemData.grid_power + ' (type: ' + typeof systemData.grid_power + ')');
node.log('Template data: ' + JSON.stringify(templateData, null, 2));
node.log('Generated HTML length: ' + html.length);
```

## Development Guidelines

### Code Style
- **Python**: Follow PEP 8, use type hints, comprehensive error handling
- **Node-RED**: Clear node names, extensive logging, proper error propagation
- **No comments unless requested**: Clean, self-documenting code

### Configuration
- **Never hardcode** sensitive values (URLs, API keys, MAC addresses)  
- **Always use dummy defaults** for public release
- **Make everything configurable** via command-line or inject nodes

### Error Handling
- **Graceful degradation**: Show error states instead of crashing
- **Comprehensive logging**: Help users debug configuration issues
- **Rate limit respect**: Don't spam TRMNL API

### Security
- **No secrets in code**: All via parameters
- **HTTP communication**: HTTPS if available
- **Local network design**: Not intended for internet exposure

## File Structure & Dependencies

### Core Files
```
evcc-trmnl-integration/
├── evcc-api-client.py              # Main Python script
├── evcc-template.html              # HTML template
├── evcc-trmnl-automated-flow.json  # Node-RED with external script
├── evcc-trmnl-native-flow.json     # Self-contained Node-RED
├── requirements.txt                # Python dependencies: requests
├── run-examples.sh                 # Testing script
├── README.md                       # User documentation
└── CLAUDE.md                       # This file
```

### Dependencies
- **Python**: `requests` library only
- **Node-RED**: Core nodes (inject, function, http request, debug)
- **EVCC**: Running instance with API access
- **TRMNL**: Device with BYOS setup and API key

## Future Enhancement Areas

### Potential Improvements
1. **WebSocket Support**: Real-time updates instead of polling
2. **Multi-TRMNL Support**: Send to multiple devices
3. **Historical Data**: Store and display trends
4. **Advanced Templating**: More flexible display layouts
5. **Home Assistant Integration**: Broader smart home connectivity
6. **Docker Container**: Simplified deployment
7. **Systemd Service**: Better service management
8. **Configuration GUI**: Web-based setup interface

### API Evolution
- Monitor EVCC API changes in future versions
- Add support for additional vehicle data fields
- Handle new loadpoint types or configurations
- Support for different EVCC installations

## Maintenance Commands

### Update Flow
```bash
# Pull latest changes
git pull origin main

# Test with current setup
python3 evcc-api-client.py --your-config --test-only

# Update Node-RED flow
# Import latest evcc-trmnl-native-flow.json
# Update configuration inject node with actual values

# Run comprehensive tests
./run-examples.sh
```

### Common Updates
- **EVCC API changes**: Update parsing logic in both Python and Node-RED
- **TRMNL API changes**: Update payload format and headers  
- **Template modifications**: Update both evcc-template.html and HTML generation function
- **Configuration changes**: Update dummy defaults and documentation

## Performance & Limitations

### Current Performance
- **Memory Usage**: ~5-10MB per execution
- **Network Usage**: ~5KB EVCC call, ~50KB TRMNL update
- **Update Frequency**: 5 minutes (TRMNL limitation)
- **Startup Time**: <2 seconds

### Known Limitations
- **TRMNL Rate Limit**: Maximum 1 update per 5 minutes
- **No Real-time Updates**: Polling-based, not event-driven
- **Single TRMNL Device**: One device per script instance
- **HTTP Only**: No HTTPS support for EVCC API (typically local)

This documentation ensures any future development or troubleshooting can be done efficiently with full context of the system architecture and implementation details.