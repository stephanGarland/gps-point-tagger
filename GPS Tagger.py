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
import string
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

# Used for various error checking
pole_num_typo_deliberate = None
line_ground_typo_deliberate = None

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
if not ser.port:
    no_gps_question = tkMsg.askyesno("Error", "No GPS Device found - do you wish to continue?")
    if no_gps_question:
        pass
    else:
        # ser.open() hasn't been called yet, nothing to flush
        raise SystemExit


def get_save_loc():
    tkMsg.showinfo("CSV Selection", "Select your CSV filename and save location")
    csv_file_name = asksaveasfilename(title="CSV Save Location",\
                    defaultextension=".csv", filetypes=(("CSV", "*.csv"),\
                    ("All Files", "*.*")), initialfile=str(date.today()))
    return csv_file_name


csv_file_name = get_save_loc()
if not csv_file_name:
    no_save_question = tkMsg.askyesno("Error", "You have not selected a savefile - do you wish to select one now?")
    if no_save_question:
        get_save_loc()
    else:
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
    #b2 = tk.Button(root, text="Save", command=(lambda e=ents: fetch(e)))
    #b2.pack(side=tk.LEFT, padx=5, pady=5)
    b3 = tk.Button(root, text="Save/Next Entry", command=(lambda e=ents: fetch(e)))
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
    b64html = b'PHA+Jm5ic3A7PC9wPg0KPGgxPkdQUyBUYWdnZXIgSGVscDwvaDE+DQo8aDQ+UmVxdWlyZW1lbnRz\
                OjwvaDQ+DQo8dWw+DQo8bGk+R1BTIGRldmljZSBjYXBhYmxlIG9mIG91dHB1dHRpbmcgTk1FQSBt\
                ZXNzYWdlcyAtIHRoZSBwcm9ncmFtIHdpbGwgYWxlcnQgeW91IGlmIG5vIHN1aXRhYmxlIGRldmlj\
                ZSBpcyBmb3VuZCwgYW5kIGFsc28gY29uZmlndXJlcyBpdHMgb3duIHBvcnQgc2VsZWN0aW9uLiBO\
                b3QgdGVzdGVkIHdpdGggVVNCIEdQUyBkZXZpY2VzLCBidXQgYW55dGhpbmcgdGhhdCB1dGlsaXpl\
                cyBhIENPTSBwb3J0ICh2aXJ0dWFsIG9yIG90aGVyd2lzZSkgc2hvdWxkIHdvcmsuIFdpbmRvd3Mg\
                MTAgbWF5IHVzZSBXaW5kb3dzIExvY2F0aW9uIFNlcnZpY2VzIGluc3RlYWQgb2YgYSBDT00gcG9y\
                dCwgd2hpY2ggd2lsbCBub3Qgd29yay48L2xpPg0KPC91bD4NCjxwPlRvIHVzZSB0aGUgYXBwLCBl\
                bnRlciBhcyBtdWNoIG9yIGFzIGxpdHRsZSBkYXRhIGFzIHlvdSB3b3VsZCBsaWtlLiBBbGwgZmll\
                bGRzIHdpdGggZGF0YSBpbiB0aGVtIHdpbGwgYmUgc2F2ZWQgdXBvbiB1c2VyIHJlcXVlc3QgaW4g\
                YSBDU1YsIHdpdGggZW50cmllcyBzZXBhcmF0ZWQgYnkgYSBibGFuayBsaW5lLjwvcD4NCjxwPk1l\
                dGVyICNzIHNob3VsZCBiZSBpbnNlcnRlZCB3aXRoIGNvbW1hcyBhcyBkZWxpbWl0ZXJzLCBpLmUu\
                IDEyMzQ1Njc4LCA4NzY1NDMyMS4uLjwvcD4NCjxwPlRoZXJlIGlzIHNvbWUgcnVkaW1lbnRhcnkg\
                ZXJyb3ItY2hlY2tpbmcuIElmIHlvdSB0cnkgdG8gaW5zZXJ0IGFueXRoaW5nIGJ1dCBudW1iZXJz\
                IGludG8gdm9sdGFnZSBvciBrVkEgZmllbGRzLCBpdCdsbCB0aHJvdyBhbiBlcnJvcjsgaWYgeW91\
                IG1peCBwaGFzZS1waGFzZSBhbmQgcGhhc2UtZ3JvdW5kIHZvbHRhZ2VzIGZvciBWcHJpL1ZzZWMs\
                IHlvdSdsbCBiZSB3YXJuZWQsIGJ1dCBhbGxvd2VkIHRvIGNvbnRpbnVlIGlmIGRlc2lyZWQuIFNp\
                bWlsYXJseSwgaWYgeW91IHVzZSBhIG5vbi1hbHBoYW51bWVyaWMgY2hhcmFjdGVyIGluIHRoZSBQ\
                b2xlICMgZmllbGQsIHlvdSdsbCBiZSB3YXJuZWQsIGJ1dCBpdCBjYW4gcmVtYWluIGlmIGRlc2ly\
                ZWQuIE5vdGUgdGhhdCBhdXRvLWluY3JlbWVudGluZyBpcyBkaXNhYmxlZCBmb3Igc3VjaCBjYXNl\
                cy48L3A+DQo8cD5UbyBnZXQgR1BTIGNvb3JkaW5hdGVzLCB1c2UgdGhlIEdldCBMYXRcTG9uZyBi\
                dXR0b24gLSB0aGVyZSBtYXkgYmUgYSBkZWxheSwgYXMgdGhlIHByb2dyYW0gbG9vcHMgcmVhZGlu\
                ZyB0aGUgbWVzc2FnZXMgdW50aWwgYSB2YWxpZCAoaS5lLiBub3QgMC4wLDAuMCBMYXQvTG9uZykg\
                aXMgcmVjZWl2ZWQuPC9wPg0KPHA+V2hlbiB5b3UgaGF2ZSBjb21wbGV0ZWQgZW50ZXJpbmcgZGF0\
                YSBmb3IgdGhlIHBvbGUvdHJhbnNmb3JtZXIsIHNlbGVjdCBTYXZlLCB0aGVuIENsZWFyXE5leHQg\
                RW50cnkuIFRoaXMgd2lsbCB3cml0ZSB0aGUgZGF0YSB0byB0aGUgQ1NWIGZpbGUgeW91IHNlbGVj\
                dGVkIHVwb24gbGF1bmNoaW5nIHRoZSBwcm9ncmFtLjwvcD4NCjxwPk5vdGUgdGhhdCAoaWYgZGF0\
                YSBpcyBlbnRlcmVkKSB0aGUgVnByaSwgVnNlYywgYW5kIE92ZXJoZWFkL1BhZG1vdW50IGZpZWxk\
                cyBhcmUgcGVyc2lzdGVudDsgdGhpcyBpcyBiZWNhdXNlIHRob3NlIHZhbHVlcyByYXJlbHkgY2hh\
                bmdlIGZyb20gb25lIHRvIHRoZSBuZXh0LCBhbmQgaXQgc2F2ZXMgb24gcmVwZXRpdGl2ZSBkYXRh\
                IGVudHJ5LiBJZiB5b3UgbmVlZCB0byBjaGFuZ2UgdGhlbSwgc2ltcGx5IG1hbnVhbGx5IG92ZXJ3\
                cml0ZSB0aGUgZmllbGRzLjwvcD4NCjxwPlRoZSAiKz0xIiBjaGVja2JveCBuZXh0IHRvIHRoZSBQ\
                b2xlIE51bWJlciBmaWVsZCBpcyB1c2VmdWwgd2hlbiByZWNvcmRpbmcgZGF0YSBpbiBvcmRlcjsg\
                aWYgc2VsZWN0ZWQsIHVwb24gaGl0dGluZyBTYXZlL05leHQgRW50cnksIHRoZSBQb2xlIE51bWJl\
                ciB3aWxsIGluY3JlbWVudCBieSBvbmUuIEV4YW1wbGVzOjwvcD4NCjx1bD4NCjxsaT5CUlc0IC0m\
                Z3Q7IEJSVzUuPC9saT4NCjxsaT5CUlc0LU45IC0mZ3Q7IEJSVzQtTjEwLjwvbGk+DQo8L3VsPg0K\
                PHA+T25seSB0aGUgbGFzdCBlbGVtZW50IG9mIHRoZSBzdHJpbmcgaXMgaW5jcmVtZW50ZWQ7IGFs\
                c28gbm90ZSB0aGF0IHRoZSBwcm9ncmFtIGRvZXMgbm90IGhhbmRsZSBpbml0aWF0aW5nIHRha2Vv\
                ZmZzLiBJZiB5b3UgbmVlZCwgZm9yIGV4YW1wbGUsIEJSVzQtTjkgdG8gYmVjb21lIEJSVzQtTjkt\
                TjEsIHlvdSB3aWxsIGhhdmUgdG8gbWFudWFsbHkgdHlwZSB0aGF0IGluLiBGb2xsb3dpbmcgaXRl\
                bXMgd291bGQgYmVjb21lIEJSVzQtTjktTjIsIGV0Yy48L3A+DQo8aDQ+S25vd24gSXNzdWVzL1dv\
                cmthcm91bmRzOjwvaDQ+DQo8cD5PY2Nhc2lvbmFsbHksIHdoZW4gcmV0cmlldmluZyBHUFMgY29v\
                cmRpbmF0ZXMsIHRoZSBDT00gcG9ydCB3aWxsIGJlY29tZSBsb2NrZWQsIGFuZCB0aGUgcHJvZ3Jh\
                bSB3aWxsIGZyZWV6ZSwgbmVjZXNzaXRhdGluZyB0aGUgY29tcHV0ZXIgdG8gYmUgcmVib290ZWQu\
                IEkgaGF2ZSBtb2RpZmllZCB0aGUgcHJvZ3JhbSB0byBvcGVuIGFuZCBjbG9zZSB0aGUgQ09NIHBv\
                cnQgYmV0d2VlbiBlYWNoIHNldCBvZiBjb29yZGluYXRlcywgd2hpY2ggSSBiZWxpZXZlIGhhcyBm\
                aXhlZCB0aGUgaXNzdWUsIGJ1dCBpZiBpdCBvY2N1cnMsIHJlYm9vdC4gQWRkaXRpb25hbGx5LCBh\
                cyBhIG1lYW5zIG9mIG1pdGlnYXRpb24sIGl0IGlzIHJlY29tbWVuZGVkIHRvIGdldCBHUFMgY29v\
                cmRpbmF0ZXMgZmlyc3QgYmVmb3JlIGlucHV0dGluZyBhbnkgb3RoZXIgZGF0YTsgdGhpcyB3YXks\
                IHlvdSB3aWxsIG5vdCBoYXZlIGxvc3QgYW55dGhpbmcgdHlwZWQgaW4sIGFzIHRoZSBDU1YgZmls\
                ZSBpcyBvcGVuZWQsIHVwZGF0ZWQsIGFuZCBjbG9zZWQgd2l0aCBlYWNoIFNhdmUuPC9wPg0KPGg0\
                PkxpY2Vuc2U8L2g0Pg0KPHA+R1BTIFRhZ2dlcjxiciAvPiBDb3B5cmlnaHQgKEMpIDIwMTcgU3Rl\
                cGhhbiBHYXJsYW5kPGJyIC8+c3RlcGhhbi5tYXJjLmdhcmxhbmRAZ21haWwuY29tPC9wPg0KPHA+\
                VGhpcyBwcm9ncmFtIGlzIGZyZWUgc29mdHdhcmU6IHlvdSBjYW4gcmVkaXN0cmlidXRlIGl0IGFu\
                ZC9vciBtb2RpZnk8YnIgLz4gaXQgdW5kZXIgdGhlIHRlcm1zIG9mIHRoZSBHTlUgR2VuZXJhbCBQ\
                dWJsaWMgTGljZW5zZSBhcyBwdWJsaXNoZWQgYnk8YnIgLz4gdGhlIEZyZWUgU29mdHdhcmUgRm91\
                bmRhdGlvbiwgZWl0aGVyIHZlcnNpb24gMyBvZiB0aGUgTGljZW5zZSwgb3I8YnIgLz4gKGF0IHlv\
                dXIgb3B0aW9uKSBhbnkgbGF0ZXIgdmVyc2lvbi48L3A+DQo8cD5UaGlzIHByb2dyYW0gaXMgZGlz\
                dHJpYnV0ZWQgaW4gdGhlIGhvcGUgdGhhdCBpdCB3aWxsIGJlIHVzZWZ1bCw8YnIgLz4gYnV0IFdJ\
                VEhPVVQgQU5ZIFdBUlJBTlRZOyB3aXRob3V0IGV2ZW4gdGhlIGltcGxpZWQgd2FycmFudHkgb2Y8\
                YnIgLz4gTUVSQ0hBTlRBQklMSVRZIG9yIEZJVE5FU1MgRk9SIEEgUEFSVElDVUxBUiBQVVJQT1NF\
                LiBTZWUgdGhlPGJyIC8+IEdOVSBHZW5lcmFsIFB1YmxpYyBMaWNlbnNlIGZvciBtb3JlIGRldGFp\
                bHMuPC9wPg0KPHA+WW91IHNob3VsZCBoYXZlIHJlY2VpdmVkIGEgY29weSBvZiB0aGUgR05VIEdl\
                bmVyYWwgUHVibGljIExpY2Vuc2U8YnIgLz4gYWxvbmcgd2l0aCB0aGlzIHByb2dyYW0uIElmIG5v\
                dCwgc2VlICZsdDtodHRwOi8vd3d3LmdudS5vcmcvbGljZW5zZXMvJmd0Oy48L3A+'

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
        # This one specific item is called out as the pole number frequently increments
        if (entry[0] == 'gs_equipment_location' and output_check_var.get() == 1):
            incremented_pole_field = increment_pole_number(entry)
            if not incremented_pole_field: # Catches increment_pole_number's none return if a typo is made
                return
            entry[1].delete(0, tk.END)
            entry[1].insert(0, incremented_pole_field)

        # Don't erase input/output voltages or OHD/PAD on transformers, as they rarely change
        elif (entry[0] == 'gs_rated_input_voltage'\
           or entry[0] == 'gs_rated_output_voltage' or entry[0] == 'gs_substype_cd'):
            pass

        else:
            text = entry[1]
            text.delete(0, tk.END)


