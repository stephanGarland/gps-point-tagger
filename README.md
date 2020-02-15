# GPS Point Tagger

Frustrated by the lack of commercial or FOSS offerings, I made a simple tool with Python. This lets you get GPS coordinates from any NMEA-compatible device, and place them, along with whatever other attributes you'd like (currently set up for utility poles, transformers, and electric meters, but it would be trivial to change the dictionaries) into a CSV.

Additionally, there is a Secondary program that maps poles to a KML file.


##Dependencies:
*************

* `Pynmea2 <https://pypi.python.org/pypi/pynmea2>`
* `Pyserial <https://pypi.python.org/pypi/pyserial>`
* `Simplekml (for Secondary Tagger) <https://pypi.python.org/pypi/simplekml>`


##How to use GPS Tagger:
************************
1. Upon launch, choose where to save the resultant CSV file.
2. Input info into text boxes. Use the Get Long/Lat button to get those inputted. Note, you may have to press this a few times to get actual readings.
3. When you have filled out as much or little as you would like, press Save to save the CSV.
4. If you have more entries, press Clear to reset all text boxes, and insert a blank row in the CSV.
5. When done, press Quit.

##How to use Secondary GPS Tagger:
************************
1. Input a pole number/name into the Primary Pole # field.
2. Press Get Lat/Long to get coordinates for the primary pole.
3. Internal counter auto-increments; press Get Lat/Long at each secondary pole you wish to add.
4. Use Next/Prev to manually skip fields.
5. Press Save to generate a KML, saved in the script's location.
6. Press Clear All to wipe all fields, and reset the counter.

##Changelog:
**********

* v1.0 - Initial release.
* v1.1 - Re-arranged items to capture to be a more logical flow.
* v1.2 - Created Secondary program that maps poles with simplekml.
* v1.3 - Integrated launching of Secondary program into Primary



