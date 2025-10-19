"""
LLM Consent management module for external LLM data access.

This module provides functionality to manage user consent specifically for
allowing their data to be analyzed by external LLMs, separate from directory
access consent which will be handled in a different module.

Note: This is specifically for LLM data access consent, not directory access consent.
"""

from .llm_consent_manager import LLMConsentManager

__all__ = ['LLMConsentManager']