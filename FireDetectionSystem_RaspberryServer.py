import serial
import pynmea2
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import datetime
import cv2
import numpy as np
from socket import *
from os.path import exists
import sys

def parseGPS(str):
    if str.find('GGA') > 0:
        msg = pynmea2.parse(str)
        print(" %s" %(msg))
        print("Timestamp: %s -- Lat: %s %s -- Lon: %s %s -- Altitude:%s %s" %(msg.timestamp,msg.lat,msg.lat_dir,msg.lon,msg.lon_dir,msg.altitude,msg.altitude_units))
        global gps_lat
        global gps_lon
        global gps_alt
        gps_lat=msg.lat
        gps_lon=msg.lon
        gps_alt=msg.altitude
        return 0
    else:
        return 1


camera=PiCamera()
camera.resolution=(640,480)
camera.framerate=32
rawCapture = PiRGBArray(camera,size=(640,480))
time.sleep(0.1)
kernel=np.ones((5,5),np.uint8)
serverSock = socket(AF_INET, SOCK_STREAM)
serverSock.bind(('', 8080))
serverSock.listen(1)
connectionSock, addr = serverSock.accept()
print(str(addr),'에서 접속했습니다')
gps_lat="aaa"
gps_lon="bbb"
gps_alt="ccc"

serialPort=serial.Serial("/dev/serial0", 9600, timeout=0.5)

count=0

for frame in camera.capture_continuous(rawCapture, format="bgr",use_video_port=True):

    image=frame.array

    bgr_lower = np.array([0, 0, 200], dtype = "uint8")
    bgr_upper = np.array([255, 255, 255], dtype = "uint8")
    bgr_mask = cv2.inRange(image, bgr_lower, bgr_upper)
    res = cv2.bitwise_and(image, image, mask = bgr_mask)

    ycbcr = cv2.cvtColor(res, cv2.COLOR_BGR2YCR_CB)
    ycbcr_lower = np.array([0,140, 0],dtype="uint8")
    ycbcr_upper = np.array([255, 255, 140],dtype="uint8")
    ycbcr_mask = cv2.inRange(ycbcr, ycbcr_lower, ycbcr_upper)

    opening = cv2.morphologyEx(ycbcr_mask, cv2.MORPH_OPEN, kernel)
    x,y,w,h=cv2.boundingRect(opening)
    cv2.rectangle(image, (x,y), (x+w,y+h), (0,255,0) ,1)

    cv2.imshow("result", image)

    image=cv2.resize(image, dsize=(128,128),interpolation=cv2.INTER_AREA)

    if x>30 and y>30 and w>30 and h>30:

        time.sleep(1)

        cv2.imwrite('fire.jpg', image, params=[cv2.IMWRITE_JPEG_QUALITY,100])
        signal='fire detected'
        connectionSock.sendall(signal.encode('utf-8'))
        now=datetime.datetime.now()
        date_time=now.strftime("%m/%d/%Y, %H:%M:%S")
        print(date_time)

        gps = connectionSock.recv(1024).decode('utf-8')
        while count <4:
            try:
                s=serialPort.readline()
                s=str(s,'utf-8')
                a=parseGPS(s)

                if a==0:
                    count+=1
                    if str(gps_alt)!="None":

                        gps_lat = float(gps_lat[0:2])+(float(gps_lat[2:len(gps_lat)]))/60
                        gps_lon = float(gps_lon[0:3])+(float(gps_lon[3:len(gps_lon)]))/60
                        print('latitude'+str(gps_lat))
                        print('longitude'+str(gps_lon))
                        print('altitude'+str(gps_alt))
            except Exception as ex:
                    print(ex)

        if gps == "yes" :
            gps=str(gps_lat)+" "+str(gps_lon)+" "+str(gps_alt)
            connectionSock.sendall(gps.encode('utf-8'))
        else:
            gps = "none"
            connectionSock.sendall(gps.encode('utf-8'))
        now_time = connectionSock.recv(1024).decode('utf-8')
        if now_time == "yes" :
            now_time = date_time
            connectionSock.sendall(now_time.encode('utf-8'))
        else:
            now_time = "none"
            connectionSock.sendall(now_time.encode('utf-8'))
        filename = connectionSock.recv(1024) #클라이언트한테 파일이름(이진 바이트 스트림 형태)을 전달 받는다
        print('받은 데이터 : ', filename.decode('utf-8')) #파일 이름을 일반 문자열로 변환한다
        data_transferred = 0
        if not exists(filename):
            print("no file")
            sys.exit()

        print("파일 %s 전송 시작" %filename)
        with open(filename, 'rb') as f:
            try:
                data = f.read(1024) #1024바이트 읽는다
                while data: #데이터가 없을 때까지 for 문으로 돌려보기
                    data_transferred += connectionSock.send(data) #1024바이트 보내고 크기 저장
                    data = f.read(1024) #1024바이트 읽음
            except Exception as ex:
                print(ex)
        print("전송완료 %s, 전송량 %d" %(filename, data_transferred))

    key=cv2.waitKey(1) & 0xFF
    rawCapture.truncate(0)
    if key == ord("q"):
        break

