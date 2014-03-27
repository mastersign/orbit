#!/usr/bin/python3

# Package tink.setup

import os, json

HOST = "localhost"
PORT = 4223

class ConnConfig:

	host = HOST
	port = PORT

	def configfilepath(self):
		return os.path.realpath(os.path.expanduser('~/.tink'))

	def writeconfigfile(self, data):
		with open(self.configfilepath(), 'w', encoding='utf-8') as f:
			f.write(json.dumps(data))

	def __init__(self):
		configfile = self.configfilepath()
		if not os.path.isfile(configfile):
			return
		with open(configfile, 'r', encoding='utf-8') as f:
			configdata = json.loads(f.read())

		if type(configdata) is dict:
			if 'host' in configdata:
				self.host = configdata['host']
			if 'port' in configdata:
				self.port = int(configdata['port'])

	def set(self, host, port = None):
		self.host = host
		if port:
			self.port = int(port)
			self.writeconfigfile({'host': host, 'port': port})
		else:
			self.writeconfigfile({'host': host})


# script execution
if __name__ == '__main__':
	cc = ConnConfig()
	print('Tink Connection Configuration:\n'
		+ 'Host = ' + cc.host + '\n'
		+ 'Port = ' + str(cc.port))
