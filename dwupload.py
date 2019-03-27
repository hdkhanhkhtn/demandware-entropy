# coding=utf8
#
# The Initial Developer of the code is Danny Gehl (SGD).
#
# Contributor(s):
#   Danny Gehl (SGD)
#   Andreas Seyfahrt (aseyfarth)
#

import sublime, sublime_plugin, re, urllib.request, urllib.error, os, zipfile, posixpath, threading, sys

threads = []

# Class which represents a local resource
class Resource():
	def __init__(self, path):
		self.path = path
		self.base_path      = None
		self.cartridge_name = None
		self.cartridge_dir  = None
		self.parse_path()

	def parse_path(self):
		self.base_dir = os.path.dirname(self.path)
		if self.is_in_cartridge():
			# backslash needs escaping in regex
			rsep = os.sep
			if rsep.find("\\") > -1:
				rsep = "\\\\"
			if self.path.find(os.sep+"cartridge"+os.sep) > -1:
				path_pattern  = "(.*)"+rsep+"([^"+rsep+"]*)"+rsep+"cartridge"+rsep
			else:
				path_pattern  = "(.*)"+rsep+"([^"+rsep+"]*)"+rsep+"[^"+rsep+"]*"
			path_elements  = re.search(re.compile(path_pattern),self.path)

			self.base_path      = path_elements.group(1)
			self.cartridge_name = path_elements.group(2)
			self.cartridge_dir  = self.base_path+os.sep+self.cartridge_name

	def is_in_cartridge(self):
		# need to have cartridge in path
		if self.path.find(os.sep+"cartridge"+os.sep) > -1:
			return True
		# or a cartridge sub directory
		else:
			cdir = os.path.join(self.base_dir, 'cartridge')
			return os.path.isdir(cdir)

	def is_cartridge(self):
		cdir = os.path.join(self.path, 'cartridge')
		return os.path.isdir(cdir)

	def get_upload_path(self):
		# convert windows path "\" to one that will work for a URL
		upload_path = self.path.replace("\\", "/")
		upload_base_path = self.base_path.replace("\\", "/")

		return posixpath.relpath(upload_path, upload_base_path)

# Class to handle the server communication
class DemandwareServer():
	def __init__(self):
		self.load_settings()

	def load_settings(self):
		settings = sublime.load_settings('DemandwareServerUpload.sublime-settings')
		self.instance = settings.get("instance")
		self.username = settings.get("username")
		self.password = settings.get("password")
		self.version  = settings.get("version")
		self.enabled  = settings.get("enabled")

	def get_opener(self):
		# create a password manager
		password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()

		# Add the username and password.
		top_level_url = "https://"+self.instance
		password_mgr.add_password(None, top_level_url, self.username, self.password)

		handler = urllib.request.HTTPBasicAuthHandler(password_mgr)

		# create "opener" (OpenerDirector instance)
		opener = urllib.request.build_opener(handler)

		return opener

	def remote_request(self, resource_path, method, data):
		opener = self.get_opener()

		url = "https://"+self.instance+":443/on/demandware.servlet/webdav/Sites/Cartridges/"+self.version+"/"+resource_path
		req = urllib.request.Request(url,data=data, method=method)

		# use the opener to send the request
		try:
			response = opener.open(req)
		except urllib.error.HTTPError as e:
		    print('The server couldn\'t fulfill the request (HTTP '+method+' to "'+url+'"). ' +str(e.reason)+' ('+str(e.code)+')')
		    self.httpCode = e.code
		    if e.code == 401:
		    	sublime.error_message('Configured credentials are incorrect!')
		    	sys.exit(1)
		    #sublime.status_message('Error code: ', e.code)
		    return False
		except urllib.error.URLError as e:
		    print('We failed to reach the server.')
		    print('Reason: ', e.reason)
		    return False
		else:
			return True

	def check_for_file(self, file_path):
		if self.remote_request(file_path,"GET", None):
			print("File '"+file_path+"' already exists...")
			return True
		else:
			return False

	def upload_file(self, data, upload_path):
		# get the contents from the current view and construct the URL
		if self.remote_request(upload_path,"PUT", data.encode("utf-8")):
			print("Upload of '"+upload_path+"' successful")
			return True
		else:
			return False

	def upload_directory(self, upload_path):
		print("Creating directory "+upload_path+" on server")
		if self.remote_request(upload_path,"MKCOL", None):
			print("Creation of directory '"+upload_path+"'' successful")
			return True
		else:
			return False

	def create_directories(self, upload_path):
		path_elements = upload_path.split("/")
		path_elements = path_elements[:len(path_elements)-1]

		dir_path = ""
		for elem in path_elements:
			dir_path = dir_path + "/" + elem
			self.upload_directory(dir_path)

	def unzip_file(self, upload_path):
		if self.remote_request(upload_path,"POST", b"method=UNZIP"):
			print("Unzipping of '"+upload_path+"' successful")
			return True
		else:
			return False

	def delete_file(self, upload_path):
		if self.remote_request(upload_path,"DELETE", None):
			print("Deletion of '"+upload_path+"' successful")
			return True
		else:
			return False

