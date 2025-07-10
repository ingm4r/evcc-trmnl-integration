# EVCC to TRMNL Integration

🔌⚡ **Automatically display your EVCC electric vehicle charging data on TRMNL e-ink displays**

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Node-RED](https://img.shields.io/badge/Node--RED-Compatible-red.svg)](https://nodered.org)
[![EVCC](https://img.shields.io/badge/EVCC-Compatible-green.svg)](https://evcc.io)
[![TRMNL](https://img.shields.io/badge/TRMNL-BYOS-orange.svg)](https://usetrmnl.com)

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/evcc-trmnl-integration.git
cd evcc-trmnl-integration

# 2. Install Python dependencies
pip3 install -r requirements.txt

# 3. Configure your settings
python3 evcc-api-client.py \
  --evcc-url http://your-evcc-host \
  --trmnl-url http://your-trmnl-host:2300 \
  --trmnl-mac AA:BB:CC:DD:EE:FF \
  --trmnl-api-key your-trmnl-api-key-here \
  --test-only

# 4. Run a live update
python3 evcc-api-client.py \
  --evcc-url http://your-evcc-host \
  --trmnl-url http://your-trmnl-host:2300 \
  --trmnl-mac AA:BB:CC:DD:EE:FF \
  --trmnl-api-key your-trmnl-api-key-here \
  --poll-once
```

## 📋 Overview

This project provides a complete integration solution between [EVCC](https://evcc.io) (Electric Vehicle Charge Controller) and [TRMNL](https://usetrmnl.com) e-ink displays.

### ✨ Features

- 🔄 **Automated Updates**: 5-minute interval updates to your TRMNL display
- 📊 **Live Data**: Real-time charging status, power consumption, and solar generation
- 🎨 **E-ink Optimized**: Clean, readable design perfect for e-ink displays
- 🛠️ **Easy Setup**: Python script + optional Node-RED automation
- ⚙️ **Configurable**: All URLs, API keys, and settings are customizable
- 📱 **No Icons**: Clean text-only design for better e-ink readability

### 🖼️ Display Example

```
┌─────────────────────────────────────────┐
│               EV Charging               │
│            your-evcc-host               │
├─────────────────┬───────────────────────┤
│     Garage      │      Driveway         │
│   CONNECTED     │      CHARGING         │
│      0W         │      7400W            │
│   Tesla Model 3 │      BMW i3           │
│      85%        │        45%            │
│     420km       │       180km           │
├─────────────────┴───────────────────────┤
│            System Overview              │
├─────────────┬─────────────┬─────────────┤
│    Grid     │    Solar    │    Home     │
│    -200W    │   8500W     │   1200W     │
└─────────────┴─────────────┴─────────────┘
│        Last updated: 14:25, 07.07.2025  │
└─────────────────────────────────────────┘
```

## 📁 Project Structure

```
evcc-trmnl-integration/
├── evcc-api-client.py              # Main Python integration script
├── evcc-template.html              # E-ink optimized HTML template
├── evcc-trmnl-automated-flow.json  # Node-RED automation flow
├── requirements.txt                # Python dependencies
├── run-examples.sh                 # Testing and demo script
└── README.md                       # This documentation
```

## 🛠️ Installation

### Prerequisites

- **EVCC Installation**: Running EVCC instance with API access
- **TRMNL Device**: TRMNL device with BYOS (Bring Your Own Server) setup
- **Python 3.7+**: For running the integration script
- **Node-RED** (optional): For automated scheduling

### 1. Python Setup

```bash
# Install required packages
pip3 install -r requirements.txt
```

**Dependencies:**
- `requests` - HTTP client for API communication

### 2. Configuration

All configuration is done via command-line arguments. No hardcoded values!

#### Required Settings

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--evcc-url` | Your EVCC web interface URL | `http://evcc.local` or `http://192.168.1.100` |
| `--trmnl-url` | Your TRMNL BYOS server URL | `http://trmnl.local:2300` |
| `--trmnl-mac` | TRMNL device MAC address | `AA:BB:CC:DD:EE:FF` |
| `--trmnl-api-key` | TRMNL API key | `your-api-key-from-trmnl-app` |

#### Finding Your Settings

**EVCC URL:**
- Usually `http://evcc.local` or the IP address of your EVCC installation
- Test with: `curl http://your-evcc-host/api/state`

**TRMNL Settings:**
- MAC Address: Found in the TRMNL mobile app under device settings
- API Key: Generated in the TRMNL app for BYOS integration
- BYOS URL: Your TRMNL server URL (typically runs on port 2300)

## 🔄 Usage Options

### Option 1: Manual Execution

```bash
# Test connection
python3 evcc-api-client.py \
  --evcc-url http://your-evcc-host \
  --trmnl-url http://your-trmnl-host:2300 \
  --trmnl-mac AA:BB:CC:DD:EE:FF \
  --trmnl-api-key your-trmnl-api-key-here \
  --test-only

# Single update
python3 evcc-api-client.py \
  --evcc-url http://your-evcc-host \
  --trmnl-url http://your-trmnl-host:2300 \
  --trmnl-mac AA:BB:CC:DD:EE:FF \
  --trmnl-api-key your-trmnl-api-key-here \
  --poll-once

# Interactive mode
python3 evcc-api-client.py \
  --evcc-url http://your-evcc-host \
  --trmnl-url http://your-trmnl-host:2300 \
  --trmnl-mac AA:BB:CC:DD:EE:FF \
  --trmnl-api-key your-trmnl-api-key-here \
  --interactive
```

### Option 2: Cron Automation

```bash
# Add to crontab for 5-minute updates
*/5 * * * * cd /path/to/evcc-trmnl-integration && python3 evcc-api-client.py --evcc-url http://your-evcc-host --trmnl-url http://your-trmnl-host:2300 --trmnl-mac AA:BB:CC:DD:EE:FF --trmnl-api-key your-trmnl-api-key-here --poll-once
```

### Option 3: Node-RED Automation (Recommended)

1. **Import Flow:**
   - Open Node-RED (usually `http://localhost:1880`)
   - Menu → Import → Select `evcc-trmnl-automated-flow.json`

2. **Configure Nodes:**
   - Update file paths in all exec nodes
   - Replace dummy values with your actual configuration
   - Deploy the flow

3. **Features:**
   - ⏰ 5-minute automatic updates
   - 🔧 Manual trigger option
   - 🏁 Startup testing (30 seconds after Node-RED starts)
   - 📊 Hourly statistics monitoring
   - 🚨 Emergency reset functionality

### Option 4: SystemD Service

```ini
# /etc/systemd/system/evcc-trmnl.service
[Unit]
Description=EVCC to TRMNL Integration
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/path/to/evcc-trmnl-integration
ExecStart=/usr/bin/python3 evcc-api-client.py --evcc-url http://your-evcc-host --trmnl-url http://your-trmnl-host:2300 --trmnl-mac AA:BB:CC:DD:EE:FF --trmnl-api-key your-trmnl-api-key-here --verbose
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 🧪 Testing

Use the interactive testing script:

```bash
./run-examples.sh
```

**Available test options:**
1. **test-only** - Send test data to TRMNL
2. **api-test** - Test with single poll and live data
3. **api-raw** - Show raw EVCC API response
4. **api-interactive** - Interactive mode with commands
5. **node-red** - Node-RED import instructions
6. **flow-test** - Test Node-RED flow components

## 📊 Command Line Options

```bash
python3 evcc-api-client.py --help
```

| Option | Default | Description |
|--------|---------|-------------|
| `--evcc-url` | `http://your-evcc-host` | EVCC web interface URL |
| `--trmnl-url` | `http://your-trmnl-host:2300` | TRMNL BYOS server URL |
| `--trmnl-mac` | `AA:BB:CC:DD:EE:FF` | TRMNL device MAC address |
| `--trmnl-api-key` | `your-trmnl-api-key-here` | TRMNL API key |
| `--poll-interval` | `300` | Polling interval in seconds |
| `--session-timeout` | `30` | HTTP session timeout |
| `--test-only` | - | Send test data and exit |
| `--poll-once` | - | Poll once and exit |
| `--show-raw` | - | Show raw API data |
| `--show-html` | - | Show generated HTML |
| `--interactive` | - | Interactive mode |
| `--verbose` | - | Enable debug logging |

## 🔍 Data Sources

### EVCC API

The integration fetches data from EVCC's `/api/state` endpoint:

```json
{
  "result": {
    "grid": {"power": -200},
    "pv": [{"power": 8500}],
    "homePower": 1200,
    "loadpoints": [
      {
        "title": "Garage",
        "chargePower": 7400,
        "connected": true,
        "charging": true,
        "vehicleName": "tesla",
        "vehicleSoc": 85,
        "vehicleRange": 420
      }
    ],
    "vehicles": {
      "tesla": {"title": "Tesla Model 3"},
      "bmw": {"title": "BMW i3"}
    }
  }
}
```

### TRMNL API

Data is sent to TRMNL using the `/api/screens` endpoint:

```json
{
  "image": {
    "content": "<html>...</html>",
    "file_name": "evcc-status.png"
  }
}
```

## 🎨 Customization

### HTML Template

Edit `evcc-template.html` to customize:
- Layout and styling
- Font sizes and colors
- Additional data fields
- Responsive design

### Display Settings

The template automatically:
- Extracts site title from EVCC URL
- Formats power values (W/kW)
- Shows charging status with text indicators
- Displays vehicle information and battery status
- Updates timestamp

## 🔧 Troubleshooting

### Common Issues

1. **Connection Errors**
   ```bash
   # Test EVCC API
   curl http://your-evcc-host/api/state
   
   # Test TRMNL with verbose logging
   python3 evcc-api-client.py --your-config --test-only --verbose
   ```

2. **No Data Displayed**
   - Verify EVCC URL is accessible
   - Check TRMNL device is online
   - Confirm API key and MAC address

3. **Rate Limiting**
   - TRMNL accepts max 1 update per 5 minutes
   - Script automatically handles rate limiting
   - Use `--verbose` to see rate limiting messages

### Debug Commands

```bash
# Show raw EVCC data
python3 evcc-api-client.py --your-config --show-raw

# Generate HTML template
python3 evcc-api-client.py --your-config --show-html

# Interactive debugging
python3 evcc-api-client.py --your-config --interactive
```

### Interactive Commands

In interactive mode:
- `stats` - Show API statistics
- `test` - Send test data to TRMNL
- `poll` - Poll EVCC and parse data
- `send` - Force send current data
- `raw` - Show raw API response
- `html` - Show generated HTML
- `quit` - Exit

## ⚡ Performance

- **Update Frequency**: 5 minutes (TRMNL limitation)
- **Memory Usage**: ~5-10MB per execution
- **Network Usage**: ~5KB per EVCC call, ~50KB per TRMNL update
- **Battery Impact**: Minimal (e-ink displays are very efficient)

## 🔒 Security

- No sensitive data is stored in code
- All configuration via command-line arguments
- HTTP communication (HTTPS support if available)
- Designed for local network use

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Projects

- **[EVCC](https://evcc.io)** - Electric Vehicle Charge Controller
- **[TRMNL](https://usetrmnl.com)** - E-ink display platform
- **[Node-RED](https://nodered.org)** - Flow-based automation

## 💬 Support

- **Issues**: Please use GitHub Issues for bug reports
- **Discussions**: Use GitHub Discussions for questions
- **Testing**: Run `./run-examples.sh` for comprehensive testing

## 🎉 Acknowledgments

- EVCC team for the excellent charging controller
- TRMNL team for the innovative e-ink display platform
- Node-RED community for the automation platform

---

**Happy charging!** ⚡🚗📺