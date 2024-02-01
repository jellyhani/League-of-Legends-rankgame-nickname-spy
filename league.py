from datetime import datetime, timezone
import json
import subprocess
import sys
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QProcess, QUrl, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QApplication, QBoxLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget
from bs4 import BeautifulSoup

import firebase_admin
from firebase_admin import credentials, db
import uuid
import os

import pyperclip
import requests
import urllib3
import urllib

#pyinstaller --onefile --add-binary "lol-rankspy.json;data/" league.py


process_name = 'LeagueClientUx.exe'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
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


def initialize_firebase():
    try:
        firebase_admin.get_app()
    except ValueError:
        # Determine the path to the bundled firebase_key.json
        

def get_uuid():
    file_path = os.path.join(os.path.expanduser("~"), "Documents", "rankspy", "uuid.json")
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return data.get("uuid")
    except FileNotFoundError:
        return None

def set_uuid(uuid_value):
    file_path = os.path.join(os.path.expanduser("~"), "Documents", "rankspy", "uuid.json")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as file:
        json.dump({"uuid": uuid_value}, file)

def generate_user_id():
    existing_uuid = get_uuid()
    if existing_uuid:
        return existing_uuid
    else:
        new_uuid = str(uuid.uuid4())
        set_uuid(new_uuid)
        return new_uuid
    

class AutoReadyThread(QThread):
    autoready = pyqtSignal(bool, str, str, str, str, str)
    def __init__(self, main_window, proc_search_thread, delay_spinbox):
        super().__init__()
        self.main_window = main_window
        self.proc_search_thread = proc_search_thread
        self.proc_search_thread.process_info_updated.connect(self.process_info_updated)
        self.delay_spinbox = delay_spinbox
    def run(self):
        while True:
            QThread.msleep(100)
            output = subprocess.check_output(f'tasklist /fi "imagename eq {process_name}"', shell=False).decode('iso-8859-1')
            if process_name in output:
                try:
                    Status_url = requests.get(self.riot_api + '/lol-gameflow/v1/gameflow-phase', verify=False)
                    Status_url_response = json.loads(Status_url.text)
                    Status = Status_url_response
                    QThread.msleep(100)
                    if Status == "ReadyCheck":
                        delay_seconds = self.delay_spinbox.value()
                        QThread.msleep(delay_seconds * 1000)
                        requests.post(self.riot_api + '/lol-matchmaking/v1/ready-check/accept', verify=False)
                        QThread.msleep(100)
                except Exception as e:
                    print(f"Error: {e}")
                    error_message = str(e)
                    pyperclip.copy(error_message)
                except requests.exceptions.RequestException as e:
                    print(f"An error occurred during the request: {e}")
                    error_message = str(e)
                    pyperclip.copy(error_message)
            else:
                self.quit()
    def process_info_updated(self, client_api, client_token, riot_api, riot_port, riot_token, client_port):
        self.client_api = client_api
        self.client_token = client_token
        self.riot_api = riot_api
        self.riot_port = riot_port
        self.riot_token = riot_token
        self.client_port = client_port
        
