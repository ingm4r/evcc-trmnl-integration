#!/bin/bash

# EVCC MQTT to TRMNL Integration - Example Usage Scripts

echo "EVCC MQTT to TRMNL Integration - Example Usage"
echo "=============================================="

# Make script executable
chmod +x evcc-mqtt-client.py

# Function to check if Python requirements are installed
check_requirements() {
    echo "Checking Python requirements..."
    python3 -c "import paho.mqtt.client, requests" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✓ Requirements satisfied"
    else
        echo "✗ Requirements missing. Installing..."
        pip3 install -r requirements.txt
    fi
}

# Function to show help
show_help() {
    echo ""
    echo "Available commands:"
    echo "  1. test-only     - Send test data to TRMNL and exit"
    echo "  2. interactive   - Run MQTT client in interactive mode"
    echo "  3. monitor       - Monitor MQTT and send data continuously"
    echo "  4. debug         - Run with verbose logging"
    echo "  5. help          - Show this help"
    echo "  6. install       - Install Python requirements"
    echo "  7. api-test      - Test API client with single poll"
    echo "  8. api-raw       - Show raw EVCC API data"
    echo "  9. api-interactive - Run API client in interactive mode"
    echo "  10. api-monitor  - Monitor with API client continuously"
    echo "  11. node-red     - Show Node-RED flow import instructions"
    echo "  12. flow-test    - Test Node-RED flow (same as option 7 + monitoring)"
    echo "  13. native-flow  - Show Node-RED native flow import instructions"
    echo "  q. quit          - Exit"
    echo ""
}

# Function to run test only
run_test_only() {
    echo "Testing TRMNL webhook with sample data..."
    echo "----------------------------------------"
    python3 evcc-mqtt-client.py --test-only --verbose
}

# Function to run interactive mode
run_interactive() {
    echo "Starting interactive mode..."
    echo "Commands available: stats, test, send, quit"
    echo "----------------------------------------"
    python3 evcc-mqtt-client.py --interactive --verbose
}

# Function to run monitoring mode
run_monitor() {
    echo "Starting MQTT monitoring mode..."
    echo "Press Ctrl+C to stop"
    echo "----------------------------------------"
    python3 evcc-mqtt-client.py --verbose
}

# Function to run debug mode
run_debug() {
    echo "Starting debug mode with verbose logging..."
    echo "----------------------------------------"
    python3 evcc-mqtt-client.py --verbose
}

# Function to install requirements
install_requirements() {
    echo "Installing Python requirements..."
    pip3 install -r requirements.txt
    echo "Installation complete!"
}

# Function to test API client once
run_api_test() {
    echo "Testing API client with single poll..."
    echo "-------------------------------------"
    python3 evcc-api-client.py --poll-once --verbose
}

# Function to show raw API data
run_api_raw() {
    echo "Fetching raw EVCC API data..."
    echo "----------------------------"
    python3 evcc-api-client.py --show-raw --verbose
}

# Function to run API client interactive mode
run_api_interactive() {
    echo "Starting API client interactive mode..."
    echo "Commands available: stats, test, poll, send, start, stop, raw, quit"
    echo "--------------------------------------------------------------------"
    python3 evcc-api-client.py --interactive --verbose
}

# Function to run API client monitoring mode
run_api_monitor() {
    echo "Starting API client monitoring mode..."
    echo "Press Ctrl+C to stop"
    echo "------------------------------------"
    python3 evcc-api-client.py --verbose
}

# Function to test TRMNL webhook directly
test_webhook() {
    echo "Testing TRMNL webhook with curl..."
    echo "--------------------------------"
    
    # Test data
    TEST_DATA='{
        "merge_variables": {
            "charging_points": [
                {
                    "name": "Garage",
                    "status": "charging",
                    "power": 7200,
                    "vehicle": "Test Vehicle",
                    "soc": 65,
                    "range": 280,
                    "last_updated": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
                },
                {
                    "name": "Stellplatz",
                    "status": "idle",
                    "power": 0,
                    "vehicle": "None",
                    "soc": null,
                    "range": null,
                    "last_updated": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
                }
            ],
            "system_status": "online",
            "grid_power": 2500,
            "solar_power": 4800,
            "battery_power": -1200,
            "battery_soc": 85,
            "last_sync": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
        }
    }'
    
    echo "Sending test data to TRMNL..."
    curl -X POST http://terminus.kaiser.host:2300/webhook/evcc-charging-status \
         -H "Content-Type: application/json" \
         -d "$TEST_DATA" \
         -v
}

