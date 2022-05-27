#  midi2vjoy.py
#
#  Copyright 2017  <c0redumb>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

import sys
import os
import time
from tkinter import E
import traceback
import ctypes
from optparse import OptionParser
import pygame.midi
import winreg
import platform

# Constants
# Axis mapping
axis_table = {
    'X': 0x30,
    'Y': 0x31,
    'Z': 0x32,
    'RX': 0x33,
    'RY': 0x34,
    'RZ': 0x35,
    'SL0': 0x36,
    'SL1': 0x37,
    'WHL': 0x38,
    'POV': 0x39
}

axis_value = {
    0x30: 0,
    0x31: 0,
    0x32: 0,
    0x33: 0,
    0x34: 0,
    0x35: 0,
    0x36: 0,
    0x37: 0,
    0x38: 0,
    0x39: 0
}

# Globals
options = None


def is_int(number):
    try:
        int(number)
        return True
    except ValueError:
        return False


def midi_test():
    device_count = pygame.midi.get_count()

    # List all the devices and make a choice
    print('Input MIDI devices:')
    for device_number in range(device_count):
        (interf, name, input, output,
         opened) = pygame.midi.get_device_info(device_number)
        if input:
            print(str(device_number) + ":", "\"" + name.decode() + "\"")
    try:
        selected_device_number = int(input('Select MIDI device to test: '))
    except KeyboardInterrupt:
        quit()
    except:
        if(options.verbose):
            traceback.print_exc()
        else:
            print('You have to specify a valid device number')
            if m is not None:
                m.close()
            midi_test()
    # Open the device for testing
    try:
        m = None
        print('Opening MIDI device:', selected_device_number)
        m = pygame.midi.Input(selected_device_number)
        print('Device opened for testing. Use ctrl-c to quit.')
        while True:
            while m.poll():
                print(m.read(1))
            time.sleep(0.1)
    except:
        if options.verbose:
            traceback.print_exc()
        else:
            print('You have to specify a valid device number')
            if m is not None:
                m.close()
            midi_test()
    finally:
        if m is not None:
            m.close()


'''
# slider starting position
X 16384
Y 0

# slider:
midi_key midi_channel --slider-> vJoy_id axis

# button-axis ("button" to increase or decrease axis):
midi_key midi_channel midi_value --button-axis-> vJoy_id axis +50
midi_key midi_channel midi_value --button-axis-> vJoy_id axis -50

# button:
midi_key midi_channel midi_value --button-> vJoy_id button down
midi_key midi_channel midi_value --button-> vJoy_id button up
'''

'''
config = {
(midi_key, midi_channel): (mode, midi_value(slider: midi_value=0) vJoy_id, vJoy_axis/button, value))
}
'''


def read_conf(conf_file):
    config = {}
    vJoy_IDs = []
    with open(conf_file, 'r') as file:
        for index, line in enumerate(file):
            try:
                if len(line.strip()) == 0 or line[0] == '#':
                    continue
                args = line.split()

                # slider starting position
                if args[0].upper() in axis_table.keys():
                    axis_value[axis_table[args[0].upper()]] = int(args[1])
                    continue

                midi_key = int(args[0])
                midi_channel = int(args[1])
                if args[2] == "--slider->":
                    mode = "slider"
                    midi_value = None
                    vJoy_id = int(args[3])
                    axis_button = axis_table[args[4]]
                    action = None
                elif args[3] == "--button->":
                    midi_value = int(args[2])
                    mode = "button"
                    vJoy_id = int(args[4])
                    axis_button = int(args[5])
                    if args[6] == "down":
                        action = 1
                    elif args[6] == "up":
                        action = 0
                elif args[3] == "--button-axis->":
                    midi_value = int(args[2])
                    mode = "button-axis"
                    vJoy_id = int(args[4])
                    axis_button = axis_table[args[5]]
                    action = int(args[6])
                if not (midi_key, midi_channel) in config:
                    config[(midi_key, midi_channel)] = [
                        (mode, midi_value, vJoy_id, axis_button, action)]
                else:
                    config[(midi_key, midi_channel)].append(
                        (mode, midi_value, vJoy_id, axis_button, action))
                if vJoy_id not in vJoy_IDs:
                    vJoy_IDs.append(vJoy_id)
            except:
                print("Encountered an error in", conf_file, "at line", index)
                if options.verbose:
                    traceback.print_exc()
                quit()

    return (config, vJoy_IDs)


