<div align="center">

# InfiniBot

**A powerful, multi-purpose Discord utility bot built for millions of servers**

![InfiniBot Header](./github-pages-site/assets/images/header-image.png)

[![GitHub stars](https://img.shields.io/github/stars/cypress-exe/InfiniBot?style=for-the-badge)](https://github.com/cypress-exe/InfiniBot/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/cypress-exe/InfiniBot?style=for-the-badge)](https://github.com/cypress-exe/InfiniBot/network)
[![GitHub issues](https://img.shields.io/github/issues/cypress-exe/InfiniBot?style=for-the-badge)](https://github.com/cypress-exe/InfiniBot/issues)
[![Discord](https://img.shields.io/discord/1009127888483799110?style=for-the-badge&logo=discord&logoColor=white&label=Discord)](https://discord.gg/mWgJJ8ZqwR)

[![Top.gg Servers](https://top.gg/api/widget/servers/991832387015159911.svg?style=for-the-badge)](https://top.gg/bot/991832387015159911)

[🚀 Quick Start](#-quick-start) • [📖 Documentation](#-documentation) • [🔧 Installation](#-installation) • [🤝 Support](#-support)

[![Add InfiniBot to Your Server](https://img.shields.io/badge/Add%20to%20Server-7289DA?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/oauth2/authorize?client_id=991832387015159911&permissions=1374809222364&scope=bot)
[![Go to Help Docs](https://img.shields.io/badge/Go%20to%20%20Help%20Docs-ffffff?style=for-the-badge)](https://cypress-exe.github.io/InfiniBot/)

</div>

## ✨ Features

InfiniBot is a multipurpose Discord utility bot designed to scale across millions of servers using SQLite for storage, docker for containerization, and sharding for distribution. InfiniBot is in thousands of servers, with hundreds of thousands of active users. It's built to be fast, efficient, and easy to use.

### 🛡️ Moderation & Security
- **Advanced Profanity Filter** - Customizable word filtering with strike system
- **Intelligent Spam Detection** - Multi-layered anti-spam protection
- **Comprehensive Logging** - Track all messages and moderator actions, including message edit and deletion history
- **Automated Moderation** - Smart auto-moderation with configurable thresholds and punishments

### 🎉 Community Features
- **Leveling System** - Reward active members with XP and role rewards
- **Birthday Celebrations** - Never miss a community member's special day
- **Reaction Roles** - Self-assignable roles via emoji reactions
- **Custom Role Messages** - Automated role assignment messages
- **Welcome/Leave Messages** - Personalized greetings for new members

### 🎪 Entertainment
- **Joke Commands** - Built-in entertainment features
- **Motivational Messages** - Boost server morale
- **And more!**

> **Note:** External contributions are welcome! You're free to fork, contribute, and self-host for personal use or small friend groups. However, please do not create competing public instances that would conflict with the official InfiniBot service.

## 📋 Prerequisites

If you just want to use the official InfiniBot, you can invite it to your server using the button below:

<div align="center">

[![Add InfiniBot to Your Server](https://img.shields.io/badge/Add%20to%20Server-7289DA?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/oauth2/authorize?client_id=991832387015159911&permissions=1374809222364&scope=bot)

</div>

If you want to self-host InfiniBot, you'll need to set up your own instance. Here's what you need:

InfiniBot runs inside a Docker container, so Docker must already be installed. You can find documentation for setting up Docker [here](https://docs.docker.com/get-docker/).

Additionally, you need to have a Discord bot registered with Discord. You can register your bot at the [Discord Developer Portal](https://discord.com/developers/applications).

Follow these steps to set up InfiniBot for a Linux environment. Some steps may vary for certain operating systems.

## 🚀 Quick Start

Get InfiniBot up and running in just a few minutes:

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/cypress-exe/InfiniBot.git
cd InfiniBot
```

### 2️⃣ Build the Container
```bash
sudo bash build.bash
```
Docker will begin building the container, which may take some time on the first run.
> 💡 **Tip:** Use `--use-cache` flag for faster builds (after initial setup)

### 3️⃣ Initial Run
```bash
sudo bash run.bash
```
> ⚠️ **Expected:** You'll see an error about missing environment variables - this is normal!

### 4️⃣ Configure Environment
```bash
sudo vim .env
```
Set your Discord bot token:
```env
DISCORD_AUTH_TOKEN=your_bot_token_here
```
> ⚠️ **Important:** Only modify the `DISCORD_AUTH_TOKEN` variable. Leave others unchanged.

### 5️⃣ Start InfiniBot
```bash
sudo bash rebuild_and_run.bash
```

🎉 **Success!** InfiniBot should now be running. Don't forget to invite your bot to a server!  

### Troubleshooting
Due to the way the bot works under the hood, you may need to restart InfiniBot after adding it to its first server. You can do this by running the previous command again:
```bash
sudo bash rebuild_and_run.bash
```

In addition, you may need to wait a few hours before all of InfiniBot's commands appear in your Discord client. This is due to Discord's caching system, which can take time to update. Try restarting your Discord client for the changes to take effect.


## ⚙️ Configuration

You can customize InfiniBot's behavior through the `./generated/configure` folder:

- **🤬 Profanity Filter** - Add/remove words from `default_profane_words.txt`
- **👨‍💻 Developer Settings** - Configure admin IDs and bot settings in `config.json`

> 📝 **Note:** Most settings are pre-configured for the official InfiniBot and should be left unchanged for self-hosted instances.

## 🛠️ Development Scripts

There are a few development scripts in the root directory of the repository to help you manage the docker container and environment. These scripts are designed to be run with `sudo` to ensure proper permissions for Docker operations.

## 📖 Documentation

User documentation is available on the [InfiniBot Docs Website](https://cypress-exe.github.io/InfiniBot/) and provides detailed information on:
- **Installation** - Step-by-step setup guide
- **Configuration** - How to customize settings
- **Commands** - List of available commands and their usage
- **Features** - Overview of all bot features and functionalities


Developer documentation is available in the `./docs` folder of this repository.

## 🤝 Support

- **🐛 Bug Reports** - [Create an issue](https://github.com/cypress-exe/InfiniBot/issues)
- **💡 Feature Requests** - [Submit a request](https://github.com/cypress-exe/InfiniBot/issues)
- **💬 Discord Support** - [Join the server](https://discord.gg/mWgJJ8ZqwR)

## 📊 Project Stats

<div align="center">

![GitHub repo size](https://img.shields.io/github/repo-size/cypress-exe/InfiniBot?style=for-the-badge)
![GitHub last commit](https://img.shields.io/github/last-commit/cypress-exe/InfiniBot?style=for-the-badge)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/cypress-exe/InfiniBot?style=for-the-badge)

</div>

## 🏗️ Built With

- **🐍 Python** - Core bot logic
- **🔗 nextcord** - Discord API wrapper
- **🗃️ SQLite** - Database storage
- **🐳 Docker** - Containerization
- **⚡ Asyncio** - Asynchronous programming

## 📜 License & Usage

This project is licensed under a **Custom Open Source License** based on GPL v3 - see the [LICENSE](LICENSE) file for details.

**Usage Guidelines:**
- ✅ **Personal Use** - Fork, modify, and self-host for personal use or small friend groups
- ✅ **Contributions** - Pull requests and contributions are welcome!
- ✅ **Open Source Derivatives** - Any modifications must also be open source
- ✅ **Learning** - Use the code for educational purposes
- ❌ **Public Competition** - Hosting competing public instances is prohibited
- ❌ **Commercial Use** - Commercial use without explicit permission is prohibited

**Contributing:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

<div align="center">

**Made by [cypress.exe](https://github.com/cypress-exe)**

⭐ Star this repository if you found it helpful!

</div>
