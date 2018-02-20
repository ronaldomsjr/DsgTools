# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DsgTools
                                 A QGIS plugin
 Brazilian Army Cartographic Production Tools
                              -------------------
        begin                : 2018-02-19
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Philipe Borba - Cartographic Engineer @ Brazilian Army
        email                : borba.philipe@eb.mil.br
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
import os, importlib
from collections import deque
# Qt imports
from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSlot, pyqtSignal, QSettings, Qt
from PyQt4.QtGui import QTableWidgetItem, QTableWidgetSelectionRange

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'orderedStructureWidget.ui'))

class OrderedStructureWidget(QtGui.QWidget, FORM_CLASS):

    def __init__(self, parent=None):
        """
        Initializates OrderedStructureWidget
        """
        super(OrderedStructureWidget, self).__init__(parent)
        self.setupUi(self)
        self.modulePath = None
        self.package = None
        self.args = None
    
    def instantiateWidgetItem(self):
        """
        Must be reimplemented in each child.
        """
        pass
    
    @pyqtSlot(bool, name = 'on_addRulePushButton_clicked')
    def addItem(self, parameterDict = {}):
        """
        1. Instantiate new line
        2. Add new line in the end
        """
        rowCount = self.tableWidget.rowCount()
        self.tableWidget.insertRow(rowCount)
        widget = self.instantiateWidgetItem()
        if parameterDict:
            widget.populateInterface(parameterDict)
        self.tableWidget.setCellWidget(rowCount, 0, widget)
    
    @pyqtSlot(bool)
    def on_removeRulePushButton_clicked(self):
        """
        1. Get selected row
        2. Remove selected row
        3. Update control list
        """
        selected = self.tableWidget.selectedIndexes()
        rowList = [i.row() for i in selected]
        rowList.sort(reverse=True)
        for row in rowList:
            self.tableWidget.removeRow(row)

    @pyqtSlot(bool)
    def on_moveRuleUpPushButton_clicked(self):
        """
        1. Get id range
        2. For each id in range, swap with pivot
        """
        selected = self.tableWidget.selectedIndexes()
        if selected == []:
            return
        firstItemIdx = selected[0].row() - 1
        if firstItemIdx < 0: #first item in selection, do nothing
            return
        for idx in selected:
            self.moveUp(self.tableWidget, idx.row(), 0)
        self.tableWidget.setRangeSelected(QTableWidgetSelectionRange(firstItemIdx, 0, selected[-1].row()-1, 0), True)

    
    @pyqtSlot(bool)
    def on_moveRuleDownPushButton_clicked(self):
        selected = self.tableWidget.selectedIndexes()
        if selected == []:
            return
        firstItemIdx = selected[-1].row() + 1
        if firstItemIdx > self.tableWidget.rowCount(): #last item in selection, do nothing
            return
        for idx in selected[::-1]:
            self.moveDown(self.tableWidget, idx.row(), 0)
        self.tableWidget.setRangeSelected(QTableWidgetSelectionRange(firstItemIdx-1, 0, selected[-1].row()+1, 0), True)
    
    def moveDown(self, tableWidget, rowIdx, columnIdx):
        """
        Moves item down
        """
        tableWidget.insertRow(rowIdx+2)
        tableWidget.takeItem(rowIdx, columnIdx)
        tableWidget.setCellWidget(rowIdx+2, columnIdx, tableWidget.cellWidget(rowIdx, columnIdx))
        tableWidget.removeRow(rowIdx)

    def moveUp(self, tableWidget, rowIdx, columnIdx):
        """
        Moves item up
        """
        tableWidget.insertRow(rowIdx-1)
        tableWidget.takeItem(rowIdx+1, columnIdx)
        tableWidget.setCellWidget(rowIdx-1, columnIdx, tableWidget.cellWidget(rowIdx+1, columnIdx))
        tableWidget.removeRow(rowIdx+1)

    def validate(self):
        for i in range(self.tableWidget.rowCount()):
            if not self.tableWidget.cellWidget(i, 0).validate():
                return False
        return True
    
    def invalidatedReason(self):
        msg = ''
        for i in range(self.tableWidget.rowCount()):
            if not self.tableWidget.cellWidget(i, 0).validate():
                msg += self.tr('Error for rule #{0}:\n'.format(i+1))+self.tableWidget.cellWidget(i, 0).invalidatedReason()
        return msg
    
    def populateInterface(self, parameterDict):
        """
        Populates interface with parameters from parameterDict.
        """
        for rule in parameterDict.keys():
            self.addItem(parameterDict = parameterDict)
    
    def getParameterDict(self):
        """
        Returns an OrderedDict with the number of the rule and the rule json
        """
        parameterDict = OrderedDict()
        for i in range(self.tableWidget.rowCount()):
            parameterDict['rule_#{0}'.format(i+1)] = self.tableWidget.cellWidget(i, 0).getParameterDict()
        return parameterDict

    def validateJson(self, inputJson):
        """
        Validates input json. Reimplemented in each child.
        """
        pass
