"""
MCP Prompts for LeoWiki Server

This package provides prompt templates that guide LLM interactions
with educational content. Prompts make it easier for users to get
structured, pedagogically sound responses.
"""

from .educational import register_educational_prompts

__all__ = [
    "register_educational_prompts",
]
