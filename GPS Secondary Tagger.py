# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# GPS Secondary Tagger.py
#
# Created on: 2017-08-23
# Stephan Garland
# stephan.marc.garland@gmail.com
#
# Captures NMEA outputs from GPS card and allows user comments to be added
# Records Long/Lat and comments in a table, and writes them to a CSV

import base64
from datetime import date
import os
import serial
import serial.tools.list_ports as test_ser
import simplekml
import pynmea2 as gps
from sys import version_info
import webbrowser

try:
    import tkinter as tk  # Python 3.x
    from tkinter import messagebox as tkMsg
    from tkinter.filedialog import asksaveasfilename
except ImportError:  # Python 2.x
    import Tkinter as tk
    import tkMessageBox as tkMsg
    from tkFileDialog import asksaveasfilename

if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
else:
    root = tk.Tk()
    root.deiconify()


ser = serial.Serial()
ser.baudrate = 9600
ser.timeout = 1

# Feel free to add more here if you need them
fields = 'gs_pri_pole_num', 'gs_pri_pole_coords', 'gs_secondary_1',\
         'gs_secondary_2', 'gs_secondary_3', 'gs_secondary_4',\
         'gs_secondary_5', 'gs_secondary_6', 'gs_secondary_7', 'gs_secondary_8',\
         'gs_secondary_9', 'gs_secondary_10', 'gs_secondary_11', 'gs_secondary_12',\
         'gs_secondary_13', 'gs_secondary_14', 'gs_secondary_15', 'gs_secondary_16',\
         'gs_secondary_17', 'gs_secondary_18'

labels = { 'gs_pri_pole_num':'Primary Pole #', 'gs_pri_pole_coords':'Primary Pole Coordinates',\
           'gs_secondary_1':'Secondary #1', 'gs_secondary_2':'Secondary #2',\
           'gs_secondary_3':'Secondary #3', 'gs_secondary_4':'Secondary #4',\
           'gs_secondary_5':'Secondary #5', 'gs_secondary_6':'Secondary #6',\
           'gs_secondary_7':'Secondary #7', 'gs_secondary_8':'Secondary #8',\
           'gs_secondary_9':'Secondary #9', 'gs_secondary_10':'Secondary #10',\
           'gs_secondary_11':'Secondary #11', 'gs_secondary_12':'Secondary #12',\
           'gs_secondary_13':'Secondary #13', 'gs_secondary_14':'Secondary #14',\
           'gs_secondary_15':'Secondary #15', 'gs_secondary_16':'Secondary #16',\
           'gs_secondary_17':'Secondary #17', 'gs_secondary_18':'Secondary #18'
         }

# Iterate over all available ports and find the GPS
ser_ports = list(test_ser.comports())

for p in ser_ports:
    if 'NMEA' in p.description:
        ser.port = p.device
        # Used for debugging
        # print("GPS found at {0}\n{1}".format(p.device, p.description))
if not ser.port:
    no_gps_question = tkMsg.askyesno("Error", "No GPS Device found - do you wish to continue?")
    if no_gps_question:
        pass
    else:
        # ser.open() hasn't been called yet, nothing to flush
        raise SystemExit


# Initialize counter for iterating through secondaries
# Starts at 1 (sorry...) because first field is Primary Pole
global counter
counter = 1

# Fills root window with labels and text boxes
def makeform(root, fields):
    entries = []
    #check_var = tk.IntVar()
    for field in fields:
        row = tk.Frame(root)
        lab = tk.Label(row, width=25, text=labels[field], anchor='w')
        ent = tk.Entry(row)
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        ent.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        entries.append((field, ent))
    return entries


