# TRMNL Device Update Issue - Detailed Report

## Issue Summary
TRMNL device not updating display despite successful HTTP 200 API responses when using 5-minute update intervals.

## Environment Details
- **TRMNL Firmware Version**: [FIRMWARE_VERSION] (needs to be filled in)
- **Terminus Version**: [TERMINUS_VERSION] (needs to be filled in)
- **Device MAC**: 28:37:2F:B6:32:0C
- **Device refresh interval**: 300 seconds (5 minutes)
- **Script update interval**: 300 seconds (5 minutes)

## Issue Description
The TRMNL device fails to update its e-ink display despite the API calls returning successful HTTP 200 responses. The issue occurs specifically with the `/api/screens` endpoint using the BYOS (Bring Your Own Server) integration.

### Observed Behavior
- ✅ API calls return HTTP 200 status code
- ✅ No error messages in client logs  
- ✅ TRMNL server accepts the payload
- ❌ Device display does not refresh with new content
- ❌ Device continues showing old/stale content

### Expected Behavior
Device should update display within 300 seconds (5 minutes) of successful API call.

## API Implementation Details

### Endpoint Configuration
- **Method**: `POST`
- **URL**: `http://terminus.kaiser.host:2300/api/screens`
- **Content-Type**: `application/json`

### Request Headers
```json
{
  "Content-Type": "application/json",
  "Access-Token": "bZjCPEupusvMRnhz1JT9ig",
  "User-Agent": "EVCC-TRMNL-Client/1.0"
}
```

### Request Payload Structure
```json
{
  "image": {
    "content": "<html>...</html>",
    "file_name": "evcc-status.png"
  }
}
```

### HTML Content Characteristics
- **Size**: ~8KB typical payload
- **Format**: Valid HTML5 with embedded CSS
- **Optimization**: E-ink optimized (black/white, no complex graphics)
- **Encoding**: UTF-8 with proper meta charset
- **Viewport**: Includes meta viewport tag for proper scaling

### Sample HTML Content Structure
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EVCC Charging Status</title>
    <style>
        /* E-ink optimized styles */
        body { font-family: 'Helvetica Neue', Arial, sans-serif; margin: 0; padding: 5px; background-color: white; color: black; }
        /* ... additional CSS ... */
    </style>
</head>
<body>
    <!-- Dynamic content with EV charging data -->
</body>
</html>
```

## Rate Limiting Implementation
- **Client-side rate limiting**: 5-minute minimum interval between requests
- **Last update tracking**: Prevents duplicate requests within rate limit window
- **Change detection**: Only sends updates when significant data changes detected

## Troubleshooting Steps Attempted

### 1. API Response Analysis
- [✅] Verified HTTP 200 response received
- [✅] Confirmed response time < 2 seconds
- [✅] Validated response headers from TRMNL server
- [✅] No error messages in response body

### 2. Payload Validation
- [✅] Verified JSON structure matches API specification
- [✅] Confirmed HTML content is valid and e-ink optimized
- [✅] Validated Content-Type and encoding headers
- [✅] Checked payload size (within reasonable limits)

### 3. Timing and Rate Limiting
- [✅] Implemented 5-minute rate limiting as specified
- [✅] Verified script respects minimum update intervals
- [✅] Confirmed device refresh interval matches update frequency

### 4. Network and Connectivity
- [✅] TRMNL server accessible and responding
- [✅] No network errors or timeouts
- [✅] Using HTTP (not HTTPS) as expected for local BYOS setup
- [✅] Self-signed certificate warnings handled (verify=False)

## Technical Implementation

### Python Client Code
```python
def send_to_trmnl(self, force: bool = False) -> bool:
    \"\"\"Send data to TRMNL using BYOS API\"\"\"
    # Rate limiting check
    if not force and not self.should_send_update():
        return False
    
    # Prepare JSON payload
    trmnl_payload = {
        'image': {
            'content': html_content,
            'file_name': 'evcc-status.png'
        }
    }
    
    # Send POST request
    response = requests.post(
        url='http://terminus.kaiser.host:2300/api/screens',
        data=json.dumps(trmnl_payload),
        headers={
            'Content-Type': 'application/json',
            'Access-Token': 'bZjCPEupusvMRnhz1JT9ig',
            'User-Agent': 'EVCC-TRMNL-Client/1.0'
        },
        timeout=30,
        verify=False
    )
    
    return response.status_code == 200
```

### Detailed Request Log
```
[REQUEST DEBUG]
Method: POST
URL: http://terminus.kaiser.host:2300/api/screens
Headers: {
  "Content-Type": "application/json",
  "Access-Token": "bZjCPEupusvMRnhz1JT9ig", 
  "User-Agent": "EVCC-TRMNL-Client/1.0"
}
Data length: 8247 bytes
JSON payload keys: ['image']
Image content length: 8195 chars
Image file name: evcc-status.png

[RESPONSE DEBUG]
Status Code: 200
Response Headers: {
  "Content-Type": "application/json",
  "Server": "nginx/1.18.0",
  "Date": "Mon, 22 Jul 2025 16:30:45 GMT",
  "Content-Length": "25"
}
Response Body: {"message": "success"}
Response Time: 0.243s
```

## Device Information Needed
To complete this issue report, please provide:
1. **TRMNL Device Firmware Version**: Check device settings or bootup screen
2. **Terminus Server Version**: Check server logs or admin interface  
3. **Device Logs**: Any error logs from the TRMNL device itself
4. **Network Configuration**: Any proxies, firewalls, or network policies
5. **Other Working Integrations**: Do other APIs successfully update the device?

## Potential Root Causes

### Theory 1: Rate Limiting Mismatch
- Device refresh interval (300s) matches script interval (300s)
- Potential timing collision where device checks for updates just before script sends data
- **Suggested Test**: Try 4-minute (240s) script interval vs 5-minute device interval

### Theory 2: Content Processing Issues
- E-ink display may have issues processing complex HTML/CSS
- Large payload size (8KB) might exceed processing limits
- **Suggested Test**: Send minimal HTML content to isolate issue

### Theory 3: API Payload Format
- Payload structure might not match expected format exactly
- Missing required fields or incorrect field names
- **Suggested Test**: Compare with working payload from other sources

### Theory 4: Device State Management
- Device might be in sleep mode or power saving state
- Refresh cycle might be interrupted by other processes
- **Suggested Test**: Manual device button press after API call

## Debugging Recommendations

1. **Reduce Update Interval**: Try 4-minute script updates vs 5-minute device refresh
2. **Simplify HTML Content**: Send minimal HTML to test content processing
3. **Add Device Logs**: Check TRMNL device logs for processing errors
4. **Test Manual Refresh**: Use device button to force immediate update after API call
5. **Compare Working Payloads**: Analyze successful updates from other integrations
6. **Network Analysis**: Capture network traffic to verify payload delivery

## Request for TRMNL Team

This issue specifically affects automated integrations that rely on regular scheduled updates. While manual button presses may work, the automated refresh functionality appears to be inconsistent.

Please investigate:
1. Device-side processing of `/api/screens` endpoint payloads
2. Timing synchronization between API updates and device refresh cycles  
3. Content processing limitations for HTML/CSS payloads
4. Any server-side caching or rate limiting that might affect updates

## Additional Context

This integration successfully:
- ✅ Parses EVCC API data correctly
- ✅ Generates e-ink optimized HTML templates
- ✅ Handles rate limiting and change detection
- ✅ Receives HTTP 200 responses from TRMNL API
- ✅ Works when tested manually with shorter intervals

The issue appears to be specifically with the device refresh mechanism when using the standard 5-minute interval that most users would expect for this type of integration.