class DodgeThread(QThread):
    dodge_signal = pyqtSignal()
    process_info_updated = pyqtSignal(str, str, str, str, str, str)
    def __init__(self, main_window, proc_search_thread, delay_spinbox):
        super().__init__()
        self.main_window = main_window
        self.proc_search_thread = proc_search_thread
        self.proc_search_thread.process_info_updated.connect(self.process_info_updated)
        self.delay_spinbox = delay_spinbox
    def run(self):
        self.power = True
        zero_dodge = True
        lobby_check = requests.get(self.riot_api + '/lol-gameflow/v1/gameflow-phase', verify=False)
        lobby_check_json = json.loads(lobby_check.text)
        QThread.msleep(100)

        while self.power and lobby_check_json == 'ChampSelect':
            check = requests.get(self.riot_api + '/lol-champ-select/v1/session', verify=False)
            check_json = json.loads(check.text)
            phase = check_json['timer']['phase']
            QThread.msleep(100)
            delay_seconds = self.delay_spinbox.value()
            
            if phase == 'FINALIZATION' and zero_dodge:
                QApplication.processEvents()
                self.checker = self.riot_api + "/lol-champ-select/v1/session/my-selection"
                response = requests.get(self.checker, verify=False).json()
                self.spell_1Id = response.get("spell1Id")
                self.spell_2Id = response.get("spell2Id")
                recovery_spell  = {
                    "spell1Id": self.spell_2Id,
                    "spell2Id": self.spell_1Id
                }
                response = requests.patch(self.checker, json=recovery_spell, verify=False)
                r = requests.get(self.riot_api + '/lol-champ-select/v1/session', verify=False)
                jsondata = json.loads(r.text)
                remaining_time_ms = jsondata["timer"]["adjustedTimeLeftInPhase"]
                remaining_time_ms -= delay_seconds
                #print(remaining_time_ms)
                QThread.msleep(remaining_time_ms)
                dodge = self.riot_api + '/lol-login/v1/session/invoke?destination=lcdsServiceProxy&method=call&args=[\"\",\"teambuilder-draft\",\"quitV2\",\"\"]'
                body = "[\"\",\"teambuilder-draft\",\"quitV2\",\"\"]"
                response = requests.post(dodge, data=body, verify=False)
                #print(response.text)
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
    def process_info_updated(self, client_api, client_token, riot_api, riot_port, riot_token, client_port):
        self.client_api = client_api
        self.client_token = client_token
        self.riot_api = riot_api
        self.riot_port = riot_port
        self.riot_token = riot_token
        self.client_port = client_port

class proc_searchThread(QThread):
    process_info_updated = pyqtSignal(str, str, str, str, str, str)
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.client_api = ""
        self.client_token = ""
        self.riot_api = ""
        self.riot_port = ""
        self.riot_token = ""
        self.client_port = ""
        self.process_name = 'LeagueClientUx.exe'

    def run(self):
        while True:
            QThread.msleep(100)
            
            try:
                tasklist_command = ['tasklist', '/fi', f'imagename eq {self.process_name}']
                tasklist_output = subprocess.check_output(tasklist_command, shell=False).decode('iso-8859-1')
                if self.process_name in tasklist_output:
                    wmic_command = ['wmic', 'PROCESS', 'WHERE', f'name=\'{self.process_name}\'', 'GET', 'commandline']
                    output = subprocess.check_output(wmic_command, shell=False).decode('iso-8859-1')
                    tokens = ["--riotclient-auth-token=", "--riotclient-app-port=", "--remoting-auth-token=", "--app-port="]
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
                    self.riot_api = f'https://riot:{self.riot_token}@127.0.0.1:{self.riot_port}'
                    self.client_api = f'https://riot:{self.client_token}@127.0.0.1:{self.client_port}'
                    self.process_info_updated.emit(
                        self.client_api, self.client_token,
                        self.riot_api, self.riot_port,
                        self.riot_token, self.client_port,
                    )

                    QThread.sleep(5)
                else:
                    self.riot_api = ""
                    self.client_api = ""
                    self.client_token = ""
                    self.client_port = ""
                    self.riot_token = ""
                    self.riot_port = ""
                    self.process_info_updated.emit("", "", "", "", "", "")
            except Exception as e:
                self.riot_api = ""
                self.client_api = ""
                self.client_token = ""
                self.client_port = ""
                self.riot_token = ""
                self.riot_port = ""
                self.process_info_updated.emit("", "", "", "", "", "")

