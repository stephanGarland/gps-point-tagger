# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# GPS Tagger.py
#
# Created on: 2017-08-08
# Stephan Garland
# stephan.marc.garland@gmail.com
#
# Captures NMEA outputs from GPS card and allows user comments to be added
# Records Long/Lat and comments in a table, and writes them to a CSV

import base64
import csv
from datetime import date
import random
import os
import serial
import serial.tools.list_ports as test_ser
import pynmea2 as gps
import subprocess
import sys
import webbrowser

try:
    import tkinter as tk  # Python 3.x
    from tkinter import messagebox as tkMsg
    from tkinter.filedialog import asksaveasfilename
    from importlib import reload
except ImportError:  # Python 2.x
    import Tkinter as tk
    import tkMessageBox as tkMsg
    from tkFileDialog import asksaveasfilename
    # Python 2.x has reload as a built-in
    
root = tk.Tk()
root.withdraw()

ser = serial.Serial()
ser.baudrate = 9600
ser.timeout = 1

fields = 'gs_equipment_location', 'gs_serial_number', 'gs_rated_input_voltage', \
         'gs_rated_output_voltage', 'gs_substype_cd', 'gs_rated_kva', 'gs_phase', 'gs_secondary_feeds',\
         'gs_amr_identification', 'long', 'lat', 'gs_height', 'gs_class'
          
labels = { 'gs_equipment_location':'Pole #', 'gs_serial_number':'Transformer Serial #', 'gs_rated_input_voltage':'Vpri',\
           'gs_rated_output_voltage':'Vsec', 'gs_substype_cd':'Overhead/Padmount', 'gs_rated_kva':'kVA',\
           'gs_phase':'Phase', 'gs_secondary_feeds':'Secondary Feeds (Meter #s)',\
           'gs_amr_identification':'Pole Meter #','long':'Longitude', 'lat':'Latitude',\
           'gs_height':'Pole Height', 'gs_class':'Pole Class' }

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


    
def save_file():
    tkMsg.showinfo("CSV Selection", "Select your CSV filename and save location")
    csv_file_name = asksaveasfilename(title="CSV Save Location",\
                    defaultextension=".csv", filetypes=(("CSV", "*.csv"),\
                    ("All Files", "*.*")), initialfile=str(date.today()))
    return csv_file_name
                


csv_file_name = save_file()
        
if not csv_file_name:
    no_save_question = tkMsg.askyesno("Error", "You have not selected a savefile - do you wish to select one now?")
    if no_save_question == True:
        save_file()
    elif no_save_question == False:
        pass                
# Open the serial port for the GPS
#ser.open()



# Fills root window with labels and text boxes
def makeform(root, fields):
    entries = []
    check_var = tk.IntVar()
    for field in fields:
        row = tk.Frame(root)
        lab = tk.Label(row, width=25, text=labels[field], anchor='w')
        ent = tk.Entry(row)
        if labels[field] == 'Pole #':
            check = tk.Checkbutton(row, text="+=1", variable=check_var)
            check.pack(side=tk.RIGHT, padx=5, pady=5)
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        ent.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        entries.append((field, ent))
    # Yeah, it's a global - it works
    # If you'd like to split the returned tuple instead, be my guest
    global output_check_var
    output_check_var = check_var
    return entries



def get_input():
    root.deiconify()
    root.title("GPS Tagger")
    ents = makeform(root, fields)
    root.bind('<Return>', (lambda event, e=ents: fetch(e)))
    # If there's no GPS, remove this button
    if ser.port:
        b1 = tk.Button(root, text="Get Long/Lat", command=(lambda e=ents: show_gps(e)))
        b1.pack(side=tk.LEFT, padx=5, pady=5)
    b2 = tk.Button(root, text="Save", command=(lambda e=ents: fetch(e)))
    b2.pack(side=tk.LEFT, padx=5, pady=5)
    b3 = tk.Button(root, text="Clear/Next Entry", command=(lambda e=ents: clear_entries(e)))
    b3.pack(side=tk.LEFT, padx=5, pady=5)
    b4 = tk.Button(root, text="Secondary Capture", command=secondary_capture)
    b4.pack(side=tk.LEFT, padx=5, pady=5)
    b5 = tk.Button(root, text="Help", command=help)
    b5.pack(side=tk.LEFT, padx=5, pady=5)
    b6 = tk.Button(root, text="Quit", command=quit_prog)
    b6.pack(side=tk.LEFT, padx=5, pady=5)
    root.mainloop()

    

