# ngrok-DNS-updater
Hi! I wrote this script to address my own troubles with ngrok's free plan as I wanted to host a small Minecraft server behind a reverse proxy, and I wanted it to be a free, passive server to run on my home server

Also, as this is a hobby project and I'm still very much a beginner in Python, I hope you forgive me for any poorly written code or improper practices, I tried my best, but please do make a pull request if you feel like you can improve on anything!

# Configs
Discord_Enabled - Whether to enable Discord notifications or not, simple

Webhook_URL - [You can get this from your Discord client](https://docs.gitlab.com/ee/user/project/integrations/discord_notifications.html#create-webhook) - Example: "`https://discord.com/api/webhooks/[Long string of numbers]/[Token]`"

Discord_ID - Input your Discord user ID if you'd like to be pinged for any errors that occur, to get this, right click on your profile with developer mode enabled, and click "Copy User ID" - Example: "`209264477709795338`"

1 - System_Name - You should specify your server's OS name here, if you're using OpenMediaVault, leave it blank - Example: "`TrueNAS`"

2 - System_icon - If you're specifying a server OS other than OMV, provide a direct URL to the profile picture you want your OS's notifications to appear - Example: "`https://cdn.discordapp.com/attachments/606168640840269846/1196589232370757734/TrueNAS.png`"

3 - System_color - If you're specifying a server OS other than OMV, provide a HEX code for the color of the embed, defaults to #63A9DF, or OMV blue - Example: "`#488ACB`", or "`488ACB`"

![Discord notification visual guide](https://github.com/iGamerTrip/ngrok-DNS-updater/assets/42869384/6036a4a1-6a53-4777-be99-234892a9e76b)


# Setting up
This guide is assuming you already [have your domain setup on Cloudflare](https://developers.cloudflare.com/fundamentals/setup/account-setup/add-site/), and [have setup ngrok on your server](https://ngrok.com/docs/using-ngrok-with/docker/) (with the protocol as `tcp` and the port as `25565` instead of `HTTP` and port `80`, of course)
1. Go to your [Cloudflare API tokens page](https://dash.cloudflare.com/profile/api-tokens)
2. Get your Token by going to "Create Token" -> "Edit Zone DNS" template -> Select your intended domain - > Continue -> Create, and keep that token safe
3. Go to your [Cloudflare Dashboard](https://dash.cloudflare.com/), and into the Zone of the domain you'd like to use, in the bottom right of the main dashboard of the zone, there should be a text field with your Zone ID as [shown in this article](https://developers.cloudflare.com/fundamentals/setup/find-account-and-zone-ids/)
5. Go to your [ngrok API tokens page](https://dashboard.ngrok.com/api/new)
6. Press the "Add API Key" button in the bottom right, and keep that token safe for the time being
7. Great! You now have all of the variables you could get, now you just need to set them all up along with the settings of the script!
8. Assuming you [have python installed](https://www.python.org/downloads/), clone this repo by pressing the blue "<> Code" button at the top right
9. Start a command prompt, and `cd` into the directory of the repo you just downloaded, and type `setup.py`, then follow the on-screen instructions
10. After completing all the above steps, you may run `update_records.py` wherever you wish, so long as it has its accompanying `configs.json`

# Finishing touches
You'll probably want this script to run everytime your system boots, so i found [this](https://www.tutorialspoint.com/run-a-script-on-startup-in-linux) great guide for Linux, try out all the different methods they provide, i found the `systemd` service method to work best for me on OMV, but your mileage may vary

For reference, my current systemd service file is:
```
[Unit]
Description=Syncs ngrok domain and port with CF's DNS Records on boot
After=network.target

[Service]
ExecStart=timeout 60 python3 /Scripts/update_records.py
User=root
Group=root
Type=simple
RestartSec=60
Restart=on-failure
RestartPreventExitStatus=0

[Install]
WantedBy=multi-user.target
```

You might also want to run `update_records.py` with a timeout by running `timeout 60 python3 [path/to/update_records.py]`, just in case the script hangs or something unforseeable happens

# Deeper customization
If you want to change the preset Discord notifications, here's how:

Boot up message : Line `70`

ngrok error: Line `94`, and `106`

Cloudflare error: Line `165`

Success message: Line `152`
