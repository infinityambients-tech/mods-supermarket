
import re

current_version = "2.12.7.5E"
remote_version = "2.13.1.2.E"

def is_newer(remote):
    try:
        def parse_version(v):
            return [int(x) for x in re.findall(r'\d+', v)]
        
        v1_parts = parse_version(current_version)
        v2_parts = parse_version(remote)
        return v2_parts > v1_parts
    except Exception as e:
        print(f"Error: {e}")
        return False

print(f"Local: {current_version}")
print(f"Remote: {remote_version}")
print(f"Is Newer? {is_newer(remote_version)}")
