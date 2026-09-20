# Discord Server Builder Bot

Bring an entire Discord server to life with a single command. This bot reads predefined configuration files and automatically creates server categories, channels, and roles, making it easy to spin up a consistent community structure in seconds.

---

## ✨ Features

* **Automated server scaffolding** – Regenerates the full channel tree via a single `!setup` command.
* **Role provisioning** – Builds custom roles with colors, hoisting, and permission sets defined in `roles.json`.
* **Channel metadata** – Populates text channel topics and applies sensible default permission overwrites.
* **Idempotent operations** – Cleans up legacy channels and roles before rebuilding so you always start fresh.
* **Structured logging** – Streams runtime information to both stdout and `bot.log` for easy diagnostics.

---

## 📦 Project Layout

```
project/
├── README.md
├── requirements.txt
├── bot.py
├── .env.example
├── roles.json
└── structure.json
```

* `bot.py` – Main entry point for the Discord bot.
* `roles.json` – Declarative role definitions (name, color, permissions).
* `structure.json` – Category and channel tree for the server.
* `.env.example` – Template for your `DISCORD_TOKEN`.
* `requirements.txt` – Python dependency pinning.

---

## ✅ Prerequisites

* Python **3.11+**
* A Discord **bot token** with proper permissions (Administrator recommended)
* Access to a Discord guild where the bot has `Manage Roles` and `Manage Channels`

> ⚠️ The `!setup` command wipes every deletable channel and custom role. Use it only in a fresh server or when you intend to rebuild from scratch.

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/Gloxiedev/setuipdcbot.git
cd setuipdcbot
```

### 2. Install dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure the bot token
Copy the example env file and set your token:
```bash
cp .env.example .env
```
Then open `.env` and replace the placeholder:
```
DISCORD_TOKEN=your_bot_token_here  # <-- replace with your bot token
```
The bot reads `DISCORD_TOKEN` from a `.env` file or an environment variable. The token is never hardcoded and `.env` is gitignored so it stays out of version control.

### 4. Adjust the server template
* Modify `structure.json` to fit your channel taxonomy.
* Customize `roles.json` to define hierarchy, colors, and permissions.

Refer to the schema references below for valid fields.

---

## 🛠️ Running the Bot

Start the bot from within the virtual environment:
```bash
python bot.py
```

When the bot status shows online in Discord, issue the setup command in any server channel where the bot can respond:
```text
!setup
```

The bot will:
1. Delete existing channels (skipping community-required ones) and removable roles.
2. Create roles defined in `roles.json` in order.
3. Build categories and channels from `structure.json` with text channel topics and voice channels.
4. Report a summary of created resources.

Use `!help` to view available commands in-app.

---

## 📄 Configuration Reference

### `structure.json`
Defines server categories and their channels.

```json
{
  "categories": [
    {
      "name": "Category Name",
      "channels": [
        {
          "name": "text-or-voice-name",
          "description": "Channel topic or purpose",
          "type": "text"
        }
      ]
    }
  ]
}
```

* `type` accepts `"text"` or `"voice"`.
* Icons in names are allowed; the bot strips Discord-forbidden characters automatically.

### `roles.json`
Describes roles the bot should create.

```json
{
  "roles": [
    {
      "name": "Moderator",
      "color": "#FFAA00",
      "hoist": true,
      "permissions": [
        "manage_messages",
        "kick_members"
      ]
    }
  ]
}
```

* Colors use standard hex notation.
* `permissions` entries should match Discord permission attribute names from [`discord.Permissions`](https://discordpy.readthedocs.io/en/stable/api.html#discord.Permissions).

---

## 🧪 Logging & Troubleshooting

* Runtime logs are written to both the console and `bot.log`.
* Check for `Failed to load structure.json` or `roles.json` messages if setup aborts early.
* Discord rate limits are respected with small delays, but extremely large templates may still require patience.
* Ensure the bot’s role is above the roles it needs to create or assign.

---


## 📜 License

This project is distributed under the MIT License. See `LICENSE` if provided, or add one to clarify usage rights in your fork.

A project made by Koalas
