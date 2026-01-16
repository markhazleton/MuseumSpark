#!/usr/bin/env python3
"""Test address extraction strategies on real museum websites."""

import sys
import requests
from address_extraction_strategies import extract_address_multi_strategy, score_address_quality


def test_website(url: str, state_code: str):
    """Test address extraction on a website."""
    print(f"\n{'='*70}")
    print(f"Testing: {url}")
    print(f"State: {state_code}")
    print('='*70)
    
    try:
        resp = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        resp.raise_for_status()
        
        result = extract_address_multi_strategy(resp.text, state_code)
        
        if result:
            print("\n✅ ADDRESS FOUND:")
            print(f"   Street: {result.get('street_address')}")
            print(f"   City: {result.get('city')}")
            print(f"   ZIP: {result.get('postal_code')}")
            
            quality = score_address_quality(result)
            print(f"\n   Quality Score: {quality:.2f} / 1.00")
            
            if quality >= 0.8:
                print("   ✓ High quality extraction")
            elif quality >= 0.5:
                print("   ⚠ Moderate quality - may need verification")
            else:
                print("   ❌ Low quality - manual review recommended")
        else:
            print("\n❌ NO ADDRESS FOUND")
            print("   Strategies failed to extract a complete address.")
            print("   This may require:")
            print("   - Manual inspection of the website")
            print("   - Checking alternate pages (contact, visit, about)")
            print("   - Using Google Places API as fallback")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    # Test cases from Oklahoma museums
    test_cases = [
        ("https://108contemporary.org", "OK"),
        ("https://nationalcowboymuseum.org", "OK"),
        ("https://www.okcmoa.com", "OK"),
        ("https://www.gilcrease.org", "OK"),
        ("https://www.pricetower.org", "OK"),
    ]
    
    # If URL provided as argument, use that
    if len(sys.argv) >= 2:
        url = sys.argv[1]
        state = sys.argv[2] if len(sys.argv) >= 3 else "OK"
        test_cases = [(url, state)]
    
    for url, state in test_cases:
        test_website(url, state)
        print()
