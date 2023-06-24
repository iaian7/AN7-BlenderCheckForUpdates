bl_info = {
	"name": "AN7 Check For Updates",
	"author": "Iaian7 - John Einselen",
	"version": (0, 3, 0),
	"blender": (2, 83, 0),
	"location": "Help > Check for Updates",
	"description": "Checks the Blender website for newer versions on startup and from the help menu",
	"warning": "inexperienced developer, use at your own risk",
	"wiki_url": "",
	"tracker_url": "",
	"category": "3D View"}

import bpy
from bpy.app.handlers import persistent
import requests
import re

###########################################################################
# Main class

class AN7_Check_For_Updates(bpy.types.Operator):
	bl_idname = "an7checkforupdates.check"
	bl_label = "Check for Updates"
	bl_description = "Check for updates on the Blender.org website"
	
	mode: bpy.props.IntProperty() # 0 == only check, 1 == check and popup, 2 == only popup
	
	def getPageData(self, path):
		try:
			r = requests.get(path)
			if r.status_code == 200:
				return r.text
			else:
				print('Error in AN7 Check for Updates: URL request failed to get the Blender download page')
				return {'FINISHED'}
		except Exception as exc:
			print(str(exc) + " | Error in AN7 Check for Updates: failed to find available versions")
			return False
	
	def findVersions(self):
		try:
			path = "http://download.blender.org/release/"
			
			# Get download page data
			page = self.getPageData(path)
			
			# Find versions
			versions = re.findall(r'(?<=Blender)\d+.\d+', page, re.M)
			
			if (versions):
				return versions
			else:
				return False
		except Exception as exc:
			print(str(exc) + " | Error in AN7 Check for Updates: failed to find available versions")
			return False
	
	def findPatchDownload(self, version, type):
		try:
			# Version must be a three part tuple for correct comparison
			# Type must be a valid Blender OS format
			base = str(version[0]) + "." + str(version[1])
			path = "http://download.blender.org/release/Blender" + base + "/"
			
			# Get download page data
			page = self.getPageData(path)
			
			# Check for newest matching download in the HTML source
			pattern = r'blender-' + base.replace(".", "\.") + '\.\d+' + type.replace(".", "\.")
			downloads = re.findall(pattern, page, re.M)
			if len(downloads) > 0:
				download = downloads[-1]
			else:
				return False
			
			# Extract new version tuple
			pattern = base.replace(".", "\.") + '\.\d+'
			newVersion = re.search(pattern, download, re.M)
			newVersion = tuple(map(int, newVersion.group().split('.')))
			
			if (newVersion > version):
				return [newVersion, path + download]
			else:
				return False
		except Exception as exc:
			print(str(exc) + " | Error in AN7 Check for Updates: failed to find available patch download")
			return False
	
	def execute(self, context):
		# Get current version
		version = bpy.app.version
		
		# Create popup title text
		popup_title = 'Update Blender ' + '.'.join(map(str, version))
		
		# Bypass checking for new updates, just show the popup with existing global variable values
		if (self.mode == 2):
			context.window_manager.popup_menu(AN7_update_popup, title=popup_title, icon='FILE_REFRESH')
			return {'FINISHED'}
		
		# Blender installation type
		type = bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.download_format
		
		# Get available major.minor versions
		available = self.findVersions()
		
		# Check for new patch update
		patch = self.findPatchDownload(version, type)
		if patch:
			print('Detected patch version:')
			print(patch[0])
			print('')
		if patch is not False and patch[0] > version:
			bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.patch_available = True
