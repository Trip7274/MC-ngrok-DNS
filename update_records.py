import http.client
import requests
import json
import datetime
from pathlib import Path
import os.path


root_directory = Path(__file__).resolve().parent  # Get the absoloute path to this script to be able to use relative paths later on
pretty_root_directory = str(root_directory)
pretty_root_directory = pretty_root_directory.replace("\\", "/")  # Make the path prettier for notifications

if not os.path.isfile(f"{root_directory}/configs.json"):  # Check if the configs file is there, and prompt the user to make it if they forgot to
    print("Error 101 - The config file was not found, you must run and configure \"setup.py\" before running this script.")
    quit(101)

# Loading and setting up the settings file
with open(f'{root_directory}/configs.json', 'r') as configsfile:
    settings = json.load(configsfile)

# Setting up some variables from the settings file
Cloudflare_Token = settings["Cloudflare_Token"]
Cloudflare_Zone_ID = settings["Cloudflare_Zone_ID"]
Cloudflare_Record_ID = settings["Cloudflare_Record_ID"]
ngrok_Token = settings["ngrok_Token"]
Subdomain = settings["Subdomain"]

# Setting up Discord's notification settings
Discord_Enabled = settings["Discord_Enabled"]
Webhook_URL = settings["Webhook_URL"]
Discord_ID = settings["Discord_ID"]
System_name = settings["System_name"]
System_icon = settings["System_icon"]
System_color = settings["System_color"]

IP = "(IP was unable to be fetched.)"  # This is just so that the script doesn't crash if the IP and port couldn't be fetched and can send you a notification
Port = "(Port was unable to be fetched.)"  # Same as above


# Setup Discord notifications function
def discord_notification(service_name, embed_title, embed_content, message_content, timestamp):
    # Set the different systems' Icons and colors, feel free to edit these if you want to use a different service or a different icon and color
    if service_name == "Cloudflare":
        service_pfp = "https://cdn.discordapp.com/attachments/606168640840269846/1194464350233178122/cloudflare.png"
        service_color = "15762471"
    elif service_name == "ngrok":
        service_pfp = "https://cdn.discordapp.com/attachments/606168640840269846/1194464350644211843/ngrok.png"
        service_color = "1379983"
    else:
        service_name = System_name
        service_pfp = System_icon
        service_color = System_color
    # Prepare the contents of the message
    dsdata = {"content": message_content, "username": service_name, "avatar_url": service_pfp,
              "allowed-mentions": "users", "embeds": [{

                "description": embed_content,
                "title": embed_title,
                "color": service_color,
                "timestamp": timestamp

                }]}
    # Send the message to Discord's API
    requests.post(
        f"{Webhook_URL}",
        json=dsdata)


if Discord_Enabled:  # Send "Syncing" message (if enabled)
    discord_notification(f"{System_name}", "Syncing...",
                         "The server has booted and is trying to sync the DNS records now.", "", f"{datetime.datetime.now(datetime.UTC)}")

# Check for the new IP and Port from ngrok's API
ngrok_response = requests.get("https://api.ngrok.com/tunnels",
                              headers={"Authorization": f"Bearer {ngrok_Token}", "Ngrok-Version": "2"}).json()
# Check if the request was successful, and if so, extract the IP and Port, then output a (beautified and anonymized) log for this transaction
if "tunnels" in ngrok_response:
    ngrok_data = ngrok_response["tunnels"][0]["public_url"]
    ngrok_data = ngrok_data.replace("tcp://", "")
    Port = ngrok_data[ngrok_data.find(":"):]
    Port = Port[1:]
    IP = ngrok_data.split(":", 1)[0]
    ngrok_reponse_data = json.dumps(ngrok_response, indent=2)
    ngrok_log = open(f"{root_directory}/logs/ngrok_log.txt", "w")
    ngrok_log.write(
        f'Request: GET \nDomain: https://api.ngrok.com/tunnels\nHeaders:\n{{"Authorization": "Bearer (ngrok_Token)", "Ngrok-Version": "2"}}\nResponse:\n{ngrok_reponse_data}\nIP: {IP}\nPort: {Port}\n\nSuccess!\n{datetime.datetime.now(datetime.UTC)}')
    ngrok_log.close()
elif "error_code" in ngrok_response:  # if there was no tunnel in the response, save an error report and optionally send a Discord notification
    ngrok_reponse_data = json.dumps(ngrok_response, indent=2)
    ngrok_report = open(f"{root_directory}/logs/ngrok_error_report.txt", "w")
    ngrok_report.write(f'Request: GET \nDomain: https://api.ngrok.com/tunnels\nHeaders:\n{{"Authorization": "Bearer {ngrok_Token}", "Ngrok-Version": "2"}}\nResponse:\n{ngrok_reponse_data}\nIP: {IP}\nPort: {Port}\n\nError 102, ngrok API transaction failed.\n{datetime.datetime.now(datetime.UTC)}')
    ngrok_report.close()
    if Discord_Enabled:  # Send ngrok error notification
        discord_notification("ngrok", "Error report:", f"```{ngrok_reponse_data}```",
                             f"The server has encountered an error while fetching the new record details, the full error log has been attached and logged in `{pretty_root_directory}/logs/ngrok_error_report.txt`.{Discord_ID}",
                             f"{datetime.datetime.now(datetime.UTC)}")
    print(f"Error 102 - The server has encountered an error while fetching the new record details, the full error log has been logged in {pretty_root_directory}/logs/ngrok_error_report.txt.")
    quit(102)

