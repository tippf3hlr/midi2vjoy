# midi2vJoy 2

works with endless encoders: use your dj controller as a steering wheel!

1. Download and install vJoy from [sourceforge](https://sourceforge.net/projects/vjoystick/)
2. Download midi2vjoy.exe from the [latest release](https://github.com/tippf3hlr/midi2vjoy/releases)
3. Test the MIDI connection with `midi2vjoy.exe -t`
4. Create mapping (Help: `midi2vjoy --config-help` or down below)
5. Start midi2vjoy.exe with `midi2vjoy.exe -c <your config file> -m <midi device id>`

If your config file is named `mapping.conf` and is located in the same directory as midi2vjoy.exe, you can start midi2vjoy with just `midi2vjoy.exe -m <midi device id>` or `midi2vjoy.exe` if your device number is 1.

```
            _     _ _ ____           _
  _ __ ___ (_) __| (_)___ \__   __  | | ___  _   _
 | '_ ` _ \| |/ _` | | __) \ \ / /  | |/ _ \| | | |
 | | | | | | | (_| | |/ __/ \ V / |_| | (_) | |_| |
 |_| |_| |_|_|\__,_|_|_____| \_/ \___/ \___/ \__, |
                                             |___/

Use MIDI controllers as joysticks with the help of midi2vJoy and vJoy.

Usage: midi2vjoy -m <midi_device> -c <config_file> [-v]
    -h  --help:         shows this help page
    --config-help       instructions to create a config file
    -t  --test:         display raw MIDI input
    -m  --midi:         MIDI device to use. To see available devices, use -t
    -c  --config:       path to a config file (see example_config.conf)
    -v  --verbose:      verbose output
    
Default config file is mapping.conf in the same directory as midi2vjoy.exe.
Default MIDI device is 1.
```
```
               __ _
  __ ___ _ _  / _(_)__ _
 / _/ _ \ ' \|  _| / _` |
 \__\___/_||_|_| |_\__, |
                   |___/

# a config file is a plain text file.
# lines starting with # are comments
# to get the midi values of your device, use -t

# blank lines are ignored
# midi2vJoy 2 has 3 modes:

# SLIDERS
# <midi_channel> <midi_subchannel> --slider-> <vJoy_id> <axis>
177 8 --slider-> 1 Z

# BUTTONS
# <midi_channel> <midi_subchannel> <midi_value> --button-> <vJoy_id> <button_id> <down/up>
146 7 127 --button-> 1 1 down
146 7 0 --button-> 1 1 up

# BUTTON-AXIS: this is a special one designed for endless encoders.
# It takes a button as an input and adds or subtracts a value to an axis.
# <midi_channel> <midi_subchannel> <midi_value> --button-axis-> <vJoy_id> <axis> <value>
178 10 1 --button-axis-> 1 Y +25
178 10 127 --button-axis-> 1 Y -25

# finally, you can use the following to set an axis to a specific value at startup:
# <axis> <value>
Y 16384
Z 0

# the axis range is 0-32768
# hint: 50% is 16384
```
