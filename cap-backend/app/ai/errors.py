class AiError(Exception):
    pass


class AiUnavailable(AiError):
    pass


class ModelRefused(AiError):
    pass


class InvalidModelOutput(AiError):
    pass