# This is a HTML file encoded into base64, so I can launch a HTML webpage for help
# The temporary file is stored temporarily in the path where the program is executed,
# and removed once the program is exited
# You are welcome to visit https://www.base64decode.org and copy/paste this block in 
# if you are (rightfully) suspicious of obfuscated code
def help():
    b64html = b'PCFET0NUWVBFIGh0bWw+DQo8aHRtbCBsYW5nID0gImVuIj4NCjxoZWFkPg0KICA8dGl0bGU+R1BTIFRhZ2dlciBIZWxwPC90aXRsZT4NCjwvaG\
             VhZD4NCjxib2R5Pg0KICA8aDE+R1BTIFRhZ2dlciBIZWxwPC9oMT4NCiAgPGg0PlJlcXVpcmVtZW50czo8L2g0Pg0KICA8dWw+DQogIDxsaT5H\
             UFMgZGV2aWNlIGNhcGFibGUgb2Ygb3V0cHV0dGluZyBOTUVBIG1lc3NhZ2VzIC0gdGhlIHByb2dyYW0gd2lsbCBhbGVydCB5b3UgaWYgbm8gc3\
             VpdGFibGUgZGV2aWNlIGlzIGZvdW5kLCBhbmQgYWxzbyBjb25maWd1cmVzIGl0cyBvd24gcG9ydCBzZWxlY3Rpb24uPC9saT4NCiAgPC91bD4N\
             CiAgPHA+VG8gdXNlIHRoZSBhcHAsIGVudGVyIGFzIG11Y2ggb3IgYXMgbGl0dGxlIGRhdGEgYXMgeW91IHdvdWxkIGxpa2UuIEFsbCBmaWVsZH\
             Mgd2l0aCBkYXRhIGluIHRoZW0gd2lsbCBiZSBzYXZlZCB1cG9uIHVzZXIgcmVxdWVzdCBpbiBhIENTViwgd2l0aCBlbnRyaWVzIHNlcGFyYXRl\
             ZCBieSBhIGJsYW5rIGxpbmUuPC9wPg0KICA8cD5UbyBnZXQgR1BTIGNvb3JkaW5hdGVzLCB1c2UgdGhlIEdldCBMYXRcTG9uZyBidXR0b24gLS\
             B0aGVyZSBtYXkgYmUgYSBkZWxheSwgYXMgdGhlIHByb2dyYW0gbG9vcHMgcmVhZGluZyB0aGUgbWVzc2FnZXMgdW50aWwgYSB2YWxpZCAoaS5l\
             LiBub3QgMC4wLDAuMCBMYXQvTG9uZykgaXMgcmVjZWl2ZWQuPC9wPg0KICA8cD5XaGVuIHlvdSBoYXZlIGNvbXBsZXRlZCBlbnRlcmluZyBkYX\
             RhIGZvciB0aGUgcG9sZS90cmFuc2Zvcm1lciwgc2VsZWN0IFNhdmUsIHRoZW4gQ2xlYXJcTmV4dCBFbnRyeS4gVGhpcyB3aWxsIHdyaXRlIHRo\
             ZSBkYXRhIHRvIHRoZSBDU1YgZmlsZSB5b3Ugc2VsZWN0ZWQgdXBvbiBsYXVuY2hpbmcgdGhlIHByb2dyYW0uPC9wPg0KICA8cD5Ob3RlIHRoYX\
             QgKGlmIGRhdGEgaXMgZW50ZXJlZCkgdGhlIFZwcmksIFZzZWMsIGFuZCBPdmVyaGVhZC9QYWRtb3VudCBmaWVsZHMgYXJlIHBlcnNpc3RlbnQ7\
             IHRoaXMgaXMgYmVjYXVzZSB0aG9zZSB2YWx1ZXMgcmFyZWx5IGNoYW5nZSBmcm9tIG9uZSB0byB0aGUgbmV4dCwgYW5kIGl0IHNhdmVzIG9uIH\
             JlcGV0aXRpdmUgZGF0YSBlbnRyeS4gSWYgeW91IG5lZWQgdG8gY2hhbmdlIHRoZW0sIHNpbXBseSBtYW51YWxseSBvdmVyd3JpdGUgdGhlIGZp\
             ZWxkcy48L3A+DQogIDxwPlRoZSAiKz0xIiBjaGVja2JveCBuZXh0IHRvIHRoZSBQb2xlIE51bWJlciBmaWVsZCBpcyB1c2VmdWwgd2hlbiByZW\
             NvcmRpbmcgZGF0YSBpbiBvcmRlcjsgaWYgc2VsZWN0ZWQsIHVwb24gaGl0dGluZyBDbGVhci9OZXh0IEVudHJ5LCB0aGUgUG9sZSBOdW1iZXIg\
             d2lsbCBpbmNyZW1lbnQgYnkgb25lLiBFeGFtcGxlczo8L3A+DQogIDx1bD4NCiAgPGxpPkJSVzQgLSZndDsgQlJXNS48L2xpPg0KICA8bGk+Ql\
             JXNC1OOSAtJmd0OyBCUlc0LU4xMC48L2xpPg0KICA8L3VsPg0KICA8cD5Pbmx5IHRoZSBsYXN0IGVsZW1lbnQgb2YgdGhlIHN0cmluZyBpcyBp\
             bmNyZW1lbnRlZDsgYWxzbyBub3RlIHRoYXQgdGhlIHByb2dyYW0gZG9lcyBub3QgaGFuZGxlIGluaXRpYXRpbmcgdGFrZW9mZnMuIElmIHlvdS\
             BuZWVkLCBmb3IgZXhhbXBsZSwgQlJXNC1OOSB0byBiZWNvbWUgQlJXNC1OOS1OMSwgeW91IHdpbGwgaGF2ZSB0byBtYW51YWxseSB0eXBlIHRo\
             YXQgaW4uIEZvbGxvd2luZyBpdGVtcyB3b3VsZCBiZWNvbWUgQlJXNC1OOS1OMiwgZXRjLjwvcD4NCiAgPGg0Pktub3duIElzc3Vlcy9Xb3JrYX\
             JvdW5kczo8L2g0Pg0KICA8cD5PY2Nhc2lvbmFsbHksIHdoZW4gcmV0cmlldmluZyBHUFMgY29vcmRpbmF0ZXMsIHRoZSBDT00gcG9ydCB3aWxs\
             IGJlY29tZSBsb2NrZWQsIGFuZCB0aGUgcHJvZ3JhbSB3aWxsIGZyZWV6ZSwgbmVjZXNzaXRhdGluZyB0aGUgY29tcHV0ZXIgdG8gYmUgcmVib2\
             90ZWQuIEkgaGF2ZSBtb2RpZmllZCB0aGUgcHJvZ3JhbSB0byBvcGVuIGFuZCBjbG9zZSB0aGUgQ09NIHBvcnQgYmV0d2VlbiBlYWNoIHNldCBv\
             ZiBjb29yZGluYXRlcywgd2hpY2ggSSBiZWxpZXZlIGhhcyBmaXhlZCB0aGUgaXNzdWUsIGJ1dCBpZiBpdCBvY2N1cnMsIHJlYm9vdC4gQWRkaX\
             Rpb25hbGx5LCBhcyBhIG1lYW5zIG9mIG1pdGlnYXRpb24sIGl0IGlzIHJlY29tbWVuZGVkIHRvIGdldCBHUFMgY29vcmRpbmF0ZXMgZmlyc3Qg\
             YmVmb3JlIGlucHV0dGluZyBhbnkgb3RoZXIgZGF0YTsgdGhpcyB3YXksIHlvdSB3aWxsIG5vdCBoYXZlIGxvc3QgYW55dGhpbmcgdHlwZWQgaW\
             4sIGFzIHRoZSBDU1YgZmlsZSBpcyBvcGVuZWQsIHVwZGF0ZWQsIGFuZCBjbG9zZWQgd2l0aCBlYWNoIFNhdmUuPC9wPg0KICA8aDQ+TGljZW5z\
             ZTwvaDQ+DQogIDxwPkdQUyBUYWdnZXI8YnIgLz4gQ29weXJpZ2h0IChDKSAyMDE3IFN0ZXBoYW4gR2FybGFuZDxiciAvPnN0ZXBoYW4ubWFyYy\
             5nYXJsYW5kQGdtYWlsLmNvbTwvcD4NCiAgPHA+VGhpcyBwcm9ncmFtIGlzIGZyZWUgc29mdHdhcmU6IHlvdSBjYW4gcmVkaXN0cmlidXRlIGl0\
             IGFuZC9vciBtb2RpZnk8YnIgLz4gaXQgdW5kZXIgdGhlIHRlcm1zIG9mIHRoZSBHTlUgR2VuZXJhbCBQdWJsaWMgTGljZW5zZSBhcyBwdWJsaX\
             NoZWQgYnk8YnIgLz4gdGhlIEZyZWUgU29mdHdhcmUgRm91bmRhdGlvbiwgZWl0aGVyIHZlcnNpb24gMyBvZiB0aGUgTGljZW5zZSwgb3I8YnIg\
             Lz4gKGF0IHlvdXIgb3B0aW9uKSBhbnkgbGF0ZXIgdmVyc2lvbi48L3A+DQogIDxwPlRoaXMgcHJvZ3JhbSBpcyBkaXN0cmlidXRlZCBpbiB0aG\
             UgaG9wZSB0aGF0IGl0IHdpbGwgYmUgdXNlZnVsLDxiciAvPiBidXQgV0lUSE9VVCBBTlkgV0FSUkFOVFk7IHdpdGhvdXQgZXZlbiB0aGUgaW1w\
             bGllZCB3YXJyYW50eSBvZjxiciAvPiBNRVJDSEFOVEFCSUxJVFkgb3IgRklUTkVTUyBGT1IgQSBQQVJUSUNVTEFSIFBVUlBPU0UuIFNlZSB0aG\
             U8YnIgLz4gR05VIEdlbmVyYWwgUHVibGljIExpY2Vuc2UgZm9yIG1vcmUgZGV0YWlscy48L3A+DQogIDxwPllvdSBzaG91bGQgaGF2ZSByZWNl\
             aXZlZCBhIGNvcHkgb2YgdGhlIEdOVSBHZW5lcmFsIFB1YmxpYyBMaWNlbnNlPGJyIC8+IGFsb25nIHdpdGggdGhpcyBwcm9ncmFtLiBJZiBub3\
             QsIHNlZSAmbHQ7aHR0cDovL3d3dy5nbnUub3JnL2xpY2Vuc2VzLyZndDsuPC9wPg0KPC9ib2R5Pg0KPC9odG1sPg0K'

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
    raise SystemExit
    


