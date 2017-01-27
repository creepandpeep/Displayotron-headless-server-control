#!/usr/bin/env python

######################################################################################
# V4 - 27/01/2017 20.30
# Lots of code pulled from pimoroni examples 
# psutils code pulled from:
# https://gist.github.com/transilluminate/bbc1eca2739badaadf58 git hub user: transilluminate
# Change percent_used_usb variable to your drive location or will crash
# Wifi code block and menu option commented out
######################################################################################

import sys
import colorsys
import time
import atexit
import psutil
import subprocess
import socket
import fcntl
import struct
#import threading
#import wifi
#import math

import dothat.backlight as backlight
import dothat.lcd as lcd
import dothat.touch as nav
from dot3k.menu import Menu, MenuOption, MenuIcon
from sys import exit

print "Displayotron system monitor - should be started as a service: sudo systemctl start dispotron.service"

#Variable for backlight RGB cycling - set from menu option 'CYCLE RGB'
cyclts = False
lcd.set_contrast(0)

def run_cmd(cmd):
	p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	output = p.communicate()[0].rstrip()
	return output

def bytes2human(n):
	# http://code.activestate.com/recipes/578019
	symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
	prefix = {}
	for i, s in enumerate(symbols):
		prefix[s] = 1 << (i + 1) * 10
	for s in reversed(symbols):
		if n >= prefix[s]:
			value = float(n) / prefix[s]
			return '%.0f%s' % (value, s)
			return "%sB" % n

######################################################################################
#Backlight 
######################################################################################

class Backlight(MenuOption):
    def __init__(self, backlight):
        self.backlight = backlight
        self.hue = 0
        self.sat = 100
        self.val = 100
        self.mode = 0
        self.r = 0
        self.g = 0
        self.b = 0
        self.modes = ['h', 's', 'v', 'r', 'g', 'b', 'e']
        self.from_hue()
        self._icons_setup = False
        MenuOption.__init__(self)

    def from_hue(self):
        rgb = colorsys.hsv_to_rgb(self.hue, self.sat / 100.0, self.val / 100.0)
        self.r = int(255 * rgb[0])
        self.g = int(255 * rgb[1])
        self.b = int(255 * rgb[2])

    def from_rgb(self):
        self.hue = colorsys.rgb_to_hsv(self.r / 255.0, self.g / 255.0, self.b / 255.0)[0]

    def setup(self, config):
        self.config = config
        self.mode = 0

        self.r = int(self.get_option('Backlight', 'r', 255))
        self.g = int(self.get_option('Backlight', 'g', 255))
        self.b = int(self.get_option('Backlight', 'b', 255))

        self.hue = float(self.get_option('Backlight', 'h', 0)) / 359.0
        self.sat = int(self.get_option('Backlight', 's', 0))
        self.val = int(self.get_option('Backlight', 'v', 100))

        self.backlight.rgb(self.r, self.g, self.b)

    def setup_icons(self, menu):
        menu.lcd.create_char(0, MenuIcon.arrow_left_right)
        menu.lcd.create_char(1, MenuIcon.arrow_up_down)
        menu.lcd.create_char(2, MenuIcon.arrow_left)
        self._icons_setup = True

    def update_bl(self):
        self.set_option('Backlight', 'r', str(self.r))
        self.set_option('Backlight', 'g', str(self.g))
        self.set_option('Backlight', 'b', str(self.b))
        self.set_option('Backlight', 'h', str(int(self.hue * 359)))
        self.set_option('Backlight', 's', str(self.sat))
        self.set_option('Backlight', 'v', str(self.val))

        self.backlight.rgb(self.r, self.g, self.b)

    def down(self):
        self.mode += 1
        if self.mode >= len(self.modes):
            self.mode = 0
        return True

    def up(self):
        self.mode -= 1
        if self.mode < 0:
            self.mode = len(self.modes) - 1
        return True

    def right(self):
        if self.mode == 6:
            return False

        if self.mode == 0:
            self.hue += (1.0 / 359.0)
            if self.hue > 1:
                self.hue = 0
            self.from_hue()

        elif self.mode == 1:  # sat
            self.sat += 1
            if self.sat > 100:
                self.sat = 0
            self.from_hue()

        elif self.mode == 2:  # val
            self.val += 1
            if self.val > 100:
                self.val = 0
            self.from_hue()

        else:  # rgb
            if self.mode == 3:  # r
                self.r += 1
                if self.r > 255:
                    self.r = 0
            elif self.mode == 4:  # g
                self.g += 1
                if self.g > 255:
                    self.g = 0
            elif self.mode == 5:  # b
                self.b += 1
                if self.b > 255:
                    self.b = 0

            self.from_rgb()

        self.update_bl()
        return True

    def left(self):
        if self.mode == 0:
            self.hue -= (1.0 / 359.0)
            if self.hue < 0:
                self.hue = 1
            self.from_hue()

        elif self.mode == 1:  # sat
            self.sat -= 1
            if self.sat < 0:
                self.sat = 100
            self.from_hue()

        elif self.mode == 2:  # val
            self.val -= 1
            if self.val < 0:
                self.val = 100
            self.from_hue()

        else:  # rgb
            if self.mode == 3:  # r
                self.r -= 1
                if self.r < 0:
                    self.r = 255
            elif self.mode == 4:  # g
                self.g -= 1
                if self.g < 0:
                    self.g = 255
            elif self.mode == 5:  # b
                self.b -= 1
                if self.b < 0:
                    self.b = 255

            self.from_rgb()

        self.update_bl()
        return True

    def cleanup(self):
        self._icons_setup = False
        self.mode = 0

    def redraw(self, menu):
        if not self._icons_setup:
            self.setup_icons(menu)

        menu.write_row(0, chr(1) + 'Backlight')
        if self.mode < 6:
            row_1 = 'HSV: ' + str(int(self.hue * 359)).zfill(3) + ' ' + str(self.sat).zfill(3) + ' ' + str(
                self.val).zfill(3)
            row_2 = 'RGB: ' + str(self.r).zfill(3) + ' ' + str(self.g).zfill(3) + ' ' + str(self.b).zfill(3)

            row_1 = list(row_1)
            row_2 = list(row_2)

            icon_char = 0

            # Position the arrow
            if self.mode == 0:  # hue
                row_1[4] = chr(icon_char)
            elif self.mode == 1:  # sat
                row_1[8] = chr(icon_char)
            elif self.mode == 2:  # val
                row_1[12] = chr(icon_char)
            elif self.mode == 3:  # r
                row_2[4] = chr(icon_char)
            elif self.mode == 4:  # g
                row_2[8] = chr(icon_char)
            elif self.mode == 5:  # b
                row_2[12] = chr(icon_char)

            menu.write_row(1, ''.join(row_1))
            menu.write_row(2, ''.join(row_2))
        else:
            menu.write_row(1, chr(2) + 'Exit')
            menu.clear_row(2)

