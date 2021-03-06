# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QuickGeocoder
                                 A QGIS plugin
 Geocode and reverse geocode using Bing Maps API
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2019-12-09
        copyright            : (C) 2019 by Diego Benincasa
        email                : diego@diegobenincasa.com
        git sha              : $Format:%H$
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QProgressBar, QPushButton, QProgressDialog
# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the DockWidget
from .geocoder_dockwidget import QuickGeocoderDockWidget
import os.path

# Import QGIS classes
from qgis.core import QgsProject, Qgis, QgsMapLayerProxyModel, QgsSettings, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPointXY, QgsField, QgsGeometry, QgsVectorLayer, QgsFeature, QgsTask, QgsApplication, QgsTaskManager
from qgis.gui import QgsMessageBar

# Import Geopy, the geocoding library
import os, sys
#print(os.path.join(os.path.dirname(os.path.abspath(__file__)),'dependencies'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),'dependencies'))
from geopy.geocoders import Bing

# CSV parsing lib
import csv

geopy_geocoders = [
    'ArcGIS',
    'AzureMaps',
    'Baidu',
    'BANFrance',
    'Bing',
    'DataBC',
    'GeocodeEarth',
    'GeocodeFarm',
    'Geolake',
    'GeoNames',
    'GoogleV3',
    'HERE',
    'IGNFrance',
    'LiveAddress',
    'MapBox',
    'OpenCage',
    'OpenMapQuest',
    'Nominatim',
    'Pelias',
    'Photon',
    'PickPoint',
    'TomTom',
    'What3Words',
    'Yandex'
]


