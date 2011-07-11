name = 'Tektronix'

from . import awg5014b, dpo7104
models = [awg5014b, dpo7104]

from .mock import mock_awg5014b, mock_dpo7104
mock_models = [mock_awg5014b, mock_dpo7104]