######################################################################################
#Contrast
######################################################################################

class Contrast(MenuOption):
    def __init__(self, lcd):
        self.lcd = lcd
        self.contrast = 30
        self._icons_setup = False
        MenuOption.__init__(self)

    def right(self):
        self.contrast += 1
        if self.contrast > 63:
            self.contrast = 0
        self.update_contrast()
        return True

    def left(self):
        self.contrast -= 1
        if self.contrast < 0:
            self.contrast = 63
        self.update_contrast()
        return True

    def setup_icons(self, menu):
        menu.lcd.create_char(0, MenuIcon.arrow_left_right)
        menu.lcd.create_char(1, MenuIcon.arrow_up_down)
        menu.lcd.create_char(2, MenuIcon.arrow_left)
        self._icons_setup = True

    def cleanup(self):
        self._icons_setup = False

    def setup(self, config):
        self.config = config
        self.contrast = int(self.get_option('Display', 'contrast', 40))
        self.lcd.set_contrast(self.contrast)

    def update_contrast(self):
        self.set_option('Display', 'contrast', str(self.contrast))
        self.lcd.set_contrast(self.contrast)

    def redraw(self, menu):
        if not self._icons_setup:
            self.setup_icons(menu)

        menu.write_row(0, 'Contrast')
        menu.write_row(1, chr(0) + 'Value: ' + str(self.contrast))
        menu.clear_row(2)

######################################################################################
#Text
######################################################################################

_MODE_CONFIRM = 1
_MODE_ENTRY = 0


