"""Backwards-compatible re-exports of the original flat ``qtc`` module.

The formulas now live in :mod:`ecg_analytics.qtc.formulas`.  This shim
keeps ``from ecg_analytics import qtc_bazett`` working.
"""

from .qtc.formulas import qtc_bazett, qtc_framingham, qtc_fridericia, qtc_hodges

__all__ = ["qtc_bazett", "qtc_framingham", "qtc_fridericia", "qtc_hodges"]
