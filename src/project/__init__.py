"""
Project aggregator module - exports key functions for merging local and git metrics.
"""
from .aggregator import (
    ProjectInfo,
    from_local,
    from_git,
    merge_local_git,
    compute_rank_inputs,
    compute_preliminary_score,
    to_dict,
)

__all__ = [
    "ProjectInfo",
    "from_local",
    "from_git",
    "merge_local_git",
    "compute_rank_inputs",
    "compute_preliminary_score",
    "to_dict",
]

