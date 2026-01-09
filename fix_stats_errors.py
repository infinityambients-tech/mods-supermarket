#!/usr/bin/env python3
"""fix_stats_errors.py
Simple emergency fixer that uses AdvancedStatsModifier to set common fields.
Usage:
  python fix_stats_errors.py path/to/save.json
"""
import sys
from pathlib import Path

from src.save_editor.advanced_stats_modifier import AdvancedStatsModifier


def emergency_fix_save_file(save_path: str):
    mod = AdvancedStatsModifier()
    # Try to set common stats
    attempts = [
        ('level', 99, 'set'),
        ('money', 9999999, 'set'),
        ('xp', 100000, 'set')
    ]

    for stat, val, op in attempts:
        res = mod.modify_statistic(save_path, stat, val, op)
        print(f"{stat}: {res.get('message')} — path: {res.get('field_path')}")

    print('Done')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: fix_stats_errors.py path/to/save.json')
        sys.exit(1)
    p = sys.argv[1]
    emergency_fix_save_file(p)
