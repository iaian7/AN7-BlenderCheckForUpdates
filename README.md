# AN7 Check For Blender Updates

Check for Blender patch updates from the Help menu and automatically on startup.

## Installation and Usage

 - Download the .py add-on file
 - Install in the Blender Preferences > Add-ons tab
 - Enable the plugin
 - Choose the correct download type (this is not auto-detected and must be set manually)

![screenshot of the plugin settings as seen in the Blender preferences add-ons tab interface](images/preferences.png)

Works in Blender 2.83, 2.93, and 3.3 for MacOS Intel, other versions and platforms probably work but have not be tested.

When automatically checking for updates on startup, Blender will try to download an available update even when you click away from the update panel if the splash screen is also enabled and still on screen. Normally, simply moving the mouse away from the popup would dismiss it, but there seems to be a conflict with the UI panels. Pressing the `escape` key will close the popups without downloading.