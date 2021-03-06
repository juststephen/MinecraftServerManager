# Minecraft Server Manager
Minecraft Server Manager written in Python for Minecraft servers running on linux accesible by SSH.

## How to build .exe
1. Install the requirements as stated in `requirements.txt`.
2. Use PyInstaller with the command in `PyInstaller_One_Folder.bat` where `ABSOLUTE_PATH_TO_YOUR_END_RESULT_FOLDER` is the absolute path to your folder where the end result will show up.
3. <b>Run the resulting .exe once and edit the `settings.json` before proceeding.</b>

    - `remote_dir` is the remote directory of the Minecraft server
    - `world_name` is the name of the world folders, for example putting in `test world` would be used as `test world`, `test world_nether` and `test world_the_end`
    - `server_jar_compiler_command` is the cmd command for generating the server jar
    - `server_jar_dir` is the directory where the server jar is stored after compiling
    - `server_jar` is the name of the server jar after compiling <b>without</b> the file extension
    - `_target_host` is the SSH address of the minecraft server
    - `_proxy_host` is the proxy address for the SSH server if used, leave empty if not
    - `_proxy_port` same as `_proxy_host` but the port
    - `_client_cert` and `_client_key` if the proxy uses certificates, put the file locations here.
    - `_known_hosts` is the known_hosts file generated by SSH containing the key
    - `_private_key` is the file location of the private SSH key

4. You should now be able to start it up and use it.

Example `settings.json`
```json
{
  "remote_dir": "/home/remote_user/Minecraft",
  "world_name": "world",
  "server_jar_compiler_command": "/home/local_user/compile.sh",
  "server_jar_dir": "/home/local_user",
  "server_jar": "server",
  "_target_host": "ssh.example.com",
  "_proxy_host": "",
  "_proxy_port": ,
  "_client_cert": "",
  "_client_key": "",
  "_known_hosts": "known_hosts",
  "_private_key": "ssh_key"
}
```

Note: If you wish to change some buttons, feel free to edit these in the MC_Main.py file.
