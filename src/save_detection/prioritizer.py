from datetime import datetime
from typing import List, Dict

class SavePrioritizer:
    @staticmethod
    def prioritize_saves(save_list: List[Dict]) -> List[Dict]:
        """Sorts saves by priority"""
        return sorted(save_list, 
                      key=lambda x: SavePrioritizer._calculate_priority(x),
                      reverse=True)
    
    @staticmethod
    def _calculate_priority(save_info: Dict) -> float:
        """Calculates save priority (0-100)"""
        priority = 50.0
        
        if 'modified' in save_info:
            try:
                days_old = (datetime.now() - save_info['modified']).days
                recency_score = max(0, 30 - days_old) / 30 * 30
                priority += recency_score
            except:
                pass
        
        file_type_bonus = {
            'json': 20,
            'binary': 10,
            'unknown': 0
        }
        priority += file_type_bonus.get(save_info.get('file_type', 'unknown'), 0)
        
        path = save_info.get('path', '').lower()
        location_bonus = {
            'appdata': 15,
            'local': 12,
            'documents': 10,
            'steam': 8,
            'gamefolder': 5
        }
        
        for loc, bonus in location_bonus.items():
            if loc in path:
                priority += bonus
                break
        
        size = save_info.get('size', 0)
        if 5000 < size < 1000000: # Adjusted slightly for typical larger JSONs
            priority += 10
        
        if save_info.get('money_amount') is not None:
            priority += 15
        
        return min(100, priority)
