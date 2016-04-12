# DriConf
Mirror of the essentially dead freedesktop project for configuring dri2/3 on oss drivers

### Purpose of git:
The purpose of this git is to continue development of the python program 'DriConf' and carry its feature support into newer graphics drivers such as the recent **amdgpu/amdgpu-pro** as well as the foss **intel** and **nvidia** drivers

Introduction
------------

DRI is the direct rendering infrastructure in XFree86 and X.org, which
provides 3D hardware acceleration. Most 3D drivers have a number of
options for tuning the performance and visual quality. DRIconf is a
configuration applet that allows you to change these parameters.

In order to use it you need at least X.org 6.8 or XFree86 4.4. 3D
drivers in earlier X releases did not support configuration.

Installation
------------

This tool is written in Python. Before installing make sure that a
Python version (>= 2.3) and the matching packages xml.parsers.expat
and python-gtk2 version 2.4 or newer are installed. The installation
uses Python's distutils package.

By default driconf will be installed into various sub-directories under
/usr/local. You can change this behaviour in setup.cfg. In that case
you may also have to adjust the driconf start-up script accordingly.

To start the installation run the following command as root:

From the 'python' folder

    python setup.py install

If everything goes well you should see something like this:

    running install
    running build
    running build_py
    creating build
    creating build/lib
    copying dri.py -> build/lib
    copying driconf.py -> build/lib
    copying driconf_commonui.py -> build/lib
    copying driconf_complexui.py -> build/lib
    copying driconf_simpleui.py -> build/lib
    running build_scripts
    creating build/scripts-2.3
    copying and adjusting driconf -> build/scripts-2.3
    changing mode of build/scripts-2.3/driconf from 644 to 755
    running install_lib
    creating /usr/local/lib/driconf
    copying build/lib/driconf.py -> /usr/local/lib/driconf
    copying build/lib/driconf_commonui.py -> /usr/local/lib/driconf
    copying build/lib/dri.py -> /usr/local/lib/driconf
    copying build/lib/driconf_simpleui.py -> /usr/local/lib/driconf
    copying build/lib/driconf_complexui.py -> /usr/local/lib/driconf
    byte-compiling /usr/local/lib/driconf/driconf.py to driconf.pyc
    byte-compiling /usr/local/lib/driconf/driconf_commonui.py to driconf_commonui.pyc
    byte-compiling /usr/local/lib/driconf/dri.py to dri.pyc
    byte-compiling /usr/local/lib/driconf/driconf_simpleui.py to driconf_simpleui.pyc
    byte-compiling /usr/local/lib/driconf/driconf_complexui.py to driconf_complexui.pyc
    running install_scripts
    copying build/scripts-2.3/driconf -> /usr/local/bin
    changing mode of /usr/local/bin/driconf to 755
    running install_data
    creating /usr/local/share/driconf
    copying card.png -> /usr/local/share/driconf
    copying screen.png -> /usr/local/share/driconf
    copying screencard.png -> /usr/local/share/driconf
    copying drilogo.jpg -> /usr/local/share/driconf
    creating /usr/local/share/locale/de
    creating /usr/local/share/locale/de/LC_MESSAGES
    copying de/LC_MESSAGES/driconf.mo -> /usr/local/share/locale/de/LC_MESSAGES
    creating /usr/local/share/locale/es
    creating /usr/local/share/locale/es/LC_MESSAGES
    copying es/LC_MESSAGES/driconf.mo -> /usr/local/share/locale/es/LC_MESSAGES
    creating /usr/local/share/locale/it
    creating /usr/local/share/locale/it/LC_MESSAGES
    copying it/LC_MESSAGES/driconf.mo -> /usr/local/share/locale/it/LC_MESSAGES
    creating /usr/local/share/locale/ru
    creating /usr/local/share/locale/ru/LC_MESSAGES
    copying ru/LC_MESSAGES/driconf.mo -> /usr/local/share/locale/ru/LC_MESSAGES

