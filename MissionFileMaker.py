import sys, os, io, folium, gpxpy, json
import requests as rq
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (QApplication, QWidget, QGroupBox, QComboBox, QPushButton
, QVBoxLayout, QHBoxLayout, QDesktopWidget, QLineEdit, QLabel, QProgressBar, QSpinBox
,QDialog, QListWidget, QCheckBox, QFileDialog)

class gpxData:

    def __init__(self, address):
        openFile = open(address, 'r', encoding='UTF8')
        gpxParse = gpxpy.parse(openFile)
        self.totalArr = []
        flag = 0
        x = 0
        while (flag != 1):
            try:
                data = gpxParse.tracks[x].segments[0].points
                self.totalArr.append([])
                for point in data:
                    # 등산로 데이터에서 똑같은 지점 위치데이터가 3번 반복됨
                    # 이유는 알 수 없으나, 굳이 세 번의 Waypoint를 찍을 필요가 없으므로
                    # 반복되는 지점은 생략하고 추출
                    if len(self.totalArr[x]) == 0:
                        self.totalArr[x].append([point.latitude, point.longitude])
                    else:
                        if not self.totalArr[x][-1] == [point.latitude, point.longitude]:
                            self.totalArr[x].append([point.latitude, point.longitude])
                x += 1

            except IndexError:
                flag = 1
        print("...Complete Getting The GPX Data")


class graphNSearch:
    def __init__(self, totalArr, listItems):
        self.totalArr = totalArr
        self.listItems = listItems
        self.indexData = []

    def initGraph(self, point0, point1):
        self.indexData = []
        edgeArr = []
        for i in self.listItems :
            for j in range(-1, 1):
                if not self.totalArr[i][j] in self.indexData:
                    self.indexData.append(self.totalArr[i][j])
            vertex1 = 2*self.indexData.index(self.totalArr[i][0])
            vertex2 = 2*self.indexData.index(self.totalArr[i][-1])
            edge = 2*self.listItems.index(i)+1
            edgeArr.append([vertex1, edge])
            edgeArr.append([vertex2, edge])
        self.point = 2*self.indexData.index(self.totalArr[point0][point1-1])
        if len(self.indexData) <= len(self.listItems):
            self.V = 2*len(self.listItems)+1
        else :
            self.V = 2*len(self.indexData)
        self.graph=[[]for i in range(self.V)]
        for i in edgeArr:
            self.graph[i[0]].append(i[1])
            self.graph[i[1]].append(i[0])

    def DFSUtil(self, u, visited):
        visited[u] = True
        self.flightNum.append(u)
        for v in self.graph[u]:
            if not visited[v]:
                self.DFSUtil(v, visited)
                self.flightNum.append(u)

    def DFS(self):
        visited = [False] * self.V
        self.flightNum = []
        self.DFSUtil(self.point, visited)

    def makePath(self):
        self.flightPointArr = []
        for i in range(0,len(self.flightNum)-2,2):
            vertex1 = int(self.flightNum[i]/2)
            vertex2 = int(self.flightNum[i+2]/2)
            edge = int((self.flightNum[i+1]-1)/2)

            if not vertex1 == vertex2 :
                if self.totalArr[self.listItems[edge]][0] == self.indexData[vertex1] and\
                        self.totalArr[self.listItems[edge]][-1] == self.indexData[vertex2]:
                    for arr in self.totalArr[self.listItems[edge]]:
                        self.flightPointArr.append(arr)
                elif self.totalArr[self.listItems[edge]][0] == self.indexData[vertex2] and\
                        self.totalArr[self.listItems[edge]][-1] == self.indexData[vertex1]:
                    for arr in reversed(self.totalArr[self.listItems[edge]]):
                        self.flightPointArr.append(arr)
                del self.flightPointArr[-1]

            else :
                if self.totalArr[self.listItems[edge]][0] == self.indexData[vertex1] :
                    for arr in self.totalArr[self.listItems[edge]]:
                        self.flightPointArr.append(arr)
                    del self.flightPointArr[-1]
                    for arr in reversed(self.totalArr[self.listItems[edge]]):
                        self.flightPointArr.append(arr)
                    del self.flightPointArr[-1]
                elif self.totalArr[self.listItems[edge]][-1] == self.indexData[vertex1] :
                    for arr in reversed(self.totalArr[self.listItems[edge]]):
                        self.flightPointArr.append(arr)
                    del self.flightPointArr[-1]
                    for arr in self.totalArr[self.listItems[edge]]:
                        self.flightPointArr.append(arr)
                    del self.flightPointArr[-1]


