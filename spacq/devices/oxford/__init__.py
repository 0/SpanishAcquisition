import logging
log = logging.getLogger(__name__)


name = 'Oxford Instruments'

from . import ips120_10
models = [ips120_10]
log.debug('Found models for "{0}": {1}'.format(name, ''.join(str(x) for x in models)))

from .mock import mock_ips120_10
mock_models = [mock_ips120_10]
log.debug('Found mock models for "{0}": {1}'.format(name, ''.join(str(x) for x in mock_models)))
