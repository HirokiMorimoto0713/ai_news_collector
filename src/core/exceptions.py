"""
Custom exceptions for AI News Collector
"""


class AINewsCollectorError(Exception):
    """Base exception for AI News Collector"""
    pass


class ConfigError(AINewsCollectorError):
    """Configuration related errors"""
    pass


class CollectionError(AINewsCollectorError):
    """Article collection related errors"""
    pass


class ProcessingError(AINewsCollectorError):
    """Article processing related errors"""
    pass


class PublishingError(AINewsCollectorError):
    """Publishing related errors"""
    pass


class ValidationError(AINewsCollectorError):
    """Data validation related errors"""
    pass 