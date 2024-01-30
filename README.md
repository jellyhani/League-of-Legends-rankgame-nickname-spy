# league-of-legends-rank-name-spy
다운로드 -> https://github.com/jellyhani/league-of-legends-rank-name-spy/releases <br>
exe 파일만 받으면 됩니다 <br>
리그오브레전드 랭크게임 멀티서치(opgg)<br>
프로그램 실행시 자동으로 롤 클라이언트 프로세스를 검색합니다<br>
롤 클라이언트를 실행하지 않았다면 프로세스를 재 확인합니다.<br>
챔피언 선택창일 경우 현재 팀원들의 닉네임을 opgg로 검색합니다.<br><br>
lcu api 기반으로 작동합니다.<br>
문의는 좌측 상단 issues 탭 or https://www.youtube.com/channel/UC0GkZ32n35grJA2eYzI-mrg 에서 해주세요<br>
<br>

# 주의

![image](https://github.com/jellyhani/League-of-Legends-rankgame-nickname-spy/assets/62514874/4e180f31-df03-460e-b392-fc99c11b3772)<br>

제품은 부정행위 프로그램이나 일부 플레이어에게 다른 플레이어가 가질 수 없는 이점을 제공하는 등 플레이어에게 불공정한 이점을 제공할 수 없습니다. <br>
제품은 가시적 정보로 합리적으로 식별할 수 없는 플레이어의 익명성을 해제할 수 없습니다. <br>

api를 사용한 프로그램이지만 약관 위반입니다. 정지가 없다고 장담 할 수 없으나 익명제거 자체는 익명패치 도입 후 지금까지 변화 없이 풀려있습니다.<br>


# 기능
현재 픽창 인원들의 닉네임을 확인할 수 있습니다. <br>
채팅 입력시 현재시간, 닉네임, 내용을 볼 수 있습니다. <br>
OP.GG 또는 FOW.KR, DEEPLOL 전적 자동 서치를 지원합니다. <br>
게임 매칭중 자동 수락기능을 지원합니다. <br>
클라이언트를 끄지 않고 닷지가 가능합니다. <br>
게임 시작 직전 0초에 닷지가 가능합니다. <br>
클라이언트를 빠르게 재실행합니다<br>
2.5 버전부터 uuid 를 생성하여 누적 유저수를 확인하고있습니다.<br>
랜덤으로 생성되며 누적유저수 파악에는 부정확하지만 대략적으로 알고싶어서..<br>
C:\Users\사용자명\Documents\rankspy\uuid.json 파일을 삭제하시면 uuid 는 랜덤한 값으로 재생성 됩니다.<br>
<br>
# 사용법

![image](https://github.com/jellyhani/League-of-Legends-rankgame-nickname-spy/assets/62514874/697b1658-86d8-4d00-9f6a-d29380f01388)
 <br>
Nickname -> 현재 픽창 인원들의 닉네임이 나열됩니다. <br>
닉네임 아래 박스는 현재 픽창에서 친 채팅을 누가 쳤는지 확인 가능합니다. <br>
Status -> 현재 롤 세션이 어디에 있는지 체크하는 용도입니다. 가끔 에러라고 표시되는데 이경우는 라이엇 서버 또는 본인 인터넷 문제인 경우 입니다. <br>
op.gg, deeplol, fow -> 자동 전적 검색 기능입니다. 체크시 해당 사이트에서 전적을 검색합니다. <br>
Auto Ready -> 자동수락 기능입니다. <br>
Auto Ready 옆 박스는 딜레이입니다(기본값 0초)<br>
0s dodge -> 체크박스 체크 후 닷지 버튼을 눌러주셔야 합니다. 0초에 닷지합니다. <br>
마찬가지로 옆에 박스는 딜레이 입니다.(기본값 300ms)<br>
restart -> 롤 클라이언트를 재시작합니다 (의미 없습니다. 테스트용 버튼) <br>
dodge -> 닷지를 진행합니다. 0초닷지를 원하실경우 체크박스 체크 후 눌러주세요 <br>
Github -> 최신버전 업데이트 시 필요할 경우 다운 받으시면 됩니다 <br>

# 디버깅
파이썬이 설치 되어 있으셔야 합니다.
코드를 직접 실행하시기 위해서는 [여기](https://github.com/jellyhani/League-of-Legends-rankgame-nickname-spy/archive/refs/heads/main.zip)를 눌러 다운로드 하시거나 프로젝트를 복사하세요.<br>
압축된 파일을 풀고 원하는 디렉토리에 푸시고 league.py 를 편집기로 실행하세요<br>
저는 visual studio code 를 이용합니다.<br>
F5 를 눌러 디버깅모드로 한번 실행하세요<br>
아래 명령어를 입력하여 필요한 패키지를 설치하세요<br>
```python
pip install -r requirements.txt
```
이후 다시 f5 를 누르시면 실행되실겁니다.<br><br>

<br><br>
[https://www.virustotal.com/gui/file/658ea4089f86b67b21f265703fb984b55be238b88067a6e0ad6f97e2747f3414?nocache=1](https://www.virustotal.com/gui/file/658ea4089f86b67b21f265703fb984b55be238b88067a6e0ad6f97e2747f3414?nocache=1)<br><br>
![league](https://user-images.githubusercontent.com/62514874/224506726-24066b6d-ea3c-4bc2-9c33-df4e8f32130e.PNG)<br>


https://user-images.githubusercontent.com/62514874/224507382-f0a8536d-d7ea-4c25-8757-6e820c6df637.mov