class mapWidget(QWidget):
    def __init__(self, parent):
        super(mapWidget, self).__init__(parent)

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

    def getSetMap(self, totalArr):
        sumX = 0
        sumY = 0
        sum = 0
        for arr in totalArr:
            for i in arr:
                sumX += i[0]
                sumY += i[1]
                sum += 1
        center = [sumX / sum, sumY / sum]
        map = folium.Map(
            tiles='CartoDB positron',
            zoom_start=15,
            location=center
        )
        for i in range(len(totalArr)):
            folium.PolyLine(
                locations=totalArr[i],
                tooltip=i
            ).add_to(map)
        for i in range(len(totalArr)):
            for j in range(-1,1):
                s =str(i)+'-'+str(j+1)+str(totalArr[i][j])
                folium.Circle(
                    location=totalArr[i][j],
                    radius=5,
                    color='orange',
                    tooltip=s
                ).add_to(map)
        return map

    def setMap(self, totalArr):
        data = io.BytesIO()
        map = self.getSetMap(totalArr)
        map.save(data, close_file=False)
        webView = QWebEngineView()
        webView.setHtml(data.getvalue().decode())
        return webView

    def itemMap(self, totalArr, index):
        map = self.getSetMap(totalArr)
        folium.PolyLine(
            locations=totalArr[index],
            color='red',
            weight=7
        ).add_to(map)
        data = io.BytesIO()
        map.save(data, close_file=False)
        webView = QWebEngineView()
        webView.setHtml(data.getvalue().decode())
        return webView

    def getPointMap(self, totalArr, point0, point1):
        map = self.getSetMap(totalArr)
        s = str(point0) + '-' + str(point1) + str(totalArr[point0][point1 - 1])
        folium.Marker(
            location=totalArr[point0][point1 - 1],
            icon=folium.Icon(color='red'),
            tooltip=s
        ).add_to(map)
        return map

    def pointMap(self, totalArr, point0, point1):
        map = self.getPointMap(totalArr, point0, point1)
        data = io.BytesIO()
        map.save(data, close_file=False)
        webView = QWebEngineView()
        webView.setHtml(data.getvalue().decode())
        return webView

    def applyMap(self, totalArr, point0, point1, listItems):
        map = self.getPointMap(totalArr, point0, point1)
        for index in listItems:
            folium.PolyLine(
                locations=totalArr[index],
                color='red',
                weight=7
            ).add_to(map)
        data = io.BytesIO()
        map.save(data, close_file=False)
        webView = QWebEngineView()
        webView.setHtml(data.getvalue().decode())
        return webView

