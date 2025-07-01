
# 🤖 Proxima Discord Bot

**Proxima** is a feature-rich Discord bot designed for **tournament and scrim management**, tailored specifically for competitive communities. With simple command execution and an intuitive setup process, Proxima empowers admins to efficiently manage matches, clean up channels, and organize events.

---

## 📌 Features

- 🏆 Set up and manage **Tournaments**  
- ⚔️ Create, start, stop, and delete **Scrims**  
- ⚙️ Configure main channels with a setup command  
- 🧹 Clean messages with a single command  
- 📜 Interactive help menu with embedded links  
- 🎯 Mention detection to guide users  
- ⏱️ Latency check with `!ping`

---

## 🛠 Commands

| Command          | Description                              | Access         |
|------------------|------------------------------------------|----------------|
| `!setup`         | Set up primary channels                  | Admin only     |
| `!tsetup`        | Set up a tournament                      | Admin only     |
| `!sttorny`       | Start the tournament                     | Admin only     |
| `!sptorny`       | Stop the tournament                      | Admin only     |
| `!dltorny`       | Delete the tournament                    | Admin only     |
| `!ssetup`        | Set up scrims                            | Admin only     |
| `!stscrim`       | Start the scrims                         | Admin only     |
| `!spscrim`       | Stop the scrims                          | Admin only     |
| `!dlscrims`      | Delete the scrims                        | Admin only     |
| `!Clear [amount]`| Clean messages (max 99 at a time)        | Admin only     |
| `!help`          | Display interactive help embed           | Admin only     |
| `!ping`          | Show bot latency                         | Everyone       |

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/manindra-455/proxima_bot.git
cd proxima_bot
```

### 2. Install Dependencies

Make sure you have Python 3.8+ installed. Then run:

```bash
pip install -r requirements.txt
```

*Sample dependencies you may need:*
```txt
discord.py
python-dotenv
```

### 3. Set up the `.env` file

Create a `.env` file in the root directory and add your bot token:

```
DISCORD_TOKEN=your_discord_bot_token_here
```

---

## 🔐 Permissions Required

Ensure the bot has the following permissions in your server:

- Read Messages
- Send Messages
- Manage Messages
- Embed Links
- Mention Everyone (optional)

---

## 📎 Example Usage

- `!tsetup` – Initializes a new tournament
- `!stscrim` – Starts a scrim session
- `!Clear 10` – Deletes 10 recent messages from a channel
- Mention the bot directly – Responds with a help suggestion

---

## 🔮 Upcoming Features

- 📊 Points Table System  
- 📥 Embedded Message Support  
- 📀 Music Playback System  

---

## 🤝 Contributing

**Proxima is open for everyone to Contribute!**  
Whether you're a beginner or an advanced developer, feel free to fork the project, improve it, and make it your own. Contributions are highly welcome in the form of pull requests, new features, documentation improvements, or bug fixes.

---

## 📌 Links

- [Invite Proxima](https://discord.com/oauth2/authorize?client_id=1273192449669468161&permissions=8&integration_type=0&scope=bot)
- [Support Server](https://discord.gg/7ZzZZFBUnY)
- [Website](http://ximabot.unaux.com/)

---

## 📝 License

This project is open-source and available under the [MIT License](LICENSE).

---

## 👨‍💻 Author

**Proxima** by `steg_crazy`  
Maintained by [manindra-455](https://github.com/manindra-455)
