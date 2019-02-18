# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DsgTools
                                 A QGIS plugin
 Brazilian Army Cartographic Production Tools
                              -------------------
        begin                : 2015-10-21
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Philipe Borba - Cartographic Engineer @ Brazilian Army
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

# DsgTools imports
from ..SqlFactory.sqlGeneratorFactory import SqlGeneratorFactory
from DsgTools.core.dsgEnums import DsgEnums

from qgis.PyQt.QtCore import QSettings, pyqtSignal, QObject

class AbstractDb(QObject):
    def __init__(self, parameters=None):
        """
        Class constructor.
        :param parameters: (dict) connection parameters map.
        """
        super(AbstractDb, self).__init__()
        parameters = parameters if parameters is not None else dict()
        if self.validateConnection(parameters):
            self.connect(parameters)
            self.gen = SqlGeneratorFactory.createSqlGenerator(self.parameters['driver'])
        else:
            self.gen = None
        self.parameters = parameters

    def validateConnection(self, parameters):
        """
        Checks if connection parameters actually leads to a valid dataset.
        :param parameters: (dict) connection parameters map to be validated.
        :return: (bool) parameters validity status.
        """
        # to be reimplemented into each supported driver
        return False

    def connect(self, parameters):
        """
        Tries to connect to a dataset from a given set of parameters.
        :param parameters: (dict) connection parameters map.
        """
        if self.isConnected():
            self.disconnect()
        # do stuff now

    def isConnected(self):
        """
        Verifies if a dataset is current being read by this object.
        :return: (bool) object connection status.
        """
        return False

    def disconnect(self):
        """
        Closes any open dataset connection.
        """
        if self.isConnected():
            # do stuff here
            pass

    def driverName(self):
        """
        Current connection's driver name.
        :return: (str) driver name.
        """
        return "NoDriver"

    def driver(self):
        """
        Gets current dataset's driver ID.
        :return: (int) driver ID.
        """
        return DsgEnums.NoDriver

    def layersWithElements(self):
        """
        Gets all non-empty layers from current loaded dataset.
        :return: (dict) map of layers to its feature count.
        """
        return dict()

    def srid(self):
        """
        Gets SRID from the first geometric layer found as dataset representative.
        :return: (int) dataset (allegedly) SRID.
        """
        return 0

    def model(self):
        """
        Identifies current dataset model (EDGV, MGCP, etc).
        :return: (str) current dataset's model.
        """
        return self.tr("Undefined") # equivalent to "Non-EDGV"

    def structure(self):
        """
        Identifies current dataset structure accordingly to EDGV model.
        :return: (dict) a map for dataset structure.
        """
        return dict()

    def valueMap(self, layerName=None):
        """
        Gets the value from all layers (or a given layer).
        """
        return { layerName : dict() }

    def layerByName(self, layerName):
        """
        Gets a layer from selected dataset. If not found, an empty layer is returned.
        :return: (QgsVectorLayer) vector layer from dataset.
        """
        return QgsVectorLayer()