def clear_entries(entries):
    for entry in entries:
        # Have to use the getter to get cleartext through
        # Have to use tkinter object for .delete and .insert
        # This one specific item is called out as the pole number frequently increments
        if (entry[0] == 'gs_equipment_location' and output_check_var.get() == 1):
            text = entry[1].get()
            mod_text = str(text)
            last_ele = mod_text.split('-')[-1:][0]
            last_alpha = ''.join(filter(lambda x: not x.isdigit(), mod_text))
            
            if not any(x.isdigit() for x in last_ele):
                # If the last element is entirely non-numeric, don't increment
                pass
            else:
                # Given an input like "BRW4-N6", it is split into ['BRW4', 'N6']
                # The last element of the list is then converted into a string via slicing
                # A filter is run to generate the numeric and non-numeric portions with .isdigit()
                # It's all joined with map, with the original mod_text being sliced to exclude 
                # the last element, last_char, and last_num incremented by one
                # Note that if the last element ends in a letter, it will be flipped, i.e.
                # "BRW4-6N" becomes "BRW4-N7"
                last_num = int(''.join(filter(lambda x: x.isdigit(), last_ele)))
                last_char = ''.join(filter(lambda x: not x.isdigit(), last_ele))
                
                if "-" in mod_text:
                    mod_text = '-'.join(map(str, mod_text.split('-')[:-1])) + '-' + last_char + str(last_num + 1)
                # If the entry has no "-", e.g. BRW4, use this instead to avoid -BRW5
                else:
                    mod_text = last_alpha + str(last_num + 1)

            entry[1].delete(0, tk.END)
            entry[1].insert(0, mod_text)
        
        # Don't erase input/output voltages or OHD/PAD on transformers, as they rarely change
        elif (entry[0] == 'gs_rated_input_voltage'\
           or entry[0] == 'gs_rated_output_voltage' or entry[0] == 'gs_substype_cd'):
            pass

        else:
            text = entry[1]
            text.delete(0, tk.END)
            
    if sys.version_info.major == 2:
        with open(csv_file_name, 'ab') as f:
            writer = csv.writer(f)
            # Inserts blank row between successive entries
            writer.writerow([])
    else:
        with open(csv_file_name, 'a', newline='') as f:
            writer = csv.writer(f)
            # Inserts blank row between successive entries
            writer.writerow([])

 
 
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
    inputs = {}
    for entry in entries:
        field = entry[0]
        text = entry[1].get()
        if text:
            inputs[field] = str(text)
    wrangle_data(inputs)


    
