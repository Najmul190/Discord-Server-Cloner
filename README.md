# Discord Server Cloner

A powerful Discord server cloning tool that creates perfect copies of Discord servers with ease, copying things most other tools miss such as onboarding settings, soundboard sounds, scheduled events, and more. This tool uses [discord.py-self](https://github.com/dolfies/discord.py-self) to enable user account automation for server cloning operations.

## ⚠️ Important Notice

This tool uses **discord.py-self**, which allows user accounts (not bots) to perform automated actions. Using self-bots is against Discord's Terms of Service. **Use this tool at your own risk.** I am not responsible for any account bans or terminations. For this reason, I recommend using an alt account for cloning operations.

## ✨ Features

- **Complete Server Cloning**: Clone entire Discord servers including:
  - [x] Categories and channel structure
  - [x] Text, voice, and forum channels
  - [x] Roles and permissions
  - [x] Emojis and stickers
  - [x] Soundboard sounds
  - [x] Scheduled events
  - [x] Server onboarding configuration
  - [x] Message history (configurable)
  - [x] Pinned messages
  - [x] Server bans
  - [x] Community features

- **No Server Restrictions**: Clone any server by specifying its Guild ID, regardless of permissions as long as your account has access
- **CLI Interface**: Rich terminal UI with real-time progress bars
- **Flexible Configuration**: Customize what gets cloned

## 🔗 Support

If you have any questions, need assistance or want news on updates, please join our dedicated Discord server. You can ask your questions there and leave once you have the help you need, or stay and be part of the community!

[![Discord Banner 2](https://discord.com/api/guilds/1269313927150309491/widget.png?style=banner2)](https://discord.gg/yUWmzQBV4P)

## ⭐ Installation:

### Requirement: Python 3.8 or higher

### 1. Download the tool:
- Go to the [Releases](https://github.com/Najmul190/Discord-Server-Cloner/releases/latest) page and download the latest release.

### 2. Extract the downloaded ZIP file to your desired location, using built-in tools or a program like WinRAR or 7-Zip.

### 3. Getting your Discord token

-   Go to [Discord](https://discord.com) and login to the account you want the token of
-   Press `Ctrl + Shift + I` (If you are on Windows) or `Cmd + Opt + I` (If you are on a Mac).
-   Go to the `Network` tab
-   Type a message in any chat, or switch server
-   Find one of the following headers: `"messages?limit=50"`, `"science"` or `"preview"` under `"Name"` and click on it
-   Scroll down until you find `"Authorization"` under `"Request Headers"`
-   Copy the value which is your token
-   **⚠️ Keep your token secret! Never share it with anyone, as it grants full access to your Discord account.**

### 4. Run the tool
- **Windows**: Simply double-click `run.bat` to start the tool.
- If you are on **Linux/Mac** or the batch file doesn't work, follow the steps in the next section.

## 📥 Installing Dependencies Manually (Linux/Mac or if batch file fails)

1. Open a terminal and navigate to the extracted folder. For example:
   ```bash
   cd /path/to/Server-Cloner
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate.bat`
   ```
3. Install the required dependencies using pip:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the main script:
   ```bash
   python main.py
   ```

## 🔧 Configuration

The tool uses `config.json` for configuration:

```json
{
    "token": false,
    "logs": true,
    "copy_settings": {
        "categories": true,
        "channels": true,
        "roles": true,
        "permissions": true,
        "emojis": true,
        "onboarding": true,
        "stickers": true,
        "forum_channels": true,
        "scheduled_events": true,
        "message_history": true,
        "message_history_limit": 15
    }
}
```

### Configuration Options

- **token**: Your Discord user token (this will be prompted on first run if set to `false`)
- **logs**: Enable/disable logging to file (`true`/`false`)
- **copy_settings**: Control what gets cloned
  - `categories`: Clone category structure
  - `channels`: Clone text and voice channels
  - `roles`: Clone server roles
  - `permissions`: Clone permission overwrites
  - `emojis`: Clone custom emojis
  - `onboarding`: Clone server onboarding setup
  - `stickers`: Clone custom stickers
  - `forum_channels`: Clone forum channels
  - `scheduled_events`: Clone scheduled events
  - `message_history`: Clone message history
  - `message_history_limit`: Number of messages to copy per channel (default: 15)
  - `clone_pins`: Clone pinned messages
  - `bans`: Clone server bans
  - `soundboard`: Clone soundboard sounds

These settings can be changed on startup or by editing `config.json` directly.

## 📝 Logging

Logs are saved to `logs/log.txt` with timestamps:

```
=== SERVER CLONER LOG STARTED AT 2025-11-09 15:30:22 ===
[2025-11-09 15:30:25] [+] Created Role: Moderator
[2025-11-09 15:30:26] [+] Created Category: General
[2025-11-09 15:30:27] [+] Created Text Channel: #welcome
```

If creating an issue or seeking support, please include relevant log entries.

## 🔍 Troubleshooting

### Common Issues

**"Invalid Token" error**:
- Make sure you're using a user token, not a bot token
- Token may have expired - get a fresh one
- Delete token from config.json and re-enter

**"Could not find guild" error**:
- Verify the server ID is correct
- Make sure your account has access to both servers
- Check that you have proper permissions

**Permission errors during cloning**:
- Ensure you have Administrator permissions in the destination server
- Some features require specific permissions (Manage Server, Manage Channels, etc.)

**Rate limiting**:
- Discord has rate limits - the tool includes delays
- Large servers may take significant time to clone

# ❤️ Donate

If you appreciate this project and want to support its development, feel free to donate by clicking this button!

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/E1E1Q7XEZ)