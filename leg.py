import subprocess
import webbrowser
import json
import requests
import urllib.parse
import urllib3
import time
import os



process_name = 'LeagueClientUx.exe'

def check_process():
    global tokens
    global output
    global riot_port
    global riot_token
    global client_port
    global client_token
    global region
    global riot_api
    global client_api
    while True:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        try:
            output = subprocess.check_output(f'tasklist /fi "imagename eq {process_name}"', shell=True).decode('iso-8859-1')
            if process_name in output:
                print(f"{process_name} process found!")
                command = 'wmic PROCESS WHERE name=\'LeagueClientUx.exe\' GET commandline'
                output = subprocess.check_output(command, shell=True).decode('utf-8')
                tokens = ["--riotclient-auth-token=", "--riotclient-app-port=", "--remoting-auth-token=", "--app-port=", "--region="]
                riot_port = None
                riot_token = None
                client_port = None
                client_token = None
                region = None

                for token in tokens:
                    value = output.split(token)[1].split()[0].strip('"')
                    print(f"{token.strip('=')} : {value}")
                    if token == "--riotclient-app-port=":
                        client_port = value
                    if token == "--riotclient-auth-token=":
                        client_token = value
                    if token == "--app-port=":
                        riot_port = value
                    if token == "--remoting-auth-token=":
                        riot_token = value
                    if token == "--region=":
                        region = value

                riot_api = f'https://riot:{riot_token}@127.0.0.1:{riot_port}'
                client_api = f'https://riot:{client_token}@127.0.0.1:{client_port}'
                time.sleep(5)
                
                lobby()
                
            else:
                print(f"{process_name} process not found. Retrying in 5 seconds...", end="\r")
        except subprocess.CalledProcessError:
            print(f"Error: {process_name} process not found. Retrying in 5 seconds...", end="\r")
        time.sleep(5)
        os.system('cls' if os.name=='nt' else 'clear')


def lobby():
    
    search_performed = False
    while True:
        global lobby_check
        global lobby_check_json
        
        lobby_check = requests.get(riot_api+'/lol-gameflow/v1/gameflow-phase', verify=False)
        lobby_check_json = json.loads(lobby_check.text)
        if lobby_check_json == 'ChampSelect':
                
                if not search_performed:
                    if client_port:
                        url = client_api + '/chat/v5/participants/champ-select/'
                        response = requests.get(url, verify=False)
                        if response.status_code == 200:
                            parsed_json = json.loads(response.text)
                            names = []
                            for participant in parsed_json["participants"]:
                                names.append(participant["name"])
                                if len(names) == 5:
                                    opgg_url = f"https://op.gg/multisearch/{region}?summoners=" + urllib.parse.quote(",".join(names))
                                    webbrowser.open(opgg_url)
                                    search_performed = True
                                    text = lobby_check.text
                                    formatted_text = f"{text:<18}"
                                    print(formatted_text.replace('"', ''), end="\r")
                                    cleared_text = formatted_text[:len(text)]  # remove the padding
                                    print(cleared_text.replace('"', ''), end="\r") 
                                    
                        else:
                            print("Error:", response.status_code)
                    else:
                        print("Error:", response.status_code)     
        else:
            text = lobby_check.text
            formatted_text = f"{text:<18}"
            print(formatted_text.replace('"', ''), end="\r")
            cleared_text = formatted_text[:len(text)]  # remove the padding
            print(cleared_text.replace('"', ''), end="\r")  
            search_performed = False
            time.sleep(5)
            output = subprocess.check_output(f'tasklist /fi "imagename eq {process_name}"', shell=True).decode('iso-8859-1')
            if process_name in output:
                lobby()
            else:
                os.system('cls' if os.name=='nt' else 'clear')
                print(f"{process_name} process not found. Retrying in 5 seconds...", end="\r")
                check_process()

check_process()