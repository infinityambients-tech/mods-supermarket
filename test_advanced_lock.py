from advanced_lock import AdvancedLockManager

m = AdvancedLockManager(lock_file='test_update.lock')
print('Instance created')
res = m.acquire_lock(operation_id='test-op')
print('acquire:', res)
if res.get('success'):
    rel = m.release_lock()
    print('release:', rel)
else:
    print('Did not acquire lock; leaving file as-is')
