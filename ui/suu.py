# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'suu.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(975, 597)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.toolButton = QtWidgets.QToolButton(self.centralwidget)
        self.toolButton.setGeometry(QtCore.QRect(150, 70, 171, 41))
        self.toolButton.setObjectName("toolButton")
        self.layoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.layoutWidget.setGeometry(QtCore.QRect(60, 270, 411, 41))
        self.layoutWidget.setObjectName("layoutWidget")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.lineEdit_1 = QtWidgets.QLineEdit(self.layoutWidget)
        self.lineEdit_1.setObjectName("lineEdit_1")
        self.horizontalLayout_2.addWidget(self.lineEdit_1)
        self.pushButton_2 = QtWidgets.QPushButton(self.layoutWidget)
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_2.setEnabled(False)
        self.horizontalLayout_2.addWidget(self.pushButton_2)
        self.pushButton_3 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_3.setGeometry(QtCore.QRect(60, 370, 171, 51))
        self.pushButton_3.setObjectName("pushButton_3")
        self.pushButton_3.setEnabled(False)
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(640, 520, 211, 17))
        self.label_3.setObjectName("label_3")
        self.toolButton_1 = QtWidgets.QToolButton(self.centralwidget)
        self.toolButton_1.setGeometry(QtCore.QRect(150, 220, 171, 41))
        self.toolButton_1.setObjectName("toolButton_1")
        self.layoutWidget1 = QtWidgets.QWidget(self.centralwidget)
        self.layoutWidget1.setGeometry(QtCore.QRect(60, 120, 411, 41))
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.layoutWidget1)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lineEdit = QtWidgets.QLineEdit(self.layoutWidget1)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout.addWidget(self.lineEdit)
        self.pushButton_1 = QtWidgets.QPushButton(self.layoutWidget1)
        self.pushButton_1.setObjectName("pushButton_1")
        self.horizontalLayout.addWidget(self.pushButton_1)
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(570, 80, 131, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(720, 80, 171, 16))
        self.label_2.setObjectName("label_2")
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(60, 440, 411, 61))
        self.pushButton.setObjectName("pushButton")
        self.pushButton_4 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_4.setGeometry(QtCore.QRect(300, 370, 171, 51))
        self.pushButton_4.setObjectName("pushButton_4")
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusBar = QtWidgets.QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.toolButton.setText(_translate("MainWindow", "物料坐标输入"))
        self.pushButton_2.setText(_translate("MainWindow", "确定"))
        self.pushButton_3.setText(_translate("MainWindow", "开始"))
        self.label_3.setText(_translate("MainWindow", "请点击矩形框内以获取坐标"))
        self.toolButton_1.setText(_translate("MainWindow", "物料坐标输出"))
        self.pushButton_1.setText(_translate("MainWindow", "确定"))
        self.label.setText(_translate("MainWindow", "利用率"))
        self.label_2.setText(_translate("MainWindow", "运行时间"))
        self.pushButton.setText(_translate("MainWindow", "暂停"))
        self.pushButton_4.setText(_translate("MainWindow", "清除"))
