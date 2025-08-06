#!/usr/bin/env python3
"""
Test script to verify negative grid power handling
"""

# Test Python formatting
test_values = [150.5, -200.3, 0, -50, 1500.9]

print("Testing Python grid power formatting:")
for value in test_values:
    formatted = f"{value:.0f}"
    print(f"Raw: {value} -> Formatted: {formatted}")

# Test JavaScript equivalent
print("\nJavaScript Math.round() equivalent:")
import math
for value in test_values:
    js_rounded = round(value)
    print(f"Raw: {value} -> Math.round: {js_rounded}")