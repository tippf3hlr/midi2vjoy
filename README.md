# midi2vjoy

## 0. This is a modified version of midi2joy

New features include:

- Can send button-up commands, not only button-down
- Can send button press-and-release after 0.1s event
- Can send button event when joystick axis reaches a value (usually highest or lowest value)

Configuration is almost the same as original, but there are changes in config file format.
Look at nanocontrol2.conf for an example:

```conf
# This example maps nanoKONTROL2 to 1 vJoy device with 6 axises and 40 buttons
# This is used for MSFS, and knobs work as buttons that are pressed and released when the knob reaches lowest or highest value
#
# Midi to vJoy translation
# The format is one line for each control in the format of
#       m_type, m_control, m_value, v_id, v_number, [v_output]
# m_type is the 176 (slider) or other (button).
# m_control is the ID of the midi message.
# m_value is the value of the midi message (valid only for buttons, use * to match any).
# The [m_type, m_control, m_value, ..] of each MIDI input can be found
#   when running the program in test mode. Just push/move the control
#   and watch the messages showing up on the screen.
# v_id is the vJoystick ID where the MIDI message is translated to.
# v_number is the axis or button number MIDI message is contolling.
# v_output is only available for buttons. If it is not specified, output is 'down'.
#   Special 'press_and_release' output preses buton and then releases it. useful for mapping slider end positions to 
#   buttons, to avoid a situation where such slider cause constant button down in a sim. In MSFS this causes heading indicator
#   to skip 10 values for some reason
# The axis may be 'X', 'Y', 'Z', 'RX', 'RY', 'RZ', 'SL0', or 'SL1'.

# sliders
# input     vjoy index      axis
176 36 *    1               X
176 37 *    1               Y
176 38 *    1               Z
176 39 *    1               RX
176 40 *    1               RY
176 41 *    1               RZ
176 42 *    1               SL0
176 43 *    1               SL1

# knobs as buttons
# input     vjoy index      output button       action
176 0 0     1               1                   press_and_release
176 0 127   1               2                   press_and_release

176 1 0     1               3                   press_and_release
176 1 127   1               4                   press_and_release

176 2 0     1               5                   press_and_release
176 2 127   1               6                   press_and_release

176 3 0     1               7                   press_and_release
176 3 127   1               8                   press_and_release

176 4 0     1               9                   press_and_release
176 4 127   1               10                  press_and_release

176 5 0     1               11                  press_and_release
176 5 127   1               12                  press_and_release

176 6 0     1               13                  press_and_release
176 6 127   1               14                  press_and_release

176 7 0     1               15                  press_and_release
176 7 127   1               16                  press_and_release

# buttons
# input     vjoy index      output button       action
144 0 *     1               17                  down
128 0 *     1               17                  up
144 72 *    1               18                  down
128 72 *    1               18                  up

144 1 *     1               19                  down
128 1 *     1               19                  up
144 37 *    1               20                  down
128 37 *    1               20                  up
144 73 *    1               21                  down
128 73 *    1               21                  up

144 2 *     1               22                  down
128 2 *     1               22                  up
144 38 *    1               23                  down
128 38 *    1               23                  up
144 74 *    1               24                  down
128 74 *    1               24                  up

144 3 *     1               25                  down
128 3 *     1               25                  up
144 39 *    1               26                  down
128 39 *    1               26                  up
144 75 *    1               27                  down
128 75 *    1               27                  up

144 4 *     1               28                  down
128 4 *     1               28                  up
144 40 *    1               29                  down
128 40 *    1               29                  up
144 76 *    1               30                  down
128 76 *    1               30                  up

144 5 *     1               31                  down
128 5 *     1               31                  up
144 41 *    1               32                  down
128 41 *    1               32                  up
144 77 *    1               33                  down
128 77 *    1               33                  up

144 6 *     1               34                  down
128 6 *     1               34                  up
144 42 *    1               35                  down
128 42 *    1               35                  up
144 78 *    1               36                  down
128 78 *    1               36                  up

144 7 *     1               37                  down
128 7 *     1               37                  up
144 43 *    1               38                  down
128 43 *    1               38                  up
144 79 *    1               39                  down
128 79 *    1               39                  up
```

The rest of this README is not updated, but the steps
for getting it working are the same.

## 1. Introduction

This software provides a way to use MIDI controllers as joysticks.

A typical real joystick usually has only a few axis. This is limited by the HID specification of joystick. However, often when one plays complex games many axis of control are needed. For example, in flight simulators, the throttle, mixture, propeller, etc. all need their own control axis that is not available on common joysticks.