class MyApp(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        vbox = QVBoxLayout()
        vbox.addWidget(self.uploadBox())
        vbox.addWidget(self.makeMissionBox())
        vbox.addWidget(self.saveBox())

        hbox1 = QHBoxLayout()
        exitBtn = QPushButton('종료',self)
        exitBtn.setCheckable(True)
        exitBtn.clicked.connect(self.close)
        hbox1.addStretch(1)
        hbox1.addWidget(exitBtn)
        vbox.addLayout(hbox1)

        hbox2 = QHBoxLayout()
        self.mapBox = QVBoxLayout()
        self.initMap = mapWidget(self).initMap()
        self.mapBox.addWidget(self.initMap)
        self.mapType = 0
        hbox2.addLayout(self.mapBox)
        hbox2.addLayout(vbox)

        self.setLayout(hbox2)

        self.setWindowTitle('QGroundControl 미션파일 제작 시스템')
        self.resize(1200, 800)
        self.center()
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def searchClicked(self):
        fileOpen = QFileDialog.getOpenFileName(self, 'Open file', './', 'gpx File(*.gpx);; All File(*)')
        self.fileAddress = fileOpen[0]
        self.uploadAddress.setText(self.fileAddress)

    def uploadClicked(self):
        try:
            gpxD = gpxData(self.fileAddress)
            self.totalArr = gpxD.totalArr
            self.removeMap()
            self.setMap = mapWidget(self).setMap(self.totalArr)
            self.mapBox.addWidget(self.setMap)
            self.mapType = 1
            for i in range(len(self.totalArr)):
                self.totalList.addItem(str(i))
                for j in range(-1, 1):
                    s = str(i) + '-' + str(j + 1) + str(self.totalArr[i][j])
                    self.pointCombo.addItem(s)
        except:
            errorWindow(self, 0)


    def uploadBox(self):
        groupbox = QGroupBox('.gpx 파일 업로드')
        self.uploadAddress = QLineEdit(self)
        searchBtn = QPushButton('파일 찾기', self)
        searchBtn.clicked.connect(self.searchClicked)
        uploadBtn = QPushButton('업로드', self)
        uploadBtn.clicked.connect(self.uploadClicked)

        hbox = QHBoxLayout()
        hbox.addWidget(self.uploadAddress)
        hbox.addWidget(searchBtn)
        hbox.addWidget(uploadBtn)
        groupbox.setLayout(hbox)
        return groupbox

    def addListItem(self):
        flag = 0
        for x in range(self.addList.count()):
            if self.totalList.currentItem().text() == self.addList.item(x).text() :
                flag = 1
        if flag == 0 :
            self.addList.addItem(self.totalList.currentItem().text())

    def delListItem(self):
        self.addList.takeItem(self.addList.currentRow())

    def removeMap(self):
        if self.mapType == 0 :
            self.mapBox.removeWidget(self.initMap)
        elif self.mapType == 1 :
            self.mapBox.removeWidget(self.setMap)
        elif self.mapType == 2 :
            self.mapBox.removeWidget(self.itemMap)
        elif self.mapType == 3 :
            self.mapBox.removeWidget(self.pointMap)
        elif self.mapType == 4 :
            self.mapBox.removeWidget(self.applyMap)

    def totalListClicked(self):
        self.removeMap()
        index = int(self.totalList.currentItem().text())
        newItemMap=mapWidget(self).itemMap(self.totalArr, index)
        self.mapBox.addWidget(newItemMap)
        self.itemMap = newItemMap
        self.mapType = 2

    def addListClicked(self):
        self.removeMap()
        index = int(self.addList.currentItem().text())
        newItemMap=mapWidget(self).itemMap(self.totalArr, index)
        self.mapBox.addWidget(newItemMap)
        self.itemMap = newItemMap
        self.mapType = 2

    def pointItem(self):
        self.removeMap()
        gettext=self.pointCombo.currentText()
        point0 = int(gettext[0:gettext.rfind('-')])
        point1 = int(gettext[gettext.rfind('-')+1:gettext.rfind('[')])
        newPointMap=mapWidget(self).pointMap(self.totalArr, point0, point1)
        self.mapBox.addWidget(newPointMap)
        self.pointMap = newPointMap
        self.mapType = 3

    def applyClicked(self):
        try:
            self.removeMap()
            gettext = self.pointCombo.currentText()
            point0 = int(gettext[0:gettext.rfind('-')])
            point1 = int(gettext[gettext.rfind('-') + 1:gettext.rfind('[')])
            listItems = []
            for x in range(self.addList.count()):
                listItems.append(int(self.addList.item(x).text()))
            newApplyMap = mapWidget(self).applyMap(self.totalArr, point0, point1, listItems)
            self.mapBox.addWidget(newApplyMap)
            self.applyMap = newApplyMap
            self.mapType = 4
            graph = graphNSearch(self.totalArr, listItems)
            graph.initGraph(point0, point1)
            graph.DFS()
            graph.makePath()
            self.flightPointArr = graph.flightPointArr
            applyW = applyWindow(self)
            applyW.apply(self.flightPointArr)
            while (True):
                if not applyW.exec_():
                    self.setPercent = applyW.setPercent
                    break
            self.waypointPercent.setText(str(self.setPercent))

        except:
            errorWindow(self,1)



    def makeMissionBox(self):
        groupbox = QGroupBox('미션 설정')

        totalLabel = QLabel('전체 등산로',self)
        self.totalList = QListWidget(self)
        self.totalList.itemDoubleClicked.connect(self.addListItem)
        self.totalList.itemClicked.connect(self.totalListClicked)
        vbox1 = QVBoxLayout()
        vbox1.addWidget(totalLabel)
        vbox1.addWidget(self.totalList)

        addBtn = QPushButton('추가',self)
        addBtn.setCheckable(True)
        addBtn.clicked.connect(self.addListItem)
        delBtn = QPushButton('삭제',self)
        delBtn.setCheckable(True)
        delBtn.clicked.connect(self.delListItem)
        vbox2 = QVBoxLayout()
        vbox2.addWidget(addBtn)
        vbox2.addWidget(delBtn)

        addLabel = QLabel('선택한 등산로', self)
        self.addList = QListWidget(self)
        self.addList.itemDoubleClicked.connect(self.delListItem)
        self.addList.itemClicked.connect(self.addListClicked)
        vbox3 = QVBoxLayout()
        vbox3.addWidget(addLabel)
        vbox3.addWidget(self.addList)

        hbox1 = QHBoxLayout()
        hbox1.addLayout(vbox1)
        hbox1.addLayout(vbox2)
        hbox1.addLayout(vbox3)

        pointLabel = QLabel('이착륙 지점 : ', self)
        self.pointCombo = QComboBox(self)
        self.pointCombo.addItem('=======등산로 지점=======')
        self.pointCombo.currentIndexChanged.connect(self.pointItem)
        hbox2 = QHBoxLayout()
        hbox2.addWidget(pointLabel)
        hbox2.addWidget(self.pointCombo)

        applyBtn = QPushButton('적용',self)
        applyBtn.clicked.connect(self.applyClicked)
        hbox3 = QHBoxLayout()
        hbox3.addStretch(1)
        hbox3.addWidget(applyBtn)

        Label0 = QLabel('', self)
        vbox4 = QVBoxLayout()
        vbox4.addLayout(hbox1)
        vbox4.addWidget(Label0)
        vbox4.addLayout(hbox2)
        vbox4.addWidget(Label0)
        vbox4.addLayout(hbox3)

        groupbox.setLayout(vbox4)

        return groupbox

    def saveClicked(self):
        try:
            SaveWindow(self, self.flightPointArr, self.waypointPercent.text(), self.altCheck.isChecked())
        except:
            errorWindow(self, 2)

    def saveBox(self):
        groupbox = QGroupBox('저장')

        waypoint = QLabel('등산로 모사율 :',self)
        self.waypointPercent = QLabel('',self)
        lab = QLabel(' %',self)
        hbox1 = QHBoxLayout()
        hbox1.addWidget(waypoint)
        hbox1.addWidget(self.waypointPercent)
        hbox1.addWidget(lab)

        self.altCheck = QCheckBox('고도 정보 포함하기',self)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addWidget(self.altCheck)
        saveBtn = QPushButton('저장',self)
        saveBtn.clicked.connect(self.saveClicked)

        hbox2 = QHBoxLayout()
        hbox2.addLayout(vbox)
        hbox2.addWidget(saveBtn)

        groupbox.setLayout(hbox2)
        return groupbox


class applyWindow(QDialog):
    def __init__(self, parent):
        super(applyWindow, self).__init__(parent)

    def apply(self, flightPointArr):
        if len(flightPointArr) >= 2000 :
            s = '등산로 모사율을 설정해주십시오. 모사율이 높을 수록 파일 저장 시간이 오래걸립니다.\n'\
                '* 현재 선택된 데이터 수가 매우 많아 파일 사용에 오류가 발생할 수 있습니다.'
        else :
            s = '등산로 모사율을 설정해주십시오. 모사율이 높을 수록 파일 저장 시간이 오래걸립니다.'
        waypointLabel = QLabel(s,self)
        setnum = QLabel('등산로 모사율 : ', self)
        self.spinBox = QSpinBox(self)
        self.spinBox.setRange(0,100)
        self.spinBox.setValue(50)
        lab = QLabel(' %', self)
        hbox1 = QHBoxLayout()
        hbox1.addWidget(setnum)
        hbox1.addWidget(self.spinBox)
        hbox1.addWidget(lab)

        applyBtn = QPushButton('적용',self)
        applyBtn.clicked.connect(self.applyClicked)
        hbox2 = QHBoxLayout()
        hbox2.addStretch(1)
        hbox2.addWidget(applyBtn)

        vbox = QVBoxLayout()
        vbox.addWidget(waypointLabel)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)

        self.setLayout(vbox)
        self.setWindowTitle('적용')
        self.show()

    def applyClicked(self):
        self.setPercent = self.spinBox.value()
        self.close()