class Text(MenuOption):
    def __init__(self):

        self.mode = _MODE_ENTRY
        self.input_prompt = ''

        self.initialized = False
        self.back_icon = chr(0)
        self.entry_char = 0
        self.entry_mode = 0
        self.entry_chars = [
            list('\'|~+-_!?.0123456789' + self.back_icon + ' abcdefghijklmnopqrstuvwxyz' + self.back_icon),
            list('"<>{}()[]:;/\^&*$%#' + self.back_icon + '@ABCDEFGHIJKLMNOPQRSTUVWXYZ' + self.back_icon)]

        self.entry_text = [' '] * 16

        self.confirm = 0
        self.final_text = ''

        self.entry_position = 0

        MenuOption.__init__(self)

        self.is_setup = False

    def set_value(self, value):
        length = len(value)
        self.entry_text = list(value + self.back_icon + (' ' * (16 - length)))
        self.entry_position = length

    def set_prompt(self, value):
        self.input_prompt = value

    def get_value(self):
        return self.final_text

    def update_char(self):
        self.entry_text[self.entry_position] = self.entry_chars[self.entry_mode][self.entry_char]

    def change_case(self):
        self.entry_mode = (self.entry_mode + 1) % len(self.entry_chars)
        self.update_char()

    def next_char(self):
        self.entry_char = (self.entry_char + 1) % len(self.entry_chars[0])
        self.update_char()

    def prev_char(self):
        self.entry_char = (self.entry_char - 1) % len(self.entry_chars[0])
        self.update_char()

    def pick_char(self, pick):
        for x, chars in enumerate(self.entry_chars):
            for y, char in enumerate(chars):
                if char == pick:
                    self.entry_mode = x
                    self.entry_char = y

    def prev_letter(self):
        self.entry_position = (self.entry_position - 1) % len(self.entry_text)
        self.pick_char(self.entry_text[self.entry_position])

    def next_letter(self):
        self.entry_position = (self.entry_position + 1) % len(self.entry_text)
        self.pick_char(self.entry_text[self.entry_position])

    def begin(self):
        self.initialized = False
        self.entry_char = 0
        self.entry_mode = 0
        self.entry_position = 0
        self.mode = _MODE_ENTRY
        self.pick_char(' ')
        self.entry_text = [' '] * 16
        self.set_value('')

    def setup(self, config):
        MenuOption.setup(self, config)

    def cleanup(self):
        self.entry_text = [' '] * 16

    def left(self):
        if self.mode == _MODE_CONFIRM:
            self.confirm = (self.confirm + 1) % 3
            return True
        if self.entry_text[self.entry_position] == self.back_icon:
            return True
        self.prev_letter()
        return True

    def right(self):
        if self.mode == _MODE_CONFIRM:
            self.confirm = (self.confirm - 1) % 3
            return True
        if self.entry_text[self.entry_position] == self.back_icon:
            return True
        self.next_letter()
        return True

    def up(self):
        if self.mode == _MODE_CONFIRM:
            return True
        self.prev_char()
        return True

    def down(self):
        if self.mode == _MODE_CONFIRM:
            return True
        self.next_char()
        return True

    def select(self):
        if self.mode == _MODE_CONFIRM:
            if self.confirm == 1:  # Yes
                return True
            elif self.confirm == 2:  # Quit
                self.cancel_input = True
                self.mode = _MODE_ENTRY
                return True
            else:  # No
                self.mode = _MODE_ENTRY
                return False

        if self.entry_text[self.entry_position] == self.back_icon:
            text = ''.join(self.entry_text)
            self.final_text = text[0:text.index(self.back_icon)].strip()
            self.mode = _MODE_CONFIRM
        else:
            self.change_case()
        return False

    def redraw(self, menu):
        if not self.initialized:
            menu.lcd.create_char(0, [0, 8, 30, 9, 1, 1, 14, 0])  # Back icon
            menu.lcd.create_char(4, [0, 4, 14, 0, 0, 14, 4, 0])  # Up down arrow
            menu.lcd.create_char(5, [0, 0, 10, 27, 10, 0, 0, 0])  # Left right arrow
            self.initialized = True

        if self.mode == _MODE_ENTRY:
            menu.write_row(0, self.input_prompt)
            menu.write_row(1, ''.join(self.entry_text))
            if self.entry_text[self.entry_position] == self.back_icon:
                if self.entry_position > 3:
                    menu.write_row(2, (' ' * (self.entry_position - 3)) + 'END' + chr(4))
                else:
                    menu.write_row(2, (' ' * self.entry_position) + chr(4) + 'END')
            else:
                menu.write_row(2, (' ' * self.entry_position) + chr(4))
        else:
            menu.write_row(0, 'Confirm?')
            menu.write_row(1, self.final_text)
            menu.write_row(2,
                           ' ' + ('>' if self.confirm == 1 else ' ') + 'Yes ' +
                           ('>' if self.confirm == 0 else ' ') + 'No ' +
                           ('>' if self.confirm == 2 else ' ') + 'Quit')

######################################################################################
#WIFI
######################################################################################

