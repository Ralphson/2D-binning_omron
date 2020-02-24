# -*- coding: utf-8 -*-

import sys, threading, os
import time

from PyQt5 import QtWidgets, QtGui, QtCore
from ui.suu import *

from hape import hape


# 计算模块
calculator = hape.Calculator()
calculator.setDaemon(True)


class MyWindow(QtWidgets.QMainWindow, threading.Thread, Ui_MainWindow):

    def __init__(self):
        super(MyWindow, self).__init__()
        self.qp = QtGui.QPainter()  # 画布
        self.readurl = ''
        self.loadurl = ''
        self.timeInterval = 0.1   # 画布刷新间隔：1为1s/0.001为 1ms
        self.now = time.time()
        self.startTime = time.time()   # 记录开始的时间戳
        self.pauseTime = 0
        self.runningTime = 0
        self.co_rect = QtCore.Qt.yellow
        self.co_tri = QtCore.Qt.green
        self.co_alarmLine = QtCore.Qt.red
        self.co_fullLine = QtCore.Qt.lightGray
        self.co_border = QtCore.Qt.darkBlue
        self.origin = (550, 100)   # 画布原点
        self.l = 40 # 绘图区域长
        self.h = 50 # 绘图区域高
        self.scale = 8  # 缩放比例
        self.iptpoints = []  # 读取的数据点: [[num, gender, [[0, 0], [0, 0], [0, 0], [0, 0]]], ...]
        self.optpoints = [[0, 0, -1, [[0,0], [0,0], [0,0]]]]  # 输出的数据点: [[s, num, gender, [[], [], [], []]], ..]
        self.fullLine = 0  # 100利用率线

        self.setupUi(self)
        self.buttonEvent()

        self.__flag = threading.Event()  # 用于暂停线程的标识
        self.__flag.set()  # 设置为True
        self.__running = threading.Event()  # 用于停止线程的标识
        self.__running.set()  # 将running设置为True
        self.__globalFlag = threading.Event()
        self.__globalFlag.clear()
        self.t1 = threading.Thread(target=self.refreshData)
        self.t1.start()
        calculator.start()

    # 捕捉键盘
    def keyPressEvent(self, a0: QtGui.QKeyEvent):
        # Esc
        if a0.key() == QtCore.Qt.Key_Escape:
            self.close()
        # S/P
        if a0.key() == QtCore.Qt.Key_P or a0.key() == QtCore.Qt.Key_S:
            self.pushButton.click()

    # 捕捉鼠标
    def mouseMoveEvent(self, a0: QtGui.QMouseEvent):
        x = a0.x()
        y = a0.y()
        l = self.l*self.scale
        h = self.h*self.scale
        x0 = self.origin[0]
        y0 = self.origin[1]

        if x0-5 < x < x0+l+5 and y0-5 < y < y0+h+5:
            x = (x-x0)/self.scale
            y = (y0+h-y)/self.scale
            text = 'x: {0}, y: {1}'.format(x, y)
        else:
            text = '请点击矩形框内以获取坐标'
        self.label_3.setText(text)

    def closeEvent(self, event):
        '''
        重写主窗口退出事件，使退出的时候关闭主线程,即t2
        :param event:
        :return:
        '''
        os._exit(0)

    # 绘图事件
    def paintEvent(self, a0: QtGui.QPaintEvent):
        self.qp.begin(self)

        # 画边界框
        co1 = QtGui.QColor(QtCore.Qt.black)
        self.qp.setPen(co1)
        x = self.origin[0]
        y = self.origin[1]
        self.qp.drawRect(x, y, self.l * self.scale, self.h * self.scale)
        # 画饱和线
        co2 = QtGui.QColor(self.co_fullLine)
        self.qp.setPen(co2)
        self.qp.drawLine(self.origin[0],
                         self.origin[1] + self.scale*(self.h - self.fullLine),
                         self.origin[0] + self.l*self.scale,
                         self.origin[1] + self.scale*(self.h - self.fullLine))
        # 显示高度
        self.qp.drawText(self.origin[0] + 40*self.scale + 7,
                         self.origin[1] + self.scale * (self.h - self.fullLine),
                         str(self.fullLine))

        # 画出图形
        try:
            for point in self.optpoints:    # point: [[s, num, gender, [[], [], [], []]], ..]
                num = point[1]
                gender = point[2]
                location = point[3]
                self.drawAShape(num, gender, location)
        except Exception as e:
            print(e, e)

        self.qp.end()

    def drawAShape(self, num, shape, location, scale=None):
        if not scale:
            scale = self.scale
        X = self.origin[0]  # 绘图原点X
        Y = self.origin[1] + self.scale * self.h  # 绘图原点Y

        if shape == 0:  # 0:矩形 1:三角形
            co0 = QtGui.QColor(self.co_border)
            co00 = QtGui.QColor(self.co_rect)
            self.qp.setPen(co0)
            self.qp.setBrush(co00)
            points = [location[0][0] * scale + X, -location[0][1] * scale + Y,
                      location[1][0] * scale + X, -location[1][1] * scale + Y,
                      location[2][0] * scale + X, -location[2][1] * scale + Y,
                      location[3][0] * scale + X, -location[3][1] * scale + Y,]
            polygon = QtGui.QPolygon(points)
            self.qp.drawPolygon(polygon)

            x = (location[0][0] * scale + location[1][0] * scale + location[2][0] * scale) / 3 + X  # 标号的位置
            y = -(location[0][1] * scale + location[1][1] * scale + location[2][1] * scale) / 3 + Y
            self.qp.drawText(x, y, str(num))

        elif shape == 1:
            co1 = QtGui.QColor(self.co_border)
            co11 = QtGui.QColor(self.co_tri)
            self.qp.setPen(co1)
            self.qp.setBrush(co11)
            points = [location[0][0] * scale + X, -location[0][1] * scale + Y,
                      location[1][0] * scale + X, -location[1][1] * scale + Y,
                      location[2][0] * scale + X, -location[2][1] * scale + Y]
            polygon = QtGui.QPolygon(points)
            self.qp.drawPolygon(polygon)

            x = (location[0][0]+ location[1][0] + location[2][0]-3) * scale / 3 + X  # 标号的位置
            y = -(location[0][1] + location[1][1] + location[2][1]-3) * scale / 3 + Y
            self.qp.drawText(x, y, str(num))
        else:
            return

        # 刷新利用率
        usage, y_max = self.get_usage()
        self.label.setText('利用率：' + str(usage) + '%')

        # 显示警戒线
        co2 = QtGui.QColor(self.co_alarmLine)
        self.qp.setPen(co2)
        self.qp.drawLine(self.origin[0],
                         Y - y_max*scale,
                         self.origin[0] + self.l*self.scale,
                         Y - y_max*scale)
        # 显示高度
        self.qp.drawText(self.origin[0] + 40*self.scale + 7,
                         self.origin[1] + (50-y_max)*self.scale,
                         str(y_max))

    def get_usage(self):
        S = 0   # 已画图形的面积
        y_arr = []
        for graph in self.optpoints:    # [[s, num, gender, [[], [], [], []]], ..]
            point = graph[3]
            S = S + graph[0]
            y_arr.extend([i[1] for i in point])

        y_max = max(y_arr)
        usage = round(S / (40 * y_max)*100, 2) # 利用率

        return usage, y_max

    # 按钮触发
    def buttonEvent(self):
        self.toolButton.clicked.connect(self.loadData)
        self.toolButton_1.clicked.connect(self.saveData)
        self.pushButton_3.clicked.connect(self.run_)
        self.pushButton_1.clicked.connect(self.confirmLoad)
        self.pushButton_2.clicked.connect(self.confirmSave)
        self.pushButton.clicked.connect(self.control)
        self.pushButton_4.clicked.connect(self.clear)

    # 读取数据
    def loadData(self):
        print('loadData...')
        self.readurl, _ = QtWidgets.QFileDialog.getOpenFileName(self, caption='选取读取路径', directory='../',
                                                             filter='*.csv')
        print(self.readurl)
        self.lineEdit.setText(self.readurl)
        self.statusBar.showMessage('    状态：选择读取路径中...')

    # 确认读取
    def confirmLoad(self):
        self.iptpoints = []  # 清除本地数据
        self.clear()

        try:
            print('confirm loading...')
            fileopen = open(self.readurl, 'r')
            k = fileopen.read()

            # dump进程序
            num = 0
            for i in k.split('\n'):
                if not i:
                    continue

                location = i.split(',')
                print(location)
                gender = int(location[0])
                amount = int(location[7])   # 该图形的总量
                if amount <= 0:
                    continue
                elif amount == 1:
                    dumped_location = []
                    for i in [1, 3, 5]:
                        dumped_location.append([int(location[i]), int(location[i+1])])
                    self.iptpoints.append([num, gender, dumped_location])    # [[0, [[], [], [], []]], []]
                    num = num + 1  # 图形编号
                else:
                    for k in range(amount):
                        dumped_location = []
                        for i in [1, 3, 5]:
                            dumped_location.append([int(location[i]), int(location[i + 1])])
                        self.iptpoints.append([num, gender, dumped_location])  # [[0, [[], [], [], []]], []]
                        num = num + 1  # 图形编号

            self.pushButton_3.setEnabled(True)
            self.statusBar.showMessage('    成功读取文件!!: ' + self.readurl)
        except Exception as e:
            print(e, '输入数据有问题')
            self.statusBar.showMessage('    输入的数据格式错误!!: ' + self.readurl)


        print(self.iptpoints)

    # 保存数据
    def saveData(self):
        print('saveData...')
        self.loadurl = QtWidgets.QFileDialog.getExistingDirectory(self, caption='选取存入路径', directory='../')
        print(self.loadurl)
        self.lineEdit_1.setText(self.loadurl)
        self.statusBar.showMessage('    状态：选择保存路径中...')

    # 确认保存
    def confirmSave(self):
        try:
            print('comfirm saving...')
            # 数据操作
            print(self.optpoints)

            # 数据流化
            b = ''
            for graphs in self.optpoints:
                gender = graphs[2]
                location = graphs[3]    # [[s, num, gender, [[], [], [], []]], ..]
                b = b + str(gender) + ','
                for i in range(3):
                    b = b + str(abs(location[i][0])) + ',' + str(abs(location[i][1])) + ','
                b = b.rstrip(',')
                b = b + '\n'
            b = b.rstrip('\n')  # 最后一行剪去\n

            print(b)
            fileopen = open(self.loadurl + '/物料坐标输出.csv', 'w')
            fileopen.write(b)
            self.statusBar.showMessage('    成功保存文件!!: ' + self.loadurl)
        except Exception as e:
            print(e)

    # 保持对optpoint的刷新
    def run_(self):
        print('running...')
        self.resume()
        self.pushButton_3.setEnabled(False) # 开始Annie
        self.pushButton_1.setEnabled(False) # 确定输入按钮
        self.pushButton_2.setEnabled(False) # 确认保存按钮

        self.startTime = time.time()   # 记录开始的时间戳
        self.pauseTime = time.time()

        self.fullLine = calculator.downloadData(self.iptpoints)
        self.__globalFlag.set()

    def clear(self):
        print('清除画布')
        calculator.clear()

        # 把图形擦掉
        self.optpoints, stop = calculator.uploadData()  # [[s, num, gender, [[], [], [], []]], ..]
        self.now = time.time()
        self.startTime = time.time()  # 记录开始的时间戳
        self.pauseTime = 0
        self.runningTime = 0
        self.update()

        self.pushButton_1.setEnabled(True)
        self.statusBar.showMessage('    状态：清除图形成功，计算终止...（请选择 输入数据/保存数据）')

    def control(self):
        try:
            if self.__flag.is_set():    # 暂停
                self.pause()
                self.pauseTime = self.now - self.startTime  # 上次运行所用时间
            else:
                self.runningTime = self.runningTime + self.pauseTime    # 将上次运行的对齐到现在时间
                self.resume()
                self.startTime = time.time()
        except Exception as e:
            print(e)

    def resume(self):
        self.pushButton.setText('暂停')
        self.pushButton_4.setEnabled(False)
        self.statusBar.showMessage('    状态：计算中...')
        self.__flag.set()   # T
        calculator.resume()

    def pause(self):
        self.pushButton.setText('继续')
        self.pushButton_4.setEnabled(True)
        self.statusBar.showMessage('    状态：暂停中...')

        self.__flag.clear()
        calculator.pause()

    def refreshData(self):
        self.pause()    # 初始化就启动程序，但不开始扫描
        while self.__running.isSet():
            self.__flag.wait()

            time.sleep(self.timeInterval)

            # 实时更新数据
            self.optpoints, stop = calculator.uploadData()    # [[s, num, gender, [[], [], [], []]], ..]
            self.optpoints.reverse()
            if len(self.optpoints) != 1 and self.optpoints[0][1] == self.optpoints[1][1]:
                self.optpoints.pop(0)

            # 刷新时间
            self.now = time.time() # 记录现在时间戳
            k = time.localtime(self.now - self.startTime + self.runningTime)
            self.label_2.setText('用时:' + str(time.strftime('%M:%S', k)))

            self.update()
            if stop:
                self.pushButton_2.setEnabled(True)
                self.statusBar.showMessage('    状态：计算完成...(请选择 保存数据/清除图形)')
                self.__globalFlag.clear()
                self.__globalFlag.wait()  # 结束


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    mywin = MyWindow()
    mywin.show()

    sys.exit(app.exec_())