#			bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.patch_version = '.'.join(map(str, patch[0]))
			bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.patch_link = patch[1]
		else:
			bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.patch_available = False
			print('AN7 Blender Update: no newer patch version available')
			print('')
			print('')
			print('')
		
		# Check for new minor update
		newMinor = [x for x in reversed(available) if str(x).startswith(str(version[0]) + '.')] # Find latest minor version
		newMinor = available[-1] if len(newMinor) == 0 else newMinor[0] # Catch error when minor version doesn't exist
		newMinor = tuple(map(int, (newMinor + '.0').split('.'))) # Convert common version number to tuple with third element
		print('Looking for minor version:')
		print(newMinor)
		minor = self.findPatchDownload(newMinor, type)
		if minor:
			print('Detected minor version:')
			print(minor[0])
			print('')
		if minor is not False and minor[0] > version:
			bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.minor_available = True
#			bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.minor_version = '.'.join(map(str, minor[0]))
			bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.minor_link = minor[1]
		else:
			bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.minor_available = False
			print('AN7 Blender Update: no newer minor version available')
			print('')
			print('')
			print('')
		
		# Check for new major update
		newMajor = available[-1] # Find latest version
		newMajor = tuple(map(int, (newMajor + '.0').split('.'))) # Convert common version number to tuple with third element
		print('Looking for major version:')
		print(newMajor)
		major = self.findPatchDownload(newMajor, type)
		if major:
			print('Detected major version:')
			print(major[0])
			print('')
		if major is not False and major[0] > version and minor[0] != major[0]:
			bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.major_available = True
#			bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.major_version = '.'.join(map(str, major[0]))
			bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.major_link = major[1]
		else:
			bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.major_available = False
			print('AN7 Blender Update: no newer major version available')
			print('')
			print('')
			print('')
		
		# Show popup with results
		if (self.mode == 1):
			context.window_manager.popup_menu(AN7_update_popup, title=popup_title, icon='FILE_REFRESH')
			
		return {'FINISHED'}



###########################################################################
# Popup window layouts

def AN7_update_popup(self, context):
	layout = self.layout
	if bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.patch_available:
		layout.label(text='New patch available:')
		patchLink = bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.patch_link
		patchName = patchLink.split('/')[-1]
		op = layout.operator('wm.url_open', text=patchName, icon='URL')
		op.url = patchLink
	if bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.minor_available:
		if bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.patch_available:
			layout.separator()
		layout.label(text='New minor update available:')
		minorLink = bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.minor_link
		minorName = minorLink.split('/')[-1]
		op = layout.operator('wm.url_open', text=minorName, icon='URL')
		op.url = minorLink
	if bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.major_available:
		if bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.patch_available or bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.minor_available:
			layout.separator()
		layout.label(text='New major update available:')
		majorLink = bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.major_link
		majorName = majorLink.split('/')[-1]
		op = layout.operator('wm.url_open', text=majorName, icon='URL')
		op.url = majorLink
	if not (bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.patch_available or bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.minor_available or bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.major_available):
		layout.label(text="You are running the latest public Blender release")



###########################################################################
# Check for updates on Blender startup

@persistent
def an7_check_for_updates_on_load(self, context):
	if (bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.auto_check):
		bpy.ops.an7checkforupdates.check("EXEC_DEFAULT", mode=0)

# Show main menu button if updates are available

def an7_check_for_updates_main_menu(self, context):
	if not (False) and (bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.patch_available or bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.minor_available or bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.major_available):
		layout = self.layout
		layout.separator()
		op = layout.operator('an7checkforupdates.check', text='Update', icon='FILE_REFRESH')
		op.mode=2
		# Icon options: FILE_REFRESH, URL, WINDOW



###########################################################################
# Check for updates from the help menu

def an7_check_for_updates_help_menu(self, context):
	if not (False):
		layout = self.layout
		op = layout.operator('an7checkforupdates.check', text='Check for Updates…', icon='FILE_REFRESH')
		op.mode=1
		# Icon options: FILE_REFRESH, URL, WINDOW



###########################################################################
# User preferences and UI rendering class

class AN7CheckForUpdatesPreferences(bpy.types.AddonPreferences):
	bl_idname = __name__

	auto_check: bpy.props.BoolProperty(
		name='Automatically Check for Updates',
		description='Check for new updates every time Blender starts up',
		default=True
	)
