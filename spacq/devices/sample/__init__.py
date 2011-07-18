import logging
log = logging.getLogger(__name__)


name = 'Sample'

from . import abc1234
models = [abc1234]
log.debug('Found models for "{0}": {1}'.format(name, ''.join(str(x) for x in models)))

from .mock import mock_abc1234
mock_models = [mock_abc1234]
log.debug('Found mock models for "{0}": {1}'.format(name, ''.join(str(x) for x in mock_models)))
