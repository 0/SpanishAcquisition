import logging
log = logging.getLogger(__name__)


name = 'Tektronix'

from . import awg5014b, dpo7104
models = [awg5014b, dpo7104]
log.debug('Found models for "{0}": {1}'.format(name, ''.join(str(x) for x in models)))

from .mock import mock_awg5014b, mock_dpo7104
mock_models = [mock_awg5014b, mock_dpo7104]
log.debug('Found mock models for "{0}": {1}'.format(name, ''.join(str(x) for x in mock_models)))