""" 
class Wlan(MenuOption):
    def __init__(self, backlight=None, interface='wlan0'):
        self.items = []
        self.interface = interface

        self.wifi_pass = ""

        self.selected_item = 0

        self.connecting = False
        self.scanning = False
        self.has_error = False
        self.error_text = ""

        self.backlight = backlight

        MenuOption.__init__(self)

        self.is_setup = False

    def run_cmd(self, cmd):
        result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout = result.stdout.read().decode()
        stderr = result.stderr.read().decode()

        return (stdout, stderr)
        #print("stdout >> ", stdout)
        #print("stderr >> ", stderr)

    def begin(self):
        self.has_errror = False
        pass

    def setup(self, config):
        MenuOption.setup(self, config)

    def update_options(self):
        pass

    def cleanup(self):
        if self.backlight is not None:
            self.backlight.set_graph(0)
        self.is_setup = False
        self.has_error = False

    def select(self):
        return True

    def left(self):
        return False

    def right(self):
        self.connect()
        return True

    def up(self):
        if len(self.items):
            self.selected_item = (self.selected_item - 1) % len(self.items)
        return True

    def down(self):
        if len(self.items):
            self.selected_item = (self.selected_item + 1) % len(self.items)
        return True

    @property
    def current_network(self):
        if self.selected_item < len(self.items):
            return self.items[self.selected_item]

        return None

    def input_prompt(self):
        return 'Password:'

    def connect(self):
        network = self.current_network
        scheme = wifi.Scheme.find(self.interface, network.ssid)
        if scheme is None:
            self.request_input()
        else: 
            print("Connecting to {}".format(self.current_network.ssid))
            t = threading.Thread(None, self.perform_connection)
            t.daemon = True
            t.start()

    def initial_value(self):
        return ""

    def receive_input(self, value):
        self.wifi_pass = value

        print("Connecting to {}".format(self.current_network.ssid))
        print("Using Password: \"{}\"".format(self.wifi_pass))

        t = threading.Thread(None, self.perform_connection)
        t.daemon = True
        t.start()

    def perform_connection(self):
        self.connecting = True
        network = self.current_network
        scheme = wifi.Scheme.find(self.interface, network.ssid)
        new = False

 
        if scheme is None:
            new = True
            scheme = wifi.Scheme.for_cell(
                self.interface,
                network.ssid,
                network,
                passkey=self.wifi_pass)
            scheme.save()

        try:
            scheme.activate()
        except wifi.scheme.ConnectionError as e:
            self.error('Connection Failed!')
            print(e)
            self.connecting = False
            if new:
                scheme.delete()
            return

        self.connecting = False

    def clear_error(self):
        self.has_error = False
        self.error_text = ""

    def error(self, text):
        self.has_error = True
        self.error_text = text

    def scan(self):
        update = threading.Thread(None, self.do_scan)
        update.daemon = True
        update.start()

    def do_scan(self):
        if self.scanning:
            return False

        self.scanning = True

        result = self.run_cmd(["sudo ifup {}".format(self.interface)])

        if "Ignoring unknown interface" in result[1]:
            self.error("{} not found!".format(self.interface))
            self.scanning = False
            return

        try:
            result = wifi.scan.Cell.all(self.interface)
            self.items = result
            print(result)

        except wifi.scan.InterfaceError as e:
            self.error("Interface Error!")
            print(e)


        self.scanning = False

    def redraw(self, menu):
        if self.has_error:
            menu.write_option(row=0, text='Error:')
            menu.write_option(row=1, text=self.error_text)
            menu.clear_row(2)
            return True

        if self.scanning:
            menu.clear_row(0)
            menu.write_option(row=1, text='Scanning...')
            menu.clear_row(2)
            return True

        if self.connecting:
            menu.clear_row(0)
            menu.write_option(row=1, text='Connecting...')
            menu.clear_row(2)
            return True

        if not self.is_setup:
            menu.lcd.create_char(0, [0, 24, 30, 31, 30, 24, 0, 0])  # Play
            menu.lcd.create_char(1, [0, 27, 27, 27, 27, 27, 0, 0])  # Pause

            menu.lcd.create_char(4, [0, 4, 14, 0, 0, 14, 4, 0])  # Up down arrow
            menu.lcd.create_char(5, [0, 0, 10, 27, 10, 0, 0, 0])  # Left right arrow

            self.scan()

            self.is_setup = True

        if self.current_network is not None:
            item = self.current_network

            status = 'Open'
            if item.encrypted:
                status = 'Secured: ' + str(item.encryption_type)

            menu.write_option(row=0, text=str(item.ssid), scroll=True)
            menu.write_option(row=1, icon='', text=status, scroll=True)
            menu.write_option(row=2, text='CH' + str(item.channel) + ' ' + item.frequency)

            signal = float(item.quality.split('/')[0])
            noise = float(item.quality.split('/')[1])

            if self.backlight is not None:
                self.backlight.set_graph(signal / noise)

        else:
            menu.clear_row(0)
            menu.write_row(1, "No networks found!")
            menu.clear_row(2)
"""