class statusThread(QThread):
    status_updated = pyqtSignal(str)
    process_info_updated = pyqtSignal(str, str, str, str, str, str)
    def __init__(self, main_window, proc_search_thread):
        super(statusThread, self).__init__()
        self.main_window = main_window
        self.proc_search_thread = proc_search_thread
        self.proc_search_thread.process_info_updated.connect(self.process_info_updated)
        self.riot_api = ""
        self.process_name = 'LeagueClientUx.exe'
        
    def process_info_updated(self, client_api, client_token, riot_api, riot_port, riot_token, client_port):
        self.client_api = client_api
        self.client_token = client_token
        self.riot_api = riot_api
        self.riot_port = riot_port
        self.riot_token = riot_token
        self.client_port = client_port
    def run(self):
        while True:
            QThread.msleep(100)
            output = subprocess.check_output(f'tasklist /fi "imagename eq {self.process_name}"', shell=False).decode('iso-8859-1')
            if self.process_name in output:
                try:
                    if self.riot_api:
                        Status_url = requests.get(self.riot_api + '/lol-gameflow/v1/gameflow-phase', verify=False)
                        Status_url.raise_for_status()  # 이 부분을 추가하여 HTTP 오류가 발생하면 예외를 발생시킵니다.
                        Status_url_response = json.loads(Status_url.text)
                        Status = Status_url_response
                        self.status_updated.emit(Status)
                        QThread.msleep(100)
                except Exception as e:
                    print(f"Error: {e}")
                    self.status_updated.emit(f"Status: {e}")
                    error_message = str(e)
                    pyperclip.copy(error_message)
                except requests.exceptions.HTTPError as http_err:
                    print(f"HTTP 에러: {http_err}")
                    self.status_updated.emit(f"HTTP 상태: {http_err}")
                    error_message = str(http_err)
                    pyperclip.copy(error_message)
                except requests.exceptions.RequestException as e:
                    print(f"An error occurred during the request: {e}")
                    self.status_updated.emit(f"Status: {e}")
                    error_message = str(e)
                    pyperclip.copy(error_message)
            else:
                    self.status_updated.emit("Not Connected")
            QThread.msleep(100)



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


        self.region_mapping = {
            'BR1': 'br',
            'EUN1': 'eune',
            'EUW1': 'euw',
            'JP1': 'jp',
            'KR': 'kr',
            'LA1': 'las',
            'LA2': 'lan',
            'NA1': 'na',
            'OC1': 'oce',
            'TR1': 'tr',
            'RU': 'ru',
            'PH2': 'ph',
            'SG2': 'sg',
            'TH2': 'th',
            'TW2': 'tw',
            'VN2': 'vn'
        }

        #status
        self.statusTimer = QTimer(self)
        self.statusTimer.setInterval(1000)
        self.statusTimer.timeout.connect(self.update_status)
        self.statusTimer.start()
        
        League_Multisearch.setObjectName("League_Multisearch")
        League_Multisearch.setFixedSize(506, 452)
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
        self.Labs = QtWidgets.QPushButton(League_Multisearch)
        self.Labs.setObjectName("Labs")
        self.horizontalLayout_2.addWidget(self.Labs)
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

        self.horizontal_layout_within_vertical = QtWidgets.QHBoxLayout()
        self.verticalLayout_4.addLayout(self.horizontal_layout_within_vertical)

        self.Auto_Ready = QtWidgets.QCheckBox(League_Multisearch)
        self.Auto_Ready.setObjectName("Auto_Ready")
        self.horizontal_layout_within_vertical.addWidget(self.Auto_Ready)

        self.ready_spinbox = QtWidgets.QSpinBox(League_Multisearch)
        self.ready_spinbox.setMaximum(99999)
        self.ready_spinbox.setValue(0)
        self.horizontal_layout_within_vertical.addWidget(self.ready_spinbox)

        self.empty_label = QtWidgets.QLabel(League_Multisearch)
        self.empty_label.setText("")
        self.empty_label.setObjectName("empty_label")
        self.empty_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.horizontal_layout_within_vertical.addWidget(self.empty_label)

        self.dodge_layout_within_vertical = QtWidgets.QHBoxLayout()
        self.verticalLayout_4.addLayout(self.dodge_layout_within_vertical)

        self.dodge_check = QtWidgets.QCheckBox(League_Multisearch)
        self.dodge_check.setObjectName("dodge_check")
        self.dodge_layout_within_vertical.addWidget(self.dodge_check)

        self.dodge_spinbox = QtWidgets.QSpinBox(League_Multisearch)
        self.dodge_spinbox.setMaximum(99999)
        self.dodge_spinbox.setValue(300)
        self.dodge_layout_within_vertical.addWidget(self.dodge_spinbox)

        self.empty_label = QtWidgets.QLabel(League_Multisearch)
        self.empty_label.setText("")
        self.empty_label.setObjectName("empty_label")
        self.empty_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.dodge_layout_within_vertical.addWidget(self.empty_label)

        #self.aram = QtWidgets.QLabel(self)
        #self.aram.setText("")
        #self.aram.setObjectName("aramrerollPoints")

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

        self.proc_searchThread = proc_searchThread(self)
        self.proc_search_thread = proc_searchThread(self)
        
        self.proc_search_thread.process_info_updated.connect(self.update_process_info)
        self.proc_search_thread.start()
        self.autoreadythread = AutoReadyThread(self, self.proc_search_thread, self.ready_spinbox)
        self.dodgethread = DodgeThread(self, self.proc_search_thread, self.dodge_spinbox)

        self.Auto_Ready.stateChanged.connect(self.Auto_Ready_Changed)
        self.status_thread = statusThread(self, self.proc_search_thread)
        self.status_thread.status_updated.connect(self.update_status_label)
        self.status_thread.start()

        

        self.checkboxes = {
            "DeepLOL_check": self.DeepLOL_check,
            "OPGG_check": self.OPGG_check,
            "Fow_check": self.Fow_check
        }
        
        self.retranslateUi(League_Multisearch)
        QtCore.QMetaObject.connectSlotsByName(League_Multisearch)


    def update_status_label(self, status):
        self.status.setText(f"Status: {status}")

    def update_process_info(self, client_api, client_token, riot_api, riot_port, riot_token, client_port):
        self.client_api = client_api
        self.client_token = client_token
        self.riot_api = riot_api
        self.riot_port = riot_port
        self.riot_token = riot_token
        self.client_port = client_port

    def Auto_Ready_Changed(self):
        output = subprocess.check_output(f'tasklist /fi "imagename eq {process_name}"', shell=False).decode('iso-8859-1')
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
        self.Now_version_label.setText(_translate("League_Multisearch", "현재버전 : 2.7  | 최신버전 : " + format(update_version_number)))
        self.Github_btn.setText(_translate("League_Multisearch", "Github"))
        self.Labs.setText(_translate("League_Multisearch", "Labs"))
        self.Dodge.setText(_translate("League_Multisearch", "Dodge"))
        self.Labs.clicked.connect(self.Labs_action)
        self.Github_btn.clicked.connect(self.open_github)
        self.Dodge.clicked.connect(self.dodge)

    def Labs_action(self):
        output = subprocess.check_output(f'tasklist /fi "imagename eq {process_name}"', shell=False).decode('iso-8859-1')
        if process_name in output:
            self.new_window = SubWindow(self.riot_api, self.client_api)
            self.new_window.show()
        else:
            QMessageBox.about(self,'error','Client not found')


    def dodge(self):
        lobby_check = requests.get(self.riot_api + '/lol-gameflow/v1/gameflow-phase', verify=False)
        lobby_check_json = json.loads(lobby_check.text)

        output = subprocess.check_output(f'tasklist /fi "imagename eq {process_name}"', shell=False).decode('iso-8859-1')
        if process_name in output and lobby_check_json == 'ChampSelect':
            if self.dodge_check.isChecked():
                self.dodgethread.dodge_signal.connect(self.dodgethread.run)
                self.dodgethread.start()
                QMessageBox.about(self,'0s dodge','게임시작 전 닷지를 진행합니다.')
            else:
                self.dodgethread.stop()
                self.dodgethread.quit()
                #print("not zero-dodge checked")
                dodge = self.riot_api + '/lol-login/v1/session/invoke?destination=lcdsServiceProxy&method=call&args=[\"\",\"teambuilder-draft\",\"quitV2\",\"\"]'
                body = "[\"\",\"teambuilder-draft\",\"quitV2\",\"\"]"
                response = requests.post(dodge, data=body, verify=False)
                #print(response)     
        else:
            print("not found " + process_name + " or ChampSelect")
            pass

    def open_github(self):
        url = QUrl("https://github.com/jellyhani/League-of-Legends-rankgame-nickname-spy")
        QDesktopServices.openUrl(url)

    def update_status(self):
            global last_printed_time, messages_exist, search_performed
            
            summoner_name = ""
            output = subprocess.check_output(f'tasklist /fi "imagename eq {process_name}"', shell=False).decode('iso-8859-1')
            if process_name in output:
                try:
                    
                    Status_url = requests.get(self.riot_api + '/lol-gameflow/v1/gameflow-phase', verify=False)
                    Status_url_response = json.loads(Status_url.text)
                    Status = Status_url_response

                    regionurl = requests.get(f'{self.riot_api}/lol-rso-auth/v1/authorization', verify=False)
                    region_data = regionurl.json()
                    region = region_data["currentPlatformId"]

                    converted_region = self.convert_region_from_http(region)
                    
                    if Status == 'ChampSelect':
                        chatlog_url = self.client_api + ''
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
                                        name = message["game_name"]
                                        tag = message["game_tag"]
                                        current_time = datetime.now().strftime("%H:%M:%S")
                                        self.Messages_textedit.append(f"[{current_time}] {name}#{tag} : {body}")
                            else:
                                messages_exist = False
                                self.Messages_textedit.clear()
                        except KeyError:
                            messages_exist = False
                            self.Messages_textedit.clear()
                            error_message = str(e)
                            pyperclip.copy(error_message)

                        url = self.client_api + ''
                        
                        response = requests.get(url, verify=False)
                        json_data = response.json()
                        ?? = [conversation[''] for conversation in json_data[''] if 'champ-select' in conversation['']]
                        ? = ', '.join(??)
                        
                        #url = self.client_api + '/chat/v5/participants/champ-select'
                        
                        nicknameurl = self.client_api + f'' 
                        response = requests.get(nicknameurl, verify=False)
                        parsed_json = json.loads(response.text)
                        names = []
                        for participant in parsed_json["participants"]:
                            name_with_tag = f"{participant['game_name']}#{participant['game_tag']}"
                            converted_name_with_tag = f"{participant['game_name']}-{participant['game_tag']}"
                            names.append(name_with_tag)
                        if len(names) >= 1:
                            self.Nickname_label.setText(", ".join(names))
                        else:
                            self.Nickname_label.setText("")
                        if not search_performed:
                            for checkbox_name, checkbox in self.checkboxes.items():
                                if checkbox.isChecked():
                                    if checkbox_name == "DeepLOL_check":
                                        if len(names) == 5:
                                            deeplol_url = QUrl(f"https://www.deeplol.gg/multi/{converted_region}/" + urllib.parse.quote(",".join(names)))
                                            QDesktopServices.openUrl(deeplol_url)
                                            search_performed = True
                                    elif checkbox_name == "OPGG_check":
                                        for i in range(len(names)):
                                            summoner_name = names[i]
                                            opgg_get = f"https://www.op.gg/summoners/{converted_region}/{converted_name_with_tag}"
                                            opgg_get = opgg_get.replace(f"{summoner_name}", summoner_name, i)
                                            opgg_search = requests.get(opgg_get, headers=opgg_get_headers)
                                            soup = BeautifulSoup(opgg_search.content, 'html.parser')
                                            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
                                            if script_tag:
                                                try:
                                                    json_data = json.loads(script_tag.string)
                                                    summoner_id = json_data['props']['pageProps']['data']['summoner_id']
                                                    opgg_post = f'https://op.gg/api/v1.0/internal/bypass/summoners/{converted_region}/{summoner_id}/renewal'
                                                    opgg_refresh = f'https://op.gg/api/v1.0/internal/bypass/summoners/{converted_region}/{summoner_id}/summary'
                                                    response = requests.post(opgg_post, headers=opgg_post_headers)
                                                    response = requests.get(opgg_refresh, headers=opgg_get_headers)
                                                except (json.JSONDecodeError, KeyError) as e:
                                                    print(f'Error decoding JSON: {e}')
                                                    error_message = str(e)
                                                    pyperclip.copy(error_message)
                                            else:
                                                print('Script tag with id="__NEXT_DATA__" not found')
                                        if len(names) == 5:
                                            opgg_url = QUrl(f"https://op.gg/multisearch/{converted_region}?summoners=" + urllib.parse.quote(",".join(names)))
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

    def convert_region_from_http(self, region_from_http):
        # 미리 정의한 매핑을 사용하여 변환
        converted_region = self.region_mapping.get(region_from_http, None)
        return converted_region


class NickNameThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.nickname = None

    def set_apis(self, riot_api, client_api):
        self.riot_api = riot_api
        self.client_api = client_api

    def set_nickname(self, nickname):
        self.nickname = nickname

    def run(self):
        input_text = self.nickname
        game_name, tag_line = input_text.split('#') if '#' in input_text else (input_text, '')
        data = {
            'gameName' : game_name,
            'tagLine' : tag_line
        }
        r = requests.post(f'{self.client_api}/chat/v6/friendrequests', json=data, verify=False)
        r = requests.get(f'{self.client_api}/chat/v6/friendrequests', verify=False)
        friend_requests = r.json().get('requests', [])
        puuid_list = [friend_request.get('puuid') for friend_request in friend_requests if friend_request.get('puuid')]
        puuid_str = ','.join(puuid_list)
        r = requests.delete(f'{self.riot_api}/lol-chat/v2/friend-requests/{puuid_str}', verify=False)
        print(puuid_str)

class EloPointThread(QThread):
    def __inint__(self):
        super().__init__()

    def set_apis(self, riot_api, client_api):
        self.riot_api = riot_api
        self.client_api = client_api

    def run(self):
        g = requests.get(f'{self.riot_api}/lol-chat/v1/me', verify=False)
        gnd = g.json()

        gn = gnd.get("gameName", "")
        gt = gnd.get("gameTag", "")
        puuid = gnd.get("puuid", "")
        rankedLeagueTier = gnd.get("lol", {}).get("rankedLeagueTier", "")
        rankedLeagueDivision = gnd.get("lol", {}).get("rankedLeagueDivision", "")


        print("puuid : " , puuid)
        print(f'RANK : {rankedLeagueTier} {rankedLeagueDivision}')

        url = f"https://www.op.gg/summoners/KR/{gn}-{gt}"
        headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})

        if script_tag:
            json_data = json.loads(script_tag.string)
            lp_histories = json_data.get('props', {}).get('pageProps', {}).get('data', {}).get('lp_histories', [])
            if lp_histories:
                    most_recent_entry = max(lp_histories, key=lambda x: datetime.fromisoformat(x['created_at']))
                    elo_point = most_recent_entry['elo_point']
                    print('Elo point :', elo_point)
        