def increment_pole_number(pole_field):
    global pole_num_typo_deliberate
    text = pole_field[1].get()
    mod_text = str(text)
    last_ele = mod_text.split('-')[-1:][0]
    last_alpha = ''.join(filter(lambda x: not x.isdigit(), mod_text))

    if not any(x.isdigit() for x in last_ele):
        # If the last element is entirely non-numeric, don't increment
        pass
    # Thanks to Brian on SO - https://stackoverflow.com/a/266162/4221094
    elif not last_ele.translate(str.maketrans('', '', string.punctuation)) == last_ele:
        # If there are punctuation marks (assuming a typo), don't try to parse it
        # but also inquire if it was deliberate, so they can fix the error
        if not pole_num_typo_deliberate:
            typo_in_pole_name = tkMsg.askyesno("Just checking", "Did you mean to include a non-alphanumeric character?")
            if typo_in_pole_name:
                tkMsg.showinfo("", "OK! I won't ask you again.")
                pole_num_typo_deliberate = True
                pass
            else:
                pole_num_typo_deliberate = False
                return
    else:
        # Given an input like "BRW4-N6", it is split into ['BRW4', 'N6']
        # The last element of the list is then converted into a string via slicing
        # A filter is run to generate the numeric and non-numeric portions with .isdigit()
        # It's all joined with map, with the original mod_text being sliced to exclude
        # the last element, last_char, and last_num, which is incremented by one
        last_num = int(''.join(filter(lambda x: x.isdigit(), last_ele)))
        last_char = ''.join(filter(lambda x: not x.isdigit(), last_ele))

        if "-" in mod_text:
            if last_ele[1].isdigit() and last_ele[0].isalpha():
                mod_text = '-'.join(map(str, mod_text.split('-')[:-1])) + '-' + last_char + str(last_num + 1)
            else:
                mod_text = '-'.join(map(str, mod_text.split('-')[:-1])) + '-' + str(last_num + 1) + last_char
        # If the entry has no "-", e.g. BRW4, use this instead to avoid -BRW5
        else:
            mod_text = last_alpha + str(last_num + 1)
    return mod_text


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
    if error_checking(entries):
        clear_entries(entries)
        inputs = {}
        for entry in entries:
            field = entry[0]
            text = entry[1].get()
            if text:
                inputs[field] = str(text)
        wrangle_data(inputs)


