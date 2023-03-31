import subprocess
import webbrowser
import json
import requests
import urllib.parse
import urllib3
import time
import os 
from bs4 import BeautifulSoup
import ctypes

process_name = 'LeagueClientUx.exe'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ctypes.windll.kernel32.SetConsoleTitleW("opgg_multisearch")

def check_process():
    while True:
        try:
            output = subprocess.check_output(f'tasklist /fi "imagename eq {process_name}"', shell=True).decode('iso-8859-1')
            if process_name in output:
                print(f"{process_name} process found!")
                command = f'wmic PROCESS WHERE name=\'{process_name}\' GET commandline'
                output = subprocess.check_output(command, shell=True).decode('utf-8')
                tokens = ["--riotclient-auth-token=", "--riotclient-app-port=", "--remoting-auth-token=", "--app-port=", "--region="]
                riot_port, riot_token, client_port, client_token, region = [next((token[len(token):-1] for token in tokens if token in output), None) for _ in range(5)]

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

                lobby(client_port, region, riot_api, client_api)
            else:
                print(f"{process_name} process not found. Retrying...", end="\r")
        except subprocess.CalledProcessError:
            print(f"Error: {process_name} process not found. Retrying...", end="\r")
        os.system('cls' if os.name=='nt' else 'clear')

def lobby(client_port, region, riot_api, client_api):
    search_performed = False
    time.sleep(10)
    while True:
        lobby_check = requests.get(riot_api + '/lol-gameflow/v1/gameflow-phase', verify=False)
        lobby_check_json = json.loads(lobby_check.text)
        if lobby_check_json == 'ChampSelect':
            text = lobby_check.text
            formatted_text = f"{text:<18}"
            print(formatted_text.replace('"', ''), end="\r")
            cleared_text = formatted_text[:len(text)]
            print(cleared_text.replace('"', ''), end="\r")
            if not search_performed:
                if client_port:
                    url = client_api + '/chat/v5/participants/champ-select'
                    response = requests.get(url, verify=False)
                    if response.status_code == 200:
                        parsed_json = json.loads(response.text)
                        names = []
                        for participant in parsed_json["participants"]:
                            names.append(participant["name"])
                            summoner_name = names[-1]
                            opgg_get = f"https://www.op.gg/summoners/{region}/{summoner_name}"
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                                'Accept-Language': 'en-US,en;q=0.9',
                                'Accept-Encoding': 'gzip, deflate, br',
                                'Connection': 'keep-alive',
                                'Content-Type': 'application/json'
                            }
                            opgg_get_headers = headers
                            opgg_search = requests.get(opgg_get, headers=opgg_get_headers)
                            if opgg_search.status_code == 200:
                                soup = BeautifulSoup(opgg_search.content, 'html.parser')
                                script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
                                if script_tag:
                                    script_content = script_tag.string
                                    try:
                                        json_data = json.loads(script_content)
                                        summoner_id = json_data['props']['pageProps']['data']['summoner_id']
                                        opgg_post = f'https://op.gg/api/v1.0/internal/bypass/summoners/{region}/{summoner_id}/renewal'
                                        opgg_refresh = f'https://op.gg/api/v1.0/internal/bypass/summoners/{region}/{summoner_id}/summary'
                                        headers = {
                                            'Accept': 'application/json, text/plain, */*',
                                            'Accept-Encoding': 'gzip, deflate, br',
                                            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,yes;q=0.6,zh-CN;q=0.5,zh;q=0.4',
                                            'Cache-Control': 'no-cache',
                                            'Content-Length': '0',
                                            'Origin': 'https://www.op.gg',
                                            'Pragma': 'no-cache',
                                            'Referer': 'https://www.op.gg/',
                                            'Sec-Ch-Ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
                                            'Sec-Ch-Ua-Mobile': '?0',
                                            'Sec-Ch-Ua-Platform': '"Windows"',
                                            'Sec-Fetch-Dest': 'empty',
                                            'Sec-Fetch-Mode': 'cors',
                                            'Sec-Fetch-Site': 'same-site',
                                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
                                        }
                                        opgg_post_headers = headers
                                        response = requests.post(opgg_post, headers=opgg_post_headers)
                                        response = requests.get(opgg_refresh, headers=opgg_get_headers)
                                    except json.JSONDecodeError as e:
                                        print(f'Error decoding JSON: {e}')
                                    except KeyError as e:
                                        print(f'Error accessing key: {e}')
                                else:
                                    print('Script tag with id="__NEXT_DATA__" not found')
                            else:
                                print("Error:", response.status_code)
                            if len(names) == 5:
                                opgg_url = f"https://op.gg/multisearch/{region}?summoners=" + urllib.parse.quote(",".join(names))
                                webbrowser.open(opgg_url)
                                search_performed = True
                    else:
                        print("Error:", response.status_code)     
        else:
            search_performed = False
            output = subprocess.check_output(f'tasklist /fi "imagename eq {process_name}"', shell=True).decode('iso-8859-1')
            if process_name in output:
                text = lobby_check.text
                formatted_text = f"{text:<18}"
                print(formatted_text.replace('"', ''), end="\r")
                cleared_text = formatted_text[:len(text)]
                print(cleared_text.replace('"', ''), end="\r")
            else:
                os.system('cls' if os.name=='nt' else 'clear')
                print(f"{process_name} process not found. Retrying...", end="\r")
                check_process()

check_process()
