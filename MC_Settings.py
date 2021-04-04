import os
import json

DefaultSettings = {
    'remote_dir' : 'Minecraft',
    'world_name' : '',
    'server_jar_compiler_command' : '',
    'server_jar_dir' : '',
    'server_jar' : 'server',
    '_target_host' : '',
    '_proxy_host' : '',
    '_proxy_port' : 443,
    '_client_cert' : '',
    '_client_key' : '',
    '_known_hosts' : 'known_hosts',
    '_private_key' : '',
    '_max_backups' : 4
        }

_CheckSettings = ('world_name', '_target_host')

def ReadSettings():
    if not os.path.exists('settings.json') or os.stat('settings.json').st_size == 0:
        Settings = DefaultSettings
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(Settings, f, indent=2)
            f.close()
    else:
        with open('settings.json', encoding='utf-8') as f:
            Settings = json.load(f)
            f.close()
    
    for Check in _CheckSettings:
        if Settings[Check] == '':
            Settings = None
            break

    return Settings