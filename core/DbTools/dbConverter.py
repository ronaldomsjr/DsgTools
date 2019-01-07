# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DsgTools
                                 A QGIS plugin
 Brazilian Army Cartographic Production Tools
                              -------------------
        begin                : 2018-11-13
        git sha              : $Format:%H$
        copyright            : (C) 2018 by João P. Esperidião - Cartographic Engineer @ Brazilian Army
        email                : esperidiao.joao@eb.mil.br
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
import os, collections

from qgis.PyQt.QtCore import QObject
from qgis.core import QgsFeatureRequest, QgsProject, QgsProcessingContext, QgsProcessingMultiStepFeedback

from DsgTools.core.dsgEnums import DsgEnums
from DsgTools.core.Factories.DbFactory.dbFactory import DbFactory
from DsgTools.core.Factories.LayerLoaderFactory.layerLoaderFactory import LayerLoaderFactory
from DsgTools.core.GeometricTools.layerHandler import LayerHandler
from DsgTools.core.GeometricTools.featureHandler import FeatureHandler
from DsgTools.core.Factories.DbCreatorFactory.dbCreatorFactory import DbCreatorFactory

class DbConverter(QObject):
    """
    Class designed to manipulate the map generated by the Datasource Conversion tool.
    What it should be doing:
    1- read map;
    2- get layers ready;
        * in this step, layers are just supposed to be read, no filters applied, in order to be reused, if needed.
    3- prepare each conversion as 1 separately;
        3.a- apply filters for each layer - layer level;
        3.b- apply feature map to destination - feature level; and
    4- each successfully filtered and mapped layer will be then sent to be perpetuated to output - layer level.
    """
    def __init__(self, iface, conversionMap=None):
        """
        Class constructor.
        :param iface: (QgsInterface) QGIS interface object (for runtime operations).
        :param conversionMap: (dict) conversion map generated by Datasource Conversion tool.
        """
        super(DbConverter, self).__init__()
        self.iface = iface
        self.conversionMap = conversionMap
        self.coordinateTransformers = {}

    def getConversionCount(self, conversionMap=None):
        """
        Gets how many conversion procedures are required.
        :param conversionMap: (dict) conversion map generated by Datasource Conversion tool.
        :return: (int) number of conversion cycles.
        """
        if conversionMap is None:
            conversionMap = self.conversionMap
        count = 0
        for outMaps in conversionMap.values():
            count += len(outMaps)
        return count

    def getAllUniqueInputDb(self, conversionMap=None):
        """
        Get a list of all UNIQUE input datasources.
        :param conversionMap: (dict) conversion map generated by Datasource Conversion tool.
        :return: (list-of-str) list of all input connections necessary.
        """
        if conversionMap is None:
            conversionMap = self.conversionMap
        dsList = []
        for ds in conversionMap:
            # datasources are key to conversion map dict
            if ds not in dsList:
                dsList.append(ds)
        return dsList

    def getAllUniqueOutputDb(self, conversionMap=None):
        """
        Get a list of all UNIQUE output datasources.
        :param conversionMap: (dict) conversion map generated by Datasource Conversion tool.
        :return: (list-of-str) list of all output connections necessary.
        """
        if conversionMap is None:
            conversionMap = self.conversionMap
        dsList = []
        for ds, convMaps in conversionMap.items():
            # datasources are key to conversion map dict
            for convMap in convMaps:
                ds = convMap['outDs']
                if ds not in dsList:
                    dsList.append(ds)
        return dsList

    def getDefaultPgDb(self, hostName):
        """
        Gets a standard PostGIS database object from a given host.
        :param hostName: (str) host name.
        :return: (AbstractDb) PostGIS database object.
        """
        abstractDb = DbFactory().createDbFactory(driver=DsgEnums.DriverPostGIS)
        (host, port, user, password) = abstractDb.getServerConfiguration(hostName)
        abstractDb.connectDatabaseWithParameters(host, port, 'postgres', user, password)
        return abstractDb

    def createDataset(self, parameters):
        """
        Creates a dataset from a set of parameters.
        :param parameters: (dict) dict with all necessary parameters for a supported drivers.
        """
        if self.connectToDb(parameters=parameters) is not None:
            raise Exception(self.tr("Dataset {0} already exists.").format(parameters["db"]))
        driverName, createParam = {
            DsgEnums.DriverPostGIS : lambda : ("QPSQL", self.getDefaultPgDb(parameters['host'])),
            DsgEnums.DriverSpatiaLite : lambda : ("QSQLITE", os.path.dirname(parameters["path"])),
            DsgEnums.DriverGeopackage : lambda : ("GPKG", os.path.dirname(parameters["path"])),
            DsgEnums.DriverShapefile : lambda : ("SHP", parameters["path"])
        }[parameters['driver']]()
        dbCreator = DbCreatorFactory().createDbCreatorFactory(driverName=driverName, createParam=createParam)
        return dbCreator.createDb(
                    dbName=parameters['db'],
                    srid=parameters['srid'],
                    paramDict=parameters,
                    parentWidget=None
                )

    def checkAndCreateDatabases(self, conversionMap=None, feedback=None):
        """
        Checks conversion map for dataset creation necessity and creates it.
        :param conversionMap: (dict) conversion map generated by Datasource Conversion tool.
        :param feedback: (QgsFeedback) QGIS progress tracker.
        :return: (tuple-of-dict) a dict containing all successfully created datasets and a list with
                 all failed ones with their failing reasons.
        """
        if conversionMap is None:
            conversionMap = self.conversionMap
        success, fail = {}, {}
        for inputDb, conversionSteps in conversionMap.items():
            for conversionStep in conversionSteps:
                output = conversionStep["outDs"]
                if conversionStep["createDs"] == "True" and not (output in success or output in fail):
                    try:
                        parameters = self.parseDatasourcePath(datasource=output)
                        # filling missing parameters as required by dbCreator
                        parameters['srid'] = conversionStep['crs'].split(":")[-1]
                        parameters['isTemplateEdgv'] = True
                        parameters['version'], parameters['templateName'] = {
                            "EDGV 2.1.3" : ("2.1.3", 'template_edgv_213'),
                            "EDGV 2.1.3 F Ter" : ("FTer_2a_Ed", 'template_edgv_fter_2a_ed'),
                            "EDGV 2.1.3 Pro" : ("2.1.3 Pro", 'template_edgv_213_pro'),
                            "EDGV 3.0" : ("3.0", 'template_edgv_3')
                            # "EDGV 3.0 Pro" : ("3.0", 'template_edgv_3_pro')
                        }[conversionStep['edgv']]
                        if 'path' in parameters:
                            parameters['db'] = os.path.basename(os.path.splitext(parameters['path'])[0])
                        success[output] = self.createDataset(parameters=parameters)
                    except Exception as e:
                        fail[output] = "{0} dataset creation has failed: '{1}'".format(output, "; ".join(e.args))
        return success, fail

    def getPgParamaters(self, parameters, conn):
        """
        Retrieves Postgres connection parameters from its connection string.
        :param parameters: (dict) parameter dict to have data saved at.
        :param conn: (str) connection string.
        """
        # connection string: USER@HOST:PORT.DATABASE
        parameters['username'], part = conn.split('@')
        parameters['host'], part = part.split(':')
        parameters['port'], parameters['db'] = part.split('.')

    def parseDatasourcePath(self, datasource):
        """
        Reads and identifies datasource's driver and separates it into connection parameters.
        :param datasouce: (str) datasource path string.
        :return: (dict) a dict containing all connection parameters.
        """
        drivers = {
            'pg' : DsgEnums.DriverPostGIS,
            'sqlite' : DsgEnums.DriverSpatiaLite,
            'shp' : DsgEnums.DriverShapefile,
            'gpkg' : DsgEnums.DriverGeopackage
            }
        parameters = dict()
        driver = datasource.split(':')[0]
        conn = datasource[len(driver) + 1:]
        if driver == 'pg':
            self.getPgParamaters(parameters=parameters, conn=conn)
        else:
            parameters['path'] = conn
        parameters['driver'] = drivers[driver]
        return parameters

    def connectToPostgis(self, parameters):
        """
        Stablishes connection to a Postgis database.
        :param parameters: (dict) a dict containing all connection parameters.
        :return: (AbstractDb) returns the DSGTools database object.
        """
        user, host, port, db = parameters['username'], parameters['host'], parameters['port'], parameters['db']
        # initiate abstractDb
        abstractDb = DbFactory().createDbFactory(driver=DsgEnums.DriverPostGIS)
        # ignore all info except for the password
        _, _, _, password = abstractDb.getServerConfiguration(name=host)
        return abstractDb if abstractDb.testCredentials(host, port, db, user, password) else None

    def connectToSpatialite(self, parameters):
        """
        Stablishes connection to a SpatiaLite database.
        :param parameters: (dict) a dict containing all connection parameters.
        :return: (AbstractDb) returns the DSGTools database object.
        """
        abstractDb = None
        if os.path.exists(parameters['path']):
            abstractDb = DbFactory().createDbFactory(driver=DsgEnums.DriverSpatiaLite)
            abstractDb.connectDatabase(conn=parameters['path'])
        return abstractDb

    def connectToGeopackage(self, parameters):
        """
        Stablishes connection to a Geopackage database.
        :param parameters: (dict) a dict containing all connection parameters.
        :return: (AbstractDb) returns the DSGTools database object.
        """
        abstractDb = None
        if os.path.exists(parameters['path']):
            abstractDb = DbFactory().createDbFactory(driver=DsgEnums.DriverGeopackage)
            abstractDb.connectDatabase(conn=parameters['path'])
        return abstractDb

    def connectToShapefile(self, parameters):
        """
        Stablishes connection to a Shapefile dataset.
        :param parameters: (dict) a dict containing all connection parameters.
        :return: (AbstractDb) returns the DSGTools database object.
        """
        abstractDb = DbFactory().createDbFactory(driver=DsgEnums.DriverShapefile)
        abstractDb.connectDatabase(conn=parameters['path'])
        return abstractDb if abstractDb.getDatabaseName() != '' else None

    def connectToDb(self, parameters):
        """
        Stablishes a connection to the datasource described by a set of connection parameters.
        :param parameters: (dict) a dict containing all connection parameters.
        :return: (AbstractDb) returns the DSGTools database object.
        """
        drivers = {
            DsgEnums.DriverPostGIS : lambda : self.connectToPostgis(parameters=parameters),
            DsgEnums.DriverSpatiaLite : lambda : self.connectToSpatialite(parameters=parameters),
            DsgEnums.DriverGeopackage : lambda : self.connectToGeopackage(parameters=parameters),
            DsgEnums.DriverShapefile : lambda : self.connectToShapefile(parameters=parameters)
        }
        driver = parameters['driver']
        return drivers[driver]() if driver in drivers else None

    def getSpatialFilterBehaviour(self, spatialFilter):
        """
        Gets the spatial behaviour option from a given spatial filter set of options regarding
        modes defined in convertLayer2LayerAlgorithm.
        :param spatialFilter: (dict) spatial filter set of options.
        :return: (int) behaviour code.
        """
        predicates = {
            "Intersects" : 1,
            "Clip" : 2,
            "Buffer" : 3
        }
        return predicates[spatialFilter["filter_type"]] if spatialFilter["filter_type"] in predicates else None

    def readInputLayers(self, datasourcePath):
        """
        Reads all input datasources and return its layers.
        :param datasourcePath: (str) input's datasource path.
        :return: (dict) a map for its layers.
        """
        inputLayerMap = dict()
        parameters = self.parseDatasourcePath(datasourcePath)
        abstractDb = self.connectToDb(parameters=parameters)
        if abstractDb is None:
            return {}
        layerLoader = LayerLoaderFactory().makeLoader(self.iface, abstractDb)
        for l in list(abstractDb.listClassesWithElementsFromDatabase([]).keys()):
            vl = layerLoader.getLayerByName(l)
            inputLayerMap[vl.name()] = vl
        for l in abstractDb.listComplexClassesFromDatabase():
            vl = layerLoader.getComplexLayerByName(l)
            if vl.featureCount() > 0:
                inputLayerMap[vl.name()] = vl
        return inputLayerMap

    def readOutputLayers(self, datasourcePath):
        """
        Prepares output layers to be filled.
        :param datasourcePath: (str) output's datasource path.
        :param context: (QgsProcessingContext) environment parameters in which processing tools are used.
        :param feedback: (QgsFeedback) QGIS tool for progress tracking.
        :return: (dict) a map for output's layers.
        """
        parameters = self.parseDatasourcePath(datasourcePath)
        abstractDb = self.connectToDb(parameters=parameters)
        if abstractDb is None:
            return {}
        layerLoader = LayerLoaderFactory().makeLoader(self.iface, abstractDb)
        outputLayerMap = dict()
        for  l in abstractDb.listGeomClassesFromDatabase([]):
            vl = layerLoader.getLayerByName(l)
            outputLayerMap[vl.name()] = vl
        for l in abstractDb.listComplexClassesFromDatabase():
            vl = layerLoader.getComplexLayerByName(l)
            outputLayerMap[vl.name()] = vl
        return outputLayerMap

    def prepareInputLayers(self, conversionMap=None, context=None, feedback=None):
        """
        Prepare layers for each translation unit (step) to be executed (e.g. applies filters).
        :param conversionMap: (dict) conversion map generated by Datasource Conversion tool.
        :param context: (QgsProcessingContext) environment parameters in which processing tools are used.
        :param feedback: (QgsFeedback) QGIS tool for progress tracking.
        :return: (dict) map of layers to have its feature mapped to output format.
        """
        if conversionMap is None:
            conversionMap = self.conversionMap
        inputLayersMap = dict()
        allInputLayers = self.readInputLayers(conversionMap=conversionMap)
        lh = LayerHandler()
        context = context if context is not None else QgsProcessingContext()
        if feedback is not None:
            multiStepFeedback = QgsProcessingMultiStepFeedback(len(conversionMap), feedback)
            currentInputStep = 0
        else:
            multiStepFeedback = None
        for inputDb, conversionSteps in conversionMap.items():
            inputLayers = allInputLayers[inputDb]
            if multiStepFeedback is not None:
                multiStepFeedback.setCurrentStep(currentInputStep)
                currentInputStep += 1
            for conversionStep in conversionSteps:
                filters = conversionStep["filter"]
                fanOut = conversionStep['spatialFanOut'] == 'True'
                # conversion map may be empty, in that case no filters should be applied
                # e.g. all layers to be translated
                layers = filters["layer"] if filters["layer"] else inputLayers
                if multiStepFeedback is not None:
                    currentFeedback = QgsProcessingMultiStepFeedback(len(layers), multiStepFeedback)
                    layerStep = 0
                # spatial filtering behaviour is set based on the modes defined in convertLayer2LayerAlgorithm
                behaviour = self.getSpatialFilterBehaviour(filters["spatial_filter"])
                spatialFilterlLayer = QgsProject.instance().mapLayersByName(filters["spatial_filter"]["layer_name"])
                spatialFilterlLayer = spatialFilterlLayer[0] if spatialFilterlLayer != [] else None
                if filters["spatial_filter"]["layer_filter"]:
                    spatialFilterlLayer = lh.filterByExpression(layer=spatialFilterlLayer,\
                                                            expression=filters["spatial_filter"]["layer_filter"],\
                                                            context=context, feedback=feedback)
                key = "{0}::{1}".format(inputDb, conversionStep["outDs"])
                if key not in inputLayersMap:
                    inputLayersMap[key] = {}
                for layer in layers:
                    if multiStepFeedback is not None:
                        multiStepFeedback.setCurrentStep(layerStep)
                        layerStep += 1
                    translatedLayer = lh.prepareConversion(
                                        inputLyr=inputLayers[layer],
                                        context=context,
                                        inputExpression=filters["layer_filter"][layer] if layer in filters["layer_filter"] else None,
                                        filterLyr=spatialFilterlLayer,
                                        behavior=behaviour,
                                        conversionMap=conversionStep,
                                        feedback=feedback
                                        )
                    # if fanOut:
                    #     # self.fanOut(***)
                    #     pass
                    # else:
                    translatedLayer.startEditing()
                    fields = [f.name() for f in inputLayers[layer].fields()]
                    removeFields = [translatedLayer.fields().indexFromName(f.name())\
                                    for f in translatedLayer.fields() if f.name() not in fields]
                    translatedLayer.deleteAttributes(removeFields)
                    translatedLayer.updateFields()
                    translatedLayer.commitChanges()
                    inputLayersMap[key][layer] = translatedLayer
        return inputLayersMap

    def mapFeatures(self, layersMap, outputMapLayer, featureConversionMap=None):
        """
        Maps features from a given set of layers to a different set of layers (including attributes).
        :param layersMap: (dict) map of layers to be translated.
        :param outputMapLayer: (dict) map of layers to be filled.
        :param featureConversionMap: (dict) map of features based on given input.
        :return: (dict) map of (list-of-QgsFeature) features to be added to a (str) layer.
        """
        if featureConversionMap is not None:
            # do the conversion in here using the map - NOT YET SUPPORTED
            pass
        else:
            featuresMap = collections.defaultdict(set)
            lh = LayerHandler()
            fh = FeatureHandler()
            ctMap = {}
            for layer, vl in layersMap.items():
                if vl.featureCount() == 0:
                    continue
                outuputLayer = outputMapLayer[layer]
                k = "{0}->{1}".format(vl.crs().authid(), outuputLayer.crs().authid())
                if k not in self.coordinateTransformers:
                    self.coordinateTransformers[k] = lh.getCoordinateTransformer(inputLyr=vl, outputLyr=outuputLayer)
                coordinateTransformer = self.coordinateTransformers[k]
                param = lh.getDestinationParameters(vl)
                for feature in vl.getFeatures(QgsFeatureRequest()):
                    featuresMap[layer] |= fh.handleConvertedFeature(
                                                feat=feature,
                                                lyr=outuputLayer,
                                                parameterDict=param,
                                                coordinateTransformer=coordinateTransformer
                                                )
            return featuresMap

    def fanOut(self, inputLayers, preparedLayers, referenceLayer, fanOutFieldName, context=None, feedback=None):
        """
        
        """
        idx = referenceLayer.fields().indexFromName(fanOutFieldName)
        reference = referenceLayer.uniqueValues(idx)
        fannedOutLayers = {}
        lh = LayerHandler()
        context = context if not context is None else QgsProcessingContext()
        for layer, featuresList in preparedLayers.items():
            vl = preparedLayers[layer]
            vl.startEditing()
            fields = [f.name() for f in inputLayers[layer].fields()]
            removeFields = [vl.fields().indexFromName(f.name()) for f in vl.fields() if f.name() not in fields]
            for value in reference:
                if value not in fannedOutLayers:
                    fannedOutLayers[value] = {}
                fannedOut = lh.filterByExpression(layer=vl, expression='{0} = {1}'.format(fanOutFieldName, value),
                                        context=context, feedback=feedback)
                vl.deleteAttributes(removeFields)
                vl.updateFields()
                vl.commitChanges()
                if fannedOut.featureCount() > 0:
                    fannedOutLayers[value][layer] = fannedOut
        return fannedOutLayers

    def removeExtraFields(self, ):
        """
        
        """
        for layer, featuresList in preparedLayers.items():
            vl = preparedLayers[layer]
            vl.startEditing()
            fields = [f.name() for f in inputLayers[layer].fields()]
            removeFields = [vl.fields().indexFromName(f.name()) for f in vl.fields() if f.name() not in fields]
            vl.deleteAttributes(removeFields)
            vl.updateFields()
            vl.commitChanges()

    def loadToOuput(self, layersMap, outputLayers, conversionMap=None, featureConversionMap=None):
        """
        
        """
        if conversionMap is None:
            conversionMap = self.conversionMap
        for layer, featureList in self.mapFeatures(layersMap, outputLayers, featureConversionMap).items():
            outputLayers[layer].startEditing()
            outputLayers[layer].addFeatures(featureList)
            outputLayers[layer].commitChanges()
            outputLayers[layer].updateExtents()

    def convertFromMap(self, conversionMap=None, featureConversionMap=None):
        """
        Converts all datasets from a conversion map.
        :param conversionMap: (dict) conversion map generated by Datasource Conversion tool.
        :param featureConversionMap: (dict) map of features based on given input.
        :return: (tuple) successfull and failed translations lists.
        """
        print("BAM! CONVERTEU!")
        status = True
        log = "CONVERTEU TUDO!"
        return status, log