######################################################################################
#CLOCK - AMMENDED - Removed dimming hours - originally from dothat examples          #
######################################################################################

class Clock(MenuOption):
    def __init__(self):
        self.modes = ['date', 'week', 'binary', 'dim', 'bright']
        self.mode = 0
        self.binary = True
        self.running = False

#        if backlight is None:
#            import dot3k.backlight
#            self.backlight = dot3k.backlight
#        else:
#            self.backlight = backlight

        self.option_time = 0

#        self.dim_hour = 20
#        self.bright_hour = 8

        self.is_setup = False

        MenuOption.__init__(self)

    def begin(self):
        self.is_setup = False
        self.running = True

    def setup(self, config):
        MenuOption.setup(self, config)
        self.load_options()

#    def set_backlight(self, brightness):
#        brightness += 0.01
#        if brightness > 1.0:
#            brightness = 1.0
#        r = int(int(self.get_option('Backlight', 'r')) * brightness)
#        g = int(int(self.get_option('Backlight', 'g')) * brightness)
#        b = int(int(self.get_option('Backlight', 'b')) * brightness)
#        if self.backlight is not None:
#            self.backlight.rgb(r, g, b)

    def update_options(self):
#        self.set_option('Clock', 'dim', str(self.dim_hour))
#        self.set_option('Clock', 'bright', str(self.bright_hour))
        self.set_option('Clock', 'binary', str(self.binary))

    def load_options(self):
 #       self.dim_hour = int(self.get_option('Clock', 'dim', str(self.dim_hour)))
 #       self.bright_hour = int(self.get_option('Clock', 'bright', str(self.bright_hour)))
        self.binary = self.get_option('Clock', 'binary', str(self.binary)) == 'True'

    def cleanup(self):
        self.running = False
        time.sleep(0.01)
#        self.set_backlight(1.0)
        self.is_setup = False

    def left(self):
        if self.modes[self.mode] == 'binary':
            self.binary = False
#        elif self.modes[self.mode] == 'dim':
#            self.dim_hour = (self.dim_hour - 1) % 24
#        elif self.modes[self.mode] == 'bright':
#            self.bright_hour = (self.bright_hour - 1) % 24
        else:
            return False
        self.update_options()
        self.option_time = self.millis()
        return True

    def right(self):
        if self.modes[self.mode] == 'binary':
            self.binary = True
#        elif self.modes[self.mode] == 'dim':
#            self.dim_hour = (self.dim_hour + 1) % 24
#        elif self.modes[self.mode] == 'bright':
#            self.bright_hour = (self.bright_hour + 1) % 24
        self.update_options()
        self.option_time = self.millis()
        return True

    def up(self):
        self.mode = (self.mode - 1) % len(self.modes)
        self.option_time = self.millis()
        return True

    def down(self):
        self.mode = (self.mode + 1) % len(self.modes)
        self.option_time = self.millis()
        return True

    def redraw(self, menu):
        if not self.running:
            return False

        if self.millis() - self.option_time > 5000 and self.option_time > 0:
            self.option_time = 0
            self.mode = 0

        if not self.is_setup:
            menu.lcd.create_char(0, [0, 0, 0, 14, 17, 17, 14, 0])
            menu.lcd.create_char(1, [0, 0, 0, 14, 31, 31, 14, 0])
            menu.lcd.create_char(2, [0, 14, 17, 17, 17, 14, 0, 0])
            menu.lcd.create_char(3, [0, 14, 31, 31, 31, 14, 0, 0])
            menu.lcd.create_char(4, [0, 4, 14, 0, 0, 14, 4, 0])  # Up down arrow
            menu.lcd.create_char(5, [0, 0, 10, 27, 10, 0, 0, 0])  # Left right arrow
            self.is_setup = True

        hour = float(time.strftime('%H'))
        brightness = 1.0
 #       if hour > self.dim_hour:
 #           brightness = 1.0 - ((hour - self.dim_hour) / (24.0 - self.dim_hour))
 #       elif hour < self.bright_hour:
 #           brightness = 1.0 * (hour / self.bright_hour)

 #       self.set_backlight(brightness)

        menu.write_row(0, time.strftime('  %a %H:%M:%S  '))

        if self.binary:
            binary_hour = str(bin(int(time.strftime('%I'))))[2:].zfill(4).replace('0', chr(0)).replace('1', chr(1))
            binary_min = str(bin(int(time.strftime('%M'))))[2:].zfill(6).replace('0', chr(2)).replace('1', chr(3))
            binary_sec = str(bin(int(time.strftime('%S'))))[2:].zfill(6).replace('0', chr(0)).replace('1', chr(1))
            menu.write_row(1, binary_hour + binary_min + binary_sec)
        else:
            menu.write_row(1, '-' * 16)

        if self.idling:
            menu.clear_row(2)
            return True

        bottom_row = ''

        if self.modes[self.mode] == 'date':
            bottom_row = time.strftime('%b %Y:%m:%d ')
        elif self.modes[self.mode] == 'week':
            bottom_row = time.strftime('   Week: %W')
        elif self.modes[self.mode] == 'binary':
            bottom_row = ' Binary ' + chr(5) + ('Y' if self.binary else 'N')
