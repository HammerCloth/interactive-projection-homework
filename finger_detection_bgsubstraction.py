import cv2
import numpy as np
import copy
import math
import pyautogui
import threading
import turret_mouse

t=threading.Thread(target=turret_mouse.run())
t.start()


#获取屏幕大小
screenWidth, screenHeight = pyautogui.size()
#用于截取roi
cap_region_x_begin=0.5  
cap_region_y_end=0.8  
threshold = 60  # BINARY threshold
blurValue = 41  # GaussianBlur parameter
bgSubThreshold = 50
learningRate = 0


isBgCaptured = 0   # 判断背景是否已被截取
triggerSwitch = False  # 判断是否开启键鼠模拟

def printThreshold(thr):
    print("更换阈值threshold "+str(thr))

#使用bgModel去除背景
def removeBG(frame):
    fgmask = bgModel.apply(frame,learningRate=learningRate)
    kernel = np.ones((3, 3), np.uint8)
    fgmask = cv2.erode(fgmask, kernel, iterations=1)
    res = cv2.bitwise_and(frame, frame, mask=fgmask)
    return res

#计算手指数量，返回是否计算完毕和手指个数
def calculateFingers(res,drawing):  
    #获取凸包
    hull = cv2.convexHull(res, returnPoints=False)
    if len(hull) > 3:
        #获取凸缺陷
        defects = cv2.convexityDefects(res, hull)
        if type(defects) != type(None): 
            cnt = 0
            #计算凸缺陷的角度
            for i in range(defects.shape[0]):  
                s, e, f, d = defects[i][0]
                start = tuple(res[s][0])
                end = tuple(res[e][0])
                far = tuple(res[f][0])
                a = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
                b = math.sqrt((far[0] - start[0]) ** 2 + (far[1] - start[1]) ** 2)
                c = math.sqrt((end[0] - far[0]) ** 2 + (end[1] - far[1]) ** 2)
                angle = math.acos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c))  
                if angle <= math.pi / 2:  # 如果角度小于90度，记为一个指缝
                    cnt += 1
                    cv2.circle(drawing, far, 8, [211, 84, 0], -1)
            return True, cnt
    return False, 0

#计算轮廓中间点
def centroid(max_contour):
    moment = cv2.moments(max_contour)
    if moment['m00'] != 0:
        cx = int(moment['m10'] / moment['m00'])
        cy = int(moment['m01'] / moment['m00'])
        return cx, cy
    else:
        return None

# Camera
#参数0表示第一个摄像头
camera = cv2.VideoCapture(0)
#分别指视频流中帧的宽度和高度
camera.set(10,200)
#cv2.namedWindow('trackbar')
#cv2.createTrackbar('trh1', 'trackbar', threshold, 100, printThreshold)


while camera.isOpened():
    ret, frame = camera.read()
    #threshold = cv2.getTrackbarPos('trh1', 'trackbar')
    frame = cv2.bilateralFilter(frame, 5, 50, 100)  # 双边滤波，去噪
    frame = cv2.flip(frame, 1)  # 水平翻转
    #画矩形
    cv2.rectangle(frame, (int(cap_region_x_begin * frame.shape[1]), 0),
                 (frame.shape[1], int(cap_region_y_end * frame.shape[0])), (255, 0, 0), 2)
    cv2.imshow('original', frame)

    # 主循环
    if isBgCaptured == 1:  
        img = removeBG(frame)
        #截取region of interest
        img = img[0:int(cap_region_y_end * frame.shape[0]),
                    int(cap_region_x_begin * frame.shape[1]):frame.shape[1]]  # clip the ROI
        #cv2.imshow('mask', img)


        #转化为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        #显示将灰度图高斯模糊后的图像
        blur = cv2.GaussianBlur(gray, (blurValue, blurValue), 0)
        #cv2.imshow('blur', blur)
        #阈值处理并显示
        ret, thresh = cv2.threshold(blur, threshold, 255, cv2.THRESH_BINARY)
        #cv2.imshow('ori', thresh)

        #获取所有轮廓
        thresh1 = copy.deepcopy(thresh)
        contours, hierarchy = cv2.findContours(thresh1, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        #找到最大轮廓
        length = len(contours)
        maxArea = -1
        if length > 0:
            for i in range(length):  
                temp = contours[i]
                area = cv2.contourArea(temp)
                if area > maxArea:
                    maxArea = area
                    ci = i

            res = contours[ci]
            #获取图像的凸包
            hull = cv2.convexHull(res)
            drawing = np.zeros(img.shape, np.uint8)
            #轮廓画成红色
            cv2.drawContours(drawing, [res], 0, (0, 255, 0), 2)
            #凸包画成绿色
            cv2.drawContours(drawing, [hull], 0, (0, 0, 255), 3)
            #计算手指数量
            isFinishCal,cnt = calculateFingers(res,drawing)
            #计算中心点
            cnt_centroid= centroid(res)
            cv2.circle(drawing, cnt_centroid, 5, [255, 0, 255], -1)
            cx,cy=centroid(res)
            if triggerSwitch is True:
                if isFinishCal is True :
                    x=int((cx-160)/160*400+screenWidth/2)
                    y=int((cy-160)/160*400+screenHeight/2)
                    print(x,y)
                    #if x>screenWidth/2-250 and x<screenHeight/2+250:
                    pyautogui.moveTo(x,y)
        cv2.imshow('output', drawing)

    # Keyboard OP
    k = cv2.waitKey(10)
    if k == 27:  # press ESC to exit
        camera.release()
        cv2.destroyAllWindows()
        break
    elif k == ord('b'):  # press 'b' to capture the background
        #建立一个提取背景帧的模型
        bgModel = cv2.createBackgroundSubtractorMOG2(0, bgSubThreshold)
        isBgCaptured = 1
        print( '背景已提取'')
    elif k == ord('r'):  # press 'r' to reset the background
        bgModel = None
        triggerSwitch = False
        isBgCaptured = 0
        print ('背景已重置')
    elif k == ord('n'):
        triggerSwitch = True
        print ('键鼠模拟已开启')

