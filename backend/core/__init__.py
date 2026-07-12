"""
Core module for enterprise metadata application.

This module contains the core functionality including:
- Database management and migrations
- Domain expression engine for conditional field behavior
- Base models and ORM functionality
- Access control and policies
"""

from .domain_engine import DomainEngine, domain_engine, DomainParseError, DomainEvaluationError

__all__ = [
    'DomainEngine',
    'domain_engine', 
    'DomainParseError',
    'DomainEvaluationError'
]