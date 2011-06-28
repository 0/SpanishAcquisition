name = 'Custom'

from . import voltage_source
models = [voltage_source]

from .mock import mock_voltage_source
mock_models = [mock_voltage_source]