# Thread to handle upload of saved file
class UploadSelectedFile(threading.Thread):
	def __init__(self, path, content):
		self.self = self
		self.path = path
		self.content = content
		self.result = None
		threading.Thread.__init__(self)

	def run(self):
		server = DemandwareServer()
		# refresh the setttings
		server.load_settings()
		if not server.enabled:
			return

		if not server.instance:
			print("Please specify the 'instance' in DemandwareServerUpload settings")
			return
		if not server.username:
			print("Please specify the 'username' in DemandwareServerUpload settings")
			return
		if not server.password:
			print("Please specify the 'password' in DemandwareServerUpload settings")
			return
		if not server.version:
			print("Please specify the 'version' in DemandwareServerUpload settings")
			return

		# Create a resource from the path
		resource = Resource(self.path)
		data = self.content

		# check if file is in a cartridge
		if resource.is_in_cartridge():
			# and if so, upload it

			# get the path to upload to
			upload_path = resource.get_upload_path()
			print("Uploading "+upload_path)

			if not server.check_for_file(upload_path):
				server.create_directories(upload_path)

			if server.upload_file(data, upload_path):
				sublime.status_message("Upload of "+upload_path+" successful")

		else:
			print("File is not in a cartridge, upload skipped.")

# Event listener for the file save
class DemandwareServerUpload(sublime_plugin.EventListener):

	def on_post_save(self, view):
		# get the current view which will ultimately get uploaded
		path = view.file_name()
		data = view.substr(sublime.Region(0, view.size()))

		thread = UploadSelectedFile(path, data)
		threads.append(thread)
		thread.start()

# The thread for handling a cartridge upload
class UploadCartridge(threading.Thread):
	def __init__(self, path):
		self.self = self
		self.path = path
		self.result = None
		threading.Thread.__init__(self)

	def run(self):
		resource = Resource(self.path)

		if not resource.is_in_cartridge():
			print("File is not in a cartridge, upload skipped.")
			return

		server = DemandwareServer()
		server.load_settings()
		if not server.enabled:
			return

		base_path      = resource.base_path
		cartridge_name = resource.cartridge_name
		cartridge_dir = resource.cartridge_dir
		zipfile_name = cartridge_dir+'.zip'

		with zipfile.ZipFile(zipfile_name, 'w') as myzip:
			for root, dirs, files in os.walk(cartridge_dir):
				for file in files:
					myzip.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), base_path))
		myzip.close()
		print("Zipped cartridge "+cartridge_name)

		sublime.status_message("Starting upload of cartridge '"+cartridge_name+"' ...")

		f = open(zipfile_name,'rb')
		if server.remote_request(cartridge_name+'.zip',"PUT", f.read()):
			print("Upload of '"+zipfile_name+"' successful")
		else:
			print("Upload of '"+zipfile_name+"' failed")
			return False
		
		f.close()
		# server.upload_file(f.read(),zipfile_name)

		# delete old cartridge first (if it exists)
		if not server.delete_file(cartridge_name):
			if server.httpCode != 404:
				return False

		if not server.unzip_file(cartridge_name+'.zip'):
			return False

		if not server.delete_file(cartridge_name+'.zip'):
			return False

		os.remove(zipfile_name)
		sublime.status_message("Upload of cartridge '"+cartridge_name+"' successful")

# The command for uploading a cartridge
class UploadCartridgeCommand(sublime_plugin.WindowCommand):

	def run(self):

		path = sublime.active_window().active_view().file_name()

		if (path is None):
			print("No file selected. Path is not available")
			return

		thread = UploadCartridge(path)
		threads.append(thread)
		thread.start()

# The thread to upload all cartridges
class UploadAllCartridges(threading.Thread):
	def __init__(self, path):
		self.self = self
		self.path = path
		self.result = None
		threading.Thread.__init__(self)

	def run(self):
		resource = Resource(self.path)

		if not resource.is_in_cartridge():
			print("File is not in a cartridge, upload skipped.")
			return

		server = DemandwareServer()
		server.load_settings()
		if not server.enabled:
			return

		base_dir = os.path.dirname(resource.cartridge_dir)
		print("Scanning directory "+base_dir+" for cartridges.")

		zipfile_name = base_dir+'upload.zip'
		cartridge_names = []

		with zipfile.ZipFile(zipfile_name, 'w') as myzip:
			for dirname in os.listdir(base_dir):
				elem = os.path.join(base_dir,dirname)
				if os.path.isdir(elem) & Resource(elem).is_cartridge():
					print("Found cartridge "+dirname)
					cartridge_names.append(dirname)

					for root, dirs, files in os.walk(elem):
						for file in files:
							myzip.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), base_dir))

		myzip.close()
		print("Zipped all cartridges.")

		sublime.status_message("Starting upload of cartridges '"+", ".join(cartridge_names)+"' ...")

		# delete old cartridge first (if it exists)
		for cartridge in cartridge_names:
			if not server.delete_file(cartridge):
				if server.httpCode != 404:
					# TODO Add proper error messages
					#sublime.error_message()
					return False

		f = open(zipfile_name,'rb')
		if server.remote_request('upload.zip',"PUT", f.read()):
			print("Upload of '"+zipfile_name+"' successful")
		else:
			print("Upload of '"+zipfile_name+"' failed")
			return False

		f.close()
		
		if not server.unzip_file('upload.zip'):
			return False

		if not server.delete_file('upload.zip'):
			return False

		os.remove(zipfile_name)
		sublime.status_message("Upload of all cartridge successful")

# The command to upload all cartidges
class UploadAllCartridgesCommand(sublime_plugin.WindowCommand):

	def run(self):
		path = sublime.active_window().active_view().file_name()

		if (path is None):
			print("No file selected. Path is not available")
			return

		thread = UploadAllCartridges(path)
		threads.append(thread)
		thread.start()
