"""
Data ingestion pipeline for JSONL files.

This module handles automated ingestion of JSONL files containing
pre-computed embeddings from colleague uploads.
"""

from .jsonl_ingestion import JSONLIngestionPipeline, validate_jsonl_document

__all__ = ["JSONLIngestionPipeline", "validate_jsonl_document"]
