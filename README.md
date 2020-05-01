# Displayotron headless Raspberry Pi web server control
Using Pimoronis [Displayotron HAT](https://shop.pimoroni.com/products/display-o-tron-hat) to control and monitor a headless Raspberry Pi webserver.  

#### Currently working
(Largely the same as from the example scripts included with the displayotron & transilluminates script)
* System stats monitoring - CPU, RAM, HDD Space, Temperature, Network Speed/Transfer Rate, IP Address etc
* Clock
* Power options - reboot/shutdown Pi

(Changed or added)
* Menu option to start systemd service - (in my case, a Pi Cam streaming service that loads in an iframe on a wordpress site)
* Backlight off menu option - but keeps text visible
* Backlight on menu option - to a predefined colour
* Cycle RGB backlights menu option - as in the demo example, but persistent throughout all the status screens and clock etc

#### Soon
* Splitting menu option code blocks back into plugins for readability and ease of updates
* Will tidy up and parameterise the code, eg service names as variables so easy to personalise for people who aren't programmers..like me...
* Visual indicators using backlight/graph lights eg for service state (webcam actively streaming etc)
* Rsync plugin
* Plugin to take still image from Pi Cam and save directly to web folder
* Plugins to start/stop video/audio record and then option to upload directly to web folder

As stated, most of this code is pulled together from either Pimoronis example scripts from their displayotron repo or transilluminates script - I believe I've creditted everyone as neccesary, but please let me know if otherwise.