def get_input():
    global counter
    root.deiconify()
    root.title("GPS Secondary Tagger")
    ents = makeform(root, fields)
    root.bind('<Return>', (lambda event, e=ents: fetch(e)))
    # If there's no GPS, remove this button
    if ser.port:
        b1 = tk.Button(root, text="Get Long/Lat", command=(lambda e=ents: show_gps(e)))
        b1.pack(side=tk.LEFT, padx=5, pady=5)
    b2 = tk.Button(root, text="Save", command=(lambda e=ents: fetch(e)))
    b2.pack(side=tk.LEFT, padx=5, pady=5)
    b3 = tk.Button(root, text = "Clear All", command=(lambda e=ents: clear_entries(e)))
    b3.pack(side=tk.LEFT, padx=5, pady=5)
    b4 = tk.Button(root, text = "Next", command=next_entry)
    b4.pack(side=tk.LEFT, padx=5, pady=5)
    b5 = tk.Button(root, text = "Previous", command=prev_entry)
    b5.pack(side=tk.LEFT, padx=5, pady=5)
    b6 = tk.Button(root, text = "Help", command=help)
    b6.pack(side=tk.LEFT, padx=5, pady=5)
    b7 = tk.Button(root, text="Quit", command=quit_prog)
    b7.pack(side=tk.LEFT, padx=5, pady=5)
    root.mainloop()


