#!/usr/bin/env python

import sys

import dothat.backlight as backlight
import dothat.lcd as lcd
from dot3k.menu import Menu, MenuOption
sys.path.append('/home/pi/Pimoroni/displayotron/examples')

backlight.off()
lcd.clear()
backlight.set_graph(0)