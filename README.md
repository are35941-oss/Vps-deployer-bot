# ⚡ VPS Deployer Discord Bot

A fast, lightweight Discord bot designed to automatically deploy and manage VPS/containers via simple slash commands, featuring strict owner-only access and automated SSH provisioning.

---

## 🌟 Features

* **Instant Provisioning:** Deploy new Linux VPS instances with a single slash command.
* **Strict Authorization:** Hardcoded check restricted strictly to authorized User IDs (`1320732831424450561`).
* **Secure Delivery:** Root IP, SSH port, and auto-generated secure credentials are sent privately.
* **Flexible Hosting:** Runs natively on Ubuntu/Debian VPS or inside containerized hosting (Pterodactyl / Python nodes).

---

## 🚀 Quick Setup (Automatic)

Run this on your main Linux VPS with root access:

```bash
git clone https://github.com/are35941-oss/Vps-deployer-bot.git
cd Vps-deployer-bot
chmod +x install.sh
sudo ./install.sh

⚙️ Manual Setup
1. Prerequisites
Python 3.10+
Docker Engine (for local container creation)
Git
2. Install Dependencies

git clone [https://github.com/are35941-oss/Vps-deployer-bot.git](https://github.com/are35941-oss/Vps-deployer-bot.git)
cd Vps-deployer-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt


3. Configure Environment
Create a .env file in the project root:

DISCORD_TOKEN=your_bot_token_here
OWNER_ID=1320732831424450561
GUILD_ID=your_guild_id_optional

To keep it running 24/7 with PM2:

pm2 start bot.py --name "vps-bot" --interpreter python3
pm2 save

💻 Commands

CommandDescriptionPermission
/create-vpsDeploys a new VPS and sends root SSH credentialsAuthorized Owner Only
/vps-statusDisplays running containers, RAM, and CPU usageAuthorized Owner Only
/pingDisplays bot latencyPublic


