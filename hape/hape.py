# -*- coding: utf-8 -*-

import time
import copy
import threading
import numpy as np
from math import cos, sin, pi
# from shapely.geometry import geo, polygon
# from shapely.geos import pointer

class pack_1D():
    def getBestRect(self, blank, rects):
        self.rects = rects      # 待计算矩形: # [[s, num, gender, [[], [], [], []]], ..]
        self.blank = blank      # 空白区域长度
        self.bestFit = blank    # 最小缝隙
        self.answer = {}    # 计算结果：{num:长或宽, ...}
        self.rollAnswer = {}    # 计算中的结果
        self.area = 0
        self.rollArea = 0

        self._go(self.blank, self.rects)
        return self.answer

    def _go(self, blank, rects):
        if blank < self.bestFit:
            self.bestFit = blank
            self.answer = self.rollAnswer.copy()

        elif blank == self.bestFit and self.rollArea > self.area:
            self.area = self.rollArea
            self.bestFit = blank
            self.answer = self.rollAnswer.copy()

        if not rects:
            return 0

        for i in range(len(rects)):  # [[s, num, gender, [[], [], [], []]], ..]

            s = rects[i][0]
            num = rects[i][1]
            gender = rects[i][2]
            graph = rects[i][3]
            l = graph[2][0] - graph[0][0]
            h = graph[2][1] - graph[0][1]
            new_rects = rects.copy()
            for j in range(i+1):
                new_rects.pop(0)

            self.rollAnswer[num] = l
            self.rollArea += s
            new_blank = blank - l

            if new_blank >= 0:
                self._go(new_blank, new_rects)

            self.rollAnswer.pop(num)
            self.rollArea -= s

            self.rollAnswer[num] = h
            self.rollArea += s
            new_blank = blank - h

            if new_blank >= 0:
                self._go(new_blank, new_rects)

            self.rollAnswer.pop(num)
            self.rollArea -= s