class SubWindow(QWidget):
    def __init__(self, riot_api, client_api):
        super().__init__()
        self.riot_api = riot_api
        self.client_api = client_api
        
        self.NickName_thread = NickNameThread()
        self.NickName_thread.set_apis(self.riot_api, self.client_api)
        self.elo_point_thread = EloPointThread()
        self.elo_point_thread.set_apis(self.riot_api, self.client_api)
        self.initUI()
        

    def initUI(self):
        self.setGeometry(400, 400, 300, 200)
        self.setWindowTitle('Labs')

        Hlayout_existing_buttons = QHBoxLayout()

        ARAM_Info = QPushButton('Display ARAM Info', self)
        ARAM_Info.clicked.connect(self.ARAM_Info)
        Hlayout_existing_buttons.addWidget(ARAM_Info)

        My_data_Info = QPushButton('My Data Info', self)
        My_data_Info.clicked.connect(self.My_Data_Info)
        Hlayout_existing_buttons.addWidget(My_data_Info)

        seasons_data = QPushButton('LOL Seasons Data', self)
        seasons_data.clicked.connect(self.Seasons_data)
        Hlayout_existing_buttons.addWidget(seasons_data)

        Vlayout = QVBoxLayout()
        self.input_nickname = QLineEdit(self)
        self.input_nickname.setPlaceholderText('Nickname#Tag')
        Vlayout.addWidget(self.input_nickname)

        self.fetch_button = QPushButton('puuid 얻기', self)
        self.fetch_button.clicked.connect(self.start_NickName_thread)
        Vlayout.addWidget(self.fetch_button)

        self.input_nickname.returnPressed.connect(self.start_NickName_thread)

        Hlayout = QVBoxLayout()
        Hlayout.addLayout(Hlayout_existing_buttons)
        Hlayout.addLayout(Vlayout)
        self.setLayout(Hlayout)

    def start_NickName_thread(self):
        nickname = self.input_nickname.text()
        self.fetch_thread.set_nickname(nickname)
        self.fetch_thread.start()


    def ARAM_Info(self):
        test_url = requests.get(f'{self.riot_api}/lol-summoner/v1/current-summoner', verify=False)
        test_url_response = json.loads(test_url.text)
        reroll_points = test_url_response['rerollPoints']
        current_points = reroll_points['currentPoints']
        number_of_rolls = reroll_points['numberOfRolls']
        points_cost_to_roll = reroll_points['pointsCostToRoll']
        points_to_reroll = reroll_points['pointsToReroll']


        print(f"현재 포인트 / 1회 비용: {current_points} / {points_cost_to_roll}")
        print(f"현재 주사위 갯 수 : {number_of_rolls}")
        print(f"다음 주사위 까지 필요 포인트: {points_to_reroll}")

    def My_Data_Info(self):
        self.elo_point_thread.start()
        My_honor = requests.get(f'{self.riot_api}/lol-honor-v2/v1/profile', verify=False)
        test_url = requests.get(f'{self.riot_api}/lol-summoner/v1/current-summoner', verify=False)
        test_url_response = json.loads(test_url.text)
        My_honor_response = json.loads(My_honor.text)

        honorLevel = My_honor_response['honorLevel']
        honorcheckpoint = My_honor_response['checkpoint']

        percent_complete_for_next_level = test_url_response['percentCompleteForNextLevel']
        xp_since_last_level = test_url_response['xpSinceLastLevel']
        xp_until_next_level = test_url_response['xpUntilNextLevel']
        summonerLevel = test_url_response['summonerLevel']

        print(f'명예 레벨 : {honorLevel} \n체크포인트 : {honorcheckpoint}')
        print(f'현재 레벨 : {summonerLevel}')
        print(f"exp: {percent_complete_for_next_level}%")
        print(f"{xp_since_last_level} / {xp_until_next_level}")

    def Seasons_data(self):
        Seasons = requests.get(f'{self.riot_api}/lol-seasons/v1/season/product/LOL', verify=False)
        Seasons_response = json.loads(Seasons.text)

        seasonId = Seasons_response['seasonId']
        adjusted_seasonId = seasonId - 1
        metadata = Seasons_response['metadata']
        currentSplit = metadata['currentSplit']
        seasonStart = Seasons_response['seasonStart']
        seasonEnd = Seasons_response['seasonEnd']

        startSeason = seasonStart
        endSeason = seasonEnd

        startSeason_s = startSeason / 1000
        endSeason_s = endSeason / 1000

        print(f'{adjusted_seasonId} 시즌 - 스플릿 {currentSplit}')

        # UTC 기준으로 타임스탬프를 datetime 객체로 변환
        startSeason_datetime = datetime.fromtimestamp(startSeason_s)
        startSeason_str = startSeason_datetime.strftime("%Y-%m-%d %H:%M:%S")
        print("시즌 시작 시간: ", startSeason_str)
        endSeason_datetime = datetime.fromtimestamp(endSeason_s)
        endSeason_str = endSeason_datetime.strftime("%Y-%m-%d %H:%M:%S")
        print("시즌 종료 시간: ", endSeason_str)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_League_Multisearch()
    ui.setupUi(Form)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    initialize_firebase()
    au = generate_user_id()
    Form.show()
    sys.exit(app.exec_())
