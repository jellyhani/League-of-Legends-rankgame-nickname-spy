from datetime import datetime
import json
import subprocess
import time
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QUrl, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QApplication, QMessageBox, QPushButton
from bs4 import BeautifulSoup

import pyperclip
import requests
import urllib3
import urllib

process_name = 'LeagueClientUx.exe'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json'
}
opgg_get_headers = headers
headers2 = {
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
opgg_post_headers = headers2


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
last_printed_time = 0
messages_exist = False
search_performed = False

class AutoReadyThread(QThread):
    autoready = pyqtSignal(bool, str, str, str, str, str, str)
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
    def run(self):
        client_api, client_token, riot_api, riot_port, riot_token, client_port, region = self.main_window.check_process_status()
        self.client_api = client_api
        self.client_token = client_token
        self.riot_api = riot_api
        self.riot_port = riot_port
        self.riot_token = riot_token
        self.client_port = client_port
        self.region = region
        
        while True:
            Status_url = requests.get(riot_api + '/lol-gameflow/v1/gameflow-phase', verify=False)
            Status_url_response = json.loads(Status_url.text)
            Status = Status_url_response
            if Status == "ReadyCheck":
                requests.post(riot_api + '/lol-matchmaking/v1/ready-check/accept', verify=False)
                QThread.msleep(100)

class DodgeThread(QThread):
    dodge_signal = pyqtSignal()
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
    def run(self):
        client_api, client_token, riot_api, riot_port, riot_token, client_port, region = self.main_window.check_process_status()
        self.client_api = client_api
        self.client_token = client_token
        self.riot_api = riot_api
        self.riot_port = riot_port
        self.riot_token = riot_token
        self.client_port = client_port
        self.region = region

        self.power = True
        zero_dodge = True
        lobby_check = requests.get(riot_api + '/lol-gameflow/v1/gameflow-phase', verify=False)
        lobby_check_json = json.loads(lobby_check.text)

        while self.power and lobby_check_json == 'ChampSelect':
            check = requests.get(riot_api + '/lol-champ-select/v1/session', verify=False)
            check_json = json.loads(check.text)
            phase = check_json['timer']['phase']
            
            if phase == 'FINALIZATION' and zero_dodge:
                QApplication.processEvents()
                self.checker = self.riot_api + "/lol-champ-select/v1/session/my-selection"
                response = requests.get(self.checker, verify=False).json()
                self.spell_1Id = response.get("spell1Id")
                self.spell_2Id = response.get("spell2Id")
                print(self.spell_1Id, self.spell_2Id)
                recovery_spell  = {
                    "spell1Id": self.spell_2Id,
                    "spell2Id": self.spell_1Id
                }
                response = requests.patch(self.checker, json=recovery_spell, verify=False)
                r = requests.get(riot_api + '/lol-champ-select/v1/session', verify=False)
                jsondata = json.loads(r.text)
                remaining_time_ms = jsondata["timer"]["adjustedTimeLeftInPhase"]
                remaining_time_ms -= 400
                print(remaining_time_ms)
                QThread.msleep(remaining_time_ms)
                dodge = riot_api + '/lol-login/v1/session/invoke?destination=lcdsServiceProxy&method=call&args=[\"\",\"teambuilder-draft\",\"quitV2\",\"\"]'
                body = "[\"\",\"teambuilder-draft\",\"quitV2\",\"\"]"
                response = requests.post(dodge, data=body, verify=False)
                print(response.text)
                zero_dodge = False
                self.power = False
                break
            else:
                if lobby_check_json != 'ChampSelect':
                    self.power = True
                    break
                pass
        self.quit()
    def stop(self):
        self.power = False
        self.quit()


class Ui_League_Multisearch(QtWidgets.QDialog):
    def setupUi(self, League_Multisearch):        
        #proc search
        self.process_name = "LeagueClientUx.exe"
        self.riot_api = ""
        self.client_api = ""
        self.client_token = ""
        self.client_port = ""
        self.riot_token = ""
        self.riot_port = ""
        self.region = ""

        self.autoreadythread = AutoReadyThread(self)
        self.dodgethread = DodgeThread(self)

        #proc search
        self.proc_search = QTimer()
        self.proc_search.setInterval(1000)
        self.proc_search.timeout.connect(self.check_process_status)
        self.proc_search.start(5000)

        #status
        self.statusTimer = QTimer(self)
        self.statusTimer.setInterval(1000)
        self.statusTimer.timeout.connect(self.update_status)
        self.statusTimer.start(1000)

        
        League_Multisearch.setObjectName("League_Multisearch")
        League_Multisearch.resize(506, 452)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(League_Multisearch.sizePolicy().hasHeightForWidth())
        League_Multisearch.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(League_Multisearch)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtWidgets.QGroupBox(League_Multisearch)
        self.groupBox.setMinimumSize(QtCore.QSize(0, 50))
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.Nickname_label = QtWidgets.QLabel(self.groupBox)
        self.Nickname_label.setText("")
        self.Nickname_label.setObjectName("Nickname_label")
        self.verticalLayout_2.addWidget(self.Nickname_label)
        self.gridLayout_2.addLayout(self.verticalLayout_2, 0, 0, 1, 1)
        self.verticalLayout.addWidget(self.groupBox)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.scrollArea = QtWidgets.QScrollArea(League_Multisearch)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 484, 275))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.gridLayout_3.addLayout(self.verticalLayout_3, 0, 0, 1, 1)
        # self.verticalLayout_3.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignLeft)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.gridLayout.addWidget(self.scrollArea, 0, 0, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.verticalLayout_5 = QtWidgets.QVBoxLayout()
        self.verticalLayout_5.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.status = QtWidgets.QLabel(League_Multisearch)
        self.status.setText("Status:")
        self.status.setObjectName("status")

        self.verticalLayout_4.addWidget(self.status)
        self.OPGG_check = QtWidgets.QCheckBox(League_Multisearch)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.OPGG_check.sizePolicy().hasHeightForWidth())
        self.OPGG_check.setSizePolicy(sizePolicy)
        self.OPGG_check.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.OPGG_check.setInputMethodHints(QtCore.Qt.ImhNoAutoUppercase)
        self.OPGG_check.setChecked(True)
        self.OPGG_check.setObjectName("OPGG_check")
        self.verticalLayout_4.addWidget(self.OPGG_check)
        self.DeepLOL_check = QtWidgets.QCheckBox(League_Multisearch)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.DeepLOL_check.sizePolicy().hasHeightForWidth())
        self.DeepLOL_check.setSizePolicy(sizePolicy)
        self.DeepLOL_check.setObjectName("DeepLOL_check")
        self.verticalLayout_4.addWidget(self.DeepLOL_check)
        self.verticalLayout_5.addLayout(self.verticalLayout_4)
        self.Fow_check = QtWidgets.QCheckBox(League_Multisearch)
        self.Fow_check.setObjectName("Fow_check")
        self.verticalLayout_4.addWidget(self.Fow_check)
        self.label_4 = QtWidgets.QLabel(League_Multisearch)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setText("")
        self.label_4.setObjectName("label_4")
        
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.verticalLayout.addLayout(self.verticalLayout_5)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.Now_version_label = QtWidgets.QLabel(League_Multisearch)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Now_version_label.sizePolicy().hasHeightForWidth())
        self.Now_version_label.setSizePolicy(sizePolicy)
        self.Now_version_label.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.Now_version_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.Now_version_label.setOpenExternalLinks(False)
        self.Now_version_label.setObjectName("Now_version_label")
        self.horizontalLayout_2.addWidget(self.Now_version_label)

        self.Update_version_label = QtWidgets.QLabel(League_Multisearch)
        self.Update_version_label.setText("")
        self.Update_version_label.setObjectName("Update_version_label")
        
        self.horizontalLayout_2.addWidget(self.Update_version_label)
        self.Restart = QtWidgets.QPushButton(League_Multisearch)
        self.Restart.setObjectName("Restart")
        self.horizontalLayout_2.addWidget(self.Restart)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.Dodge = QtWidgets.QPushButton(League_Multisearch)
        self.Dodge.setObjectName("Dodge")
        self.horizontalLayout_2.addWidget(self.Dodge)
        self.Github_btn = QtWidgets.QPushButton(League_Multisearch)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Github_btn.sizePolicy().hasHeightForWidth())
        self.Github_btn.setSizePolicy(sizePolicy)
        self.Github_btn.setObjectName("Github_btn")
        self.horizontalLayout_2.addWidget(self.Github_btn)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.Auto_Ready = QtWidgets.QCheckBox(League_Multisearch)
        self.Auto_Ready.setObjectName("Auto_Ready")
        self.verticalLayout_4.addWidget(self.Auto_Ready)
        self.dodge_check = QtWidgets.QCheckBox(League_Multisearch)
        self.dodge_check.setObjectName("dodge_check")
        self.verticalLayout_4.addWidget(self.dodge_check)

        self.Messages_textedit = QtWidgets.QTextEdit(self.scrollAreaWidgetContents)
        self.Messages_textedit.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Messages_textedit.sizePolicy().hasHeightForWidth())
        self.Messages_textedit.setSizePolicy(sizePolicy)
        self.Messages_textedit.setBaseSize(QtCore.QSize(0, 0))
        self.Messages_textedit.setMidLineWidth(-1)
        self.Messages_textedit.setReadOnly(True)
        self.Messages_textedit.setObjectName("Messages_textedit")
        self.verticalLayout_3.addWidget(self.Messages_textedit)
        
        self.Auto_Ready.stateChanged.connect(self.Auto_Ready_Changed)

        self.checkboxes = {
            "DeepLOL_check": self.DeepLOL_check,
            "OPGG_check": self.OPGG_check,
            "Fow_check": self.Fow_check
        }
        self.retranslateUi(League_Multisearch)
        QtCore.QMetaObject.connectSlotsByName(League_Multisearch)


        


        
    def Auto_Ready_Changed(self):
        output = subprocess.check_output(f'tasklist /fi "imagename eq {process_name}"', shell=True).decode('iso-8859-1')
        if process_name in output and self.Auto_Ready.isChecked():
            self.autoreadythread.autoready.connect(self.autoreadythread.start)
            self.autoreadythread.start()
        else:
            self.autoreadythread.quit()
            self.autoreadythread.terminate()



    def retranslateUi(self, League_Multisearch):
        _translate = QtCore.QCoreApplication.translate
        League_Multisearch.setWindowTitle(_translate("League_Multisearch", "League_Multisearch"))
        self.groupBox.setTitle(_translate("League_Multisearch", "NickName"))
        self.Auto_Ready.setText(_translate("League_Multisearch", "Auto Ready"))
        self.OPGG_check.setText(_translate("League_Multisearch", "OP.GG"))
        self.DeepLOL_check.setText(_translate("League_Multisearch", "DeepLOL"))
        self.Fow_check.setText(_translate("League_Multisearch", "Fow"))
        update_url = "https://raw.githubusercontent.com/jellyhani/League-of-Legends-rankgame-nickname-spy/main/version.txt"
        update_url_response = requests.get(update_url)
        update_version_number = update_url_response.text.strip()
        self.dodge_check.setText(_translate("League_Multisearch", "0s dodge"))
        self.Now_version_label.setText(_translate("League_Multisearch", "현재버전 : 2.0  | 최신버전 : " + format(update_version_number)))
        self.Github_btn.setText(_translate("League_Multisearch", "Github"))
        self.Restart.setText(_translate("League_Multisearch", "Restart"))
        self.Dodge.setText(_translate("League_Multisearch", "Dodge"))
        self.Restart.clicked.connect(self.Restart_action)
        self.Github_btn.clicked.connect(self.open_github)
        self.Dodge.clicked.connect(self.dodge)

    def Restart_action(self):
        client_api, client_token, riot_api, riot_port, riot_token, client_port, region = self.check_process_status()
        self.client_api = client_api
        self.client_token = client_token
        self.riot_api = riot_api
        self.riot_port = riot_port
        self.riot_token = riot_token
        self.client_port = client_port
        self.region = region

        output = subprocess.check_output(f'tasklist /fi "imagename eq {process_name}"', shell=True).decode('iso-8859-1')
        if process_name in output:
            requests.post(riot_api + '/riotclient/kill-and-restart-ux', verify=False)
        else:
            QMessageBox.about(self,'error','Client not found')

    def dodge(self):
        client_api, client_token, riot_api, riot_port, riot_token, client_port, region = self.check_process_status()
        self.client_api = client_api
        self.client_token = client_token
        self.riot_api = riot_api
        self.riot_port = riot_port
        self.riot_token = riot_token
        self.client_port = client_port
        self.region = region

        lobby_check = requests.get(riot_api + '/lol-gameflow/v1/gameflow-phase', verify=False)
        lobby_check_json = json.loads(lobby_check.text)

        
        output = subprocess.check_output(f'tasklist /fi "imagename eq {process_name}"', shell=True).decode('iso-8859-1')
        if process_name in output and lobby_check_json == 'ChampSelect':
            if self.dodge_check.isChecked():
                self.dodgethread.dodge_signal.connect(self.dodgethread.run)
                self.dodgethread.start()
                QMessageBox.about(self,'0s dodge','게임시작 0.3초 전 닷지를 진행합니다.')
            else:
                self.dodgethread.stop()
                self.dodgethread.quit()
                print("not zero-dodge checked")
                dodge = riot_api + '/lol-login/v1/session/invoke?destination=lcdsServiceProxy&method=call&args=[\"\",\"teambuilder-draft\",\"quitV2\",\"\"]'
                body = "[\"\",\"teambuilder-draft\",\"quitV2\",\"\"]"
                response = requests.post(dodge, data=body, verify=False)
                print(response)     
        else:
            print("not found " + process_name + " or ChampSelect")
            pass

    def open_github(self):
        url = QUrl("https://github.com/jellyhani/League-of-Legends-rankgame-nickname-spy")
        QDesktopServices.openUrl(url)

    def check_process_status(self):
        try:
            # check if process is running
            output = subprocess.check_output(f'tasklist /fi "imagename eq {self.process_name}"', shell=True).decode('iso-8859-1')
            if self.process_name in output:
                command = f'wmic PROCESS WHERE name=\'{self.process_name}\' GET commandline'
                output = subprocess.check_output(command, shell=True).decode('iso-8859-1')
                tokens = ["--riotclient-auth-token=", "--riotclient-app-port=", "--remoting-auth-token=", "--app-port=", "--region="]
                for token in tokens:
                    value = output.split(token)[1].split()[0].strip('"')
                    if token == "--riotclient-app-port=":
                        self.client_port = value
                    if token == "--riotclient-auth-token=":
                        self.client_token = value
                    if token == "--app-port=":
                        self.riot_port = value
                    if token == "--remoting-auth-token=":
                        self.riot_token = value
                    if token == "--region=":
                        self.region = "oce" if value.lower() == "oc1" else value
                self.riot_api = f'https://riot:{self.riot_token}@127.0.0.1:{self.riot_port}'
                self.client_api = f'https://riot:{self.client_token}@127.0.0.1:{self.client_port}'
                
            else:
                self.riot_api = ""
                self.client_api = ""
                self.client_token = ""
                self.client_port = ""
                self.riot_token = ""
                self.riot_port = ""
                self.region = ""
        except Exception as e:
            print(f"Error: {e}")
            self.riot_api = ""
            self.client_api = ""
            self.client_token = ""
            self.client_port = ""
            self.riot_token = ""
            self.riot_port = ""
            self.region = ""

        return self.client_api, self.client_token, self.riot_api, self.riot_port, self. riot_token, self.client_port,self.region
    
    def update_status(self):
            global last_printed_time, messages_exist, search_performed
            
            client_api, client_token, riot_api, riot_port, riot_token, client_port, region = self.check_process_status()
            self.client_api = client_api
            self.client_token = client_token
            self.riot_api = riot_api
            self.riot_port = riot_port
            self.riot_token = riot_token
            self.client_port = client_port
            self.region = region

            summoner_name = ""
            output = subprocess.check_output(f'tasklist /fi "imagename eq {process_name}"', shell=True).decode('iso-8859-1')
            if process_name in output:
                try:
                    chatlog_url = client_api + '/chat/v5/messages/champ-select'
                    chatlog_response = requests.get(chatlog_url, verify=False)
                    chatlog = json.loads(chatlog_response.text)

                    Status_url = requests.get(riot_api + '/lol-gameflow/v1/gameflow-phase', verify=False)
                    Status_url_response = json.loads(Status_url.text)
                    Status = Status_url_response
                    self.status.setText(f"Status: {Status}")

                    if Status == 'ChampSelect':
                        
                        chatlog_url = client_api + '/chat/v5/messages/champ-select'
                        chatlog_response = requests.get(chatlog_url, verify=False)
                        chatlog = json.loads(chatlog_response.text)
                        
                        try:
                            if chatlog["messages"]:
                                messages_exist = True
                                for message in chatlog["messages"]:
                                    timestamp = int(message["time"])
                                    if timestamp > last_printed_time:
                                        last_printed_time = timestamp
                                        body = message["body"]
                                        name = message["name"]
                                        current_time = datetime.now().strftime("%H:%M:%S")
                                        self.Messages_textedit.append(f"[{current_time}] {name} : {body}")
                            else:
                                messages_exist = False
                                self.Messages_textedit.clear()
                        except KeyError:
                            messages_exist = False
                            self.Messages_textedit.clear()

                        url = client_api + '/chat/v5/participants/champ-select'
                        response = requests.get(url, verify=False)
                        parsed_json = json.loads(response.text)
                        names = []
                        for participant in parsed_json["participants"]:
                            names.append(participant["name"])
                        if len(names) >= 1:
                            self.Nickname_label.setText(", ".join(names))
                        else:
                            self.Nickname_label.setText("")
                        if not search_performed:
                            for checkbox_name, checkbox in self.checkboxes.items():
                                if checkbox.isChecked():
                                    if checkbox_name == "DeepLOL_check":
                                        if len(names) == 5:
                                            deeplol_url = QUrl(f"https://www.deeplol.gg/multi/{region}/" + urllib.parse.quote(",".join(names)))
                                            QDesktopServices.openUrl(deeplol_url)
                                            search_performed = True
                                    elif checkbox_name == "OPGG_check":
                                        for i in range(len(names)):
                                            summoner_name = names[i]
                                            opgg_get = f"https://www.op.gg/summoners/{region}/{summoner_name}"
                                            opgg_get = opgg_get.replace(f"{summoner_name}", summoner_name, i)
                                            opgg_search = requests.get(opgg_get, headers=opgg_get_headers)
                                            soup = BeautifulSoup(opgg_search.content, 'html.parser')
                                            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
                                            if script_tag:
                                                script_content = script_tag.string
                                                try:
                                                    json_data = json.loads(script_content)
                                                    summoner_id = json_data['props']['pageProps']['data']['summoner_id']
                                                    opgg_post = f'https://op.gg/api/v1.0/internal/bypass/summoners/{region}/{summoner_id}/renewal'
                                                    opgg_refresh = f'https://op.gg/api/v1.0/internal/bypass/summoners/{region}/{summoner_id}/summary'
                                                    response = requests.post(opgg_post, headers=opgg_post_headers)
                                                    response = requests.get(opgg_refresh, headers=opgg_get_headers)
                                                except json.JSONDecodeError as e:
                                                    print(f'Error decoding JSON: {e}')
                                                except KeyError as e:
                                                    print(f'Error accessing key: {e}')
                                            else:
                                                print('Script tag with id="__NEXT_DATA__" not found')
                                        if len(names) == 5:
                                            opgg_url = QUrl(f"https://op.gg/multisearch/{region}?summoners=" + urllib.parse.quote(",".join(names)))
                                            QDesktopServices.openUrl(opgg_url)
                                            search_performed = True
                                    elif checkbox_name == "Fow_check":
                                        if len(names) == 5:
                                            Fow_url = QUrl(f"https://fow.kr/multi#"+ urllib.parse.quote(",".join(names)))
                                            QDesktopServices.openUrl(Fow_url)
                                            search_performed = True
                    
                    else:
                        self.Nickname_label.setText("")
                        messages_exist = False
                        self.Messages_textedit.clear()
                        search_performed = False
                        
                except Exception as e:
                    print(f"Error: {e}")
                    self.status.setText(f"Status: {e}")
                    error_message = str(e)
                    pyperclip.copy(error_message)
                    self.Nickname_label.setText("")
                    messages_exist = False
                    search_performed = False
                    self.Messages_textedit.clear()
                
            else:
                self.status.setText("Status: Not Connected")
                self.Nickname_label.setText("")
                messages_exist = False
                search_performed = False
                self.Messages_textedit.clear()
        

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_League_Multisearch()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())
