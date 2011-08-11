import logging
log = logging.getLogger(__name__)


name = 'Rohde & Schwarz'

from . import smf100a
models = [smf100a]
log.debug('Found models for "{0}": {1}'.format(name, ''.join(str(x) for x in models)))

from .mock import mock_smf100a
mock_models = [mock_smf100a]
log.debug('Found mock models for "{0}": {1}'.format(name, ''.join(str(x) for x in mock_models)))
