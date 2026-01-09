from advanced_lock import AdvancedLockManager
import time
m = AdvancedLockManager(lock_file='test_hb.lock')
res = m.acquire_lock(operation_id='hb-test')
print('acquire', res)
m.start_heartbeat(interval=1)
print('heartbeat started')
time.sleep(2.5)
print('stopping heartbeat')
m.stop_heartbeat()
print('release', m.release_lock())
