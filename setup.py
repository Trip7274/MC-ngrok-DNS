import http.client
import json
from pathlib import Path

print("\nWelcome to the setup script!\n\n")
Cloudflare_Token = input("\nInput your Cloudflare API Token\n")
Cloudflare_Zone_ID = input("\nInput your Cloudflare Zone ID\n")
ngrok_Token = input("\nInput your ngrok Token\n")
Subdomain = input("\nInput your desired subdomain, for example, to use \"minecraft.example.com\", input \"minecraft\"\n")
Discord_Enabled = input("\nWould you like to recieve notifications on Discord using a webhook? (Y/N, Default: N)\n").lower().strip() == 'y'

if Discord_Enabled:
    print("\n\nDiscord settings:\n")
    Webhook_URL = input("\nWhat's your Discord webhook URL?\n")
    System_name = input("\nWhat's the name of your server's OS? (Default: \"OpenMediaVault\")\n")
    System_icon = input("\nPlease provide a direct URL to the profile picture you'd like your OS notifications to have (Default: OMV logo)\n")
    System_color = input("\nWhat do you want the color of your OS notifications to be? (HEX code, Default: #63A9DF)\n")
    Discord_ID = input("\nIf you'd like to be pinged for any errors, please provide your Discord user ID (Default: Off)\n")
    # Set everything to default if none of these were provided
    if System_name == "":
        System_name = "OpenMediaVault"
    if System_icon == "":
        System_icon = "https://cdn.discordapp.com/attachments/606168640840269846/1194467895120515083/OMV.png"
    if System_color == "":
        System_color = "63A9DF"
    if Webhook_URL == "":  # Disables Discord notifications if the webhook URL wasn't provided
        Discord_Enabled = False
        print("\nDiscord notifications were disabled as the Webhook URL wasn't set\n")
else:
    print("\nSkipping Discord settings and disabling notifications.\n")
    Webhook_URL = ""
    System_name = ""
    System_icon = ""
    System_color = ""
    Discord_ID = ""  # Setting some empty variables just so it doesn't break without Discord

# Filtering some inputs
if Discord_Enabled:
    Discord_ID = Discord_ID.replace("<", "")  # vv Make sure no angled brackets or @s are in the User ID
    Discord_ID = Discord_ID.replace("@", "")
    Discord_ID = Discord_ID.replace(">", "")  # ^^ This can probably be shortened or improved if you knew your way around python enough, but this only runs once, so it's alright

    if "#" in System_color:  # Remove the # if found in the HEX code
        System_color = System_color.replace("#", "")

    System_color = int(System_color, 16)  # Convert HEX codes into integers for Discord's API
    Discord_ID = f" <@{Discord_ID}>"  # Format the User ID to be a mention


root_directory = Path(__file__).resolve().parent  # Get the absoloute path to this script to be able to use relative paths later on
pretty_root_directory = str(root_directory)
pretty_root_directory = pretty_root_directory.replace("\\", "/")  # Make the path prettier for terminal responses

input(f"\nPlease make sure that an SRV record with the subdomain \"{Subdomain}\" doesn't already exist, if you're just following the tutorial, or are sure, press enter.\n")

print(f"\nCreating a new DNS record with the subdomain \"{Subdomain}\"...\n")

# Send a POST request to Cloudflare to create the required record
cloudflare_connection = http.client.HTTPSConnection("api.cloudflare.com")

cloudflare_payload = json.dumps({
    "type": "SRV",
    "ttl": 120,
    "data": {
        "service": "_minecraft",
        "proto": "_tcp",
        "name": Subdomain,
        "priority": 1,
        "weight": 5,
        "port": 0,
        "target": "www.example.com"  # Just as a placeholder for the time being, same with the port above
    }
})

cloudflare_headers = {
    'Content-Type': "application/json",
    'Authorization': f"Bearer {Cloudflare_Token}"
}

cloudflare_connection.request("POST", f"/client/v4/zones/{Cloudflare_Zone_ID}/dns_records", cloudflare_payload, cloudflare_headers)

# Process the response and ready a beautified version for logs
cloudflare_response = cloudflare_connection.getresponse()
cloudflare_data = cloudflare_response.read()
cloudflare_data = cloudflare_data.decode("utf-8")
cloudflare_data = json.loads(cloudflare_data)
success = cloudflare_data["success"]
pretty_postdata = json.dumps(cloudflare_data, indent=2)

if success:  # Check if the request was a success, and if so, write the configs for the other script to read
    Cloudflare_Record_ID = cloudflare_data["result"]["id"]
    print("Success!\nWriting to configs.json...\n")
    configs = {  # Data to be written
        "Cloudflare_Token": Cloudflare_Token,
        "Cloudflare_Zone_ID": Cloudflare_Zone_ID,
        "Cloudflare_Record_ID": Cloudflare_Record_ID,
        "ngrok_Token": ngrok_Token,
        "Subdomain": Subdomain,
        "Discord_Enabled": Discord_Enabled,
        "Webhook_URL": Webhook_URL,
        "System_name": System_name,
        "System_icon": System_icon,
        "System_color": System_color,
        "Discord_ID": Discord_ID
    }

    # Serializing json
    settings = json.dumps(configs, indent=4)

    # Writing to json file
    with open(f"{root_directory}/configs.json", "w") as outfile:
        outfile.write(settings)

    print("Done!\nYou should run update_records.py now.")
    quit(0)  # Hooray!

elif not success:  # If the request was rejected by Cloudflare, create an error log and quit
    print(f"The request to create a new SRV record failed, please make sure your credintals are valid and there is no record already under the \"{Subdomain}\" subdomain, the failed response will be printed and logged in \"{pretty_root_directory}/error_log.txt\"\n")
    errorlog = open(f"{root_directory}/error_log.txt", "w")
    errorlog.write(
        f'Request: POST\nURL: "https://api.cloudflare.com/client/v4/zones/{Cloudflare_Zone_ID}/dns_records"\nHeaders: {cloudflare_headers}\nPayload: {cloudflare_payload}\n\nResponse:\n{pretty_postdata}\n\nError 103, Cloudflare response failed.')
    errorlog.close()
    print(f"\n{pretty_postdata}\n\nError 103")
    input("\nPress enter to quit...\n")
    quit(103)
