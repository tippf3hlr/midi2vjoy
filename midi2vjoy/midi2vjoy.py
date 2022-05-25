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
axis = {
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
    'X': 0,
    'Y': 0,
    'Z': 0,
    'RX': 0,
    'RY': 0,
    'RZ': 0,
    'SL0': 0,
    'SL1': 0,
    'WHL': 0,
    'POV': 0
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
# slider:
midi_key midi_channel --slider-> vJoy_id axis

# button-axis ("button" to increase or decrease axis):
midi_key midi_channel midi_status --button-axis-> vJoy_id axis +50
midi_key midi_channel midi_status --button-axis-> vJoy_id axis -50

# button:
midi_key midi_channel midi_status --button-> vJoy_id button down
midi_key midi_channel midi_status --button-> vJoy_id button up
midi_key midi_channel midi_status(down),midi_status(up) --button-> vJoy_id button down,up
'''

'''
config = {
(midi_key, midi_channel): (mode, midi_status(slider: midi_status=0) vJoy_id, vJoy_axis/button, value))
}
'''


def read_conf(conf_file):
    config = {}
    vJoy_IDs = []
    with open(conf_file, 'r') as file:
        for line in file:
            try:
                if len(line.strip()) == 0 or line[0] == '#':
                    continue
                fs = line.split()

                if fs[3] is not "->":
                    raise Exception('Unknown command in config file')

                if fs[0] == 'axis':
                    return
                elif fs[0] == 'wheel':
                    return
                elif fs[0] == 'button':
                    return
                else:
                    raise Exception('Unknown command in config file')
                if fs[0] == '176':
                    key = (int(fs[0]), int(fs[1]), 0)
                    val = (int(fs[3]), fs[4])

                    if options.verbose:
                        print('slider', key, val)
                    config[key] = val
                    vid = int(fs[3])
                    if not vid in vJoyIDs:
                        vJoyIDs.append(vid)

                if is_int(fs[4]):
                    input_value = int(-1)
                    if fs[2] != '*':
                        input_value = int(fs[2])
                    key = (int(fs[0]), int(fs[1]), 1, input_value)

                    v_value = int(1)
                    if len(fs) >= 6 and fs[5] == 'up':
                        v_value = int(0)
                    if len(fs) >= 6 and fs[5] == 'press_and_release':
                        # we do like using obscure integers to signal things in this project, right?
                        v_value = int(-1)

                    val = (int(fs[3]), int(fs[4]), v_value)

                    if options.verbose:
                        print('button', key, val)
                    config[key] = val
                    vid = int(fs[3])
                    if not vid in vJoyIDs:
                        vJoyIDs.append(vid)

            except:
                print('error at line', line)
                traceback.print_exc()

    return (config, vJoy_IDs)


def joystick_run():
    # Process the configuration file
    if options.conf == None:
        print('You have to specify a configuration file')
        return
    try:
        verbose('Opening configuration file:', options.conf)
        (config, vJoy_IDs) = read_conf(options.conf)
        verbose("Config:", config)
        verbose("vJoy IDs:", vJoy_IDs)
    except:
        print('Error processing the configuration file:', options.conf)
        return

    # Getting the MIDI device ready
    if options.midi == None:
        print('You have to specify a MIDI interface to use')
        return
    try:
        verbose('Opening MIDI device:', options.midi)
        midi = pygame.midi.Input(options.midi)
    except:
        print('Error opening MIDI device', options.midi)
        return

    # Load vJoysticks
    try:
        # Load the vJoy library
        # Load the registry to find out the install location
        vjoy_reg_key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{8E31F76F-74C3-47F1-9550-E041EEDC5FBB}_is1')
        installpath = winreg.QueryValueEx(vjoy_reg_key, 'InstallLocation')[0]
        winreg.CloseKey(vjoy_reg_key)

        verbose("VJoy install path", installpath)

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
        print('Error initializing virtual joysticks')
        return

    try:
        print('Ready. Use ctrl-c to quit.')
        while True:
            while midi.poll():
                input = midi.read(1)
                verbose("MIDI input:", input)

                key = (input[0][0], input[0][1])
                if key in config:
                    task = config[key]
                    if task[0] is "slider":
                        vJoy_ID = task[2]
                        value = input[0][0][2]
                        vjoy.SetAxis(value, opt[0], axis[opt[1]])
                # slider key has 0 as 3rd element
                slider_key = (input[0][0][0], input[0][0][1], 0)
                if slider_key in config:
                    # A slider input
                    # Check that the output axis is valid
                    # Note: We did not check if that axis is defined in vJoy
                    opt = config[slider_key]
                    if opt[1] in axis:
                        value = input[0][0][2]
                        verbose('slider', slider_key, '->', opt, value)

                        # MIDI is 0-127, vJoy is 1-32768 (?)
                        value = (value + 1) << 8
                        vjoy.SetAxis(value, opt[0], axis[opt[1]])

                # button key has 1 as 3rd element, if button value is not * then this value is 4th element
                button_key = (
                    input[0][0][0], input[0][0][1], 1, input[0][0][2])
                # if no mapping for exact match
                if not button_key in config:
                    # set button key for "any" match (* in config)
                    button_key = (input[0][0][0],
                                  input[0][0][1], 1, -1)

                if button_key in config:
                    opt = config[button_key]

                    # A button input
                    if opt[2] == -1:
                        verbose('button', button_key, '->',
                                opt, 'press_and_release')

                        already_waiting_for_release = False
                        for rq_index in range(len(release_queue)):
                            if release_queue[rq_index][1] == opt[0] and release_queue[rq_index][2] == opt[1]:
                                already_waiting_for_release = True
                                verbose('button', button_key,
                                        'already pressed and waiting for release')

                        if not already_waiting_for_release:
                            vjoy.SetBtn(1, opt[0], opt[1])
                            delay = 0.1  # in seconds
                            release_queue.append(
                                (0, opt[0], opt[1], button_key, time.time() + delay))
                    else:
                        verbose('button', button_key, '->', opt, opt[2])
                        vjoy.SetBtn(opt[2], opt[0], opt[1])

            time.sleep(0.01)
    except KeyboardInterrupt:
        quit()
    except:
        traceback.print_exc()
        pass

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
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose")
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