class writePlanFile:
    def __init__(self, flightPointArr, address):
        self.Arr = flightPointArr
        self.address = address

    def getParams(self, index, comm):
        if (comm == 16 or comm == 21 or comm == 22):
            lat = self.Arr[index][0]
            # lat = self.Arr[index][0]+20
            lon = self.Arr[index][1]
            alt = self.Arr[index][2]
            return [0, 0, 0, None, lat, lon, alt]
        else:
            return

    def getCommand(self, index):
        # index에 따라 command 부여
        # 현재는 Takeoff(22), Land(21), Waypoint(16)만 제공
        if (index == 0):
            return 22  # Takeoff
        elif (index == (len(self.Arr) - 1)):
            return 21  # Land
        else:
            return 16  # Waypoint

    def makeAItem(self, index):
        # item 하나 제작
        item = dict()
        item["AMSLAltAboveTerrain"] = None
        item["Altitude"] = self.Arr[index][2]
        # item["Altitude"] = 100
        item["AltitudeMode"] = 1
        item["autoContinue"] = True
        comm = self.getCommand(index)
        item["command"] = comm
        item["doJumpId"] = index + 1
        item["frame"] = 3
        getParams = self.getParams(index, comm)
        item["params"] = getParams
        item["type"] = "SimpleItem"
        return item

    def makeItems(self):
        # 전체 items 제작
        items = []
        for i in range(len(self.Arr)):
            items.append(self.makeAItem(i))
        return items

    def mainValue(self):
        main = dict()
        main["fileType"] = "Plan"
        geoFence = dict()
        geoFence["circles"] = []
        geoFence["polygons"] = []
        geoFence["version"] = 2
        main["geoFence"] = geoFence
        main["groundStation"] = "QGroundControl"
        mission = dict()
        mission["cruiseSpeed"] = 15
        mission["firmwareType"] = 12
        mission["globalPlanAltitudeMode"] = 0
        mission["hoverSpeed"] = 5
        mission["items"] = self.makeItems()
        homeP = [self.Arr[0][0], self.Arr[0][1], self.Arr[0][2]]
        mission["plannedHomePosition"] = homeP
        mission["vehicleType"] = 2
        mission["version"] = 2
        main["mission"] = mission
        rallyPoints = dict()
        rallyPoints["points"] = []
        rallyPoints["version"] = 2
        main["rallyPoints"] = rallyPoints
        main["version"] = 1
        # print(main)
        with open(self.address, 'w', encoding='utf-8') as makeFile:
            json.dump(main, makeFile, indent="\t")
        print("...Saved The Plan File")


