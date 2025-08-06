#!/usr/bin/env python3
"""
Capture live TRMNL API request details for GitHub issue
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from evcc_api_client import EVCCAPIClient
import logging
import json
from datetime import datetime

# Set up debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("Capturing TRMNL API request details...")
    
    # Create client with real configuration
    client = EVCCAPIClient(
        evcc_url='http://evcc.kaiser.host',
        trmnl_url='http://terminus.kaiser.host:2300', 
        trmnl_mac='28:37:2F:B6:32:0C',
        trmnl_api_key='bZjCPEupusvMRnhz1JT9ig'
    )
    
    print("Sending test data to capture request details...")
    success = client.send_test_data()
    
    print(f"Request completed. Success: {success}")
    print("\nCheck the debug output above for detailed request information.")
    
    return success

if __name__ == "__main__":
    main()