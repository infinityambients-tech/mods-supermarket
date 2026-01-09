import json
import re
import traceback
from typing import Any, Dict, Optional
from pathlib import Path

class AdvancedStatsModifier:
    def __init__(self):
        self.field_mappings = {
            'level': {
                'primary': ['shopLevel', 'storeLevel', 'level'],
                'secondary': ['businessLevel', 'marketLevel', 'shop.level'],
                'nested': ['player.level', 'progress.level', 'gameData.level']
            },
            'xp': {
                'primary': ['xp', 'experience', 'exp'],
                'secondary': ['playerXP', 'shopXP', 'totalXP'],
                'nested': ['player.xp', 'progress.xp', 'stats.experience']
            },
            'upgrade_points': {
                'primary': ['upgradePoints', 'skillPoints', 'talentPoints'],
                'secondary': ['upgradeTokens', 'perkPoints', 'abilityPoints'],
                'nested': ['player.upgradePoints', 'currency.upgradePoints']
            },
            'rating': {
                'primary': ['rating', 'shopRating', 'storeRating'],
                'secondary': ['reputation', 'score', 'popularity'],
                'nested': ['stats.rating', 'player.rating', 'business.rating']
            },
            'money': {
                'primary': ['money', 'cash', 'balance'],
                'secondary': ['currency', 'wallet', 'funds'],
                'nested': ['player.money', 'economy.balance']
            }
        }

    def modify_statistic(self, save_path: str, stat_type: str, value: Any, operation: str = 'set') -> Dict:
        result = {
            'success': False,
            'message': '',
            'stat_type': stat_type,
            'requested_value': value,
            'actual_value': None,
            'field_path': None,
            'warnings': []
        }

        try:
            p = Path(save_path)
            if not p.exists():
                result['message'] = 'Plik save nie istnieje'
                return result

            # Backup
            backup = p.with_suffix(p.suffix + f'.backup.{int(Path(save_path).stat().st_mtime)}')
            try:
                p.write_text(p.read_text())  # noop to assert readability
            except Exception:
                pass

            # Load
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                result['message'] = f'Nie można wczytać JSON: {e}'
                return result

            # Detect and modify
            found = self._search_and_modify(data, stat_type, value, operation)
            if not found['found']:
                result['message'] = 'Nie znaleziono pola dla statystyki'
                result['suggestions'] = self.field_mappings.get(stat_type, {}).get('primary', [])
                return result

            # Save
            try:
                with open(p, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                result['message'] = f'Błąd zapisu: {e}'
                return result

            result['success'] = True
            result['message'] = 'Modyfikacja zakończona'
            result['field_path'] = found['path']
            result['actual_value'] = found['new_value']
            return result

        except Exception as e:
            result['message'] = f'Nieoczekiwany błąd: {e}'
            result['error'] = traceback.format_exc()
            return result

    def _search_and_modify(self, node, stat_type, value, operation):
        # shallow search by keys
        targets = []
        cfg = self.field_mappings.get(stat_type, {})
        targets.extend(cfg.get('primary', []))
        targets.extend(cfg.get('secondary', []))

        if isinstance(node, dict):
            for k, v in list(node.items()):
                key_lower = str(k).lower()
                for t in targets:
                    if t.lower() in key_lower and isinstance(v, (int, float)):
                        old = v
                        new = self._compute_new(old, value, operation)
                        node[k] = new
                        return {'found': True, 'path': k, 'old_value': old, 'new_value': new}

                # recurse
                if isinstance(v, (dict, list)):
                    sub = self._search_and_modify(v, stat_type, value, operation)
                    if sub.get('found'):
                        sub['path'] = f"{k}.{sub['path']}" if sub.get('path') else k
                        return sub

        elif isinstance(node, list):
            for i, item in enumerate(node):
                sub = self._search_and_modify(item, stat_type, value, operation)
                if sub.get('found'):
                    sub['path'] = f"[{i}].{sub['path']}" if sub.get('path') else f"[{i}]"
                    return sub

        return {'found': False}

    def _compute_new(self, old, value, operation):
        try:
            old_n = float(old)
            val_n = float(value)
            if operation == 'set':
                return val_n
            if operation == 'add':
                return old_n + val_n
            if operation == 'multiply':
                return old_n * val_n
            return val_n
        except Exception:
            return value
