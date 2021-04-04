import socket
import ssl
import asyncio
import asyncssh
import time
import os
import ResourcePath
import re
import zipfile
import shutil
from datetime import date, datetime
import glob
import base64
import MC_Settings

local_dir = os.getcwd()

# Dummy standard variables
remote_dir = ''
world_name = ''
server_jar_compiler_command = ''
server_jar_dir = ''
server_jar = ''
_target_host = ''
_proxy_host = ''
_proxy_port = 443
_client_cert = ''
_client_key = ''
_known_hosts = ''
_private_key = ''
_max_backups = 4

# Read settings from settings file
_Variables = MC_Settings.ReadSettings()

assert _Variables is not None, 'Missing settings in settings.json'

locals().update(_Variables)

_known_hosts = ResourcePath.resource_path(_known_hosts)
_private_key = ResourcePath.resource_path(_private_key)

Progress_Bar = None
Progress_Text = None
CurrentWorldSize = 0

if not os.path.isdir(f'{local_dir}/files'):
    os.mkdir(f'{local_dir}/files')
if not os.path.isdir(f'{local_dir}/files/plugins'):
    os.mkdir(f'{local_dir}/files/plugins')

class SSL_Socket:
    async def create_connection(self, protocol_factory, host, port):
        loop = asyncio.get_event_loop()
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH) # Verify Server cert
        context.load_cert_chain(certfile=_client_cert, keyfile=_client_key) # Load Client cert
        context.set_alpn_protocols(['ssh/2.0'])
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((_proxy_host, _proxy_port))
        return (await loop.create_connection(protocol_factory, sock=s, ssl=context, server_hostname=host))

if _proxy_host == '':
    _tunnel = ()
else:
    _tunnel = SSL_Socket()
    _client_cert = ResourcePath.resource_path(_client_cert)
    _client_key = ResourcePath.resource_path(_client_key)

def ProgressBarHandler(FilePathA, FilePathB, CurrentSize, TotalSize):
    if Progress_Bar is None:
        return
    Progress_Bar['value'] = CurrentSize / TotalSize * 100
    Progress_Bar.update()

def BackupProgressBarHandler(FilePathA, FilePathB, CurrentSize, TotalSize):
    global CurrentWorldSize
    if Progress_Bar is None or Progress_Text is None:
        return
    else:
        if TotalSize != 0:
            if CurrentSize / TotalSize == 1:
                CurrentWorldSize += TotalSize
                Progress_Bar['value'] = CurrentWorldSize / TotalWorldSize * 100
                Progress_Bar.update()
                Progress_Text['text'] = f'{CurrentWorldSize / 1048576:.2f} [MB] out of {TotalWorldSize / 1048576:.2f} [MB]'
                Progress_Text.update()

def zipdir(path, ziph):
    """ziph is zipfile handle"""
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(path, '..')))

async def StopStartServer(StopStart, conn):
    """
    Stops or starts the Minecraft server.
    StopStart='Stop' or 'Start',
    conn=(asyncssh connection class)
    """
    if StopStart == 'Start':
        # Start server
        await conn.run('screen -dmS Minecraft bash -c \"/home/mc/Minecraft/start.sh\"')
        if Progress_Text is not None:
            Progress_Text['text'] = 'Starting Server...'
            Progress_Text.update()
        if Progress_Bar is not None:
            Progress_Bar['value'] = 0
            Progress_Bar.update()
        time.sleep(5)
    elif StopStart == 'Stop':
        # 1 minute warning
        await conn.run('screen -S Minecraft -X stuff \'say \u00A7c Restart in 1 minute...\u00A7r\r\'')
        if Progress_Text is not None:
            Progress_Text['text'] = 'Stopping Server in 1 minute...'
            Progress_Text.update()
        time.sleep(30)
        # 30 seconds warning
        await conn.run('screen -S Minecraft -X stuff \'say \u00A7c Restart in 30 seconds...\u00A7r\r\'')
        if Progress_Text is not None:
            Progress_Text['text'] = 'Stopping Server in 30 seconds...'
            Progress_Text.update()
        time.sleep(20)
        # 10 seconds warning
        await conn.run('screen -S Minecraft -X stuff \'say \u00A7c Restart in 10 seconds...\u00A7r\r\'')
        if Progress_Text is not None:
            Progress_Text['text'] = 'Stopping Server in 10 seconds...'
            Progress_Text.update()
        time.sleep(10)
        # Shutdown server
        await conn.run('screen -S Minecraft -X stuff \'stop\r\'')
        if Progress_Text is not None:
            Progress_Text['text'] = 'Stopping Server...'
            Progress_Text.update()
        # Waiting for max 60 seconds for shutdown
        for _ in range(60):
            if not 'Minecraft' in (await conn.run('screen -list')).stdout:
                break
            time.sleep(1)