# This is a HTML file encoded into base64, so I can launch a HTML webpage for help
# The temporary file is stored temporarily in the path where the program is executed,
# and removed once the program is exited
# You are welcome to visit https://www.base64decode.org and copy/paste this block in
# if you are (rightfully) suspicious of obfuscated code
def help():
    b64html = b'PCFET0NUWVBFIGh0bWw+DQo8aHRtbCBsYW5nID0gImVuIj4NCjxoZWFkPg0KICA8dGl0bGU+R1BT\
                IFNlY29uZGFyeSBUYWdnZXIgSGVscDwvdGl0bGU+DQo8L2hlYWQ+DQo8Ym9keT4NCiAgICA8aDE+\
                R1BTIFNlY29uZGFyeSBUYWdnZXIgSGVscDwvaDE+DQogICAgPGg0PlJlcXVpcmVtZW50czo8L2g0\
                Pg0KICAgIDx1bD4NCiAgICA8bGk+R1BTIGRldmljZSBjYXBhYmxlIG9mIG91dHB1dHRpbmcgTk1F\
                QSBtZXNzYWdlcyAtIHRoZSBwcm9ncmFtIHdpbGwgYWxlcnQgeW91IGlmIG5vIHN1aXRhYmxlIGRl\
                dmljZSBpcyBmb3VuZCwgYW5kIGFsc28gY29uZmlndXJlcyBpdHMgb3duIHBvcnQgc2VsZWN0aW9u\
                LiBOb3QgdGVzdGVkIHdpdGggVVNCIEdQUyBkZXZpY2VzLCBidXQgYW55dGhpbmcgdGhhdCB1dGls\
                aXplcyBhIENPTSBwb3J0ICh2aXJ0dWFsIG9yIG90aGVyd2lzZSkgc2hvdWxkIHdvcmsuIFdpbmRv\
                d3MgMTAgbWF5IHVzZSBXaW5kb3dzIExvY2F0aW9uIFNlcnZpY2VzIGluc3RlYWQgb2YgYSBDT00g\
                cG9ydCwgd2hpY2ggd2lsbCBub3Qgd29yay48L2xpPg0KICAgIDwvdWw+DQogICAgPHA+VG8gdXNl\
                IHRoZSBhcHAsIHlvdSBhdCBhIG1pbmltdW0gbXVzdCBpbmNsdWRlIGEgUHJpbWFyeSBQb2xlICMs\
                IGFzIHRoZSBhcHAgYXV0by1uYW1lcyB0aGUgcmVzdWx0YW50IEtNTCBiYXNlZCBvbiB0aGF0IG5h\
                bWUuPC9wPg0KICAgIDxwPlRvIGdldCBHUFMgY29vcmRpbmF0ZXMsIHVzZSB0aGUgR2V0IExhdFxM\
                b25nIGJ1dHRvbiAtIHRoZXJlIG1heSBiZSBhIGRlbGF5LCBhcyB0aGUgcHJvZ3JhbSBsb29wcyBy\
                ZWFkaW5nIHRoZSBtZXNzYWdlcyB1bnRpbCBhIHZhbGlkIChpLmUuIG5vdCAwLjAsMC4wIExhdC9M\
                b25nKSBpcyByZWNlaXZlZC48L3A+DQogICAgPHA+V2hlbiB5b3UgaGF2ZSBjb21wbGV0ZWQgZW50\
                ZXJpbmcgZGF0YSBmb3IgdGhlIHBvbGUvdHJhbnNmb3JtZXIsIHNlbGVjdCBTYXZlLCB0aGVuIENs\
                ZWFyIEFsbC4gVGhpcyB3aWxsIHdyaXRlIHRoZSBkYXRhIHRvIGEgS01MIGZpbGUsIGFuZCByZXNl\
                dCB0aGUgY291bnRlciAoc2VlIGJlbG93KS48L3A+DQogICAgPHA+V2hlbiB5b3UgZmlyc3QgdXNl\
                IEdldCBMb25nL0xhdCwgdGhlIHByb2dyYW0gd2lsbCBwdXQgeW91ciBjb29yZGluYXRlcyBpbnRv\
                IHRoZSBQcmltYXJ5IFBvbGUgQ29vcmRpbmF0ZXMgZmllbGQuIEl0IHRoZW4gaW5jcmVtZW50cyBh\
                biBpbnRlcm5hbCBjb3VudGVyIGJ5IG9uZSwgc28gdGhhdCB0aGUgbmV4dCB0aW1lIHlvdSBwcmVz\
                cyBHZXQgTG9uZy9MYXQsIHRoZSBTZWNvbmRhcnkgIzEgZmllbGQgaXMgZmlsbGVkLCBhbmQgc28g\
                b24uIElmIHlvdSBuZWVkIHRvIG1hbnVhbGx5IHNraXAgYWhlYWQgb3IgYmVoaW5kLCB1c2UgdGhl\
                IE5leHQvUHJldmlvdXMgYnV0dG9ucy48L3A+DQogICAgPGg0Pktub3duIElzc3Vlcy9Xb3JrYXJv\
                dW5kczo8L2g0Pg0KICAgIDxwPk9jY2FzaW9uYWxseSwgd2hlbiByZXRyaWV2aW5nIEdQUyBjb29y\
                ZGluYXRlcywgdGhlIENPTSBwb3J0IHdpbGwgYmVjb21lIGxvY2tlZCwgYW5kIHRoZSBwcm9ncmFt\
                IHdpbGwgZnJlZXplLCBuZWNlc3NpdGF0aW5nIHRoZSBjb21wdXRlciB0byBiZSByZWJvb3RlZC4g\
                SSBoYXZlIG1vZGlmaWVkIHRoZSBwcm9ncmFtIHRvIG9wZW4gYW5kIGNsb3NlIHRoZSBDT00gcG9y\
                dCBiZXR3ZWVuIGVhY2ggc2V0IG9mIGNvb3JkaW5hdGVzLCB3aGljaCBJIGJlbGlldmUgaGFzIGZp\
                eGVkIHRoZSBpc3N1ZSwgYnV0IGlmIGl0IG9jY3VycywgcmVib290LjwvcD4NCiAgICA8aDQ+TGlj\
                ZW5zZTwvaDQ+DQogICAgPHA+R1BTIFNlY29uZGFyeSBUYWdnZXI8YnIgLz4gQ29weXJpZ2h0IChD\
                KSAyMDE3IFN0ZXBoYW4gR2FybGFuZDxiciAvPnN0ZXBoYW4ubWFyYy5nYXJsYW5kQGdtYWlsLmNv\
                bTwvcD4NCiAgICA8cD5UaGlzIHByb2dyYW0gaXMgZnJlZSBzb2Z0d2FyZTogeW91IGNhbiByZWRp\
                c3RyaWJ1dGUgaXQgYW5kL29yIG1vZGlmeTxiciAvPiBpdCB1bmRlciB0aGUgdGVybXMgb2YgdGhl\
                IEdOVSBHZW5lcmFsIFB1YmxpYyBMaWNlbnNlIGFzIHB1Ymxpc2hlZCBieTxiciAvPiB0aGUgRnJl\
                ZSBTb2Z0d2FyZSBGb3VuZGF0aW9uLCBlaXRoZXIgdmVyc2lvbiAzIG9mIHRoZSBMaWNlbnNlLCBv\
                cjxiciAvPiAoYXQgeW91ciBvcHRpb24pIGFueSBsYXRlciB2ZXJzaW9uLjwvcD4NCiAgICA8cD5U\
                aGlzIHByb2dyYW0gaXMgZGlzdHJpYnV0ZWQgaW4gdGhlIGhvcGUgdGhhdCBpdCB3aWxsIGJlIHVz\
                ZWZ1bCw8YnIgLz4gYnV0IFdJVEhPVVQgQU5ZIFdBUlJBTlRZOyB3aXRob3V0IGV2ZW4gdGhlIGlt\
                cGxpZWQgd2FycmFudHkgb2Y8YnIgLz4gTUVSQ0hBTlRBQklMSVRZIG9yIEZJVE5FU1MgRk9SIEEg\
                UEFSVElDVUxBUiBQVVJQT1NFLiBTZWUgdGhlPGJyIC8+IEdOVSBHZW5lcmFsIFB1YmxpYyBMaWNl\
                bnNlIGZvciBtb3JlIGRldGFpbHMuPC9wPg0KICAgIDxwPllvdSBzaG91bGQgaGF2ZSByZWNlaXZl\
                ZCBhIGNvcHkgb2YgdGhlIEdOVSBHZW5lcmFsIFB1YmxpYyBMaWNlbnNlPGJyIC8+IGFsb25nIHdp\
                dGggdGhpcyBwcm9ncmFtLiBJZiBub3QsIHNlZSAmbHQ7aHR0cDovL3d3dy5nbnUub3JnL2xpY2Vu\
                c2VzLyZndDsuPC9wPg0KPC9ib2R5Pg0KPC9odG1sPg=='

    path = os.path.abspath('temp_help.html')
    url = 'file://' + path
    html = base64.b64decode(b64html).decode('utf-8', 'ignore')
    with open(path, 'w') as f:
        f.write(html)
        webbrowser.open(url)


