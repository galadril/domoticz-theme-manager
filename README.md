# domoticz-theme-manager
Domoticz Theme manager
BEWARE, this plugin can be used ONLY ON LINUX SYSTEMS and Raspberry Pi!!!!!!


I used pp-manager from [ycahome](https://github.com/ycahome/pp-manager) to build this theme manager for Domoticz.
So all credits for you ycahome!


This plugin 
- has a predefined list of themes to be installed (available on github)
- auto updates itself on every self.stop()


To install a plugin: select it on "Domoticz Themes" field and press update

To continuously update all themes: Select "All" from "Auto Update" drop-down box and press 

To continuously update selected theme: Select desired plugin from "Domoticz Theme" field put "Selected" on "Auto Update" drop-down box and press update

To check all themes for updates and receive notification email: Select "All (NotifyOnly)" from "Auto Update" drop-down box and press update

To check selected theme for updates and receive notification email: Select desired theme from "Domoticz Theme" field put "Selected (NotifyOnly)" on "Auto Update" drop-down box and press update

- supports only themes located on GitHub
- performs theme installation only if theme directory not exists
- performs theme installation and prompts you to restart Domoticz in order to activate it.
- self updates every 24 hours
- update selected plugin (ad-hoc update) every 24 hours
- more theme added

To install another plugin, just select it and press update.


You can install and test it from GitHub bellow (git tools required):

go to your plugins folder
and execute 

git clone https://github.com/galadril/domoticz-theme-manager.git THEME-MANAGER


BEWARE, this is a very early Beta version. Use it on your test server first.
Also, can be used ONLY ON LINUX SYSTEMS and Raspberry Pi!!!!!!


Waiting for your comments!!!!