class QuickGeocoder:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """

        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'QuickGeocoder_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&QuickGeocoder')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'QuickGeocoder')
        self.toolbar.setObjectName(u'QuickGeocoder')

        #print "** INITIALIZING QuickGeocoder"

        self.pluginIsActive = False
        self.dockwidget = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('QuickGeocoder', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToWebMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/QuickGeocoder/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'QuickGeocoder'),
            callback=self.run,
            parent=self.iface.mainWindow())

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING QuickGeocoder"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD QuickGeocoder"

        for action in self.actions:
            self.iface.removePluginWebMenu(
                self.tr(u'&QuickGeocoder'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""
        global geopy_geocoders

        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING QuickGeocoder"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = QuickGeocoderDockWidget()

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

            # load layers to layers combo box
            self.dockwidget.layersCombo.setFilters(QgsMapLayerProxyModel.PointLayer)

            # make signal/slot connections
            self.dockwidget.geocodeButton.clicked.connect(self.checkOperation)
            self.dockwidget.serviceCombo.currentTextChanged.connect(self.serviceChanged)

            self.dockwidget.apiKeyEdit.textChanged.connect(self.setApiKey)
            self.dockwidget.param1Edit.textChanged.connect(self.setParam1)
            self.dockwidget.param2Edit.textChanged.connect(self.setParam2)

            self.dockwidget.inputFileWidget.fileChanged.connect(self.inputFileSelected)
            
            self.dockwidget.serviceCombo.addItems(geopy_geocoders)
            self.dockwidget.serviceCombo.setCurrentText('Bing')

    def setParam1(self, p):
        service = self.dockwidget.serviceCombo.text()
        s = QgsSettings()
        if service == 'HERE':
            s.setValue("QuickGeocoder/" + sv + "/appid", p)

        elif service == 'Pelias':
            s.setValue("QuickGeocoder/" + sv + "/domain", p)

        elif service == 'LiveAddress':
            s.setValue("QuickGeocoder/" + sv + "/auth_id", p)

        else:
            pass

    def setParam2(self, p):
        service = self.dockwidget.serviceCombo.text()
        s = QgsSettings()
        
        if service == 'HERE':
            s.setValue("QuickGeocoder/" + sv + "/appcode", p)

        elif service == 'LiveAddress':
            s.setValue("QuickGeocoder/" + sv + "/auth_token", p)

        else:
            pass

    def serviceChanged(self, sv):
        s = QgsSettings()
        apiKey = s.value("QuickGeocoder/" + sv + "/apiKey")
        self.dockwidget.apiKeyEdit.setText(apiKey)
        if sv in ['ArcGIS', 'BANFrance','DataBC', 'GeoNames', 'Nominatim', 'Photon']:
            apiKey = s.value("QuickGeocoder/" + sv + "/apiKey")
            self.dockwidget.apiKeyEdit.setEnabled(False)
            self.dockwidget.apiKeyLabel.setEnabled(False)
            self.dockwidget.param1Edit.setVisible(False)
            self.dockwidget.param1Label.setVisible(False)
            self.dockwidget.param2Edit.setVisible(False)
            self.dockwidget.param2Label.setVisible(False)
        
        elif sv == 'HERE':
            apiKey = s.value("QuickGeocoder/" + sv + "/apiKey")
            appid = s.value("QuickGeocoder/" + sv + "/appid")
            appcode = s.value("QuickGeocoder/" + sv + "/appcode")

            self.dockwidget.apiKeyEdit.setEnabled(False)
            self.dockwidget.apiKeyLabel.setEnabled(False)
            self.dockwidget.param1Edit.setVisible(True)
            self.dockwidget.param1Label.setVisible(True)
            self.dockwidget.param2Edit.setVisible(True)
            self.dockwidget.param2Label.setVisible(True)
            
            self.dockwidget.param1Label.setText('App ID')
            self.dockwidget.param2Label.setText('App Code')
            self.dockwidget.param1Edit.setText(appid)
            self.dockwidget.param2Edit.setText(appcode)

        elif sv == 'Pelias':
            apiKey = s.value("QuickGeocoder/" + sv + "/apiKey")
            dom = s.value("QuickGeocoder/" + sv + "/domain")
            
            self.dockwidget.apiKeyEdit.setEnabled(False)
            self.dockwidget.apiKeyLabel.setEnabled(False)
            self.dockwidget.param1Edit.setVisible(True)
            self.dockwidget.param1Label.setVisible(True)
            self.dockwidget.param2Edit.setVisible(False)
            self.dockwidget.param2Label.setVisible(False)
            
            self.dockwidget.param1Label.setText('Domain')
            self.dockwidget.param1Edit.setText(dom)

        elif sv == 'LiveAddress':
            apiKey = s.value("QuickGeocoder/" + sv + "/apiKey")
            authid = s.value("QuickGeocoder/" + sv + "/auth_id")
            authtoken = s.value("QuickGeocoder/" + sv + "/auth_token")

            self.dockwidget.apiKeyEdit.setEnabled(False)
            self.dockwidget.apiKeyLabel.setEnabled(False)
            self.dockwidget.param1Edit.setVisible(True)
            self.dockwidget.param1Label.setVisible(True)
            self.dockwidget.param2Edit.setVisible(True)
            self.dockwidget.param2Label.setVisible(True)
            
            self.dockwidget.param1Label.setText('Auth ID')
            self.dockwidget.param2Label.setText('Auth Token')
            self.dockwidget.param1Edit.setText(authid)
            self.dockwidget.param2Edit.setText(authtoken)

        else:
            apiKey = s.value("QuickGeocoder/" + sv + "/apiKey")

            self.dockwidget.apiKeyEdit.setEnabled(True)
            self.dockwidget.apiKeyLabel.setEnabled(True)
            self.dockwidget.param1Edit.setVisible(False)
            self.dockwidget.param1Label.setVisible(False)
            self.dockwidget.param2Edit.setVisible(False)
            self.dockwidget.param2Label.setVisible(False)

    def inputFileSelected(self, f):
        outFile = os.path.join(os.path.dirname(os.path.abspath(f)),'errors.csv')
        self.dockwidget.errorOutputFileWidget.setFilePath(outFile)

        with open(f) as csv_file:
            header = csv_file.readline()
            header = header.replace('\n','')
            header = header.split(';')

            self.dockwidget.addressCombo.clear()
            self.dockwidget.neighborhoodCombo.clear()
            self.dockwidget.cityCombo.clear()
            self.dockwidget.stateCombo.clear()
            self.dockwidget.countryCombo.clear()

            self.dockwidget.addressCombo.addItems(header)
            self.dockwidget.neighborhoodCombo.addItems(header)
            self.dockwidget.cityCombo.addItems(header)
            self.dockwidget.stateCombo.addItems(header)
            self.dockwidget.countryCombo.addItems(header)

            self.dockwidget.neighborhoodCombo.addItem('-- NOT AVAILABLE --')
            self.dockwidget.cityCombo.addItem('-- NOT AVAILABLE --')
            self.dockwidget.stateCombo.addItem('-- NOT AVAILABLE --')
            self.dockwidget.countryCombo.addItem('-- NOT AVAILABLE --')
        
            self.dockwidget.fullAddressCombo.addItems(header)


    def setApiKey(self, k):
        service = self.dockwidget.serviceCombo.currentText()
        s = QgsSettings()
        s.setValue("QuickGeocoder/" + service + "/apiKey", k)

        # apiKey = k

    def checkOperation(self):
        if self.dockwidget.tabWidget.currentIndex() == 0:
            self.doGeocode()
        else:
            self.doReverseGeocode()
    
    def getGeocoder(self):
        global geopy_geocoders

        apiKey = self.dockwidget.apiKeyEdit.text()

        service = self.dockwidget.serviceCombo.text()

        if service in ['ArcGIS', 'BANFrance','DataBC', 'GeoNames', 'Nominatim', 'Photon']:
            # geocoder = geopy_geocoders[service]()
            geocoder = eval(service + '()')
        elif service == 'HERE':
            appid = self.dockwidget.param1Edit.text()
            appcode = self.dockwidget.param2Edit.text()
            # geocoder = geopy_geocoders[service](app_id=appid, app_code=appcode)
            geocoder = eval(service + "(app_id='" + appid + "', app_code='" + appcode + "')")
        elif service == 'Pelias':
            dom = self.dockwidget.param1Edit.text()
            # geocoder = geopy_geocoders[service](domain=dom, api_key=apiKey)
            geocoder = eval(service + "(domain='" + dom + ", api_key='" + apiKey + "')")
        elif service == 'LiveAddress':
            authid = self.dockwidget.param1Edit.text()
            authtoken = self.dockwidget.param2Edit.text()
            # geocoder = geopy_geocoders[service](auth_id=authid, auth_token=authtoken)
            geocoder = eval(service + "(auth_id='" + authid + ", auth_token='" + authtoken + "')")
        else:
            # geocoder = geopy_geocoders[service](apiKey)
            geocoder = eval(service + "('" + apiKey + "')")

        return geocoder

    def doReverseGeocode(self):
        apiKey = self.dockwidget.apiKeyEdit.text()

        if apiKey is None or apiKey == '':
            self.iface.messageBar().pushMessage("Erro", "API key not defined!", level=Qgis.Critical, duration=5)
            return

        progressDialog = QProgressDialog()
        progressDialog.setMinimum(0)
        progressDialog.setCancelButtonText('Cancel')
        progressDialog.setWindowModality(Qt.WindowModal)
        progressDialog.setMinimumWidth(300)
        progressDialog.show()

        layer = self.dockwidget.layersCombo.currentLayer()
        inputCRS = layer.crs()
        destCRS = QgsCoordinateReferenceSystem.fromEpsgId(4326)
        transformer = QgsCoordinateTransform(inputCRS, destCRS, QgsProject.instance())
        
        totalFeatures = layer.featureCount()

        progressDialog.setMaximum(totalFeatures)
        progressDialog.setWindowTitle('Geocoding ' + str(totalFeatures) + ' features...')

        layer.startEditing()
        novoAttr = QgsField(self.dockwidget.newAttributeEdit.text(), QVariant.String)
        layer.dataProvider().addAttributes([novoAttr])
        layer.updateFields()
        addrIdx = len(layer.fields()) - 1
        
        geolocator = self.getGeocoder()

        counter = 0
        for f in layer.getFeatures():
            oldPoint = f.geometry().asPoint()
            newPoint = transformer.transform(oldPoint)
            address, (latitude, longitude) = geolocator.reverse(str(newPoint.y()) + ', ' + str(newPoint.x()))

            layer.changeAttributeValue(f.id(), addrIdx, address)
            counter += 1
            progressDialog.setValue(counter)
            print(address, latitude, longitude)

        layer.commitChanges()
        
        self.iface.messageBar().pushMessage("Success", "Button clicked correctly!", level=Qgis.Success, duration=5)

    def doGeocode(self):
        global apiKey

        if apiKey is None or apiKey == '':
            self.iface.messageBar().pushMessage("Erro", "API key not defined!", level=Qgis.Critical, duration=5)
            return
        
        progressDialog = QProgressDialog()
        progressDialog.setMinimum(0)
        progressDialog.setCancelButtonText('Cancel')
        progressDialog.setWindowModality(Qt.WindowModal)
        progressDialog.setMinimumWidth(300)
        progressDialog.show()
        
        inputFile = self.dockwidget.inputFileWidget.filePath()
        errorFile = self.dockwidget.errorOutputFileWidget.filePath()

        addrPartsIdxs = []
        inputAddrList = []

        if self.dockwidget.toolBox.currentIndex() == 0:
            addrPartsIdxs.append(self.dockwidget.addressCombo.currentIndex())
            if self.dockwidget.neighborhoodCombo.currentIndex() != self.dockwidget.neighborhoodCombo.count() - 1:
                addrPartsIdxs.append(self.dockwidget.neighborhoodCombo.currentIndex())
            if self.dockwidget.cityCombo.currentIndex() != self.dockwidget.cityCombo.count() - 1:
                addrPartsIdxs.append(self.dockwidget.cityCombo.currentIndex())
            if self.dockwidget.stateCombo.currentIndex() != self.dockwidget.stateCombo.count() - 1:
                addrPartsIdxs.append(self.dockwidget.stateCombo.currentIndex())
            if self.dockwidget.countryCombo.currentIndex() != self.dockwidget.countryCombo.count() - 1:
                addrPartsIdxs.append(self.dockwidget.countryCombo.currentIndex())
        
        else:
            addrPartsIdxs.append(self.dockwidget.fullAddressCombo.currentIndex())

        with open(inputFile, 'r') as iFile:
            csv_reader = csv.reader(iFile, delimiter=';')
            lineCount = 0

            for row in csv_reader:
                if lineCount == 0:
                    lineCount += 1
                else:
                    addr = ', '.join(row[i] for i in addrPartsIdxs)
                    addr = '"' + addr + '"'
                    inputAddrList.append(addr)

        # geolocator = Bing(api_key=apiKey)
        geolocator = self.getGeocoder()

        temp = QgsVectorLayer("Point?crs=epsg:4326", "Geocoding output", "memory")
        temp_data = temp.dataProvider()
        temp.startEditing()

        fl = open(inputFile, 'r')
        fo = open(errorFile, 'w')

        header = fl.readline()
        header = header.replace('\n','')
        header = header.split(';')
        temp_data.addAttributes([QgsField(header[i],QVariant.String) for i in range(len(header))])
        temp_data.addAttributes([QgsField('addr_geocoded', QVariant.String)])
        temp.updateFields()

        fo.writelines(';'.join(header))

        totalAddresses = len(inputAddrList)
        progressDialog.setWindowTitle('Geocoding ' + str(totalAddresses) + ' addresses...')
        progressDialog.setMaximum(totalAddresses)

        counter = 2
        for a in inputAddrList:
            if progressDialog.wasCanceled():
                self.iface.messageBar().clearWidgets()
                self.iface.messageBar().pushMessage("Geocoding canceled", 'Saved ' + str(counter-2) + ' addresses.', level=Qgis.Info, duration=5)
                locked = 0
                break
            address, (latitude, longitude) = geolocator.reverse(a)
            print(counter, address, latitude, longitude)
            counter += 1

            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(longitude, latitude)))
            attributes = fl.readline().replace('\n','').split(';')
            attributes.append(address)
            feat.setAttributes(attributes)
            temp.addFeatures([feat])
            temp.updateExtents()

            # progress.setValue(counter-2)
            progressDialog.setValue(counter-2)
            self.iface.mainWindow().repaint()

        temp.commitChanges()
        
        QgsProject.instance().addMapLayer(temp)
        
        self.iface.messageBar().clearWidgets()
        self.iface.messageBar().pushMessage("Success", 'Geocoded ' + str(totalAddresses) + ' addresses!', level=Qgis.Success, duration=5)
