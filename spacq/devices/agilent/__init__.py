import logging
log = logging.getLogger(__name__)


name = 'Agilent'

from . import dm34410a
models = [dm34410a]
log.debug('Found models for "{0}": {1}'.format(name, ''.join(str(x) for x in models)))

from .mock import mock_dm34410a
mock_models = [mock_dm34410a]
log.debug('Found mock models for "{0}": {1}'.format(name, ''.join(str(x) for x in mock_models)))
