# GPS Tagger

Frustrated by the lack of commercial or FOSS offerings, I made a simple tool with Python. This allows you to get GPS coordinates from any NMEA-capable device, and add them and (as currently setup) information about utility poles, electric meters, and transformers, and save them as rows in a CSV. It would be trivial to edit the dictionaries to have whatever other information you would like captured.

Verified to work with Python 2.7 and 3.6.


Dependencies:
*************

* `Pynmea2 <https://pypi.python.org/pypi/pynmea2>`_


How to use GPS Tagger:
************************
1. Upon launch, choose where to save the resultant CSV file.
2. Input info into text boxes. Use the Get Long/Lat button to get those inputted. Note, you may have to press this a few times to get actual readings.
3. When you have filled out as much or little as you would like, press Save to save the CSV.
4. If you have more entries, press Clear to reset all text boxes, and insert a blank row in the CSV.
5. When done, press Quit.


Changelog:
**********

* v1.0 - Initial release.


TODO:
*******************

* Add KML output, also perhaps a ring of your track. $GPRMC message contains speed, which would be useful.


