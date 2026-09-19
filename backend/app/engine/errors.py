class EngineError(Exception):
    pass


class InvalidAssumptionError(EngineError):
    pass


class NoValuationError(EngineError):
    pass