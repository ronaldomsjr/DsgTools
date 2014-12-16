# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DsgTools
                               
                             -------------------
        begin                : 2014-09-19
        git sha              : $Format:%H$
        copyright            : (C) 2014 by Felipe Ferrari
        email                : ferrari@dsg.eb.mil.br
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt4 import QtGui, uic
from PyQt4.QtCore import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui_create_inom_dialog_base.ui'))


class CreateInomDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(CreateInomDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.listaCombos = []
        self.listaCombos.append(self.comboBox500k)
        self.listaCombos.append(self.comboBox250k)
        self.listaCombos.append(self.comboBox100k)
        self.listaCombos.append(self.comboBox50k)
        self.listaCombos.append(self.comboBox25k)
        self.listaCombos.append(self.comboBox10k)
        self.listaCombos.append(self.comboBox5k)
        self.listaCombos.append(self.comboBox2k)
        self.listaCombos.append(self.comboBox1k)
        self.disable(0)
        self.inom=""
        self.constructINOM()
        QObject.connect(self.hemisphereComboBox, SIGNAL("currentIndexChanged(int)"),self.constructINOM)
        QObject.connect(self.latitudeComboBox, SIGNAL("currentIndexChanged(int)"),self.constructINOM)
        QObject.connect(self.longitudeComboBox, SIGNAL("currentIndexChanged(int)"),self.constructINOM)
        QObject.connect(self.comboBox500k, SIGNAL("currentIndexChanged(int)"),self.constructINOM)
        QObject.connect(self.comboBox250k, SIGNAL("currentIndexChanged(int)"),self.constructINOM)
        QObject.connect(self.comboBox100k, SIGNAL("currentIndexChanged(int)"),self.constructINOM)
        QObject.connect(self.comboBox50k, SIGNAL("currentIndexChanged(int)"),self.constructINOM)
        QObject.connect(self.comboBox25k, SIGNAL("currentIndexChanged(int)"),self.constructINOM)
        QObject.connect(self.comboBox10k, SIGNAL("currentIndexChanged(int)"),self.constructINOM)
        QObject.connect(self.comboBox5k, SIGNAL("currentIndexChanged(int)"),self.constructINOM)
        QObject.connect(self.comboBox2k, SIGNAL("currentIndexChanged(int)"),self.constructINOM)
        QObject.connect(self.comboBox1k, SIGNAL("currentIndexChanged(int)"),self.constructINOM)
       
       
        
        
        
    #Disable all scale option after a given scale index
    # 0 for 1:1M
    # 1 for 1:500k
    # 2 for 1:250k
    # 3 for 1:100k
    # 4 for 1:50k
    # 5 for 1:25k
    # 6 for 1:10k
    # 7 for 1:5k
    # 8 for 1:2k
    # 9 for 1:1k        
    def disable(self, min):
        for i in range(0, len(self.listaCombos)):
            self.listaCombos[i].setEnabled(False)
        for i in range(0, min):
            self.listaCombos[i].setEnabled(True)
        

    @pyqtSlot(int)            
    def on_scaleComboBox_currentIndexChanged(self, i):
        self.disable(i)
        self.constructINOM()
        
    def constructINOM(self):
        self.inom = self.hemisphereComboBox.itemText(self.hemisphereComboBox.currentIndex())+\
                self.latitudeComboBox.itemText(self.latitudeComboBox.currentIndex())+"-"+\
                self.longitudeComboBox.itemText(self.longitudeComboBox.currentIndex())
        scale = self.scaleComboBox.currentIndex()
        if scale ==0:
            self.inomLineEdit.setText(self.inom)
            return
        if scale >=1:
            self.inom += "-"+self.comboBox500k.itemText(self.comboBox500k.currentIndex())
        if scale >=2:
            self.inom += "-"+self.comboBox250k.itemText(self.comboBox250k.currentIndex())
        if scale >=3:
            self.inom += "-"+self.comboBox100k.itemText(self.comboBox100k.currentIndex())
        if scale >=4:
            self.inom += "-"+self.comboBox50k.itemText(self.comboBox50k.currentIndex())
        if scale >=5:
            self.inom += "-"+self.comboBox25k.itemText(self.comboBox25k.currentIndex())
        if scale >=6:
            self.inom += "-"+self.comboBox10k.itemText(self.comboBox10k.currentIndex())
        if scale >=7:
            self.inom += "-"+self.comboBox5k.itemText(self.comboBox5k.currentIndex())
        if scale >=8:
            self.inom += "-"+self.comboBox2k.itemText(self.comboBox2k.currentIndex())
        if scale >=9:
            self.inom += "-"+self.comboBox1k.itemText(self.comboBox1k.currentIndex())
        self.inomLineEdit.setText(self.inom)
        
    def getInom(self):
        return self.inom