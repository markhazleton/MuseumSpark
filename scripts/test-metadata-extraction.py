#!/usr/bin/env python3
"""Quick test to show what metadata we can extract from 108contemporary.org"""

import sys
from pathlib import Path

# Add parent directory to path to import enrich-open-data
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

import requests
from bs4 import BeautifulSoup
import re
from typing import Optional, Dict

# Import needed functions directly by loading the module
import importlib.util
spec = importlib.util.spec_from_file_location("enrich_open_data", script_dir / "enrich-open-data.py")
eod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eod)

url = "https://108contemporary.org"
print(f"🔍 Extracting metadata from: {url}\n")

# Fetch the page
resp = requests.get(url, timeout=15, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})
html = resp.text

# Test each extraction
print("=" * 70)
print("1. META DESCRIPTION")
print("=" * 70)
meta_desc = eod._extract_meta_description(html)
if meta_desc:
    print(f"✅ {meta_desc[:200]}...")
else:
    print("❌ Not found")

print("\n" + "=" * 70)
print("2. CONTACT INFO")
print("=" * 70)
contact = eod._extract_contact_info(html)
if contact['phone']:
    print(f"✅ Phone: {contact['phone']}")
else:
    print("❌ Phone not found")
if contact['email']:
    print(f"✅ Email: {contact['email']}")
else:
    print("❌ Email not found")

print("\n" + "=" * 70)
print("3. HOURS INFORMATION")
print("=" * 70)
hours = eod._extract_hours_info(html)
if hours:
    print(f"✅ {hours[:200]}...")
else:
    print("❌ Not found")

print("\n" + "=" * 70)
print("4. VISITOR URLs")
print("=" * 70)
urls = eod._extract_visitor_urls(html, url)
if urls['hours_url']:
    print(f"✅ Hours URL: {urls['hours_url']}")
else:
    print("❌ Hours URL not found")
if urls['tickets_url']:
    print(f"✅ Tickets URL: {urls['tickets_url']}")
else:
    print("❌ Tickets URL not found")
if urls['accessibility_url']:
    print(f"✅ Accessibility URL: {urls['accessibility_url']}")
else:
    print("❌ Accessibility URL not found")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
extracted_count = sum([
    1 if meta_desc else 0,
    1 if contact['phone'] else 0,
    1 if contact['email'] else 0,
    1 if hours else 0,
    1 if urls['hours_url'] else 0,
    1 if urls['tickets_url'] else 0,
    1 if urls['accessibility_url'] else 0
])
print(f"Extracted {extracted_count}/7 metadata fields")