# If the IP or Port was (for some reason) not successfully fetched, save an error log, optionally send a Discord notification, and close
if IP == "(IP was unable to be fetched.)" or Port == "(Port was unable to be fetched.)":
    ngrok_reponse_data = json.dumps(ngrok_response, indent=2)
    ngrok_report = open(f"{root_directory}/logs/ngrok_error_report.txt", "w")
    ngrok_report.write(f'Request: GET \nDomain: https://api.ngrok.com/tunnels\nHeaders:\n{{"Authorization": "Bearer {ngrok_Token}", "Ngrok-Version": "2"}}\nResponse:\n{ngrok_reponse_data}\nIP: {IP}\nPort: {Port}\n\nError 102, ngrok API transaction failed.\n{datetime.datetime.now(datetime.UTC)}')
    ngrok_report.close()
    if Discord_Enabled:  # Send ngrok error notification
        discord_notification("ngrok", "Error report:", f"```{ngrok_reponse_data}```",
                             f"The server has encountered an error while fetching the new record details, the full error log has been attached and logged in `{pretty_root_directory}/logs/ngrok_error_report.txt`.{Discord_ID}",
                             f"{datetime.datetime.now(datetime.UTC)}")
    print(f"The server has encountered an error while fetching the new record details, the full error log has been logged in {pretty_root_directory}/logs/ngrok_error_report.txt.")
    quit(102)

# Ready all paramaters to send the updates to Cloudflare
cloudflare_connnection = http.client.HTTPSConnection("api.cloudflare.com")

cloudflare_payload = json.dumps({
    "type": "SRV",
    "ttl": 120,
    "data": {
        "service": "_minecraft",  # the service name must start with a _
        "proto": "_tcp",
        "name": Subdomain,
        "priority": 1,
        "weight": 5,
        "port": Port,
        "target": IP
    }
})

cloudflare_headers = {
    'Content-Type': "application/json",
    'Authorization': f"Bearer {Cloudflare_Token}"
}

# Send the request to Cloudflare
cloudflare_connnection.request("PATCH", f"/client/v4/zones/{Cloudflare_Zone_ID}/dns_records/{Cloudflare_Record_ID}", cloudflare_payload, cloudflare_headers)

# Process the response
cloudflare_response = cloudflare_connnection.getresponse()
cloudflare_data = cloudflare_response.read()
cloudflare_data = cloudflare_data.decode("utf-8")
cloudflare_data = json.loads(cloudflare_data)
success = cloudflare_data["success"]  # Read the "Success" response bool to figure out if there was an error or not
cloudflare_data = json.dumps(cloudflare_data, indent=2)  # Beautify the data for logs

# Check if Cloudflare accepted the changes
if success:  # If the changes were successful, log and optionally send a Discord notification, then close
    anonmyized_cloudflare_headers = {  # Make an anonymized version for logs
        'Content-Type': "application/json",
        'Authorization': "Bearer (Cloudflare_Token)"
    }
    cloudflare_request = f"PATCH \n\nDomain:\nhttps://api.cloudflare.com/client/v4/zones/{Cloudflare_Zone_ID}/dns_records/{Cloudflare_Record_ID} \n\nPayload:\n{cloudflare_payload} \n\nHeaders:\n{anonmyized_cloudflare_headers} \n"
    cloudflare_log = open(f"{root_directory}/logs/Cloudflare_log.txt", "w")
    cloudflare_log.write(f"Request: {cloudflare_request}\nResponse:\n{cloudflare_data}\n\nSuccess: {success}!\n{datetime.datetime.now(datetime.UTC)}")
    cloudflare_log.close()
    if Discord_Enabled:  # Send success notification
        discord_notification("Cloudflare", "Success!",
                             f"The DNS record change to `{IP}:{Port}` has been accepted by Cloudflare's API", "",
                             f"{datetime.datetime.now(datetime.UTC)}")
    print("Success!")
    quit(0)  # Hooray!

elif not success:  # If the changes were rejected by Cloudflare, write an error log and optionally send a Discord Notification
    cloudflare_request = f"PATCH\n\nDomain:\nhttps://api.cloudflare.com/client/v4/zones/{Cloudflare_Zone_ID}/dns_records/{Cloudflare_Record_ID}\n\nPayload:\n{cloudflare_payload}\n\nHeaders:\n{cloudflare_headers}\n"
    cloudflare_report = open(f"{root_directory}/logs/Cloudflare_error_report.txt", "w")
    cloudflare_report.write(f"Request: {cloudflare_request}\nResponse:\n{cloudflare_data}\nError 103, Cloudflare API transaction failed.\n{datetime.datetime.now(datetime.UTC)}")
    cloudflare_report.close()
    if Discord_Enabled:  # Send Cloudflare error notification
        discord_notification("Cloudflare", "Error report:",
                             f"```Request: {cloudflare_request}\nResponse:\n{cloudflare_data}\n\nSuccess: {success}```",
                             f"The server has encountered an error while submitting the changes to Cloudflare's API, the error log has been attached and logged in `{pretty_root_directory}/logs/CF_error_report.txt`.{Discord_ID}",
                             f"{datetime.datetime.now(datetime.UTC)}")
    print(f"Error 103 - The server has encountered an error while submitting the changes to Cloudflare's API, the error log has been logged in {pretty_root_directory}/logs/CF_error_report.txt.")
    quit(103)