# Function to test EVCC API
test_evcc_api() {
    echo "Testing EVCC API endpoint..."
    echo "----------------------------"
    
    echo "Fetching EVCC state..."
    curl -s http://evcc.kaiser.host/api/state | python3 -m json.tool
    
    echo ""
    echo "Testing EVCC loadpoint info..."
    curl -s http://evcc.kaiser.host/api/loadpoints | python3 -m json.tool
}

# Function to monitor MQTT topics
monitor_mqtt() {
    echo "Monitoring EVCC MQTT topics..."
    echo "Press Ctrl+C to stop"
    echo "-----------------------------"
    
    # Check if mosquitto_sub is available
    if command -v mosquitto_sub >/dev/null 2>&1; then
        echo "Subscribing to EVCC MQTT topics..."
        mosquitto_sub -h evcc.kaiser.host -t "evcc/+/+" -v
    else
        echo "mosquitto_sub not found. Install with: sudo apt-get install mosquitto-clients"
        echo "Or use the Python script instead."
    fi
}

# Function to show Node-RED flow instructions
show_node_red_instructions() {
    echo "Node-RED Flow Import Instructions (External Script)"
    echo "=================================================="
    echo ""
    echo "1. Open Node-RED in your browser (usually http://localhost:1880)"
    echo "2. Click the hamburger menu (☰) → Import"
    echo "3. Select 'select a file to import'"
    echo "4. Choose: evcc-trmnl-automated-flow.json"
    echo "5. Click 'Import'"
    echo ""
    echo "IMPORTANT: Update configuration in exec nodes:"
    echo "  1. Change: cd /path/to/evcc-trmnl-linker"
    echo "     To:     cd $(pwd)"
    echo "  2. Change: --evcc-url http://your-evcc-host"
    echo "     To:     --evcc-url http://your-actual-evcc-host"
    echo "  3. Change: --trmnl-url http://your-trmnl-host:2300"
    echo "     To:     --trmnl-url http://your-actual-trmnl-host:2300"
    echo "  4. Change: --trmnl-mac AA:BB:CC:DD:EE:FF"
    echo "     To:     --trmnl-mac your-actual-mac-address"
    echo "  5. Change: --trmnl-api-key your-trmnl-api-key-here"
    echo "     To:     --trmnl-api-key your-actual-api-key"
    echo ""
    echo "Flow Features:"
    echo "  • 5-minute automatic updates"
    echo "  • Manual trigger for instant updates"
    echo "  • Startup test with 30-second delay"
    echo "  • Hourly statistics monitoring"
    echo "  • Emergency reset with test data"
    echo ""
    echo "See: node-red-automation-guide.md for complete documentation"
    echo ""
    read -p "Press Enter to continue..."
}