async def ASYNC_MC_Management(Action, Username, Password, File=None):
    try:
        async with asyncssh.connect(_target_host, tunnel=_tunnel, username=base64.b64decode(Username).decode('utf-8'), password=base64.b64decode(Password).decode('utf-8'), client_keys=_private_key, known_hosts=_known_hosts) as conn:
            async with conn.start_sftp_client() as sftp:
                if Action == 'Update':
                    await StopStartServer('Stop', conn)
                    # Upload new server.jar
                    if Progress_Text is not None:
                        Progress_Text['text'] = 'Updating Server...'
                        Progress_Text.update()
                    await sftp.put(f'{local_dir}/files/{server_jar}.jar', remote_dir, progress_handler=ProgressBarHandler)
                    await StopStartServer('Start', conn)
                    conn.close()

                elif Action == 'UpdatePlugins':
                    await StopStartServer('Stop', conn)
                    if Progress_Text is not None:
                        Progress_Text['text'] = 'Updating Plugins...'
                        Progress_Text.update()
                    # Removing old plugin jars
                    Files = await sftp.listdir(f'{remote_dir}/plugins')
                    for File in [i for i in Files if i.endswith('.jar')]:
                        await sftp.remove(f'{remote_dir}/plugins/{File}')
                    # Upload new plugin jars
                    await sftp.put(f'{local_dir}/files/plugins', remote_dir, recurse=True, progress_handler=ProgressBarHandler)
                    await StopStartServer('Start', conn)
                    conn.close()
                
                elif Action == 'Backup':
                    global TotalWorldSize
                    global CurrentWorldSize
                    CurrentWorldSize = 0
                    # Download world folders
                    TotalWorldSize = sum([int(i) for i in re.split('\t|\n', (await conn.run(f'du {remote_dir}/\"{world_name}\"* -bs')).stdout)[:-1:2]])
                    for directory in (world_name, f'{world_name}_nether', f'{world_name}_the_end'):
                        await sftp.get(f'{remote_dir}/{directory}', local_dir, recurse=True, preserve=True, progress_handler=BackupProgressBarHandler)
                    conn.close()
                    # Say program is zipping files
                    if Progress_Text is not None:
                        Progress_Text['text'] = 'Compressing Backup into Zip...'
                        Progress_Text.update()
                    # Generate Zip name
                    if not os.path.isdir(f'{local_dir}/files/backups'):
                        os.mkdir(f'{local_dir}/files/backups')
                    Name = f"MC_{date.today().strftime('%d-%m-%Y')}_"
                    Glob = glob.glob(f'{local_dir}/files/backups/{Name}*.zip')
                    if len(Glob) != 0:
                        ZipInt = max([int(re.split('_|\.', i)[-2]) for i in Glob]) + 1
                    else:
                        ZipInt = 0
                    # Zip world folders
                    zipf = zipfile.ZipFile(f'{local_dir}/files/backups/{Name}{ZipInt}.zip', 'w', zipfile.ZIP_DEFLATED)
                    for directory in (f'{local_dir}/{world_name}', f'{local_dir}/{world_name}_nether', f'{local_dir}/{world_name}_the_end'):
                        zipdir(directory, zipf)
                    zipf.close()
                    # Delete temporary world folders, backup zip remains
                    for directory in (f'{local_dir}/{world_name}', f'{local_dir}/{world_name}_nether', f'{local_dir}/{world_name}_the_end'):
                        shutil.rmtree(directory)
                    # Remove backups older than the most recent 4
                    Backups = glob.glob(f'{local_dir}/files/backups/MC_*_*.zip')
                    Backups.sort(key=lambda date: datetime.strptime(date.split('_')[-2], "%d-%m-%Y"))
                    if len(Backups) > _max_backups:
                        for i in Backups[:-_max_backups]:
                            os.remove(i)
                    # Set progressbar back to 0%
                    if Progress_Bar is not None:
                        Progress_Bar['value'] = 0
                        Progress_Bar.update()

                elif Action == 'DownloadFile':
                    if File is not None:
                        if not os.path.isdir(f'{local_dir}/files'):
                            os.mkdir(f'{local_dir}/files')
                        # Download File
                        await sftp.get(f'{remote_dir}/{File}', f'{local_dir}/files', preserve=True, progress_handler=ProgressBarHandler)
                    conn.close()
                    # Set progressbar back to 0%
                    if Progress_Bar is not None:
                        Progress_Bar['value'] = 0
                        Progress_Bar.update()

                elif Action == 'UploadFile':
                    if File is not None:
                        # Upload File
                        File = File.split('/')
                        Filename = File[-1]
                        Filepath = '/'.join(File[:-1])
                        await sftp.put(f'{local_dir}/files/{Filename}', f'{remote_dir}/{Filepath}', progress_handler=ProgressBarHandler)
                    conn.close()
                    # Set progressbar back to 0%
                    if Progress_Bar is not None:
                        Progress_Bar['value'] = 0
                        Progress_Bar.update()

                elif Action == 'RestartServer':
                    await StopStartServer('Stop', conn)
                    await StopStartServer('Start', conn)
                    conn.close()

                elif Action == 'Login':
                    conn.close()

        SFTP_Succes = True
    except:
        SFTP_Succes = False
    finally:
        Username, Password = None, None
        return SFTP_Succes

