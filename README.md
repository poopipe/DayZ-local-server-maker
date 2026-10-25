# Initial setup

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e .
.venv\Scripts\python.exe -m local_server_maker new_server CONFIG.json
```

Initial Setup:

You will be asked a series of questions - answer them. 
A fresh DayZ Server and all specified mods will be downloaded into the specified server directory.
Server will be configured to load mods
Helpful .bat scripts are added to the server directory

```
Server directory: desired server directory
Server name [directory name]:
Port [2302]:
Max players [10]:
Join password []:
Admin password []:
CPU count [4]:
Instance id [2]:
Shard id [local1]:
Steam account name: your Steam username
Steam ID: your Steam ID
Steam Web API key: a valid Steam Web Api key
DayZ client directory: your DayZ client directory
Client mod name (blank to finish): enter mod name to search workshop, select from results list. 
Server mod name (blank to finish): enter mod name to search workshop, select from results list. 
```

# Configuration

Run `configure.bat` in the server directory.

1. Install a mod
2. Uninstall a mod
3. Rename
4. Change the mission

Press Enter to finish. Rename changes the server name shown in the game and in `start.bat`. It does not rename the directory. Change the mission picks from that server's `mpmissions` directory.



# Server startup and play

`start.bat` starts the server.

Because this tool uses SteamCmd it will log you out of your active steam client session when downloading the server or mods. 

`play.bat` starts DayZ and connects to `127.0.0.1` on the server port. If Steam is not signed in, it restarts Steam and waits. Finish a Steam Guard prompt if one appears. If the server is not already running, it starts `start.bat` and waits until the mission is ready, then starts the client.

This .bat file is not 100% reliable. If you encounter and authloginstate error after running it, manually restart your steam client and try again


# Steam Web API key

Sign in to Steam and open https://steamcommunity.com/dev/apikey

Enter `localhost` as the domain name. This value is only a label. Agree to the terms and register. The page shows a 32 character key. Paste that key when setup asks for `Steam Web API key`.

If you already registered a key, the same page shows it. There is no need to register another one.