def quit_prog():
    try:
        os.remove(os.path.abspath('temp_help.html'))
    except FileNotFoundError:
        pass

    # If program is launched as a stand-alone, Quit == Quit
    # If program is launched from main tagger, Quit == Hide
    if __name__ == '__main__':
        raise SystemExit
    else:
        root.withdraw()


def clear_entries(entries):
    for entry in entries:
        # Have to use the getter to get cleartext through
        # Have to use tkinter object for .delete and .insert
        text = entry[1]
        text.delete(0, tk.END)
    global counter
    counter = 1


def next_entry():
    global counter
    counter += 1


def prev_entry():
    global counter
    counter -= 1


def get_gps():
    ser.open()
    while True:
        # Pull NMEA message, decode from binary, remove NULLs
        raw_msg = ser.readline().decode().lstrip('\x00')
        # $GPRMC is also useful, and contains speed as well
        if raw_msg[0:6] == '$GPGGA':
            break
    msg = gps.parse(raw_msg)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    ser.close()
    return msg


def fetch(entries):
    kml = simplekml.Kml()
    inputs = {}
    #span_coords = []
    for entry in entries:
        field = entry[0]
        text = entry[1].get()
        if field == 'gs_pri_pole_num':
            pole_num = text
        elif field == 'gs_pri_pole_coords':
            if text:
                coords_list = ''.join(text)
                coords_list = coords_list.split(',')
                geo_long = coords_list[0]
                geo_lat = coords_list[1]
                #span_coords.append([(geo_long, geo_lat)])
                kml.newpoint(name=pole_num, coords=[(geo_long, geo_lat)])
        else:
            if text:
                coords_list = ''.join(text)
                coords_list = coords_list.split(',')
                geo_long = coords_list[0]
                geo_lat = coords_list[1]
                #span_coords.append([(geo_long, geo_lat)])
                kml.newpoint(name=labels[field], coords=[(geo_long, geo_lat)])
    #print(span_coords)
    #span = kml.newlinestring(name="Spans", coords=[span_coords])
    kml_file_name = pole_num + '.kml'
    kml.save(kml_file_name)


def show_gps(entries):
    msg = get_gps()
    # Loop until a valid message is returned
    while float(msg.latitude) == 0.0:
        msg = get_gps()
    field = entries[counter][0]
    text = entries[counter][1]
    text.delete(0, tk.END)
    text.insert(0, float(msg.latitude))
    text.insert(0, str(","))
    text.insert(0, float(msg.longitude))
    # Once a valid message is returned, move to the next
    if not text.get() == '0.0,0.0':
        next_entry()

get_input()
