#!/usr/bin/env python3
"""Test normalization function"""

def normalize_placeholders(value):
    """Normalize placeholder values to None"""
    if value is None:
        return None
    if isinstance(value, str):
        value_lower = value.strip().lower()
        # Known placeholder patterns
        placeholders = [
            'unknown', 'not known', 'n/a', 'na', 'tbd', 'to be determined',
            'none', 'null', 'not available', 'not provided', 'not applicable',
            'pending', 'coming soon', '--', '---', 'tba', 'to be announced'
        ]
        if value_lower in placeholders or value.strip() == '':
            return None
    return value

test_values = [
    ('UNKNOWN', None),
    ('Unknown', None),
    ('unknown', None),
    ('TBD', None),
    ('tbd', None),
    ('N/A', None),
    ('na', None),
    ('Not Available', None),
    ('not known', None),
    ('--', None),
    ('---', None),
    ('', None),
    ('   ', None),
    ('Valid Data', 'Valid Data'),
    ('9079299200', '9079299200'),
    (None, None)
]

print('\n✅ NORMALIZATION TEST RESULTS')
print('=' * 60)
passed = 0
failed = 0

for val, expected in test_values:
    result = normalize_placeholders(val)
    status = '✓' if result == expected else '✗'
    
    val_str = 'None' if val is None else f"'{val}'"
    result_str = 'null' if result is None else f"'{result}'"
    expected_str = 'null' if expected is None else f"'{expected}'"
    
    if result == expected:
        passed += 1
        print(f"{status} {val_str:25} → {result_str:20} (expected: {expected_str})")
    else:
        failed += 1
        print(f"{status} {val_str:25} → {result_str:20} (EXPECTED: {expected_str})")

print('=' * 60)
print(f'\nPassed: {passed}/{len(test_values)}')
if failed == 0:
    print('✅ All tests passed!')
else:
    print(f'❌ {failed} tests failed')
