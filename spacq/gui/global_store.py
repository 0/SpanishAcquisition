from functools import partial
from threading import RLock
from pubsub import pub
import wx

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

		send = partial(wx.CallAfter, pub.sendMessage)

		self.devices = PubDict(self.lock, send, 'device')
		self.resources = PubDict(self.lock, send, 'resource')
		self.variables = PubDict(self.lock, send, 'variable')

		self.pulse_program = None