#        elif self.modes[self.mode] == 'dim':
#            bottom_row = ' Dim at ' + chr(5) + str(self.dim_hour).zfill(2)
#        elif self.modes[self.mode] == 'bright':
#            bottom_row = ' Bright at ' + chr(5) + str(self.bright_hour).zfill(2)

        menu.write_row(2, chr(4) + bottom_row)




######################################################################################
#IP ADDRESS
######################################################################################
class IPAddress(MenuOption):
   
    """
    A plugin which gets the IP address for wlan0
    and eth0 and displays them on the screen.
    """
    
    def __init__(self):
        self.mode = 0
        self.wlan0 = self.get_addr('wlan0')
        self.eth0 = self.get_addr('eth0')
        self.is_setup = False
        MenuOption.__init__(self)

    def get_addr(self, ifname):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', ifname[:15].encode('utf-8'))
            )[20:24])
        except IOError:
            return 'Not Found!'

    def redraw(self, menu):
        if not self.is_setup:
            menu.lcd.create_char(0, [0, 4, 14, 0, 0, 14, 4, 0])  # Up down arrow
            self.is_setup = True

        menu.write_row(0, 'IP Address')
        if self.mode == 0:
            menu.write_row(1, chr(0) + ' Wired:')
            menu.write_row(2, self.eth0)
        else:
            menu.write_row(1, chr(0) + ' Wireless:')
            menu.write_row(2, self.wlan0)

    def down(self):
        self.mode = 1

    def up(self):
        self.mode = 0

    def left(self):
        return False

    def cleanup(self):
        self.is_setup = False
######################################################################################
#Temperature
######################################################################################
class GraphTemp(MenuOption):
    """
    A simple "plug-in" example, this gets the Temperature
    and draws it to the LCD when active
    """

    def __init__(self):
        self.last = self.millis()
        MenuOption.__init__(self)

    def get_cpu_temp(self):
        tempFile = open("/sys/class/thermal/thermal_zone0/temp")
        cpu_temp = tempFile.read()
        tempFile.close()
        return float(cpu_temp) / 1000

    def get_gpu_temp(self):
        proc = subprocess.Popen(['/opt/vc/bin/vcgencmd', 'measure_temp'], stdout=subprocess.PIPE)
        out, err = proc.communicate()
        out = out.decode('utf-8')
        gpu_temp = out.replace('temp=', '').replace('\'C', '')
        return float(gpu_temp)

    def redraw(self, menu):
        now = self.millis()
        if now - self.last < 1000:
            return False

        menu.write_row(0, 'Temperature')
        menu.write_row(1, 'CPU:' + str(self.get_cpu_temp()))
        menu.write_row(2, 'GPU:' + str(self.get_gpu_temp()))
######################################################################################
#Net Transfers 
######################################################################################

class GraphNetTrans(MenuOption):
    """
    Gets the total transferred amount of the raspberry and displays to the LCD, ONLY on eth0.
    """

    def __init__(self):
        self.last = self.millis()
        MenuOption.__init__(self)

    def get_down(self):
        show_dl_raw = ""
        show_dl_hr = "ifconfig eth0 | grep bytes | cut -d')' -f1 | cut -d'(' -f2"
        hr_dl = run_cmd(show_dl_hr)
        return hr_dl

    def get_up(self):
        show_ul_raw = ""
        show_ul_hr = "ifconfig eth0 | grep bytes | cut -d')' -f2 | cut -d'(' -f2"
        hr_ul = run_cmd(show_ul_hr)
        return hr_ul

    def redraw(self, menu):
        now = self.millis()
        if now - self.last < 1000:
            return false

        menu.write_row(0, 'ETH0 Transfers')
        menu.write_row(1, str('Dn:' + self.get_down())[:-1])
        menu.write_row(2, str('Up:' + self.get_up())[:-1])

