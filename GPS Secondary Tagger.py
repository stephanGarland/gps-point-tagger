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
    if no_gps_question == True:
        pass
    elif no_gps_question == False:
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
    b64html = b'PCFET0NUWVBFIGh0bWw+DQo8aHRtbCBsYW5nID0gImVuIj4NCjxoZWFkPg0KICA8dGl0bGU+R1BTIFNlY29uZGFyeSBUYWdnZXIgSGVscDwvdGl\
                0bGU+DQo8L2hlYWQ+DQo8Ym9keT4NCiAgICA8aDE+R1BTIFNlY29uZGFyeSBUYWdnZXIgSGVscDwvaDE+DQogICAgPGg0PlJlcXVpcmVtZW50cz\
                o8L2g0Pg0KICAgIDx1bD4NCiAgICA8bGk+R1BTIGRldmljZSBjYXBhYmxlIG9mIG91dHB1dHRpbmcgTk1FQSBtZXNzYWdlcyAtIHRoZSBwcm9nc\
                mFtIHdpbGwgYWxlcnQgeW91IGlmIG5vIHN1aXRhYmxlIGRldmljZSBpcyBmb3VuZCwgYW5kIGFsc28gY29uZmlndXJlcyBpdHMgb3duIHBvcnQg\
                c2VsZWN0aW9uLjwvbGk+DQogICAgPC91bD4NCiAgICA8cD5UbyB1c2UgdGhlIGFwcCwgeW91IGF0IGEgbWluaW11bSBtdXN0IGluY2x1ZGUgYSB\
                QcmltYXJ5IFBvbGUgIywgYXMgdGhlIGFwcCBhdXRvLW5hbWVzIHRoZSByZXN1bHRhbnQgS01MIGJhc2VkIG9uIHRoYXQgbmFtZS48L3A+DQogIC\
                AgPHA+VG8gZ2V0IEdQUyBjb29yZGluYXRlcywgdXNlIHRoZSBHZXQgTGF0XExvbmcgYnV0dG9uIC0gdGhlcmUgbWF5IGJlIGEgZGVsYXksIGFzI\
                HRoZSBwcm9ncmFtIGxvb3BzIHJlYWRpbmcgdGhlIG1lc3NhZ2VzIHVudGlsIGEgdmFsaWQgKGkuZS4gbm90IDAuMCwwLjAgTGF0L0xvbmcpIGlz\
                IHJlY2VpdmVkLjwvcD4NCiAgICA8cD5XaGVuIHlvdSBoYXZlIGNvbXBsZXRlZCBlbnRlcmluZyBkYXRhIGZvciB0aGUgcG9sZS90cmFuc2Zvcm1\
                lciwgc2VsZWN0IFNhdmUsIHRoZW4gQ2xlYXIgQWxsLiBUaGlzIHdpbGwgd3JpdGUgdGhlIGRhdGEgdG8gYSBLTUwgZmlsZSwgYW5kIHJlc2V0IH\
                RoZSBjb3VudGVyIChzZWUgYmVsb3cpLjwvcD4NCiAgICA8cD5XaGVuIHlvdSBmaXJzdCB1c2UgR2V0IExvbmcvTGF0LCB0aGUgcHJvZ3JhbSB3a\
                WxsIHB1dCB5b3VyIGNvb3JkaW5hdGVzIGludG8gdGhlIFByaW1hcnkgUG9sZSBDb29yZGluYXRlcyBmaWVsZC4gSXQgdGhlbiBpbmNyZW1lbnRz\
                IGFuIGludGVybmFsIGNvdW50ZXIgYnkgb25lLCBzbyB0aGF0IHRoZSBuZXh0IHRpbWUgeW91IHByZXNzIEdldCBMb25nL0xhdCwgdGhlIFNlY29\
                uZGFyeSAjMSBmaWVsZCBpcyBmaWxsZWQsIGFuZCBzbyBvbi4gSWYgeW91IG5lZWQgdG8gbWFudWFsbHkgc2tpcCBhaGVhZCBvciBiZWhpbmQsIH\
                VzZSB0aGUgTmV4dC9QcmV2aW91cyBidXR0b25zLjwvcD4NCiAgICA8aDQ+S25vd24gSXNzdWVzL1dvcmthcm91bmRzOjwvaDQ+DQogICAgPHA+T\
                2NjYXNpb25hbGx5LCB3aGVuIHJldHJpZXZpbmcgR1BTIGNvb3JkaW5hdGVzLCB0aGUgQ09NIHBvcnQgd2lsbCBiZWNvbWUgbG9ja2VkLCBhbmQg\
                dGhlIHByb2dyYW0gd2lsbCBmcmVlemUsIG5lY2Vzc2l0YXRpbmcgdGhlIGNvbXB1dGVyIHRvIGJlIHJlYm9vdGVkLiBJIGhhdmUgbW9kaWZpZWQ\
                gdGhlIHByb2dyYW0gdG8gb3BlbiBhbmQgY2xvc2UgdGhlIENPTSBwb3J0IGJldHdlZW4gZWFjaCBzZXQgb2YgY29vcmRpbmF0ZXMsIHdoaWNoIE\
                kgYmVsaWV2ZSBoYXMgZml4ZWQgdGhlIGlzc3VlLCBidXQgaWYgaXQgb2NjdXJzLCByZWJvb3QuPC9wPg0KICAgIDxoND5MaWNlbnNlPC9oND4NC\
                iAgICA8cD5HUFMgU2Vjb25kYXJ5IFRhZ2dlcjxiciAvPiBDb3B5cmlnaHQgKEMpIDIwMTcgU3RlcGhhbiBHYXJsYW5kPGJyIC8+c3RlcGhhbi5t\
                YXJjLmdhcmxhbmRAZ21haWwuY29tPC9wPg0KICAgIDxwPlRoaXMgcHJvZ3JhbSBpcyBmcmVlIHNvZnR3YXJlOiB5b3UgY2FuIHJlZGlzdHJpYnV\
                0ZSBpdCBhbmQvb3IgbW9kaWZ5PGJyIC8+IGl0IHVuZGVyIHRoZSB0ZXJtcyBvZiB0aGUgR05VIEdlbmVyYWwgUHVibGljIExpY2Vuc2UgYXMgcH\
                VibGlzaGVkIGJ5PGJyIC8+IHRoZSBGcmVlIFNvZnR3YXJlIEZvdW5kYXRpb24sIGVpdGhlciB2ZXJzaW9uIDMgb2YgdGhlIExpY2Vuc2UsIG9yP\
                GJyIC8+IChhdCB5b3VyIG9wdGlvbikgYW55IGxhdGVyIHZlcnNpb24uPC9wPg0KICAgIDxwPlRoaXMgcHJvZ3JhbSBpcyBkaXN0cmlidXRlZCBp\
                biB0aGUgaG9wZSB0aGF0IGl0IHdpbGwgYmUgdXNlZnVsLDxiciAvPiBidXQgV0lUSE9VVCBBTlkgV0FSUkFOVFk7IHdpdGhvdXQgZXZlbiB0aGU\
                gaW1wbGllZCB3YXJyYW50eSBvZjxiciAvPiBNRVJDSEFOVEFCSUxJVFkgb3IgRklUTkVTUyBGT1IgQSBQQVJUSUNVTEFSIFBVUlBPU0UuIFNlZS\
                B0aGU8YnIgLz4gR05VIEdlbmVyYWwgUHVibGljIExpY2Vuc2UgZm9yIG1vcmUgZGV0YWlscy48L3A+DQogICAgPHA+WW91IHNob3VsZCBoYXZlI\
                HJlY2VpdmVkIGEgY29weSBvZiB0aGUgR05VIEdlbmVyYWwgUHVibGljIExpY2Vuc2U8YnIgLz4gYWxvbmcgd2l0aCB0aGlzIHByb2dyYW0uIElm\
                IG5vdCwgc2VlICZsdDtodHRwOi8vd3d3LmdudS5vcmcvbGljZW5zZXMvJmd0Oy48L3A+DQo8L2JvZHk+DQo8L2h0bWw+'
                
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