#	update_type: bpy.props.EnumProperty(
#		name='Update Type',
#		description='Choose the type of Blender download that should be checked for',
#		items=[
#			('patch', 'Patch Updates (' + re.sub(r'\.\d+$', ".x", bpy.app.version_string) + ')', 'Semantic versioning patch updates'),
#			('minor', 'Minor and Patch Updates (' + re.sub(r'\.\d+', ".x", bpy.app.version_string) + ')', 'Semantic versioning minor updates'),
#			('major', 'Major, Minor, and Patch Updates (x.x.x)', 'Semantic versioning major updates')
#			],
#		default='patch'
#	)
	download_format: bpy.props.EnumProperty(
		name='Download Format',
		description='Choose the type of Blender download that should be suggested',
		items=[
			('-linux-x64.tar.xz', 'Linux', 'Linux x64 tar.xy file'),
			('-macos-arm64.dmg', 'MacOS ARM', 'Apple MacOS arm64 dmg file'),
			('-macos-x64.dmg', 'MacOS Intel', 'Apple MacOS x64 dmg file'),
			('-windows-x64.msi', 'Windows MSI', 'Microsoft Windows x64 msi file'),
			('-windows-x64.msix', 'Windows MSIX', 'Microsoft Windows x64 msix file'),
			('-windows-x64.zip', 'Windows ZIP', 'Microsoft Windows x64 zip file')
			],
		default='-macos-x64.dmg'
	)
	# Patch updates
	patch_available: bpy.props.BoolProperty(
		name='Patch available',
		description='Status of available patch updates',
		default=False
	)
#	patch_version: bpy.props.StringProperty(
#		name='Update Version',
#		description='Updated version number',
#		default=''
#	)
	patch_link: bpy.props.StringProperty(
		name='Update Link',
		description='Updated version number',
		default=''
	)
	# Minor updates
	minor_available: bpy.props.BoolProperty(
		name='Patch available',
		description=' of available patch updates',
		default=False
	)
#	minor_version: bpy.props.StringProperty(
#		name='Upgrade Version',
#		description='Updated version number',
#		default=bpy.app.version_string
#	)
	minor_link: bpy.props.StringProperty(
		name='Upgrade Link',
		description='Updated version number',
		default=""
	)
	# Major updates
	major_available: bpy.props.BoolProperty(
		name='Patch available',
		description=' of available patch updates',
		default=False
	)
#	major_version: bpy.props.StringProperty(
#		name='Upgrade Version',
#		description='Updated version number',
#		default=bpy.app.version_string
#	)
	major_link: bpy.props.StringProperty(
		name='Upgrade Link',
		description='Updated version number',
		default=""
	)
	
	# Plugin preferences rendering
	def draw(self, context):
		layout = self.layout
		layout.prop(self, "auto_check")
#		layout.prop(self, "update_type")
		layout.prop(self, "download_format")



###########################################################################
# Classes for registration

classes = (AN7_Check_For_Updates, AN7CheckForUpdatesPreferences)



###########################################################################
# Addon registration functions

def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	if not an7_check_for_updates_on_load in bpy.app.handlers.load_post:
		bpy.app.handlers.load_post.append(an7_check_for_updates_on_load)
	bpy.types.TOPBAR_MT_help.append(an7_check_for_updates_help_menu)
	bpy.types.TOPBAR_MT_editor_menus.append(an7_check_for_updates_main_menu)

def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
	if an7_check_for_updates_on_load in bpy.app.handlers.load_post:
		bpy.app.handlers.load_post.remove(an7_check_for_updates_on_load)
	bpy.types.TOPBAR_MT_help.remove(an7_check_for_updates_help_menu)
	bpy.types.TOPBAR_MT_editor_menus.remove(an7_check_for_updates_main_menu)

if __name__ == "__main__":
	register()
	