from os import listdir
from os.path import isfile, join
import csv
import itertools
import logging

from cubetl.core import Node, Component
from cubetl.fs import FileReader
from cubetl.script import Eval
from cubetl.table import TableLookup
from cubetl.util.cache import Cache
import chardet
import re


# Get an instance of a logger
logger = logging.getLogger(__name__)


class CachedTableLookup(TableLookup):

    NOT_CACHED = "NOT_CACHED"

    def __init__(self, table, lookup, default=None):
        super().__init__(table=table, lookup=lookup, default=default)

        self.cache_hits = 0
        self.cache_misses = 0

        self._cache = None

    def initialize(self, ctx):

        super(CachedTableLookup, self).initialize(ctx)
        self._cache = Cache().cache()

    def finalize(self, ctx):

        logger.info("%s  hits/misses: %d/%d (%.2f%%)" % (self, self.cache_hits, self.cache_misses, float(self.cache_hits) / (self.cache_hits + self.cache_misses) * 100))

        super(CachedTableLookup, self).finalize(ctx)

    def process(self, ctx, m):

        keys = self._resolve_lookup_keys(ctx, m)
        cache_key = tuple(sorted(keys.items()))

        result = self._cache.get(cache_key, CachedTableLookup.NOT_CACHED)
        if (result != CachedTableLookup.NOT_CACHED):
            self.cache_hits = self.cache_hits + 1
            if (ctx.debug2):
                logger.debug("Query cache hit: %s" % (result))
        else:
            self.cache_misses = self.cache_misses + 1
            result = self._do_lookup(ctx, m, keys)
            self._cache.put(cache_key, result)

        if (result):
            Eval.process_evals(ctx, m, self.mappings, result)
        else:
            m.update({ k: ctx.interpolate(m, v) for k, v in self.default.items() })

        yield m

