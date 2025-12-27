import json

class VersionCheck:
    @staticmethod
    def get_local_version(version_file_path='version.json'):
        try:
            with open(version_file_path, 'r') as f:
                data = json.load(f)
                return data.get('version', '0.0.0')
        except:
            return '0.0.0'
