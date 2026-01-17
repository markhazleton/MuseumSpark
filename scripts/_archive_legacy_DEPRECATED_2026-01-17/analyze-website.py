#!/usr/bin/env python3
"""Analyze website HTML to understand address extraction challenges."""

import sys
import requests
import re
import json
from bs4 import BeautifulSoup

def analyze_website(url):
    """Fetch and analyze website for address extraction."""
    print(f"\n🔍 Analyzing: {url}\n")
    
    try:
        resp = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 1. Check footer
        print("=" * 60)
        print("1. FOOTER CONTENT")
        print("=" * 60)
        footer = soup.find('footer')
        if footer:
            footer_text = footer.get_text(separator=' ', strip=True)
            print(footer_text[:500])
        else:
            print("❌ No <footer> tag found")
        
        # 2. Check for common address containers
        print("\n" + "=" * 60)
        print("2. COMMON ADDRESS CONTAINERS")
        print("=" * 60)
        address_tags = soup.find_all(['address', 'div'], class_=re.compile(r'address|contact|location|footer', re.I))
        for i, tag in enumerate(address_tags[:3]):
            print(f"\n  Container {i+1} ({tag.name}.{tag.get('class', '')}):")
            print(f"  {tag.get_text(separator=' ', strip=True)[:200]}")
        
        # 3. Structured data (JSON-LD, microdata)
        print("\n" + "=" * 60)
        print("3. STRUCTURED DATA (JSON-LD)")
        print("=" * 60)
        scripts = soup.find_all('script', type='application/ld+json')
        if scripts:
            print(f"Found {len(scripts)} JSON-LD script(s)")
            for i, script in enumerate(scripts):
                try:
                    data = json.loads(script.string)
                    print(f"\nScript {i+1}:")
                    print(json.dumps(data, indent=2)[:400])
                except:
                    print(f"Script {i+1}: Failed to parse")
        else:
            print("❌ No JSON-LD found")
        
        # 4. Regex pattern matching
        print("\n" + "=" * 60)
        print("4. REGEX PATTERN MATCHING")
        print("=" * 60)
        text = soup.get_text(separator=' ')
        
        # Pattern 1: Standard US address
        pattern1 = r'\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Place|Pl|Parkway|Pkwy)\.?\s*,?\s*\w+\s*,?\s*(?:OK|Oklahoma)\s*\d{5}'
        matches1 = re.findall(pattern1, text, re.IGNORECASE)
        print(f"Pattern 1 (Standard): {len(matches1)} matches")
        for m in matches1[:3]:
            print(f"  • {m}")
        
        # Pattern 2: Relaxed (any street + city + state)
        pattern2 = r'\d+[^\n,]{5,50}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)[^\n]{0,50}(?:Tulsa|Oklahoma City|Norman|Stillwater)[^\n]{0,30}(?:OK|Oklahoma)\s*\d{5}'
        matches2 = re.findall(pattern2, text, re.IGNORECASE)
        print(f"\nPattern 2 (Relaxed): {len(matches2)} matches")
        for m in matches2[:3]:
            print(f"  • {m}")
        
        # 5. Search for obvious address markers
        print("\n" + "=" * 60)
        print("5. CONTEXTUAL SEARCH (near 'address', 'visit', 'location')")
        print("=" * 60)
        for keyword in ['address', 'visit us', 'location', 'directions', 'find us']:
            idx = text.lower().find(keyword)
            if idx != -1:
                snippet = text[max(0, idx-50):idx+150]
                print(f"\nNear '{keyword}':")
                print(f"  {snippet}")
                break
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://108contemporary.org"
    analyze_website(url)
