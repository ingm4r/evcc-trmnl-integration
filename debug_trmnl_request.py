#!/usr/bin/env python3
"""
Debug script to capture full TRMNL API request details for GitHub issue reporting
"""

import sys
import logging
import json
from datetime import datetime
from evcc_api_client import EVCCAPIClient

def setup_debug_logging():
    """Setup comprehensive logging for request debugging"""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Remove default handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create file handler
    debug_file = f"trmnl_request_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(debug_file, mode='w')
    file_handler.setLevel(logging.DEBUG)
    
    # Create console handler  
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return debug_file

def main():
    """Run debug test and capture all request details"""
    
    print("TRMNL API Request Debug Capture")
    print("===============================")
    
    debug_file = setup_debug_logging()
    logger = logging.getLogger(__name__)
    
    # Configuration
    config = {
        'evcc_url': 'http://evcc.kaiser.host',
        'trmnl_url': 'http://terminus.kaiser.host:2300', 
        'trmnl_mac': '28:37:2F:B6:32:0C',
        'trmnl_api_key': 'bZjCPEupusvMRnhz1JT9ig'
    }
    
    logger.info("Starting TRMNL API debug session")
    logger.info(f"Debug log file: {debug_file}")
    logger.info(f"Configuration: {json.dumps(config, indent=2)}")
    
    try:
        # Create client
        client = EVCCAPIClient(
            evcc_url=config['evcc_url'],
            trmnl_url=config['trmnl_url'],
            trmnl_mac=config['trmnl_mac'], 
            trmnl_api_key=config['trmnl_api_key']
        )
        
        logger.info("Client created successfully")
        
        # Send test data to capture request details
        logger.info("Sending test data to TRMNL...")
        success = client.send_test_data()
        
        if success:
            logger.info("Test data sent successfully - check TRMNL device for update")
        else:
            logger.error("Failed to send test data")
        
        # Print statistics
        client.print_stats()
        
        print(f"\nDebug information saved to: {debug_file}")
        print("This file contains complete request/response details for GitHub issue reporting.")
        
    except Exception as e:
        logger.error(f"Debug session failed: {e}")
        logger.error(f"Exception details: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()