# =============================================================================
# File: bloom_filter.py
# Author: deArrudal
# Description: Bloom filter implementation for IP membership testing.
# Created: 2025-05-21
# License: GPL-3.0 License
# =============================================================================

import math
import mmh3
from bitarray import bitarray

# Constants
DEFAULT_ITEMS_COUNT = 10_000
DEFAULT_FP_PROB = 0.01
LOG2 = math.log(2)
LOG2_SQUARED = LOG2**2


# Bloom filter implementation using bitarray and mmh3 (geeksforgeeks.org)
class BloomFilter:
    def __init__(self, items_count=DEFAULT_ITEMS_COUNT, fp_prob=DEFAULT_FP_PROB):
        # Compute Bloom filter parameters
        self.items_count = items_count
        self.fp_prob = fp_prob
        self.size = self._get_size(items_count, fp_prob)
        self.hash_count = self._get_hash_count(self.size, items_count)

        # Initialize bit array
        self.bit_array = bitarray(self.size)
        self.bit_array.setall(0)

    # Add an item to the Bloom filter
    def add(self, item):
        for index in self._hashes(item):
            self.bit_array[index] = 1

    # Returns True if probably present, False if definitely not
    def check(self, item):
        return all(self.bit_array[index] for index in self._hashes(item))

    # Allow check inside loop
    def __contains__(self, item):
        return self.check(item)

    # Calculate optimal bit array size (m) to achieve desired false positive rate
    def _get_size(self, n, p):
        return int(-(n * math.log(p)) / (LOG2_SQUARED))

    # Calculate optimal number of hash functions (k)
    def _get_hash_count(self, m, n):
        return int((m / n) * LOG2)

    # Generate hash values using mmh3 with different seeds
    def _hashes(self, item):
        return [mmh3.hash(item, seed) % self.size for seed in range(self.hash_count)]
