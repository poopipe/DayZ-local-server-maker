# Install
- Clone this repo
- run `install.bat`

# Server Setup

- run `launch.bat` from the install directory to begin the server creation process
    - Initial setup will run and install your server/mods
    - `config.json` will be created in your server directory

## Initial Setup Parameters:
Press enter to accept the default value [default]

- Server directory: path to desired server directory
- Server name [directory name]:
- Port [2302]:
- Max players [10]:
- Join password []:
- Admin password []:
- CPU count [4]:
- Instance id [2]:
- Shard id [local1]:
- Steam account name: your Steam username
- Steam ID: your Steam ID
- Steam Web API key: a valid Steam Web Api key
- DayZ client directory: your DayZ client directory
- Client mod name (blank to finish): enter mod name to search workshop, select from results list. this will repeat til you stop adding mods 
- Server mod name (blank to finish): enter mod name to search workshop, select from results list. this will repeat til you stop adding mods


# Server Configuration

Run `configure.bat` in the server directory.

1. Install a mod
2. Uninstall a mod
3. Rename
4. Change the mission

Press Enter to finish. Rename changes the server name shown in the game and in `start.bat`. It does not rename the directory. 

Change the mission picks from that server's `mpmissions` directory.


# Server Update

run `update.bat` to update the server and mods 


# Server Startup and Play

`start.bat` starts the server.

Because this tool uses SteamCmd it will log you out of your active steam client session when downloading the server or mods. 

`play.bat` starts DayZ and connects to the local server. 
If Steam is not signed in, it restarts Steam and waits - you may be prompted by Steam to login. 
If the server is not already running, it will be started.

This .bat file is not 100% reliable. If you encounter and authloginstate error after running it, manually restart your steam client and try again



# Getting a Steam Web API key
Sign in to Steam and open https://steamcommunity.com/dev/apikey

Enter `localhost` as the domain name. This value is only a label. Agree to the terms and register. The page shows a 32 character key. Paste that key when setup asks for `Steam Web API key`.

If you already registered a key, the same page shows it. There is no need to register another one.