def MC_Management(Action, Username, Password, File=None, Tries=4, ProgressBar=None, ProgressText=None):
    """
    Manages the Minecraft server.
    Action='Login', 'Update', 'UpdatePlugins', 'Backup', 'DownloadFile', 'UploadFile' or 'RestartServer',
    Username=(str),
    Password=(str),
    Tries=(int), default = 4,
    ProgressBar=None (ttk.Progressbar)
    """
    if ProgressBar is not None:
        global Progress_Bar
        Progress_Bar = ProgressBar
    if ProgressText is not None:
        global Progress_Text
        Progress_Text = ProgressText
    tried = 0
    while tried < Tries:
        SFTP_Succes = asyncio.get_event_loop().run_until_complete(ASYNC_MC_Management(Action, Username, Password, File))
        if SFTP_Succes:
            break
        tried += 1
        time.sleep(0.5)
    return SFTP_Succes

def CompileServerJar(Progress_Text=None):
    if (server_jar_compiler_command or server_jar_dir) == '' and Progress_Text is not None:
        Progress_Text['text'] = 'No Compile Command'
        Progress_Text.update()
        Progress_Text.after(1000, lambda: Progress_Text.config(text='', fg='white'))
        Progress_Text.update()
        return
    if Progress_Text is not None:
        Progress_Text['text'] = 'Compiling server jar...'
        Progress_Text.update()
    os.system(server_jar_compiler_command)
    shutil.copyfile(f'{server_jar_dir}/{server_jar}.jar', f'{local_dir}/files/{server_jar}.jar')
    if Progress_Text is not None:
        Progress_Text.config(text='Done', fg='green')
        Progress_Text.update()
        Progress_Text.after(1000, lambda: Progress_Text.config(text='', fg='white'))
        Progress_Text.update()