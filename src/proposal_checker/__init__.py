"""proposal-checker: grade an Upwork proposal before you send it."""
from .checker import Check, Report, check_proposal

__all__ = ["Check", "Report", "check_proposal"]
__version__ = "0.1.0"