def error_checking(entries):
    global line_ground_typo_deliberate
    common_input_voltages = ([2770, 4800, 7200, 12470, 13220, 22900, 19920, 34500,
        39840, 69000, 66400, 115000, 132800, 230000, 199200, 345000,
        288680, 500000, 441690, 765000])
    common_output_voltages = [120, 208, 240, 415, 277, 480]
    try:
        if not entries[2][1].get() == '':
            input_voltage = int(entries[2][1].get()) # gs_rated_input_voltage
        else:
            input_voltage = None
        if not entries[3][1].get() == '':
            output_voltage = int(entries[3][1].get()) # gs_rated_output_voltage
        else:
            output_voltage = None
        if not entries[5][1].get() == '':
            rated_kva = int(entries[3][1].get()) # gs_rated_kva
    except ValueError:
        tkMsg.showerror("Error", "Please only input numbers into voltage fields.")
        return
    except TypeError:
        pass

    if  (
        output_voltage in common_output_voltages[0::2]
            and
        input_voltage in common_input_voltages[1::2]
        ):
            if line_ground_typo_deliberate:
                pass
            else:
                check_voltage_sanity = tkMsg.askyesno("Just checking", \
                    "Did you mean to mix line-ground and line-phase voltages?")
                if check_voltage_sanity:
                    tkMsg.showinfo("", "OK! I won't ask you again.")
                    line_ground_typo_deliberate = True
                else:
                    line_ground_typo_deliberate = False
                    return
    return True


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
                writer.writerow([]) # Inserts a blank row between entries
            else:
                for k,v in inputs.items():
                    writer.writerow([k, v])
                writer.writerow([])

    # Naturally, Python 3 has a new way of dealing with this
    else:
        with open(csv_file_name, 'a', newline='') as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(["Parameter", "Value"])
                for k,v in inputs.items():
                    writer.writerow([k, v])
                writer.writerow([])
            else:
                for k,v in inputs.items():
                    writer.writerow([k, v])
                writer.writerow([])


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