def joystick_run():
    # Process the configuration file
    if options.conf == None:
        print('You have to specify a configuration file')
        return
    verbose('Opening configuration file:', options.conf)
    try:
        (config, vJoy_IDs) = read_conf(options.conf)
    except:
        print('Error processing the configuration file:', options.conf)
        if config.verbose:
            traceback.print_exc()
        return
    verbose("Config:", config)

    verbose("vJoy IDs:", vJoy_IDs)
    if options.verbose:
        verbose("---------------------")
        for axis in axis_value:
            verbose("   " + list(axis_table.keys())[
                    list(axis_table.values()).index(axis)], (3 - len(list(axis_table.keys())[
                        list(axis_table.values()).index(axis)])) * " ", axis_value[axis])
        verbose("---------------------\n")

    # Getting the MIDI device ready
    if options.midi == None:
        print('You have to specify a MIDI interface to use')
        return
    try:
        verbose('Opening MIDI device:', options.midi)
        midi = pygame.midi.Input(options.midi)
    except:
        print('Error opening MIDI device', options.midi)
        if config.verbose:
            traceback.print_exc()
        return

    # Load vJoysticks
    try:
        # Load the vJoy library
        # Load the registry to find out the install location
        vjoy_reg_key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{8E31F76F-74C3-47F1-9550-E041EEDC5FBB}_is1')
        installpath = winreg.QueryValueEx(vjoy_reg_key, 'InstallLocation')[0]
        winreg.CloseKey(vjoy_reg_key)

        verbose("vJoy install path:", installpath)

        if platform.machine().endswith('64'):
            arch = 'x64'
        else:
            arch = 'x86'
        dll_path = os.path.join(installpath, arch, 'vJoyInterface.dll')
        vjoy = ctypes.WinDLL(dll_path)
        verbose("VJoy version", vjoy.GetvJoyVersion())

        # Getting ready
        for vid in vJoy_IDs:
            verbose('Acquiring vJoystick:', vid)
            assert(vjoy.AcquireVJD(vid) == 1)
            assert(vjoy.GetVJDStatus(vid) == 0)
            vjoy.ResetVJD(vid)
    except:
        traceback.print_exc()
        print('Error initializing virtual joysticks. Is vJoy installed?')
        return

    try:
        print('Ready. Use Ctrl-C to quit.')
        for axis in axis_table:
            vjoy.SetAxis(axis_table[axis], 1, axis)
        while True:
            while midi.poll():
                input = midi.read(1)[0][0]
                input.pop()
                input_pretty = "MIDI: {: 4d} {: 4d} {: 4d}".format(
                    input[0], input[1], input[2])
                key = (input[0], input[1])
                if key in config:
                    for (mode, midi_value, vJoy_id, axis_button, action) in config[key]:
                        if mode == "slider":
                            # MIDI is 0-127, vJoy is 1-32768 (?)
                            value = (input[2] + 1) << 8
                            axis_value[axis_button] = value
                            vjoy.SetAxis(value, vJoy_id, axis_button)
                            verbose(input_pretty, "   --slider->   ", "vJoy#", vJoy_id,
                                    "axis", list(axis_table.keys())[list(axis_table.values()).index(axis_button)], "value", value)
                        elif mode == "button":
                            if midi_value == input[2]:
                                vjoy.SetBtn(action, vJoy_id, axis_button)
                                verbose(input_pretty, "   --button->   ", "vJoy#", vJoy_id,
                                        "button", axis_button, "on" if action else "off")
                        elif mode == "button-axis":
                            if midi_value == input[2]:
                                axis_value[axis_button] += action
                                if axis_value[axis_button] > 32768:
                                    axis_value[axis_button] = 32768
                                elif axis_value[axis_button] < 0:
                                    axis_value[axis_button] = 0
                                vjoy.SetAxis(
                                    axis_value[axis_button], vJoy_id, axis_button)
                                verbose(input_pretty, " --button-axis->", "vJoy#", vJoy_id,
                                        "axis", list(axis_table.keys())[list(axis_table.values()).index(axis_button)], "value", "{: 6d}".format(axis_value[axis_button]))
                else:
                    verbose(input_pretty)
            time.sleep(0.01)
    except KeyboardInterrupt:
        quit()
    except:
        traceback.print_exc()
        pass
    finally:
        # Relinquish vJoysticks
        for vid in vJoy_IDs:
            print('Relinquishing vJoystick:', vid)
            vjoy.RelinquishVJD(vid)

        print('Closing MIDI device')
        midi.close()


def verbose(*message):
    if options.quiet:
        return
    if not options.verbose:
        return
    string = ""
    for s in message:
        string += ' ' + str(s)
    print(string)


def help_page():
    print(
        '''            _     _ _ ____           _
  _ __ ___ (_) __| (_)___ \__   __  | | ___  _   _
 | '_ ` _ \| |/ _` | | __) \ \ / /  | |/ _ \| | | |
 | | | | | | | (_| | |/ __/ \ V / |_| | (_) | |_| |
 |_| |_| |_|_|\__,_|_|_____| \_/ \___/ \___/ \__, |
                                             |___/

Use MIDI controllers as joysticks with the help of midi2vJoy and vJoy.

usage: python midi2vjoy.py -m <midi_device> -c <config_file> [-v] [-q]
    -t  --test:         display raw MIDI input
    -m  --midi:         MIDI device to use. To see available devices, use -t
    -c  --config:       path to a config file (see example_config.conf)
    -v  --verbose:      verbose output
    -q  --quiet:        no output
'''
    )


def main():
    parser = OptionParser()
    parser.add_option("-t", "--test", dest="runtest",
                      action="store_true", help="To test the midi inputs")
    parser.add_option("-m", "--midi", dest="midi", action="store",
                      type="int", help="File holding the list of file to be checked")
    parser.add_option("-c", "--conf", dest="conf", action="store",
                      help="Configuration file for the translation")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose")
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet")
    global options
    options, args = parser.parse_args()

    pygame.midi.init()

    if options.runtest:
        midi_test()
    elif not options.midi and not options.conf:
        help_page()
    else:
        joystick_run()

    pygame.midi.quit()


if __name__ == '__main__':
    main()
