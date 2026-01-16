import sys
sys.path.insert(0, 'scripts')
from enrich_open_data import _try_google_places_lookup
import json

result = _try_google_places_lookup('108 Contemporary', 'Tulsa', detailed=True)
print(json.dumps(result, indent=2, default=str))