class SaveWindow(QDialog):
    def __init__(self, parent,flightPointArr, waypointPercent, altcheck):
        super(SaveWindow, self).__init__(parent)
        self.flightPointArr = flightPointArr
        self.waypointPercent = int(100/int(waypointPercent))
        self.altcheck = altcheck
        self.save()
        self.resize(300,100)
        self.show()

    def save(self):
        self.downloadAddress = QLineEdit(self)
        downloadBtn = QPushButton('경로 선택', self)
        downloadBtn.clicked.connect(self.downloadClicked)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.downloadAddress)
        hbox1.addWidget(downloadBtn)

        self.pbar = QProgressBar(self)
        self.pbar.setMinimum(0)
        self.pbar.setMaximum(100)

        self.stateLabel = QLabel('저장 상태',self)
        startSaveBtn = QPushButton('저장하기',self)
        startSaveBtn.clicked.connect(self.startSaveClicked)
        endBtn = QPushButton('닫기',self)
        endBtn.clicked.connect(self.endClicked)
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.stateLabel)
        hbox2.addWidget(startSaveBtn)
        hbox2.addWidget(endBtn)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addWidget(self.pbar)
        vbox.addLayout(hbox2)

        self.setLayout(vbox)
        self.setWindowTitle('저장')

    def downloadClicked(self):
        FileSave = QFileDialog.getSaveFileName(self, 'Save file', '/'+'sample.plan')
        self.filedownAddress = FileSave[0]
        self.downloadAddress.setText(self.filedownAddress)

    def startSaveClicked(self):
        saveFlight = []
        for i in range(0, len(self.flightPointArr), self.waypointPercent):
            saveFlight.append(self.flightPointArr[i])
        print(saveFlight)
        if self.altcheck :
            for i in range(len(saveFlight)):
                self.pbar.setValue(int(i /len(saveFlight) * 100))
                self.stateLabel.setText('고도 크롤링 중...')
                lat = saveFlight[i][0]
                lon = saveFlight[i][1]
                url = "https://secure.geonames.org/srtm3JSON?lat=" + str(lat) + "&lng=" + str(
                    lon) + "&username=galwayireland"
                res = rq.get(url).json()
                ele = res['srtm3']
                print(ele)
                saveFlight[i].append(ele)
        else :
            for i in range(len(saveFlight)):
                self.pbar.setValue(int(i / len(saveFlight) * 100))
                self.stateLabel.setText('저장 중...')
                saveFlight[i].append(100)

        plan = writePlanFile(saveFlight, self.filedownAddress)
        plan.mainValue()
        self.pbar.setValue(100)
        self.stateLabel.setText('저장 완료')

    def endClicked(self):
        self.close()

