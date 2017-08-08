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

import csv
from datetime import date
import serial
import serial.tools.list_ports as test_ser
import pynmea2 as gps
from sys import version_info

try:
    import tkinter as tk  # Python 3.x
    from tkinter import messagebox as tkMsg
    from tkinter.filedialog import asksaveasfilename
except ImportError:  # Python 2.x
    import Tkinter as tk
    import tkMessageBox as tkMsg
    from tkFileDialog import asksaveasfilename
    
root = tk.Tk()
root.withdraw()


csv_file_name = asksaveasfilename(title="CSV Save Location",\
                defaultextension=".csv", filetypes=(("CSV", "*.csv"),\
                ("All Files", "*.*")), initialfile=str(date.today()))

ser = serial.Serial()
ser.baudrate = 9600
ser.timeout = 1

fields = 'gs_rated_input_voltage', 'gs_rated_output_voltage',\
          'gs_rated_kva', 'gs_serial_number', 'gs_phase', 'gs_substype_cd',\
          'gs_amr_identification', 'long', 'lat', 'gs_equipment_location', 'gs_height', 'gs_class'
          
labels = { 'gs_rated_input_voltage':'Vpri', 'gs_rated_output_voltage':'Vsec',\
           'gs_rated_kva':'kVA', 'gs_serial_number':'Serial #', 'gs_phase':'Phase',\
           'gs_substype_cd':'Overhead/Padmount', 'gs_amr_identification':'Meter #',\
           'long':'Longitude', 'lat':'Latitude', 'gs_equipment_location':'Pole #',\
           'gs_height':'Pole Height', 'gs_class':'Pole Class' }

# Iterate over all available ports and find the GPS          
ser_ports = list(test_ser.comports())

for p in ser_ports:
    if 'NMEA' in p.description:
        ser.port = p.device
        print("GPS found at {0}\n{1}".format(p.device, p.description))  
if not ser.port:
    tkMsg.showerror("Error", "No GPS Device found, exiting")
    # ser.open() hasn't been called yet, nothing to flush
    raise SystemExit

ser.open()

# Fills root window with labels and text boxes
def makeform(root, fields):
    entries = []
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
    root.deiconify()
    root.title("GPS Tagger")
    ents = makeform(root, fields)
    root.bind('<Return>', (lambda event, e=ents: fetch(e)))
    b1 = tk.Button(root, text="Get Long/Lat", command=(lambda e=ents: show_gps(e)))
    b1.pack(side=tk.LEFT, padx=5, pady=5)
    b2 = tk.Button(root, text="Save", command=(lambda e=ents: fetch(e)))
    b2.pack(side=tk.LEFT, padx=5, pady=5)
    b3 = tk.Button(root, text = "Clear", command=(lambda e = ents: clear_entries(e)))
    b3.pack(side=tk.LEFT, padx=5, pady=5)
    b4 = tk.Button(root, text="Quit", command=quit_prog)
    b4.pack(side=tk.LEFT, padx=5, pady=5)
    root.mainloop()


    
def quit_prog():
    # Found that if buffers aren't flushed, Python hangs on exit
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    ser.close()
    raise SystemExit
    


def clear_entries(entries):
    for entry in entries:
        text = entry[1]
        text.delete(0, tk.END)
    if version_info.major == 2:
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
    while True:
        # Pull NMEA message, decode from binary, remove NULLs
        raw_msg = ser.readline().decode().lstrip('\x00')
        # $GPRMC is also useful, and contains speed as well
        if raw_msg[0:6] == '$GPGGA':
            break
    msg = gps.parse(raw_msg)
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
    if version_info.major == 2:
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

        
        

get_input()


        