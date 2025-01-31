import loguru

from submaku_stream.utils.storage import ConfigStorage

logger = loguru.logger
config = ConfigStorage.get_instance().config