# Function to show native Node-RED flow instructions
show_native_node_red_instructions() {
    echo "Node-RED Native Flow Import Instructions (No External Scripts)"
    echo "============================================================="
    echo ""
    echo "1. Open Node-RED in your browser (usually http://localhost:1880)"
    echo "2. Click the hamburger menu (☰) → Import"
    echo "3. Select 'select a file to import'"
    echo "4. Choose: evcc-trmnl-native-flow.json"
    echo "5. Click 'Import'"
    echo ""
    echo "IMPORTANT: Configure settings by clicking 'Configuration' inject node:"
    echo "  1. Change: evcc_url from 'http://your-evcc-host'"
    echo "     To:     'http://your-actual-evcc-host'"
    echo "  2. Change: trmnl_url from 'http://your-trmnl-host:2300'"
    echo "     To:     'http://your-actual-trmnl-host:2300'"
    echo "  3. Change: trmnl_mac from 'AA:BB:CC:DD:EE:FF'"
    echo "     To:     'your-actual-mac-address'"
    echo "  4. Change: trmnl_api_key from 'your-trmnl-api-key-here'"
    echo "     To:     'your-actual-api-key'"
    echo "  5. Deploy the flow"
    echo "  6. Click the 'Configuration' inject node to set global variables"
    echo ""
    echo "Native Flow Features:"
    echo "  • All logic contained within Node-RED (no external scripts)"
    echo "  • 5-minute automatic updates with rate limiting"
    echo "  • Manual trigger for instant updates"
    echo "  • Test data functionality"
    echo "  • Startup test with 30-second delay"
    echo "  • Hourly statistics monitoring"
    echo "  • Emergency reset functionality"
    echo "  • Complete EVCC API parsing"
    echo "  • HTML template generation"
    echo "  • TRMNL API integration"
    echo ""
    echo "Advantages of Native Flow:"
    echo "  • No external dependencies (Python script not needed)"
    echo "  • Easier debugging within Node-RED"
    echo "  • All configuration in one place"
    echo "  • Better error handling and logging"
    echo ""
    read -p "Press Enter to continue..."
}

# Function to test Node-RED flow components
test_node_red_components() {
    echo "Testing Node-RED Flow Components"
    echo "================================"
    echo ""
    echo "Running detailed Node-RED flow test..."
    echo ""
    
    # Run the comprehensive test script
    ./test-node-red-flow.sh
    
    echo ""
    read -p "Press Enter to continue..."
}

# Main menu
main_menu() {
    while true; do
        show_help
        read -p "Choose an option: " choice
        
        case $choice in
            1|test-only)
                run_test_only
                ;;
            2|interactive)
                run_interactive
                ;;
            3|monitor)
                run_monitor
                ;;
            4|debug)
                run_debug
                ;;
            5|help)
                show_help
                ;;
            6|install)
                install_requirements
                ;;
            7|api-test)
                run_api_test
                ;;
            8|api-raw)
                run_api_raw
                ;;
            9|api-interactive)
                run_api_interactive
                ;;
            10|api-monitor)
                run_api_monitor
                ;;
            11|node-red)
                show_node_red_instructions
                ;;
            12|flow-test)
                test_node_red_components
                ;;
            13|native-flow)
                show_native_node_red_instructions
                ;;
            14|webhook)
                test_webhook
                ;;
            15|evcc)
                test_evcc_api
                ;;
            16|mqtt)
                monitor_mqtt
                ;;
            q|quit)
                echo "Goodbye!"
                exit 0
                ;;
            *)
                echo "Invalid option. Please try again."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Check for command line arguments
if [ $# -eq 0 ]; then
    check_requirements
    main_menu
else
    case $1 in
        test)
            check_requirements
            run_test_only
            ;;
        interactive)
            check_requirements
            run_interactive
            ;;
        monitor)
            check_requirements
            run_monitor
            ;;
        debug)
            check_requirements
            run_debug
            ;;
        install)
            install_requirements
            ;;
        webhook)
            test_webhook
            ;;
        evcc)
            test_evcc_api
            ;;
        mqtt)
            monitor_mqtt
            ;;
        api-test)
            check_requirements
            run_api_test
            ;;
        api-raw)
            check_requirements
            run_api_raw
            ;;
        api-interactive)
            check_requirements
            run_api_interactive
            ;;
        api-monitor)
            check_requirements
            run_api_monitor
            ;;
        node-red)
            show_node_red_instructions
            ;;
        flow-test)
            check_requirements
            test_node_red_components
            ;;
        native-flow)
            show_native_node_red_instructions
            ;;
        *)
            echo "Usage: $0 [test|interactive|monitor|debug|install|webhook|evcc|mqtt|api-test|api-raw|api-interactive|api-monitor|node-red|flow-test|native-flow]"
            echo "Or run without arguments for interactive menu"
            ;;
    esac
fi