######################################################################################
#Net Speed
######################################################################################

class GraphNetSpeed(MenuOption):
    """
    Gets the total network transferred amount of the raspberry and displays to the LCD, ONLY on eth0.
    """

    def __init__(self):
        self.last = self.millis()
        self.last_update = 0
        self.raw_dlold = 0
        self.raw_ulold = 0
        self.dlspeed = 0
        self.ulspeed = 0
        self.iface = 'eth0'
        MenuOption.__init__(self)

    def get_current_down(self, iface='eth0'):
        show_dl_raw = "ifconfig " + iface + " | grep bytes | cut -d':' -f2 | cut -d' ' -f1"
        raw_dl = run_cmd(show_dl_raw)
        return raw_dl[:-1]

    def get_current_up(self, iface='eth0'):
        show_ul_raw = "ifconfig " + iface + " | grep bytes | cut -d':' -f3 | cut -d' ' -f1"
        raw_ul = run_cmd(show_ul_raw)
        return raw_ul[:-1]

    def up(self):
        self.iface = 'eth0'

    def down(self):
        self.iface = 'wlan0'

    def redraw(self, menu):
        if self.millis() - self.last_update > 1000:

            tdelta = self.millis() - self.last_update
            self.last_update = self.millis()

            raw_dlnew = self.get_current_down(self.iface)
            raw_ulnew = self.get_current_up(self.iface)

            self.dlspeed = 0
            self.ulspeed = 0

            try:
                ddelta = int(raw_dlnew) - int(self.raw_dlold)
                udelta = int(raw_ulnew) - int(self.raw_ulold)

                self.dlspeed = round(float(ddelta) / float(tdelta), 1)
                self.ulspeed = round(float(udelta) / float(tdelta), 1)
            except ValueError:
                pass

            self.raw_dlold = raw_dlnew
            self.raw_ulold = raw_ulnew

        menu.write_row(0, self.iface + ' Speed')
        menu.write_row(1, str('Dn:' + str(self.dlspeed) + 'kB/s'))
        menu.write_row(2, str('Up:' + str(self.ulspeed) + 'kB/s'))

######################################################################################
#Shutdown
######################################################################################

class GraphSysShutdown(MenuOption):
    """Shuts down the Raspberry Pi"""

    def __init__(self):
        self.last = self.millis()
        MenuOption.__init__(self)

    def redraw(self, menu):
        shutdown = "sudo shutdown -h now"

        now = self.millis()
        if now - self.last < 1000 * 5:
            return False

        a = run_cmd(shutdown)

        menu.write_row(0, 'RPI Shutdown')
        menu.write_row(1, '')
        menu.write_row(2, time.strftime('  %a %H:%M:%S  '))

######################################################################################
#Reboot
######################################################################################

class GraphSysReboot(MenuOption):
    """Reboots the Raspberry Pi"""

    def __init__(self):
        self.last = self.millis()
        MenuOption.__init__(self)

    def redraw(self, menu):
        reboot = "sudo reboot"

        now = self.millis()
        if now - self.last < 1000 * 5:
            return False

        a = run_cmd(reboot)

        menu.write_row(0, 'RPI Reboot')
        menu.write_row(1, '')
        menu.write_row(2, time.strftime('  %a %H:%M:%S  '))
######################################################################################
#CPU
######################################################################################

class GraphCPU(MenuOption):
    """
    A simple "plug-in" example, this gets the CPU load
    and draws it to the LCD when active
    """

    def __init__(self, backlight=None):
        self.backlight = backlight
        self.cpu_samples = [0, 0, 0, 0, 0]
        self.cpu_avg = 0
        self.last = self.millis()
        MenuOption.__init__(self)

    def redraw(self, menu):
        now = self.millis()
        if now - self.last < 1000:
            return false

        self.cpu_samples.append(psutil.cpu_percent())
        self.cpu_samples.pop(0)
        self.cpu_avg = sum(self.cpu_samples) / len(self.cpu_samples)

        self.cpu_avg = round(self.cpu_avg * 100.0) / 100.0

        menu.write_row(0, 'CPU Load')
        menu.write_row(1, str(self.cpu_avg) + '%')
        menu.write_row(2, '#' * int(16 * (self.cpu_avg / 100.0)))

        if self.backlight is not None:
            self.backlight.set_graph(self.cpu_avg / 100.0)

    def left(self):
        if self.backlight is not None:
            self.backlight.set_graph(0)
        return False
######################################################################################
#Disk Information
######################################################################################

