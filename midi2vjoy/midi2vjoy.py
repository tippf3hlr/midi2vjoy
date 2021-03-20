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

import sys, os, time, traceback
import ctypes
from optparse import OptionParser
import pygame.midi
import winreg

# Constants
# Axis mapping
axis = {'X': 0x30, 'Y': 0x31, 'Z': 0x32, 'RX': 0x33, 'RY': 0x34, 'RZ': 0x35,
		'SL0': 0x36, 'SL1': 0x37, 'WHL': 0x38, 'POV': 0x39}

# Globals
options = None

def is_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def midi_test():
	n = pygame.midi.get_count()

	# List all the devices and make a choice
	print('Input MIDI devices:')
	for i in range(n):
		(i_interf, i_name, i_input, i_output, i_opened) = pygame.midi.get_device_info(i)
		if i_input == 1:
			print(i, "\"" + i_name.decode() + "\"")
	d = int(input('Select MIDI device to test: '))

	# Open the device for testing
	try:
		m = None
		print('Opening MIDI device:', d)
		m = pygame.midi.Input(d)
		print('Device opened for testing. Use ctrl-c to quit.')
		while True:
			while m.poll():
				print(m.read(1))
			time.sleep(0.1)
	except:
		traceback.print_exc()
		if m != None:
			m.close()

def read_conf(conf_file):
	'''Read the configuration file'''
	table = {}
	vids = []
	with open(conf_file, 'r') as f:
		for l in f:
			try:

				if len(l.strip()) == 0 or l[0] == '#':
					continue
				fs = l.split()

				if fs[0] == '176':
					key = (int(fs[0]), int(fs[1]), 0)
					val = (int(fs[3]), fs[4])

					if options.verbose:
						print('slider', key, val)
					table[key] = val
					vid = int(fs[3])
					if not vid in vids:
						vids.append(vid)
				
				if is_int(fs[4]):
					input_value = int(-1)
					if fs[2] != '*':
						input_value = int(fs[2])
					key = (int(fs[0]), int(fs[1]), 1, input_value)

					v_value = int(1)
					if len(fs) >= 6 and fs[5] == 'up':
						v_value = int(0)
					if len(fs) >= 6 and fs[5] == 'press_and_release':
						v_value = int(-1) # we do like using obscure integers to signal things in this project, right?

					val = (int(fs[3]), int(fs[4]), v_value)

					if options.verbose:
						print('button', key, val)
					table[key] = val
					vid = int(fs[3])
					if not vid in vids:
						vids.append(vid)
				
			except:
				print('error at line', l)
				traceback.print_exc()

	return (table, vids)

def joystick_run():
	# Process the configuration file
	if options.conf == None:
		print('Must specify a configuration file')
		return
	try:
		if options.verbose:
			print('Opening configuration file:', options.conf)
		(table, vids) = read_conf(options.conf)
		print(table)
		print(vids)
	except:
		print('Error processing the configuration file:', options.conf)
		return

	# Getting the MIDI device ready
	if options.midi == None:
		print('Must specify a MIDI interface to use')
		return
	try:
		if options.verbose:
			print('Opening MIDI device:', options.midi)
		midi = pygame.midi.Input(options.midi)
	except:
		print('Error opting MIDI device:', options.midi)
		return

	release_queue = []
	removed_queue_indices = []

	# Load vJoysticks
	try:
		# Load the vJoy library
		# Load the registry to find out the install location
		#vjoyregkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{8E31F76F-74C3-47F1-9550-E041EEDC5FBB}_is1')
		#winreg.QueryValueEx(vjoyregkey, 'InstallLocation')
		installpath = ["C:\\Program Files\\vJoy\\"]
		#winreg.CloseKey(vjoyregkey)

		if options.verbose:
			print("VJoy install path", installpath[0])

		dll_file = os.path.join(installpath[0], 'x64', 'vJoyInterface.dll')
		vjoy = ctypes.WinDLL(dll_file)
		if options.verbose:
			print("VJoy version", vjoy.GetvJoyVersion())

		# Getting ready
		for vid in vids:
			if options.verbose:
				print('Acquiring vJoystick:', vid)
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
			if len(release_queue) > 0:
				time_now = time.time()
				for i in range(len(release_queue)):
					queue_item = release_queue[i]
					if time_now > queue_item[4]:
						if options.verbose:
							print('button', queue_item[3], '->', 'release')
						removed_queue_indices.insert(0, i)
						vjoy.SetBtn(queue_item[0], queue_item[1], queue_item[2])

				if len(removed_queue_indices) > 0:
					for removed_index in removed_queue_indices:
						release_queue.pop(removed_index)
					removed_queue_indices = []
					

			while midi.poll():
				ipt = midi.read(1)
				if options.verbose:
					print(ipt)

				# slider key has 0 as 3rd element
				slider_key = (ipt[0][0][0], ipt[0][0][1], 0)
				if slider_key in table:
					# A slider input
					# Check that the output axis is valid
					# Note: We did not check if that axis is defined in vJoy
					opt = table[slider_key]
					if opt[1] in axis:
						reading = ipt[0][0][2]
						if options.verbose:
							print('slider', slider_key, '->', opt, reading)

						reading = (reading + 1) << 8
						vjoy.SetAxis(reading, opt[0], axis[opt[1]])

				# button key has 1 as 3rd element, if button value is not * then this value is 4th element
				button_key = (ipt[0][0][0], ipt[0][0][1], 1, ipt[0][0][2])
				# if no mapping for exact match
				if not button_key in table:
					# set button key for "any" match (* in config)
					button_key = (ipt[0][0][0], ipt[0][0][1], 1, -1)
				
				if button_key in table:
					opt = table[button_key]
					
					# A button input
					if opt[2] == -1:
						if options.verbose:
							print('button', button_key, '->', opt, 'press_and_release')

						already_waiting_for_release = False
						for rq_index in range(len(release_queue)):
							if release_queue[rq_index][1] == opt[0] and release_queue[rq_index][2] == opt[1]:
								already_waiting_for_release = True
								if options.verbose:
									print('button', button_key, 'already pressed and waiting for release')

						if not already_waiting_for_release:
							vjoy.SetBtn(1, opt[0], opt[1])
							delay = 0.1 # in seconds
							release_queue.append((0, opt[0], opt[1], button_key, time.time() + delay))
					else:
						if options.verbose:
							print('button', button_key, '->', opt, opt[2])
						vjoy.SetBtn(opt[2], opt[0], opt[1])

			time.sleep(0.01)
	except:
		traceback.print_exc()
		pass

	# Relinquish vJoysticks
	for vid in vids:
		print('Relinquishing vJoystick:', vid)
		vjoy.RelinquishVJD(vid)

	print('Closing MIDI device')
	midi.close()

def main():
	# parse arguments
	parser = OptionParser()
	parser.add_option("-t", "--test", dest="runtest", action="store_true",
					  help="To test the midi inputs")
	parser.add_option("-m", "--midi", dest="midi", action="store", type="int",
					  help="File holding the list of file to be checked")
	parser.add_option("-c", "--conf", dest="conf", action="store",
					  help="Configuration file for the translation")
	parser.add_option("-v", "--verbose",
						  action="store_true", dest="verbose")
	parser.add_option("-q", "--quiet",
						  action="store_false", dest="verbose")
	global options
	(options, args) = parser.parse_args()

	pygame.midi.init()

	if options.runtest:
		midi_test()
	else:
		joystick_run()

	pygame.midi.quit()

if __name__ == '__main__':
	main()
