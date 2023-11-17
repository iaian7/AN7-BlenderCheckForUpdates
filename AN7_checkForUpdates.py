bl_info = {
	"name": "AN7 Check For Updates",
	"author": "Iaian7 - John Einselen",
	"version": (0, 5, 3),
	"blender": (2, 83, 0),
	"location": "Help > Check for Updates…",
	"description": "Checks the Blender website for newer versions on startup and from the help menu",
	"warning": "inexperienced developer, use at your own risk",
	"doc_url": "https://github.com/iaian7/AN7-BlenderCheckForUpdates",
	"tracker_url": "https://github.com/iaian7/AN7-BlenderCheckForUpdates/issues",
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
	bl_description = "Check for updates from https://download.blender.org/release/ (this may take a few seconds)"
	
	mode: bpy.props.IntProperty() # 0 == only check, 1 == check and popup, 2 == only popup
	
	def getPageData(self, path):
		try:
			r = requests.get(path)
			if r.status_code == 200:
				return r.text
			bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.error_message = 'Failed to get Blender website, check network status'
			print('Error in AN7 Check for Updates: URL request failed to get Blender website, check network status')
			return {'FINISHED'}
		except Exception as exc:
			print(str(exc) + " | Error in AN7 Check for Updates: failed to get Blender website")
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
			return False
		except Exception as exc:
			bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.error_message = 'Failed to get Blender version list, check network status'
			print(str(exc) + " | Error in AN7 Check for Updates: failed to get Blender version list, check network status")
			return False
	
	def findDownload(self, oldVersion, checkVersion, type):
		try:
			# Version must be a three part tuple for correct comparison
			# Type must be a valid Blender OS format
			base = str(checkVersion[0]) + "." + str(checkVersion[1])
			path = "http://download.blender.org/release/Blender" + base + "/"
			
			# Get download page data
			page = self.getPageData(path)
			
			# Check for newest matching download in the HTML source
			pattern = r'(?<=")blender-' + base.replace(".", "\.") + '\.\d+' + type.replace(".", "\.") + '(?=")'
			downloads = re.findall(pattern, page, re.M)
			
			# If no downloads were found, check again with just the file extension instead of the full 
			if len(downloads) == 0:
				newType = re.sub(r'^[-\w]+', ".+?", type.replace(".", "\."))
				pattern = r'(?<=")blender-' + base.replace(".", "\.") + '\.\d+' + newType + '(?=")'
				downloads = re.findall(pattern, page, re.M)
			
			# If still no downloads were found, return false
			if len(downloads) > 0:
				download = downloads[-1]
			else:
				return False
			
			# Extract new version tuple
			pattern = base.replace(".", "\.") + '\.\d+'
			newVersion = re.search(pattern, download, re.M)
			newVersion = tuple(map(int, newVersion.group().split('.')))
			
			if (newVersion > oldVersion):
				return [newVersion, path + download]
			return False
		except Exception as exc:
			bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.error_message = 'Failed to get Blender download list, check network status'
			print(str(exc) + " | Error in AN7 Check for Updates: failed to get Blender download list, check network status")
			return False
	
	def execute(self, context):
		# Reset error message
		context.preferences.addons['AN7_checkForUpdates'].preferences.error_message = ''
		
		# Get current version
		version = bpy.app.version
		
		# Create popup title text
		popup_title = 'Update Blender ' + '.'.join(map(str, version))
		
		# Bypass checking for new updates, just show the popup with existing global variable values
		if (self.mode == 2):
			context.window_manager.popup_menu(AN7_update_popup, title=popup_title, icon='FILE_REFRESH')
			return {'FINISHED'}
		
		# Blender installation type
		type = context.preferences.addons['AN7_checkForUpdates'].preferences.download_format
		
		# Check for new patch update
		patch = self.findDownload(version, version, type)
		if patch is not False and patch[0] > version:
			context.preferences.addons['AN7_checkForUpdates'].preferences.patch_available = True
			context.preferences.addons['AN7_checkForUpdates'].preferences.patch_version = '.'.join(map(str, patch[0]))
			context.preferences.addons['AN7_checkForUpdates'].preferences.patch_link = patch[1]
		else:
			context.preferences.addons['AN7_checkForUpdates'].preferences.patch_available = False
		
		# Skip checking for major and minor versions if this is during startup and "All Updates" is not enabled
		if self.mode == 0 and context.preferences.addons['AN7_checkForUpdates'].preferences.auto_check != 'all':
			return {'FINISHED'}
		
		# Set full check to true (even if it fails, we've tried)
		context.preferences.addons['AN7_checkForUpdates'].preferences.full_check = True
		
		# Get available major.minor versions
		available = self.findVersions()
		
		if available is not False:
			# Check for new minor update
			newMinor = [x for x in reversed(available) if str(x).startswith(str(version[0]) + '.')] # Find latest minor version
			newMinor = available[-1] if len(newMinor) == 0 else newMinor[0] # Catch error when minor version doesn't exist
			newMinor = tuple(map(int, (newMinor + '.0').split('.'))) # Convert common version number to tuple with third element
			if newMinor > version: # Skip the network call if we already know we don't need it
				minor = self.findDownload(version, newMinor, type)
				if minor is not False and minor[0] > version:
					context.preferences.addons['AN7_checkForUpdates'].preferences.minor_available = True
					context.preferences.addons['AN7_checkForUpdates'].preferences.minor_version = '.'.join(map(str, minor[0]))
					context.preferences.addons['AN7_checkForUpdates'].preferences.minor_link = minor[1]
				else:
					context.preferences.addons['AN7_checkForUpdates'].preferences.minor_available = False
			else:
				minor = newMinor
			
			# Check for new major update
			newMajor = available[-1] # Find latest version
			newMajor = tuple(map(int, (newMajor + '.0').split('.'))) # Convert common version number to tuple with third element
			if newMajor > version: # Skip the network call if we already know we don't need it
				major = self.findDownload(version, newMajor, type)
				if major is not False and major[0] > version and minor[0] != major[0]:
					context.preferences.addons['AN7_checkForUpdates'].preferences.major_available = True
					context.preferences.addons['AN7_checkForUpdates'].preferences.major_version = '.'.join(map(str, major[0]))
					context.preferences.addons['AN7_checkForUpdates'].preferences.major_link = major[1]
				else:
					context.preferences.addons['AN7_checkForUpdates'].preferences.major_available = False
		
		# Show popup with results
		if (self.mode == 1):
			context.window_manager.popup_menu(AN7_update_popup, title=popup_title, icon='FILE_REFRESH')
			
		return {'FINISHED'}



###########################################################################
# Popup window layouts

def AN7_update_popup(self, context):
	layout = self.layout
	if len(context.preferences.addons['AN7_checkForUpdates'].preferences.error_message) > 0:
		layout.label(text=context.preferences.addons['AN7_checkForUpdates'].preferences.error_message)
	else:
		if context.preferences.addons['AN7_checkForUpdates'].preferences.patch_available:
			layout.label(text=context.preferences.addons['AN7_checkForUpdates'].preferences.patch_version + ' patch available')
			patchLink = context.preferences.addons['AN7_checkForUpdates'].preferences.patch_link
			patchName = patchLink.split('/')[-1]
			op = layout.operator('wm.url_open', text=patchName, icon='URL')
			op.url = patchLink
		if context.preferences.addons['AN7_checkForUpdates'].preferences.minor_available:
			if context.preferences.addons['AN7_checkForUpdates'].preferences.patch_available:
				layout.separator()
			layout.label(text=context.preferences.addons['AN7_checkForUpdates'].preferences.minor_version + ' minor upgrade')
			minorLink = context.preferences.addons['AN7_checkForUpdates'].preferences.minor_link
			minorName = minorLink.split('/')[-1]
			op = layout.operator('wm.url_open', text=minorName, icon='URL')
			op.url = minorLink
		if context.preferences.addons['AN7_checkForUpdates'].preferences.major_available:
			if context.preferences.addons['AN7_checkForUpdates'].preferences.patch_available or context.preferences.addons['AN7_checkForUpdates'].preferences.minor_available:
				layout.separator()
			layout.label(text=context.preferences.addons['AN7_checkForUpdates'].preferences.major_version + ' major update')
			majorLink = context.preferences.addons['AN7_checkForUpdates'].preferences.major_link
			majorName = majorLink.split('/')[-1]
			op = layout.operator('wm.url_open', text=majorName, icon='URL')
			op.url = majorLink
		if not (context.preferences.addons['AN7_checkForUpdates'].preferences.patch_available or context.preferences.addons['AN7_checkForUpdates'].preferences.minor_available or context.preferences.addons['AN7_checkForUpdates'].preferences.major_available):
			layout.label(text="You are running the latest public Blender release")
		elif not context.preferences.addons['AN7_checkForUpdates'].preferences.full_check:
			layout.separator()
			op = layout.operator('an7checkforupdates.check', text='Check for All Updates…', icon='FILE_REFRESH')
			op.mode=1



###########################################################################
# Check for updates on Blender startup

@persistent
def an7_check_for_updates_on_load(self, context):
	if bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.auto_check != 'none':
		# Reset toggles
		bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.patch_available = False
		if bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.auto_check == 'all':
			bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.minor_available = False
			bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.major_available = False
		else:
			bpy.context.preferences.addons['AN7_checkForUpdates'].preferences.full_check = False
		# Check for updates
		bpy.ops.an7checkforupdates.check("EXEC_DEFAULT", mode=0)

# Show main menu button if updates are available

def an7_check_for_updates_main_menu(self, context):
	if not (False) and (context.preferences.addons['AN7_checkForUpdates'].preferences.patch_available or context.preferences.addons['AN7_checkForUpdates'].preferences.minor_available or context.preferences.addons['AN7_checkForUpdates'].preferences.major_available):
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
	
	# Global Settings
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
	auto_check: bpy.props.EnumProperty(
		name='Automatically Check',
		description='Choose the type of Blender download that should be checked for',
		items=[
			('none', 'None', 'Do not automatically check for updates on launch'),
			('patch', 'Patch Updates', 'Check for patch updates on launch'),
			('all', 'All Updates (slow)', 'Check for major, minor, and patch updates on launch')
		],
		default='patch'
	)
	
	# Error and status tracking system
	error_message: bpy.props.StringProperty(
		name='Error Message',
		description='Error Message',
		default=""
	)
	full_check: bpy.props.BoolProperty(
		name='All Upgrades Checked',
		description='True if a full upgrade check has been performed',
		default=False
	)
	
	# Patch updates
	patch_available: bpy.props.BoolProperty(
		name='Patch available',
		description='Status of available patch updates',
		default=False
	)
	patch_version: bpy.props.StringProperty(
		name='Update Version',
		description='Updated version number',
		default=''
	)
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
	minor_version: bpy.props.StringProperty(
		name='Upgrade Version',
		description='Updated version number',
		default=bpy.app.version_string
	)
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
	major_version: bpy.props.StringProperty(
		name='Upgrade Version',
		description='Updated version number',
		default=bpy.app.version_string
	)
	major_link: bpy.props.StringProperty(
		name='Upgrade Link',
		description='Updated version number',
		default=""
	)
	
	# Plugin preferences rendering
	def draw(self, context):
		layout = self.layout
		layout.prop(self, "download_format")
		layout.prop(self, "auto_check")
		box = layout.box()
		box.label(text='Warning: Blender will freeze for several seconds when checking for updates.')
		col = box.column(align=True)
		col.label(text='You can improve app launch speed by choosing "Patch Updates" or "None"')
#		col.label(text='then using the "Help" menu to check for all updates only when needed.')
		col.label(text='then checking for all upgrades from the "Help" menu only when needed.')



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
	