class disk_info(MenuOption):
	
    def redraw(self,menu):
        percent_used_root = psutil.disk_usage('/').percent
	percent_used_usb = psutil.disk_usage('/media/backup').percent
		
	menu.write_row(0,'Disk Space')
	menu.write_row(1,'Used (/):   %.0f%%' % percent_used_root)
	menu.write_row(2,'Used (USB): %.0f%%' % percent_used_usb)
######################################################################################
#CPU Information
######################################################################################

class cpu_info(MenuOption):
	
	def begin(self):
		self.load_average_5m = run_cmd("uptime | grep -ohe 'load average[s:][: ].*' | awk '{ print $4 }'| tr -d ','")
	
	def get_cpu_temp(self):
		tempFile = open("/sys/class/thermal/thermal_zone0/temp")
		cpu_temp = tempFile.read()
		tempFile.close()
		return int(cpu_temp) / 1000
		
	def redraw(self,menu):
		cpu_percent = psutil.cpu_percent(interval=0.25)
		cpu_temp = self.get_cpu_temp()
		
#		lcd_colour(cpu_percent)
		menu.write_row(0,'CPU Info')
		menu.write_row(1,'Load: %.0f%% (%s)' % (cpu_percent, self.load_average_5m))
		menu.write_row(2,'Temp: %s C' % str(cpu_temp))
######################################################################################
#RAM Information
######################################################################################

class memory_info(MenuOption):
	
	def redraw(self,menu):
		available_memory = bytes2human(psutil.virtual_memory().available)
		active_memory = bytes2human(psutil.virtual_memory().active)
		percent_used = psutil.virtual_memory().percent
		percent_free = 100 - percent_used
		
#		lcd_colour(percent_used)
		menu.write_row(0,'RAM')
		menu.write_row(1,'Used: %s (%.0f%%)' % (active_memory, percent_used))
		menu.write_row(2,'Free: %s (%.0f%%)' % (available_memory, percent_free))

######################################################################################
# ATEXT Tidyup script
######################################################################################

def tidyup():
    global cyclts
    cyclts  = False
    backlight.off()
    lcd.clear()
    lcd.set_contrast(0)
    backlight.set_graph(0)
######################################################################################
#Cycle RGB menu option - Set cycle lights variable to true - changes while loop at end of file
######################################################################################
def cyclelights():
    global cyclts
    cyclts = True
    x = 0
######################################################################################
#Backlight Off menu option - Turn backlight off and stop cyclelights loop
######################################################################################
def lightsoff():
    global cyclts
    cyclts = False
    backlight.off()
    backlight.set_graph(0)
######################################################################################
#Turn backlight on and set to red
######################################################################################
def lightson():
    global cyclts
    cyclts = False
    backlight.rgb(255, 0, 25)
######################################################################################
#Cam stream menu option - starts/stops cam streaming service (cmstrm)
######################################################################################

def camon():
    run_cmd("systemctl start cmstrm.service")

def camoff():
    run_cmd("systemctl stop cmstrm.service")

######################################################################################
#Menu Structure
######################################################################################

menu = Menu(
    structure={
        #'WiFi': Wlan(),       
        'Clock': Clock(),
        'Status': {
            'IP': IPAddress(),
            'CPU Load': GraphCPU(),
            'CPU Load & Temp': cpu_info(),
            'CPU & GPU Temp': GraphTemp(),
            'NetSpeed': GraphNetSpeed(),
            'NetTrans': GraphNetTrans(),
            'Disk Usage': disk_info(),
            'RAM': memory_info()
        },
        'Display': {
            'Backlight Off': lightsoff,
            'Backlight On': lightson,
	    'Contrast': Contrast(lcd),
            'Colour': Backlight(backlight),
            'Cycle RGB': cyclelights
            },
	'Power': {
		'Reboot': GraphSysReboot(),
		'Shutdown': GraphSysShutdown()
		},
        'Cam stream': {
                'Start Stream': camon,
                'Stop Stream' : camoff
        }
    },
    lcd=lcd,
    idle_handler=lightsoff,
    idle_timeout=1,
    input_handler=Text())

backlight.off()
lcd.clear()
backlight.set_graph(0)

nav.bind_defaults(menu)

atexit.register(tidyup)

x = 0
######################################################################################
#Background while loop - defaults to jsut redraw the screen, no backlight unless Backlight turned on from menu OR Cycle RGB loop initiated from menu
######################################################################################

while True:
    if cyclts == False:
        menu.redraw()
        time.sleep(0.01)
        
    else:
        x += 1
        backlight.sweep((x % 360) / 360.0)
        menu.redraw()
        time.sleep(0.01)
