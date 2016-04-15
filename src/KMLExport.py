from PySide import QtCore, QtGui
from xml.sax.saxutils import escape

class KMLExport:
   def __init__(self, analyzer):
      self.analyzer = analyzer

   def save(self, log_id):

      kml_filename, _ = QtGui.QFileDialog.getSaveFileName(
#         parent=widget,
         caption="Save PNG file",
         filter="All files (*.*);;KML (*.kml)",
         selectedFilter="KML (*.kml)"
      )

      if kml_filename is None:
        return

      uilog = self.analyzer.extract_ui_by_log_id(log_id)
      gpslog = self.analyzer.extract_gps_by_log_id(log_id)
      data = self.merge_ui_gps_log(uilog, gpslog)

      ui_info = self.analyzer.extract_info_by_log_id(log_id)
      info = ui_info["model"] + " - " + ui_info["battery"] + " (" + ui_info["date"] + ")"

      try:
         fp = open(kml_filename, "w")
         fp.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
         fp.write('<kml xmlns="http://earth.google.com/kml/2.2">\n')
         fp.write('   <Document>\n')
         fp.write('      <name>VBar Control flkight path</name>\n')
         fp.write('      <description>\n')
         fp.write('      </description>\n')
         fp.write('      <open>0</open>\n')
         fp.write('      <Folder>\n')
         fp.write('         <name>Max height</name>\n')
         fp.write('         <open>0</open>\n')
         fp.write('         <visibility>1</visibility>\n')
         fp.write('         <Placemark>\n')
         fp.write('            <name>Height</name>\n')
         fp.write('            <Style>\n')
         fp.write('               <LineStyle>\n')
         fp.write('                  <color>99ffaa00</color>\n')
         fp.write('                  <width>3</width>\n')
         fp.write('               </LineStyle>\n')
         fp.write('               <PolyStyle>\n')
         fp.write('                  <color>99ffaa00</color>\n')
         fp.write('                  <colorMode>normal</colorMode>\n')
         fp.write('               </PolyStyle>\n')
         fp.write('            </Style>\n')
         fp.write('            <LineString>\n')
         fp.write('               <tessellate>0</tessellate>')
         fp.write('               <altitudeMode>absolute</altitudeMode>\n')
         fp.write('               <coordinates>\n')
         for row in data:
            fp.write("                  " + str(row["longitude"]) + "," + str(row["latitude"]) + "," + str(row["height"]) + "\n")
         fp.write('               </coordinates>\n')
         fp.write('            </LineString>\n')
         fp.write('         </Placemark>\n')
         fp.write('         <Folder>\n')
         fp.write('            <name>Details Speed (GPS) km/h</name>\n')
         fp.write('            <open>0</open>\n')
         fp.write('            <visibility>1</visibility>\n')

         max_speed_index = 0
         max_height_index = 0
         max_speed = 0
         max_height = 0
         for i in xrange(len(data)):
            row = data[i]
            if row["height"] > max_height:
               max_height_index = i
               max_height = row["height"]
            if row["speed"] > max_speed:
               max_speed_index = i
               max_speed = row["speed"]

         i = 0
         for row in data:
            fp.write('            <Placemark>\n')
            if i == 0:
               fp.write('              <name>' + escape(info) + '</name>\n')
            elif i == max_speed_index:
               fp.write('              <name>Max speed: ' + str(row["speed"]) + 'kmh</name>\n')
            elif i == max_height_index:
               fp.write('              <name>Max height: ' + str(row["height"]) + 'm</name>\n')
            fp.write('              <description><![CDATA[<TABLE><TR><TD width=160>Sec: ' + str(float(int(row["sec"] * 10)) / 10 ) + '<br><hr><b>Speed: ' + str(row["speed"]) + 'kmh </b><br>Height: ' + str(row["height"]) + 'm<br><hr>Voltage: ' + str(row["voltage"]) + 'V<br>Current: ' + str(row["current"]) + 'A<br>Power: ' + str(row["current"] * row["voltage"]) + 'W<br>Headspeed ' + str(row["headspeed"]) +'rpm<br>PWM: ' + str(row["pwm"]) + '%</TD></TR></TABLE>]]></description>\n')
            fp.write('              <Style>\n')
            fp.write('                <IconStyle>\n')
            icon_color = 255.0 - (float(row["speed"]))
            if icon_color < 0:
               icon_color = 0
            icon_color="ff00" + hex(int(icon_color))[2:] + "ff"
            fp.write('                  <color>' + icon_color+ '</color>\n')
            fp.write('                  <scale>0.50</scale>\n')
            fp.write('                  <Icon>\n')
            fp.write('                    <href>http://maps.google.com/mapfiles/kml/shapes/target.png</href>\n')
            fp.write('                  </Icon>\n')
            fp.write('                </IconStyle>\n')
            fp.write('                <LabelStyle>\n')
            fp.write('                  <color>ff00ff00</color>\n')
            fp.write('                  <scale>1.2</scale>\n')
            fp.write('                </LabelStyle>\n')
            fp.write('              </Style>\n')
            fp.write('              <Point>\n')
            fp.write('                <extrude>1</extrude>\n')
            fp.write('                <altitudeMode>absolute</altitudeMode>\n')
            fp.write('                <coordinates>' + str(row["longitude"]) + "," + str(row["latitude"]) + "," + str(row["height"]) +'</coordinates>\n')
            fp.write('              </Point>\n')
            fp.write('            </Placemark>\n')
            i += 1



         fp.write('         </Folder>\n')
         fp.write('      </Folder>\n')
         fp.write('   </Document>\n')
         fp.write('</kml>\n')

      finally:
         fp.close()


   def merge_ui_gps_log(self, uilog, gpslog):
      data = uilog["data"]
      for j in xrange(len(uilog["data"])):
         row = uilog["data"][j]

         if gpslog is not None:
            timestamp_ui_row = row["sec"] + uilog["start"]
            nearest_timestamp = None
            nearest_index = -1
            for i in xrange(len(gpslog["data"])):
               row_gps = gpslog["data"][i]
               timestamp_gps_row = row_gps["sec"] + gpslog["start"]
               if nearest_index == -1 or abs(timestamp_ui_row - timestamp_gps_row) < nearest_timestamp:
                  nearest_timestamp = abs(timestamp_ui_row - timestamp_gps_row)
                  nearest_index = i
            data[j]["height"] = gpslog["data"][nearest_index]["height"]
            data[j]["speed"] = gpslog["data"][nearest_index]["speed"]
            data[j]["longitude"] = gpslog["data"][nearest_index]["longitude"]
            data[j]["latitude"] = gpslog["data"][nearest_index]["latitude"]
      return data
