Frustrated by the lack of commercial or FOSS offerings, I made a simple tool with Python. This lets you get GPS coordinates from any NMEA-compatible device, and place them, along with whatever other attributes you'd like (currently set up for utility poles, transformers, and electric meters, but it would be trivial to change the dictionaries) into a CSV.


Dependencies:
*************

* `Pynmea2 <https://pypi.python.org/pypi/pynmea2>`_
* `Pyserial <https://pypi.python.org/pypi/pyserial>`_


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


