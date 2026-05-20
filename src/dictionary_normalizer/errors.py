class DictionaryNormalizerError(Exception):
    """Base exception for expected dictionary-normalizer failures."""


class ManifestError(DictionaryNormalizerError):
    """Raised when sources.toml is malformed."""


class ParserError(DictionaryNormalizerError):
    """Raised when an input source cannot be parsed."""


class ValidationError(DictionaryNormalizerError):
    """Raised when an artifact violates the interchange contract."""