MIDI controllers have many sliders, and is a good candidate for use in this scenario. A few things are needed to get that to work as game controllers. Fortunately, a software called vJoy (http://vjoystick.sourceforge.net) can emulate joysticks in the system. This software reads the input from MIDI controllers, and drives the virtual joysticks created by vJoy.

This code is available through "Simplified BSD License".

## 2. How to use it

### 2.1. Overview

I will use the M-Audio Xsession-Pro as an example to show you how to use the midi2vjoy software.

1. Download and install vJoy from http://vjoystick.sourceforge.net/.
2. Use the vJoyConf tool ("vJoy" ->"Configure vJoy") to define the virtual joysticks (detail in 2.2).
3. Install midi2vjoy software.
4. Run "midi2vjoy -t" to test the code generated by MIDI device. These codes will be used for the configuration, so midi2vjoy know this vjoy axis or button to drive then the MIDI device is used (detail in 2.3).
5. Write/edit the mapping configuration file (detail in 2.4).
6. Run "midi2vjoy -m *midi* -c *conf*", where midi is the midi device and conf is the configuration file.

### 2.2. Configure vJoy

We need to configure the virtual joysticks based on the MIDI device we like to use. Here I use M-Audio Xsession-Pro as example. Xsession-Pro has 17 sliders and 10 buttons, so I divide that into three virtual joysticks.

![xsessionpro](/readme_images/xsessionpro.png)

With that, we will need to configure three virtual joysticks with vJoyConf tool. They are configured as following.

- vJoy #1: Z, Rx, Ry, Rz, Slider, and 8 Buttons;
- vJoy #2: Z, Rx, Ry, Rz, Slider, Slider2, and 1 Button;
- vJoy #3: Z, Rx, Ry, Rz, Slider, Slider2, and 1 Button.

### 2.3. Test MIDI device

To test the MIDI device, just run "midi2vjoy -t". First the program will print out a list of available MIDI input devices for you to choose. You will need to select the MIDI you want to use. For my Xsession-pro, it is number 1.

When the device is opened, you can mode the axis and press the buttons. The MIDI code that are sent by the MIDI device will be displayed on the screen. Just write down the first number (usually 176 for axis and 144 for buttons), and the second number (which is the index of the axis or buttons). Do this for all the axis and buttons you like to use. Use ctrl-c to exit the program.

Now you have all the necessary information to write a mapping configuration file.

In the example shown below, I am testing the MIDI interface 1. The axis I moved sent (176, 12), and the button I pressed sent (144, 46).

![test_cmd](/readme_images/test_cmd.png)

### 2.4. Edit mapping configuration file

The mapping configuration file is a simple text file. All lines starts with "#" are comments and will be ignored by the parser.

Each mapping line has four numbers. This correspond to mapping an axis or button from MIDI to the corresponding control on the virtual joysticks. The first two numbers are those you recorded in the midi test step above.

- m_type: This is 176 for axis and 144 for buttons;
- m_control: This is the index (the second number you recorded in the testing session for each control);
- v_id: The ID of the vJoy device (1, 2, 3, etc.);
- v_number: The axis name or button number on the vJoy device ("Z" for Z axis, and 3 for Button3).

Below the my mapping configuration file for Xsession-Pro.

```
# Midi to vJoy translation
# The format is one line for each control in the format of
#       m_type, m_control, m_value, v_id, v_number, [v_output]
# m_type is the 176 (slider) or other (button).
# m_control is the ID of the midi message.
# m_value is the value of the midi message (valid only for buttons, use * to match any).
# The [m_type, m_control, m_value, ..] of each MIDI input can be found
# when running the program in test mode. Just push/move the control
# and watch the messages showing up on the screen.
# v_id is the vJoystick ID where the MIDI message is translated to.
# v_number is the axis or button number MIDI message is contolling.
# v_output is only available for buttons. if it is not specified, output is 'down'
# The axis may be 'X', 'Y', 'Z', 'RX', 'RY', 'RZ', 'SL0', or 'SL1'.

176	12 * 1  Z
176	11 * 1	RX
176	14 * 1	RY
176	15 * 1	RZ
176	17 * 1	SL0
144	46 * 1	1
144	43 * 1	2
144	70 * 1	3
144	58 * 1	4
144	56 * 1	5
144	57 * 1	6
144	69 * 1	7
144	59 * 1	8

176	24 * 2	Z
176	25 * 2	SL0
176	26 * 2	SL1
176	27 * 2	RX
176	28 * 2	RY
176	29 * 2	RZ
144	44 * 2	1

176	31 * 3	Z
176	32 * 3	SL0
176	33 * 3	SL1
176	34 * 3	RX
176	35 * 3	RY
176	36 * 3	RZ
144	45 * 3	1
```

Once you have the configuration file, just run "midi2vjoy -m midi -c conf" to enjoy.

In my case, I will run:

```
midi2vjoy -m 1 -c xsessionpro.conf
```

See [nanokontrol2.conf](midi2vjoy/nanokontrol2.conf) file for nanoKONTROL2 example.
