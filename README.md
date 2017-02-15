# Displayotron headless Raspberry Pi web server control
Using Pimoronis [Displayotron HAT](https://shop.pimoroni.com/products/display-o-tron-hat) to control and monitor a headless Raspberry Pi webserver.  

#### Bodged together using code from [Pimoronis displayotron repo](../../../../pimoroni/dot3k) and [transilluminates display.py] (https://gist.github.com/transilluminate/bbc1eca2739badaadf58)

It works, but is very much a work in progress.  I knew nothing about Python before I got the displayotron and only did a couple of hours online course, so I'm very aware the code is an abomination - but it does work.  Very much a linux amatuer as well.  I realise this won't be much use to anyone else, but it's to make keeping track of changes easier for mysellf.

#### The aim

I have a Raspberry Pi 3 which I use as a webserver.  The displayotron is an excellent way to control/monitor a Raspberry Pi without connecting a monitor/keyboard or using SSH.  I started playing with the menu.py in Pimoronis examples and decided to try and add further functionality like the ability to start/stop services etc - This is still in the early stages, but the foundation is now there.  The end goal is to have a webserver that I rarely have to log into to maintain or administer - to be able to start and stop services (such as webcam streaming, audio streaming etc) and launch other tasks (like ad-hoc backups to dev web server etc) at the push of a button on the displayotron HAT...whilst also having a fancy colour changing clock lighting up my living room :) .  
 Details of the picam streaming/wordpress embedding of stream can be found at creepandpeep.net/board
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