def show_gps(entries):
    msg = get_gps()
    # Loop until a valid message is returned
    while float(msg.latitude) == 0.0:
        msg = get_gps()
        
    # As entries are made in makeform() with an iterator, update Lat/Long here
    for entry in entries:
        field = entry[0]
        text = entry[1]
        if field == 'long':
            text.delete(0, tk.END)
            text.insert(0, msg.longitude)
        elif field == 'lat':
            text.delete(0, tk.END)
            text.insert(0, msg.latitude)
        else:
            pass



def wrangle_data(inputs):
    # Python 2 skips inserting blank rows if it's opened as a binary file
    if sys.version_info.major == 2:
        with open(csv_file_name, 'ab') as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(["Parameter", "Value"])
                for k,v in inputs.items():
                    writer.writerow([k, v])
            else:
                for k,v in inputs.items():
                    writer.writerow([k, v])
                    
    # Naturally, Python 3 has a new way of dealing with this
    else:
        with open(csv_file_name, 'a', newline='') as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(["Parameter", "Value"])
                for k,v in inputs.items():
                    writer.writerow([k, v])
            else:
                for k,v in inputs.items():
                    writer.writerow([k, v])


                    
def secondary_capture():
    try:
        if 'python' in os.path.split(sys.executable)[1]:
            try:
                # Currently non-functional
                GPS_Secondary_Tagger = reload(GPS_Secondary_Tagger)
            except Exception:
                GPS_Secondary_Tagger = __import__('GPS Secondary Tagger')
        else:
            subprocess.Popen('GPS Secondary Tagger.exe')    
    except FileNotFoundError:
        tkMsg.showerror("File Not Found", "Secondary tagger not found")
    
    
get_input()
