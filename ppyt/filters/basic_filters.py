# coding: utf-8
import logging
from ppyt.filters import FilterBase

logger = logging.getLogger(__name__)


class AllPassFilter(FilterBase):
    """全ての銘柄を対象にするフィルタ"""
    _findkey = '全て通過'

    def _setup(self):
        pass

    def _filter_stocks(self, stocks):
        return stocks