class Calculator(threading.Thread, pack_1D):
    def __init__(self):
        super(Calculator, self).__init__()
        self.__flag = threading.Event()
        self.__flag.set()
        self.__globalFlag = threading.Event()
        self.__globalFlag.clear()
        self.__running = threading.Event()
        self.__running.set()

        self.iptpoints = []  # 读取的数据点:[[s, num, gender, [[], [], [], []]], ..]
        self.optpoints = [[0, 0, -1, [[0,0], [0,0], [0,0]]]]  # 输出的数据点:[[s, num, gender, [[], [], [], []]], ..]
        self.rects = [] # [[s, num, gender, [[], [], [], []]], ..]
        self.tris = []  # [[s, num, gender, [[], [], [], []]], ..]
        self.virticalTris = []  # [[s, num, gender, [[], [], [], []]], ..]
        self.grids = {}  # 栅格:0代表未使用，1代表使用
        self.settledPoints = [] # 已经拍好的图形：[[Yc, y_max, Xc, gender, location, num, s], ..]
        self.y_full = 0 # 传入所有图形拼整以40 为底后的最高线，最终结果肯定是高于这个线的，主要用来区分什么时候用什么排样模式
        self.y_max = 0  # 排布时图形现在的最高线
        self.y_list = [] # 存放seetledpoint的所有Y坐标：[[y_max, num], [], []..]
        self.pastPoint = []
        self.bestChoice = []    # 回溯的最好选择:[[Yc, y_max, Xc, gender, location, num, s], ..]

        self.finishFlag = False  # 计算结束表示
        self.stopFlag = False   # 计算终止表示
        self.numScale = 6  # 小数四舍五入位数,推荐：3，4
        self.sleepTime = 0  # 睡眠时间,用来调整计算速度，推荐：1，0.001，0
        self.roundScale = 180   # 每次旋转的刻度,推荐：如4代表每次旋转90°，8代表每次旋转45°
        self.gridScale = 2  # 遍历时使用的栅格的放大倍数
        self.gridX = 40 # 排布时的X范围
        self.gridY = 50 # Y

    def initGrid(self):
        '''
        简历40×50网格
        :return:
        '''
        k = np.zeros((self.gridX * self.gridScale + 1) * (self.gridY * self.gridScale + 1)).reshape([self.gridX * self.gridScale + 1, self.gridY * self.gridScale + 1])
        k[0] = 0.5
        k[-1] = 0.5
        k.T[0] = 0.5
        k.T[-1] = 0.5
        self.grids = k

    def calculating(self):
        '''
        更新optpoints
        :return:
        '''
        print('开始计算')

        # ====================优先排矩形====================
        self.place_rect()
        print(self.settledPoints)
        # ====================优先排矩形====================

        # ====================排三角形====================
        y_max = 0
        for graphs in self.tris:   # [[s, num, gender, [[], [], [], []]], ..]
            chosenOne = self.getBestPos(graphs[0], graphs[1], graphs[2], graphs[3], mode=1)

            self.__flag.wait()  # 暂停
            if self.stopFlag:  # 终止循环
                return False
            print('保存图形', chosenOne)    # [Yc, y_max, Xc, gender, location, num, s]
            self.refreshData(chosenOne, save=True)
            y_max = self.saveData(chosenOne)
        print(self.settledPoints)
        # ====================排三角形====================

        # ====================回溯====================
        self.backtrace(y_max)
        # ====================回溯====================
        self.optpoints.clear()
        for i in self.bestChoice:
            self.refreshData(i, save=True)
        self.settledPoints = self.bestChoice
        return True
    
    def place_rect(self):
        self.rects.sort(reverse=True)
        rects = copy.deepcopy(self.rects)  # [[s, num, gender, [[], [], [], []]], ..]
        print('rects', rects)
        gridScale = self.gridScale
        _xcoor = list(range(self.gridX * gridScale + 1))  # x坐标列表:[0, 1, ...40] 共41个
        _ycoor = list(range(self.gridY * gridScale + 1))  # y坐标列表:[0, 1, ...50] 共50个
        for ycoor in _ycoor:
            y = ycoor / gridScale  # y坐标
            if not rects:  # 没有矩形排
                break
            end = -1
            for xcoor in _xcoor:
                x = xcoor / gridScale  # x坐标
                if xcoor <= end:
                    continue
                blank = -1 / gridScale  # 凹陷区域要减去1,同时也要加上比例
                if self.grids[xcoor, ycoor] == 1:
                    continue

                # 空白区域
                start = xcoor
                cursor = xcoor
                for cursor in range(xcoor, self.gridX * gridScale + 1):
                    if self.grids[cursor, ycoor] < 1:
                        blank += 1 / gridScale
                    else:
                        break
                end = cursor
                print('-----起点x', start / gridScale, '-----终点x', end / gridScale, 'y', y)

                answer = self.getBestRect(blank, rects)  # {num:长或宽, ...}
                print('answer:', answer)

                for num, key in answer.items():
                    print('num:', num, ' key:', key)
                    rect = None
                    new_graph = None
                    for rect in rects:  # [[s, num, gender, [[], [], [], []]], ..]
                        if rect[1] != num:
                            continue
                        # 把矩形移到x，y处
                        graph = rect[3]
                        l = graph[2][0] - graph[0][0]
                        h = graph[2][1] - graph[0][1]
                        if l == key:    # 横着放
                            new_graph = [[x, y], [l + x, y],
                                         [l + x, h + y], [x, h + y]
                                         ]
                        else:   # 竖着放
                            new_graph = [[x, y], [h + x, y],
                                         [h + x, l + y], [x, l + y]
                                         ]
                        break

                    self.__flag.wait()  # 暂停
                    if self.stopFlag:  # 终止循环
                        return False

                    Xc, Yc, y_max = self.caculateCenter(0, new_graph)  # 旋转后的形心
                    self.refreshData([Yc, y_max, Xc, 0, new_graph, num, rect[0]],
                                     save=True)  # [[Yc, y_max, Xc, gender, location, num, s],..]
                    self.saveData([Yc, y_max, Xc, 0, new_graph, num, rect[0]])
                    x += key
                    rects.remove(rect)
    
    def backtrace(self, y_max):
        print('~~~~~~ok')
        self.y_max = y_max
        self.bestChoice = copy.deepcopy(self.settledPoints)
        # 开始回溯
        overFlow = 1
        stopLine = self.y_max  # 停止回溯
        while stopLine > self.y_full:  # 如果删除后的最高线比100线低则退出
            highLevel = self.y_list[0:overFlow]  # y_list:[[y_max, num], [], []..]
            # 按高度顺序取出此次回溯的图形
            graphs = []  # [[Yc, y_max, Xc, gender, location, num, s], ..]
            for i in highLevel:
                num = i[1]
                for j in self.settledPoints:  # [[Yc, y_max, Xc, gender, location, num, s], ..]
                    if j[5] == num:
                        graphs.append(j)
            print('---', overFlow, self.y_list[0:overFlow])

            # 删掉部分很高的图形
            y_max = 0
            for graph in graphs:
                print('此次删除', graph[5], graph)
                self.refreshData(graph, delMode=True)
                y_max = self.saveData(graph, delMode=True)
            stopLine = y_max

            # 按面积重新排
            graphs.sort(key=lambda x: x[-1], reverse=True)  # 按面积
            for graph in graphs:  # 直接排是按graphs里面的从高到底排   # [[Yc, y_max, Xc, gender, location, num, s], ..]
                s = graph[6]
                num = graph[5]
                gender = graph[3]
                location = graph[4]
                chosenOne = self.getBestPos(s, num, gender, location, mode=2)

                self.__flag.wait()  # 暂停
                if self.stopFlag:  # 终止循环
                    return False

                self.refreshData(chosenOne, save=True)
                y_max = self.saveData(chosenOne)
                if y_max >= self.y_max:  # 最高线比已排最高限高或等于则直接下一个
                    print(y_max, '大于', self.y_max)

                    self.settledPoints.clear()
                    self.y_list.clear()
                    self.initGrid()
                    for graph_ in self.bestChoice:
                        self.saveData(graph_)

                    self.optpoints.clear()
                    for graph_ in self.settledPoints:
                        self.refreshData(graph_, save=True)
                    break
            # 找到更好的姿态
            if y_max < self.y_max:
                self.y_max = y_max
                self.bestChoice = copy.deepcopy(self.settledPoints)
                print(self.bestChoice)
                print('找到一次更好的:', self.y_max, self.y_list[0:overFlow], end='\n')

            overFlow += 2  # 取的图形往下深1

    def getBestPos(self, s, num, gender, thisGraph, mode=1):

        lock = -1  # 锁顶栅格的x值
        bigTravel = []  # 大循环 :[Yc, y_max, Xc, gender, location, num, s]
        Y_level = self.gridY  # 当一个图形在遍历时，该值为合格姿势下的Y最大值，任何比该值打的栅格点都不做遍历
        x_coor = list(range(self.gridX * self.gridScale + 1)) # x坐标列表:[0, 1, ...40] 共40个 /[0, 1... 80]
        y_coor = list(range(self.gridY * self.gridScale + 1)) # y坐标列表:[0, 1, ...50] 共50个 /[0, 1...100]
        for xcoor in x_coor:
            x = xcoor / self.gridScale  # x坐标

            for ycoor in y_coor:
                y = ycoor / self.gridScale  # y坐标

                # # 在小图新较多的情况下效率提升才显著,但是不但全
                # if y > Y_level:
                #     # print('-----------------', '该栅格超限', x, '-', y, '该栅格超限', '------------------')
                #     break
                if lock == x:
                    # print('-----------------', '该列已锁定', x, '-', y, '该列已锁定', '------------------')
                    break
                if self.grids[xcoor, ycoor] == 1:  # 该栅格已被使用, 上去一个
                    # print('-----------------', '该栅格已被使用', x, '-', y, '该栅格已被使用', '------------------')
                    continue

                if not gender:  # 矩形
                    list0, list1 = [0, 1], [0, 1, 2, 3]
                else:  # 三角形
                    list0, list1 = [0, 1, 2], [0, 1, 2]

                smallTravel = []  # 小循环:[y_max, Yc, Xc, gender, location]
                for i in list0:
                    x0 = thisGraph[i][0]  # 图形的点
                    y0 = thisGraph[i][1]
                    dx = x0 - x  # x方向移动的距离
                    dy = y0 - y  # y

                    # 将图形拖到排样点
                    thisGrapf_cal = copy.deepcopy(thisGraph)  # 将用作计算的点与原始数据隔离
                    for j in list1:
                        thisGrapf_cal[j][0] = thisGrapf_cal[j][0] - dx
                        thisGrapf_cal[j][1] = thisGrapf_cal[j][1] - dy

                    # 计算睡眠时间
                    time.sleep(self.sleepTime)
                    # 旋转执行刻度
                    for scale in range(self.roundScale + 1):

                        alpha = 2 * pi * scale / self.roundScale  # 旋转角度为弧度
                        location = self.rotate(thisGrapf_cal, x, y, alpha)  # 将图形旋转
                        Xc, Yc, y_max = self.caculateCenter(gender, location)  # 旋转后的形心

                        # 重叠检测
                        overlap = self.judgeCoin(Xc, Yc, location)
                        # overlap = self.judgeCoin_(location)
                        if overlap:  # 发现重叠则跳过
                            continue

                        # 小循环添加
                        smallTravel.append([Yc, y_max, Xc, gender, location, num, s])

                self.__flag.wait()  # 暂停
                if self.stopFlag:  # 终止循环
                    return False

                if not smallTravel:  # 此栅格放不下，往上去一个
                    continue
                else:
                    smallChosenOne = min(smallTravel, key=lambda x: x[1])  # 小循环取y_max值最小的位置
                    self.refreshData(smallChosenOne)
                    bigTravel.append(smallChosenOne)

                    lock = x  # 锁定整列栅格
                    if Y_level > smallChosenOne[1]:
                        Y_level = smallChosenOne[1]  # 根据最高点设置警戒线

        bigTravel.sort()
        if mode == 1:
            bigChosenOne = min(bigTravel)  # 大循环取Yc值最小的位置
        else:
            bigChosenOne = min(bigTravel, key=lambda x:x[1])
        return bigChosenOne # [Yc, y_max, Xc, gender, location, num, s]

    # 将图形旋转alpha角
    def rotate(self,location=None,cankaoX=None,cankaoY=None,angle=None):
        '''
        angle为正则为顺时针转
        location为图形坐标，cankaoX,cankaoY分别为参考点横纵坐标。angle为旋转角度。
        x0= (x - rx0)*cos(a) - (y - ry0)*sin(a) + rx0 ;
        y0= (x - rx0)*sin(a) + (y - ry0)*cos(a) + ry0 ;
        :return:返回新的坐标点。
        '''
        new_location = []
        location = location.copy()
        # 矩形
        if len(location) == 4:
            x0, y0, x1, y1 = location[0][0], location[0][1], location[1][0], location[1][1]
            x2, y2, x3, y3 = location[2][0], location[2][1], location[3][0], location[3][1]
            X0 = (x0-cankaoX)*cos(angle) - (y0-cankaoY)*sin(angle)+cankaoX
            X1 = (x1-cankaoX)*cos(angle) - (y1-cankaoY)*sin(angle)+cankaoX
            X2 = (x2-cankaoX)*cos(angle) - (y2-cankaoY)*sin(angle)+cankaoX
            X3 = (x3-cankaoX)*cos(angle) - (y3-cankaoY)*sin(angle)+cankaoX
            Y0 = (x0-cankaoX)*sin(angle) + (y0-cankaoY)*cos(angle)+cankaoY
            Y1 = (x1-cankaoX)*sin(angle) + (y1-cankaoY)*cos(angle)+cankaoY
            Y2 = (x2-cankaoX)*sin(angle) + (y2-cankaoY)*cos(angle)+cankaoY
            Y3 = (x3-cankaoX)*sin(angle) + (y3-cankaoY)*cos(angle)+cankaoY
            # new_location.extend([[X0, Y0], [X1, Y1], [X2, Y2], [X3, Y3]])
            new_location.extend([[round(X0, self.numScale), round(Y0, self.numScale)],
                                 [round(X1, self.numScale), round(Y1, self.numScale)],
                                 [round(X2, self.numScale), round(Y2, self.numScale)],
                                 [round(X3, self.numScale), round(Y3, self.numScale)]])
        # 三角形
        else:
            x0, y0, x1, y1 = location[0][0], location[0][1], location[1][0], location[1][1]
            x2, y2 = location[2][0], location[2][1]
            X0 = (x0 - cankaoX) * cos(angle) - (y0 - cankaoY) * sin(angle) + cankaoX
            X1 = (x1 - cankaoX) * cos(angle) - (y1 - cankaoY) * sin(angle) + cankaoX
            X2 = (x2 - cankaoX) * cos(angle) - (y2 - cankaoY) * sin(angle) + cankaoX
            Y0 = (x0 - cankaoX) * sin(angle) + (y0 - cankaoY) * cos(angle) + cankaoY
            Y1 = (x1 - cankaoX) * sin(angle) + (y1 - cankaoY) * cos(angle) + cankaoY
            Y2 = (x2 - cankaoX) * sin(angle) + (y2 - cankaoY) * cos(angle) + cankaoY
            # new_location.extend([[X0, Y0], [X1, Y1], [X2, Y2]])
            new_location.extend([[round(X0, self.numScale), round(Y0, self.numScale)],
                                 [round(X1, self.numScale), round(Y1, self.numScale)],
                                 [round(X2, self.numScale), round(Y2, self.numScale)]])

        return new_location

    # 形心/三个点的y值和最低
    def caculateCenter(self, gender, location=None):
        '''
        lei为图形的种类0为矩形，三角形为1
        location为顶点坐标，逆时针顺序。
        :return:Xc,Yc分别为形心的横坐标和纵坐标
        '''
        # 三角形
        if gender == 1:
            Xc = (location[0][0] + location[1][0]+location[2][0]) / 3    # 利用重心的形心
            Yc = (location[0][1] + location[1][1]+location[2][1]) / 3

            y_max = max(location[0][1], location[1][1], location[2][1])
        # 矩形
        else:
            # 形心的横坐标  Xc=(x0+x1+...)/4
            Xc = 1/4*(location[0][0]+location[1][0]+location[2][0]+location[3][0])
            # 形心的纵坐标  Yc=(y1+y2+...)/4
            Yc = 1/4*(location[0][1]+location[1][1]+location[2][1]+location[3][1])
            y_max = max(location[0][1], location[1][1], location[2][1], location[3][1])
        Xc = round(Xc, self.numScale)
        Yc = round(Yc, self.numScale)
        return Xc, Yc, y_max

    def getThisArea(self, graph):
        '''
        得到多边形的 面积
        :param graph: 必须时封闭且按顺时针或逆时针排序:[[], [], [], [].....]
        :return:
        '''
        S = 0   # 面积

        point0 = graph[0]   # 随便取的一个基点，以该点划分除三角行
        for i in range(1, len(graph) - 1):
            point1 = graph[i]
            point2 = graph[i + 1]
            v1 = [point1[0] - point0[0], point1[1] - point0[1]]
            v2 = [point2[0] - point0[0], point2[1] - point0[1]]

            s = abs(v1[0]*v2[1] - v1[1]*v2[0]) / 2  # 一块小三角形的面积
            S = S + s

        return S

    # 判断线香蕉
    def judgeLineCross(self, line1, line2):
        '''
        两条线重叠不相交，只有一个端点在另一条上也不相交,只有穿过才香蕉
        :line1:[[x0, y0], [x1, y1]]
        :line2:[[x0, y0], [x1, y1]]
        :return:    香蕉T/不相交F
        '''
        x0, y0 = line1[0][0], line1[0][1]
        x1, y1 = line1[1][0], line1[1][1]
        x2, y2 = line2[0][0], line2[0][1]
        x3, y3 = line2[1][0], line2[1][1]

        # a交b
        vec0 = (x1-x0, y1-y0)
        vec1 = (x2-x0, y2-y0)
        vec2 = (x3-x0, y3-y0)
        a = vec0[0]*vec1[1] - vec0[1]*vec1[0]
        b = vec0[0]*vec2[1] - vec0[1]*vec2[0]

        # b交a
        vec0 = (x3 - x2, y3 - y2)
        vec1 = (x0 - x2, y0 - y2)
        vec2 = (x1 - x2, y1 - y2)
        c = vec0[0] * vec1[1] - vec0[1] * vec1[0]
        d = vec0[0] * vec2[1] - vec0[1] * vec2[0]

        if a*b<0 and c*d<0:
            return True
        else:
            return False

    def judgePointInner(self, x, y, location):
        '''
        判断点在多边形内, T在里面,在外面或在边上F
        进行区域规整的快速判断
        :param x: 判断点x
        :param y: 判断点y
        :param location:待检测区域。必须是按照边的顺序，连着给的点; 图形坐标:[[], [], [], []]
        :return:
        '''
        # 若点在规整区域外则直接返回F
        x_set = [i[0] for i in location]
        y_set = [i[1] for i in location]
        x_min = min(x_set)
        x_max = max(x_set)
        y_min = min(y_set)
        y_max = max(y_set)
        if x < x_min or x > x_max:
            return 1    # 在外面
        if y < y_min or y > y_max:
            return 1    # 在外面

        flag = -1   # -1在里面；0在边上；1在外面
        for i in range(len(location)):
            point = location[i]
            if i == 0:
                point_next = location[i + 1]
                point_bef = location[-1]
            elif i == len(location) - 1:
                point_next = location[0]
                point_bef = location[i - 1]
            else:
                point_next = location[i + 1]
                point_bef = location[i - 1]
            v0 = [x - point[0], y - point[1]]
            v1 = [point_next[0] - point[0], point_next[1] - point[1]]
            v2 = [point_bef[0] - point[0], point_bef[1] - point[1]]

            # 叉乘之积
            answer = (v0[0]*v1[1] - v1[0]*v0[1]) * (v0[0]*v2[1] - v2[0]*v0[1])
            if answer > 0:  # 在外面或在边上
                flag = 1
                return flag
            if answer == 0:
                flag = 0

        return flag # 在里面

    # 重叠检测，出界检测
    def judgeCoin(self, Xc, Yc, location):
        '''
        待排图形与已排图形的重叠检测
        根据已排图形来

        location:待检查图形, [[], [], []]
        Xc:形心x
        Yc:形心y
        :return:    重叠T/不重叠F
        '''

        # 判断是否出界
        for point in location:
            x = point[0]
            y = point[1]
            if (x < 0) or (x > self.gridX):
                return True # 出现出界
            if (y < 0) or (y > self.gridY):
                return True # 出现出界

        # 最开始的情况
        if not self.settledPoints:
            return False

        x_list = [i[0] for i in location]
        y_list = [i[1] for i in location]
        x_min = min(x_list) # 带派图形的x最低值
        x_max = max(x_list)
        y_min = min(y_list)
        y_max = max(y_list)

        # 遍历已经排放图形的顶点信息
        for Point in self.settledPoints: # [[Yc, y_max, Xc, gender, location, num, s], ..]
            settledGraph = Point[4] # [[], [], [], []] # 以排图形
            x_list_set = [i[0] for i in settledGraph]
            y_list_set = [i[1] for i in settledGraph]
            x_min_set = min(x_list_set)  # 已派图形的x最低值
            x_max_set = max(x_list_set)
            y_min_set = min(y_list_set)
            y_max_set = max(y_list_set)
            # 离得太远的直接跳过
            if x_max<x_min_set or x_min>x_max_set or y_max<y_min_set or y_min>y_max_set:
                continue

            # 检查形心
            exist0 = self.judgePointInner(Xc, Yc, settledGraph)
            if exist0 == -1 or exist0 == 0:   # 形心不能在里面或边上
                return True # 形心在里面

            # 检查点在图形内
            for i in range(len(location)):
                x = location[i][0]
                y = location[i][1]
                exist1 = self.judgePointInner(x, y, settledGraph)  # 图形的顶点
                if exist1  == -1:   # 顶点可以在边上但不能在里面
                    return True #形心在里面

            # 检查边界线香蕉
            line_already = []   # 已排图形的线
            if len(settledGraph) == 3:    # 三角形
                l = [[settledGraph[0], settledGraph[1]],   # 边线1
                      [settledGraph[1], settledGraph[2]],   # 边线2
                      [settledGraph[2], settledGraph[0]],   # 边线3
                      # [settledGraph[0], [(settledGraph[1][0] + settledGraph[2][0])/2, (settledGraph[1][1] + settledGraph[2][1])/2]] ,   # 中线1
                      # [settledGraph[1], [(settledGraph[0][0] + settledGraph[2][0])/2, (settledGraph[0][1] + settledGraph[2][1])/2]]      # 中线2
                    ]
                line_already.extend(l)
            else:   # 矩形
                l = [[settledGraph[0], settledGraph[1]],  # 边线1
                     [settledGraph[1], settledGraph[2]],  # 边线2
                     [settledGraph[2], settledGraph[3]],  # 边线3
                     [settledGraph[3], settledGraph[0]],  # 边线4
                     # [settledGraph[0], settledGraph[2]],  # 中线1
                     # [settledGraph[1], settledGraph[3]]  # 中线2
                    ]
                line_already.extend(l)
            line_noready = []   # 未排图形的线
            if len(location) == 3:
                l = [[location[0], location[1]],   # 边线1
                     [location[1], location[2]],   # 边线2
                     [location[2], location[0]],   # 边线3
                     [location[0], [(location[1][0] + location[2][0]) / 2, (location[1][1] + location[2][1]) / 2]],    # 中线1
                     [location[1], [(location[0][0] + location[2][0]) / 2, (location[0][1] + location[2][1]) / 2]]    # 中线2
                    ]
                line_noready.extend(l)
            else:   # 矩形
                l = [[location[0], location[1]],  # 边线1
                     [location[1], location[2]],  # 边线2
                     [location[2], location[3]],  # 边线3
                     [location[3], location[0]],  # 边线4
                     [location[0], location[2]],  # 中线1
                     [location[1], location[3]]  # 中线2
                    ]
                line_noready.extend(l)

            for line0 in line_already:
                for line1 in line_noready:
                    exist = self.judgeLineCross(line1, line0) # 检查线段
                    if exist:
                        return True # 出现香蕉

        return False    # 检查中没有发现重叠的情况

    #使用shapely
    # def judgeCoin_(self, location):
    #     # 判断是否出界
    #     for point in location:
    #         x = point[0]
    #         y = point[1]
    #         if (x < 0) or (x > self.gridX):
    #             return True # 出现出界
    #         if (y < 0) or (y > self.gridY):
    #             return True # 出现出界
    #
    #     # 最开始的情况
    #     if not self.settledPoints:
    #         return False
    #
    #     polygon0 = Polygon(location)
    #
    #     # 遍历已经排放图形的顶点信息
    #     for settledPoint in self.settledPoints:  # [[s, num, gender, [[], [], [], []]], ..]
    #         points = settledPoint[3]  # [[], [], [], []]
    #         polygon1 = Polygon(points)
    #         k = polygon1.disjoint(polygon0)    # 不重叠T/重叠F
    #         if not k:
    #             return True # 出现香蕉
    #     return False

    def refreshGrid(self, gender, location, delMode=False):
        '''
        刷新排样点
        将self.grid置1
        :location:需要刷新排样点的区域:[[], [], [], [], [], []...] 需要时按几何顺序排序且封闭
        :return:
        '''
        gridScale = self.gridScale

        if not delMode:
            for ycoor in range(self.gridY * gridScale + 1):
                for xcoor in range(self.gridX * gridScale + 1):
                    y = ycoor / gridScale
                    x = xcoor / gridScale
                    exist = self.judgePointInner(x, y, location)
                    if exist == 1:     # 点在外面
                        continue
                    elif exist == 0:    # 在边上
                        self.grids[xcoor,ycoor] = self.grids[xcoor,ycoor] + 0.5
                    else:   # 在里面
                        self.grids[xcoor,ycoor] = 1

                    for point in location:
                        self.grids[int(point[0]) * gridScale, int(point[1]) * gridScale] = 0.5
        else:
            for ycoor in range(self.gridY * gridScale + 1):
                for xcoor in range(self.gridX * gridScale + 1):
                    y = ycoor / gridScale
                    x = xcoor / gridScale

                    exist = self.judgePointInner(x, y, location)

                    if exist == 1:  # 点在外面
                        continue
                    elif exist == 0:  # 在边上
                        self.grids[xcoor, ycoor] = self.grids[xcoor, ycoor] - 0.5
                    else:  # 在里面
                        self.grids[xcoor, ycoor] = 0

                    for point in location:
                        self.grids[int(point[0]) * gridScale, int(point[1]) * gridScale] = 0.5

    def refreshData(self, chosenOne, save=False, delMode=False):
        '''
        刷新正在排样的图形
        :param chosenOne: [Yc, y_max, Xc, gender, location, num, s]
        :param notSave: 正常刷新，来下一个图形就把上衣个删除
        :param addFlag: 添加模式/删除模式
        :return:
        '''
        k = [chosenOne[6], chosenOne[5], chosenOne[3], chosenOne[4]]
        if not delMode:
            try:
                self.optpoints.remove(self.pastPoint)
                self.optpoints.append(k)    # optpoint:[[s, num, gender, [[], [], [], []]], ..]
            except Exception:
                self.optpoints.append(k)    # optpoint:[[s, num, gender, [[], [], [], []]], ..]

            if not save:
                self.pastPoint = k
            else:
                self.pastPoint = []
        else:
            self.optpoints.remove(k)

    def pause(self):
        self.__flag.clear()

    def resume(self):
        self.__flag.set()

    def saveData(self, chosenOne, delMode=False):
        '''
        将拍好的图形保存, 同时关闭在图形内部的栅格
        :param chosenOne: [Yc, y_max, Xc, gender, location, num, s]
        :param location:
        :return:
        '''
        location = chosenOne[4]
        num = chosenOne[5]
        gender = chosenOne[3]

        y_max = max(location, key=lambda x: x[1])
        if not delMode:
            # 保存图形
            self.settledPoints.append(chosenOne)    # settledPoints:[[Yc, y_max, Xc, gender, location, num, s], ..]
            # 保存最高线
            self.y_list.append([y_max[1], num])  # y_max列表：[[y_max, num], [], []..]
            # 刷新栅格
            self.refreshGrid(gender, location)
        else:
            # 删除图形
            self.settledPoints.remove(chosenOne)
            # 删除最高线
            self.y_list.remove([y_max[1], num])

            self.refreshGrid(gender, location, delMode=True)

        self.y_list.sort(reverse=True)
        return self.y_list[0][0]    # 返回y_max

    def sortData(self, graphs):
        '''
        将self.iptpoint 的点按逆时针排列,并且图形左下角的点排第一个
        :graphs:原始数据信息：[[0, [[], [], [], []]], []...]
        :return:
        '''
        new_graph = []

        for graph in graphs:
            num = graph[0]
            gender = graph[1]   # 0/1
            location = graph[2] # [[], [], [], []...]

            x_arr = [i[0] for i in location]
            y_arr = [i[1] for i in location]
            if gender == 0: # 矩形
                x_min = min(x_arr)
                x_max = max(x_arr)
                y_min = min(y_arr)
                y_max = max(y_arr)
                new_graph.append([num, gender, [[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]]])
            else:   # 三角形不做规整直接返回
                new_graph.append(copy.deepcopy(graph))
        return new_graph

    # 上传（刷新）数据
    def uploadData(self):
        return copy.deepcopy(self.optpoints), self.finishFlag

    # 下载数据，入口函数
    def downloadData(self, iptpoints):

        self.stopFlag = False   # 将上次清除画布用的退出标志还原
        self.finishFlag = False

        # 数据一次规整：完整矩形并按逆时针排序    [[num, gender, [[], [], [], []]], ..]
        dumpedData = self.sortData(iptpoints)

        # 栅格初始化
        self.initGrid()

        # 数据二次规整：添加面积并且保存到本地    [[s, num, gender, [[], [], [], []]], ..]
        S = 0   # 总面积
        for graph in dumpedData:
            num = graph[0]  # 图形标号
            gender = graph[1]   # 图形性别
            location = graph[2] # 图形坐标
            s = self.getThisArea(location)  # 图形面积
            S += s
            self.iptpoints.append([s, num, gender, location])

            if gender == 0:
                self.rects.append([s, num, gender, location])
            else:
                self.tris.append([s, num, gender, location])

        for tri in self.tris:   # [[s, num, gender, [[], [], [], []]], ..]
            graph = tri[3]
            vec0 = [graph[1][0] - graph[0][0], graph[1][1] - graph[0][1]]
            vec1 = [graph[2][0] - graph[1][0], graph[2][1] - graph[1][1]]
            vec2 = [graph[0][0] - graph[2][0], graph[0][1] - graph[2][1]]

            a = vec0[0] * vec1[0] - vec0[1] * vec1[1]   # 为0则垂直
            b = vec0[0] * vec2[0] - vec0[1] * vec2[1]
            c = vec1[0] * vec2[0] - vec1[1] * vec2[1]

            if not a or not b or not c:
                self.virticalTris.append(tri)
            else:
                continue

        self.y_full = S / self.gridX    # 标准警戒线  # 1.138*S

        # 按面积由大到小排
        self.iptpoints.sort(reverse=True)
        self.tris.sort(reverse=True)
        self.rects.sort(reverse=True)

        print('下载完成', self.iptpoints)
        self.__globalFlag.set() # 释放计算器

        return self.y_full  # 返回警戒线

    def clear(self):
        # 数据重置
        self.stopFlag = True
        self.iptpoints.clear()
        self.optpoints = [[0, 0, -1, [[0,0], [0,0], [0,0]]]]
        self.y_list.clear()
        self.tris.clear()
        self.rects.clear()
        self.grids = np
        self.settledPoints.clear()

        self.__globalFlag.clear()   # 锁定计算器
        self.resume()

    def run(self):

        while self.__running.isSet():
            self.__globalFlag.wait()
            # 开始计算
            answer = self.calculating()
            if answer:
                print('计算完成')
            else:
                print('计算终止')

            self.finishFlag = True
            self.__globalFlag.clear()   # 锁定计算器
            print('~~~~~~~~~~over~~~~~~~~~~~')



