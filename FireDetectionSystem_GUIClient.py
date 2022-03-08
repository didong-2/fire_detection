import sys, folium, io, os, cv2, torch
from socket import *
import numpy as np
from playsound import playsound
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer, pyqtSlot, QTime
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QApplication, QWidget, QGroupBox, QVBoxLayout, QLabel, QDesktopWidget, QHBoxLayout, QPushButton)

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        vbox = QVBoxLayout()
        vbox.addWidget(self.connectBox())

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.mapBox())
        hbox1.addWidget(self.imageBox())
        hbox1.addWidget(self.setData())

        vbox.addLayout(hbox1)

        endBtn = QPushButton("종료")
        endBtn.clicked.connect(self.endClicked)
        hbox2 = QHBoxLayout()
        hbox2.addStretch(1)
        hbox2.addWidget(endBtn)
        vbox.addLayout(hbox2)

        self.setLayout(vbox)
        self.setWindowTitle('화재 판단 시스템')
        self.resize(800,600)
        self.center()
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def endClicked(self):
        self.close()

    def connectBox(self):
        groupbox = QGroupBox('라즈베리파이 통신', self)
        connectBtn = QPushButton('연결 시작', self)
        connectBtn.clicked.connect(self.connectClicked)
        self.timeLabel = QLabel('time', self)
        current_time = QTime.currentTime()
        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간 : " + text_time
        self.timeLabel.setText(time_msg)
        self.nowtime()
        self.stateLabel = QLabel('연결 상태', self)

        hbox = QHBoxLayout()
        hbox.addWidget(connectBtn)
        hbox.addStretch(1)
        hbox.addWidget(self.timeLabel)
        hbox.addStretch(1)
        hbox.addWidget(self.stateLabel)

        groupbox.setLayout(hbox)
        return groupbox

    def connectClicked(self):
        print("connectClicked")
        self.connecting_start()

    def connecting_start(self):
        print("connect start")

        try:
            clientSock = socket(AF_INET, SOCK_STREAM)
            # clientSock.connect(('IP Address Of Raspberry Server', 8080))
            clientSock.connect(('192.168.43.131', 8080))
            while True:
                f = self.firedetected(clientSock.recv(1024).decode('utf-8'), clientSock)
                if f == 0:
                    self.stateLabel.setText("연결 종료")
                    break
        except:
            print('connecting fail')
        self.fire_alarm()

    def firedetected(self, mesg, clientSock):
        if mesg == 'fire detected':
            print("fire detected")
            sendYes = 'yes'
            # gps 값 받기
            self.gps = self.getGPS(sendYes, clientSock)
            # 시간 값 받기
            self.time = self.getTime(sendYes, clientSock)
            print("time data is : ", self.time)
            # 이미지 받기
            self.getImage(clientSock)
            return 0
        else:
            return 1

    def changeImage(self):
        self.imageBox.removeWidget(self.initImage)
        self.newImage = QLabel(self)
        self.image = QPixmap("C:/Users/eeee/Desktop/화재 통합/fire.jpg")
        self.newImage.setPixmap(QPixmap(self.image))
        self.newImage.show()
        self.newImage.setObjectName("Fire_graphic")
        self.imageBox.addWidget(self.newImage)

    def fire_alarm(self):
        model = torch.hub.load('ultralytics/yolov5', 'custom', path='C:/Users/content/yolov5/best.pt')
        # img = 'C:/Users/content/test.png'
        img = 'C:/Users/eeee/Desktop/화재 통합/fire.jpg'
        results = model(img)
        results.xyxy[0]
        print(results.pandas().xyxy[0])
        print('\n')
        print("confidence list")
        a = results.pandas().xyxy[0].loc[:, 'confidence']
        aa = a.values
        print(aa)
        if (len(aa) > 0):
            for x in range(0, len(aa), 1):
                if (aa[x] > 0.25):
                    print("화재가 감지되었습니다.")
                    self.stateL.setText('화재 발견')
                    self.timeDataLabel.setText(str(self.time))
                    if str(self.gps) != 'None':
                        lat = self.gps.split(' ')[0]
                        lon = self.gps.split(' ')[1]
                        print('lat ',lat, 'lon ',lon)
                        s = lat+lon
                        self.gpsLabel.setText(s)
                    else:
                        print('gps ',gps)
                        self.gpsLabel.setText(gps)
                    self.mapChange(float(lat), float(lon))
                    self.changeImage()
                    self.conf.setText(str(aa[x]))
                    self.sound_play()

    def getGPS(self,sendYes, clientSock):
        clientSock.sendall(sendYes.encode('utf-8'))
        gpsdata = clientSock.recv(1024)
        gps = gpsdata.decode('utf-8')
        return gps

    def getTime(self, sendYes, clientSock):
        clientSock.sendall(sendYes.encode('utf-8'))
        timedata = clientSock.recv(1024)
        time = timedata.decode('utf-8')
        return time

    def getImage(self, clientSock):
        filename = "fire.jpg"
        clientSock.sendall(filename.encode('utf-8'))

        nowdir = os.getcwd()
        print(nowdir)

        with open(nowdir + "\\" + filename, 'wb') as f:  # 현재dir에 filename으로 파일을 받는다
            data = b''
            try:
                while True:
                    buf = clientSock.recv(1024)
                    print(len(buf), len(data))
                    print(data)
                    # data_transferred+=len(data)
                    data += buf
                    if len(buf) != 1024:
                        break
            except :
                print(ex)

        # print('파일 %s 받기 완료. 전송량 %d' % (filename, data_transferred))
        print('파일 %s 받기 완료. ' % (filename))
        encoded_img = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)
        cv2.imwrite('./fire.jpg', img)

    def nowtime(self):
        self.timer = QTimer()
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout_run)

    def timeout_run(self):
        current_time = QTime.currentTime()
        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간 : " + text_time
        self.timeLabel.setText(time_msg)
        self.timeLabel.repaint()

    def mapBox(self):
        groupbox = QGroupBox('화재 발생 위치')
        self.mapWidgetBox = QHBoxLayout()
        self.initMapWidget = self.initMap()
        self.mapWidgetBox.addWidget(self.initMapWidget)
        groupbox.setLayout(self.mapWidgetBox)
        return groupbox

    def mapChange(self, lat, lon):
        self.mapWidgetBox.removeWidget(self.initMapWidget)
        self.gpsMapWidget = self.gpsMap(lat, lon)
        self.mapWidgetBox.addWidget(self.gpsMapWidget)

    def initMap(self):
        coordinate = (38, 127)
        m = folium.Map(
            tiles='CartoDB positron',
            zoom_start=6,
            location=coordinate
        )
        data = io.BytesIO()
        m.save(data, close_file=False)
        webView = QWebEngineView()
        webView.setHtml(data.getvalue().decode())
        return webView

    def gpsMap(self, lat, lon):
        m = folium.Map(
            tiles='CartoDB positron',
            zoom_start=16,
            location=(lat, lon)
        )
        folium.Marker(
            location=(lat,lon),
            icon=folium.Icon(color='red')
        ).add_to(m)
        data = io.BytesIO()
        m.save(data, close_file=False)
        webView = QWebEngineView()
        webView.setHtml(data.getvalue().decode())
        return webView


    def imageBox(self):
        groupbox = QGroupBox('화재 사진')
        self.initImage = QLabel(self)
        self.image = QPixmap("C:/Users/eeee/Desktop/화재 통합/기본이미지.png")
        self.initImage.setPixmap(QPixmap(self.image))
        self.initImage.show()
        self.initImage.setObjectName("Fire_graphic")

        self.imageBox = QHBoxLayout()
        self.imageBox.addWidget(self.initImage)
        groupbox.setLayout(self.imageBox)
        return groupbox

    def setData(self):
        groupbox = QGroupBox('화재 정보')
        self.stateL = QLabel('화재 감지되지 않음',self)
        timeDataL = QLabel('발견 시간',self)
        self.timeDataLabel = QLabel('00:00:00',self)
        gpsL = QLabel('위치 정보',self)
        self.gpsLabel = QLabel('00.00, 00.00',self)
        conf = QLabel('confidence', self)
        self.conf = QLabel('0.000',self)

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addWidget(self.stateL)
        vbox.addStretch(1)
        vbox.addWidget(timeDataL)
        vbox.addWidget(self.timeDataLabel)
        vbox.addStretch(1)
        vbox.addWidget(gpsL)
        vbox.addWidget(self.gpsLabel)
        vbox.addStretch(1)
        vbox.addWidget(conf)
        vbox.addWidget(self.conf)
        vbox.addStretch(1)

        groupbox.setLayout(vbox)
        return groupbox

    def sound_play(self):
        playsound("firesound.mp3")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())