class errorWindow(QDialog):
    def __init__(self, parent, index):
        super(errorWindow, self).__init__(parent)
        if index == 0 :
            self.upload()
        elif index == 1:
            self.apply()
        elif index == 2:
            self.save()
        self.show()
        
    def upload(self):
        s = "파일 선택 문제가 발생했습니다. 다음을 확인해주십시오.\n\n"+\
            "1. '산림청 홈페이지-정보공개-공공데이터 개방-공공데이터 개방목록-휴양문화-등산로정보'\n"+\
            "   에서 제공되는 gpx 데이터를 이용해주십시오.\n"+\
            "2. 파일명에 '_SPOT_'이 포함된 gpx 파일은 '등산로 지점' 데이터입니다.\n"+\
            "   '_SPOT_'이 포함되지 않은 등산로 gpx 파일을 선택해주십시오."
        lab = QLabel(s)
        close = QPushButton("확인")
        close.clicked.connect(self.closeClicked)
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(close)
        box = QVBoxLayout()
        box.addWidget(lab)
        box.addLayout(hbox)
        self.setLayout(box)
        self.setWindowTitle('파일 선택 에러')

    def apply(self):
        s = "경로 선택 및 생성 문제가 발생했습니다. 다음을 확인해주십시오.\n\n"+\
            "1. 알맞는 gpx 파일을 선택 및 업로드해주십시오.\n"+\
            "2. 등산로를 1개 이상 선택해주십시오.\n"+\
            "3. 연속된 등산로를 선택해주십시오.\n"+\
            "4. 이착륙 지점을 선택해주십시오.\n"+\
            "5. 선택한 등산로 위의 이착륙 지점을 선택해주십시오.\n"
        lab = QLabel(s)
        close = QPushButton("확인")
        close.clicked.connect(self.closeClicked)
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(close)
        box = QVBoxLayout()
        box.addWidget(lab)
        box.addLayout(hbox)
        self.setLayout(box)
        self.setWindowTitle('경로 선택 및 생성 에러')

    def save(self):
        s = "파일 제작 문제가 발생했습니다. 다음을 확인해주십시오.\n\n"+\
            "1. 알맞는 gpx 파일을 선택 및 업로드해주십시오.\n"+\
            "2. 등산로 및 이착륙 지점을 선택 후 적용버튼을 눌러 등산로 모사율을 설정해주십시오.\n"
        lab = QLabel(s)
        close = QPushButton("확인")
        close.clicked.connect(self.closeClicked)
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(close)
        box = QVBoxLayout()
        box.addWidget(lab)
        box.addLayout(hbox)
        self.setLayout(box)
        self.setWindowTitle('파일 제작 에러')

    def closeClicked(self):
        self.close()
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())