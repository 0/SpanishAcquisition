from threading import RLock
from pubsub import pub

from spacq.tool.box import PubDict

"""
A single storage location for everything globally-unique.
"""


class GlobalStore(object):
	"""
	A global value store for an entire application.
	"""

	def __init__(self):
		self.lock = RLock()

		self.devices = PubDict(self.lock, pub, 'device')
		self.resources = PubDict(self.lock, pub, 'resource')
		self.variables = PubDict(self.lock, pub, 'variable')

		self.pulse_program = None
