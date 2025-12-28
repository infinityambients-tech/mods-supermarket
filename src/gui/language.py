import json
from pathlib import Path

class Language:
    def __init__(self, locale_code='pl'):
        self.locale_code = locale_code
        self.translations = {}
        self.load_locale(locale_code)
    
    def load_locale(self, code):
        try:
            # Assumes locales are in a directory relative to the project root or executable
            # Adjust path logic as necessary for dev vs built env
            base_path = Path(__file__).parent.parent.parent
            locale_path = base_path / 'locales' / f'{code}.json'
            
            if not locale_path.exists():
                # Fallback to internal path if running from source differently
                locale_path = Path('locales') / f'{code}.json'

            if locale_path.exists():
                with open(locale_path, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
                self.locale_code = code
                return True
        except Exception as e:
            print(f"Error loading locale {code}: {e}")
        return False

    def get(self, key):
        return self.translations.get(key, key)
