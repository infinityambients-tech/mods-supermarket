import json
import tempfile
from pathlib import Path
from src.save_editor.advanced_stats_modifier import AdvancedStatsModifier


def test_modify_level_set():
    tmp = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json')
    data = {"player": {"shopLevel": 1, "xp": 10}, "money": 100}
    json.dump(data, tmp)
    tmp.flush()
    tmp.close()

    p = Path(tmp.name)
    mod = AdvancedStatsModifier()
    res = mod.modify_statistic(str(p), 'level', 50, 'set')
    assert res['success']

    # verify file updated
    with open(p, 'r', encoding='utf-8') as f:
        new = json.load(f)
    # shopLevel should be updated to 50 (or at least one level-like field changed)
    assert new.get('player', {}).get('shopLevel') == 50 or any('level' in k.lower() and v==50 for k,v in new.get('player', {}).items())

    p.unlink()


def test_modify_money_add():
    tmp = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json')
    data = {"money": 1000, "store": {"balance": 200}}
    json.dump(data, tmp)
    tmp.flush()
    tmp.close()

    p = Path(tmp.name)
    mod = AdvancedStatsModifier()
    res = mod.modify_statistic(str(p), 'money', 500, 'add')
    assert res['success']

    with open(p, 'r', encoding='utf-8') as f:
        new = json.load(f)

    # one of money/balance should have increased
    assert new.get('money') == 1500 or new.get('store', {}).get('balance') == 700
    p.unlink()
