from toolTip import ToolTip
from qgis.core import QgsDistanceArea, QgsCoordinateReferenceSystem
from qgis.core import QgsProject 
from PyQt4.QtGui import QToolTip, QColor, QFont
from PyQt4.QtCore import QPoint

class DistanceToolTip(ToolTip):
	def __init__(self, iface):
		super(DistanceToolTip, self).__init__(iface)
		self.iface = iface
		self.canvas = iface.mapCanvas()      
		self.last_distance = 0  
		self.showing = False	
			

	def calculateDistance(self, p1, p2):
		distance = QgsDistanceArea()
		distance.setSourceCrs(self.iface.activeLayer().crs())
		distance.setEllipsoidalMode(True)
		# Sirgas 2000
		distance.setEllipsoid('GRS1980')
		m = distance.measureLine(p1, p2) 
		return m

	def canvasMoveEvent(self, last_p, current_p):
		m =  int(self.calculateDistance(last_p, current_p))		
		
		if self.showing:
			if m != self.last_distance:
				color = 'red'
				if m >= 4:
					color = 'green'				
				txt = "<p style='color:{color}'><b>{distance}</b></p>".format(color=color, distance=str(m))
				super(DistanceToolTip, self).show(txt, current_p)		
				self.last_distance = m  
		else:
			if m > 1:
				color = 'red'
				if m >= 4:
					color = 'green'				
				txt = "<p style='color:{color}'><b>{distance}</b></p>".format(color=color, distance=str(m))
				super(DistanceToolTip, self).show(txt, current_p)		  	
				self.last_distance = m
				self.showing = True

   	def deactivate(self):
   		super(DistanceToolTip, self).deactivate()
   		self.showing = False