After successful installation you can run driconf from the shell. The
release includes an example driconf.desktop file. You can copy that to
/usr/share/applications/driconf.desktop to add driconf to your desktop's
settings menu.

Getting Started
---------------

When you start DRIconf for the first time, it will automatically
create a configuration file for you. It automatically detects
configurable 3D accelerators, usually only one. If it doesn't find any
devices then it will start in Expert Mode (see below). Let's assume
that your system is set up correctly and that DRIconf starts normally.

At the top of the window you see a line that describes your 3D
graphics card and driver. Below that there is a notebook with one or
more tabs that contains options that can be tweaked in the 3D
driver. You can go ahead and experiment with them. Changes apply
immediately to any 3D applications that are newly started.

At the bottom of the window there is an expander labeled "Application
settings". If you never created any application-specific settings,
this area is hidden until you click on that line. If that is the case
click on it now.

You see a row of four buttons. In order to add settings for an
application click on the "Add" button. Now you are asked for the name
of the application and the name of the executable. The name is just a
description for your convenience. The executable name is important for
identifying the application. Beware that some applications and games
end up running a different executable than what you type in the
shell. For example q3demo is only a shell script that starts an
executable called q3demo.x86 on my system. In this example you'd need
to enter "q3demo.x86", otherwise your settings would not apply.

After clicking OK, the left-most button shows you the name of the
application you just entered. If you create settings for multiple
applications you can choose the application by clicking on the button
and selecting the desired application from the menu.

Below the row of buttons you now see an invitation to add settings for
the selected application. Click on the button on the right hand
side. You will see a menu that presents all the options of the 3D
driver. Pick one option. This will add the option to that area and
allow you to change it. The settings you make here will override the
default settings for the device in the selected application. You can
add more settings in the same way. Remove settings that you don't want
any more by clicking on the "Remove" button on the right hand side of
an option.

You can remove all settings for an application by selecting the big
"Remove" button above the Application settings. If you change your
mind about the name of the application or the executable, use the
"Properties" button.

That's really all there is to it. If that's not enough for you, read
on about the expert mode.

Expert Mode
-----------

Usually you will not run DRIconf in expert mode. It happens
automatically under some exceptional conditions which usually mean
that something in your system setup is broken. In such cases it may
help with the diagnosis. You can also enter expert mode from the
standard mode using the "Expert Mode" button at the bottom of the
window or by starting DRIconf with the "-e" option.

In expert mode the configuration file structure is represented by a
tree on the left hand side of the window. The tree has one node for
each 3D graphics device you may have, usually only one though. Below
that node there are application nodes. If none is selected, select one
now.

The right pane of the window shows the available options of the 3D
driver. Options are organized in several tabs of a notebook. Left of
each option there is a check box. Activating it will allow you to
change the value of that option. Only options whose check box is
active will be written to the configuration file. With the button on
the right of each option you can always restore the respective default
value for reference.

In expert mode changes don't take effect immediately. When you're done
changing options, click on the "Save" button in the button bar at the
top of the DRIconf window to save and apply the settings.

Adding an Application-Specific Configuration
--------------------------------------------

Select a device node in the configuration tree on the left hand
side. Then click on the "New" button at the top of the window. This
opens a small dialog that asks for the name of the application. This
is really only a descriptive string. After confirming with "OK" you
will have a new application node with the name you just entered.

The right pane of the window now shows the driver options with their
settings for the new application. Note the entry above the tabs
containing the actual options. If you activate it you can enter the
name of the application's executable file. This will make the settings
below apply only to that particular application. If you leave the
entry disabled, the settings will apply to all applications.

Beware that some applications and games end up running a different
executable than what you type in the shell. For example q3demo is only
a shell script that starts an executable called q3demo.x86 on my
system. In this example you'd need to enter "q3demo.x86", otherwise
the settings would not apply.

Advanced Features
-----------------

Some advanced features include adding more devices and changing the
order of devices and applications. The order matters only in rare
cases, when multiple application nodes apply to the same
application. If they set the same options, then only the last setting
takes effect.
