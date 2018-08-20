# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DsgTools
                                 A QGIS plugin
 Brazilian Army Cartographic Production Tools
                              -------------------
        begin                : 2018-08-13
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
from DsgTools.core.GeometricTools.layerHandler import LayerHandler
from .validationAlgorithm import ValidationAlgorithm
from ...algRunner import AlgRunner
import processing
from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsFeature,
                       QgsDataSourceUri,
                       QgsProcessingOutputVectorLayer,
                       QgsProcessingParameterVectorLayer,
                       QgsWkbTypes,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingUtils,
                       QgsSpatialIndex,
                       QgsGeometry)

class TopologicalCleanAlgorithm(ValidationAlgorithm):
    INPUTLAYERS = 'INPUTLAYERS'
    SELECTED = 'SELECTED'
    TOLERANCE = 'TOLERANCE'
    MINAREA = 'MINAREA'
    FLAGS = 'FLAGS'
    

    def initAlgorithm(self, config):
        """
        Parameter setting.
        """
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUTLAYERS,
                self.tr('Polygon Layers'),
                QgsProcessing.TypeVectorPolygon
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SELECTED,
                self.tr('Process only selected features')
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TOLERANCE,
                self.tr('Snap radius'),
                minValue=0,
                defaultValue=1
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MINAREA,
                self.tr('Minimum area'),
                minValue=0,
                defaultValue=0.0001
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.FLAGS,
                self.tr('{0} Flags').format(self.displayName())
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        layerHandler = LayerHandler()
        algRunner = AlgRunner()

        inputLyrList = self.parameterAsLayerList(parameters, self.INPUTLAYERS, context)
        if inputLyrList is None or inputLyrList == []:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUTLAYERS))
        onlySelected = self.parameterAsBool(parameters, self.SELECTED, context)
        snap = self.parameterAsDouble(parameters, self.TOLERANCE, context)
        minArea = snap = self.parameterAsDouble(parameters, self.MINAREA, context)
        self.prepareFlagSink(parameters, inputLyrList[0], QgsWkbTypes.MultiPolygon, context)

        coverage = layerHandler.createAndPopulateUnifiedVectorLayer(inputLyrList, geomType=QgsWkbTypes.MultiPolygon, onlySelected = onlySelected, feedback=feedback, progressDelta=30)
        cleanedCoverage, error = algRunner.runClean(coverage, \
                                                    [algRunner.RMSA, algRunner.Break, algRunner.RmDupl, algRunner.RmDangle], \
                                                    context, \
                                                    returnError=True, \
                                                    snap=snap, \
                                                    minArea=minArea)
        layerHandler.updateOriginalLayersFromUnifiedLayer(inputLyrList, cleanedCoverage, feedback=feedback, progressDelta=70)
        if error:
            for feat in error.getFeatures():
                self.flagFeature(feat.geometry(), self.tr('Clean error on coverage.'))

        return {self.INPUTLAYERS : inputLyrList, self.FLAGS : self.flagSink}

    

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'topologicalclean'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Topological Clean Geometries')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Validation Tools (Topological Processes)')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'DSGTools: Validation Tools (Topological Processes)'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return TopologicalCleanAlgorithm()