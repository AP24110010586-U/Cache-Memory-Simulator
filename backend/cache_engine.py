"""
cache_engine.py  –  Cache Memory Simulation Engine (Python)
Mirrors the C++ engine logic exactly.
Used when the compiled C++ binary is unavailable.
All simulation logic lives here — Flask merely calls this module.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Optional
from collections import deque
from copy import deepcopy

# ================================================================
# Enums / Constants
# ================================================================
DIRECT = "direct"
FULLY_ASSOCIATIVE = "fully_associative"
SET_ASSOCIATIVE = "set_associative"
FIFO = "fifo"
LRU = "lru"


# ================================================================
# Data Structures
# ================================================================
@dataclass
class CacheLine:
    valid: bool = False
    tag: int = 0
    block: int = 0  # which memory block is stored

    def to_dict(self):
        return {"valid": self.valid, "tag": self.tag, "block": self.block}


@dataclass
class CacheSet:
    lines: List[CacheLine]
    fifo_order: deque = field(default_factory=deque)   # indices of lines in insertion order
    lru_time: List[int] = field(default_factory=list)  # timestamps per line

    @classmethod
    def create(cls, ways: int) -> "CacheSet":
        return cls(
            lines=[CacheLine() for _ in range(ways)],
            fifo_order=deque(),
            lru_time=[0] * ways,
        )


@dataclass
class CacheConfig:
    main_memory_size: int = 256
    cache_size: int = 64
    block_size: int = 4
    mapping: str = DIRECT
    associativity: int = 1
    replacement: str = LRU
    # derived
    num_blocks: int = 0
    num_cache_lines: int = 0
    num_sets: int = 0
    offset_bits: int = 0
    index_bits: int = 0
    tag_bits: int = 0

    def compute_derived(self):
        self.num_blocks = self.main_memory_size // self.block_size
        self.num_cache_lines = self.cache_size // self.block_size
        self.offset_bits = int(math.log2(self.block_size))
        if self.mapping == DIRECT:
            self.num_sets = self.num_cache_lines
            self.index_bits = int(math.log2(self.num_cache_lines))
        elif self.mapping == FULLY_ASSOCIATIVE:
            self.num_sets = 1
            self.index_bits = 0
        else:
            self.num_sets = self.num_cache_lines // self.associativity
            self.index_bits = int(math.log2(self.num_sets)) if self.num_sets > 1 else 0
        self.tag_bits = max(0, 32 - self.index_bits - self.offset_bits)


@dataclass
class SimEvent:
    address: int = 0
    block_number: int = 0
    tag: int = 0
    index: int = 0
    offset: int = 0
    hit: bool = False
    replacement: bool = False
    victim_line: int = -1
    evicted_block: int = 0
    inserted_block: int = 0
    event_type: str = ""
    cache_snapshot: list = field(default_factory=list)
    total_accesses: int = 0
    hits: int = 0
    misses: int = 0

    def to_dict(self):
        return {
            "address": self.address,
            "block_number": self.block_number,
            "tag": self.tag,
            "index": self.index,
            "offset": self.offset,
            "hit": self.hit,
            "replacement": self.replacement,
            "victim_line": self.victim_line,
            "evicted_block": self.evicted_block,
            "inserted_block": self.inserted_block,
            "event_type": self.event_type,
            "cache_snapshot": self.cache_snapshot,
            "total_accesses": self.total_accesses,
            "hits": self.hits,
            "misses": self.misses,
        }


# ================================================================
# Helpers
# ================================================================
def is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def validate_config(cfg: CacheConfig) -> Optional[str]:
    if cfg.main_memory_size <= 0:
        return "Main memory size must be positive."
    if cfg.cache_size <= 0:
        return "Cache size must be positive."
    if cfg.block_size <= 0:
        return "Block size must be positive."
    if not is_power_of_two(cfg.block_size):
        return "Block size must be a power of two."
    if not is_power_of_two(cfg.main_memory_size):
        return "Main memory size must be a power of two."
    if not is_power_of_two(cfg.cache_size):
        return "Cache size must be a power of two."
    if cfg.cache_size < cfg.block_size:
        return "Cache size must be greater than or equal to block size."
    if cfg.cache_size % cfg.block_size != 0:
        return "Cache size must be divisible by block size."
    if cfg.associativity <= 0:
        return "Associativity must be a positive integer."
    num_lines = cfg.cache_size // cfg.block_size
    if num_lines % cfg.associativity != 0:
        return "Number of cache lines must be divisible by associativity."
    if cfg.associativity > num_lines:
        return "Associativity cannot exceed the number of cache lines."
    if cfg.main_memory_size < cfg.cache_size:
        return "Main memory size must be >= cache size."
    return None


def breakdown_address(address: int, cfg: CacheConfig) -> dict:
    block_number = address // cfg.block_size
    offset = address % cfg.block_size

    if cfg.mapping == DIRECT:
        index = block_number % cfg.num_cache_lines
        tag = block_number // cfg.num_cache_lines
        has_index = True
    elif cfg.mapping == FULLY_ASSOCIATIVE:
        index = 0
        tag = block_number
        has_index = False
    else:  # SET_ASSOCIATIVE
        index = block_number % cfg.num_sets
        tag = block_number // cfg.num_sets
        has_index = True

    return {
        "address": address,
        "block_number": block_number,
        "tag": tag,
        "index": index,
        "offset": offset,
        "has_index": has_index,
        "offset_bits": cfg.offset_bits,
        "index_bits": cfg.index_bits,
        "tag_bits": cfg.tag_bits,
    }


def snapshot_sets(sets: List[CacheSet]) -> list:
    return [[ln.to_dict() for ln in s.lines] for s in sets]


# ================================================================
# Direct Mapping
# ================================================================
class DirectMappedCache:
    def __init__(self, cfg: CacheConfig):
        self.cfg = cfg
        self.lines: List[CacheLine] = [CacheLine() for _ in range(cfg.num_cache_lines)]
        self.total_accesses = 0
        self.hits = 0
        self.misses = 0

    def access(self, address: int) -> SimEvent:
        self.total_accesses += 1
        bd = breakdown_address(address, self.cfg)
        ev = SimEvent(
            address=address,
            block_number=bd["block_number"],
            tag=bd["tag"],
            index=bd["index"],
            offset=bd["offset"],
            inserted_block=bd["block_number"],
        )
        line = self.lines[bd["index"]]

        if line.valid and line.tag == bd["tag"]:
            # HIT
            ev.hit = True
            ev.event_type = "HIT"
            self.hits += 1
        else:
            # MISS
            self.misses += 1
            if line.valid:
                ev.replacement = True
                ev.victim_line = bd["index"]
                ev.evicted_block = line.block
                ev.event_type = "MISS_REPLACE"
            else:
                ev.replacement = False
                ev.event_type = "MISS"
            line.valid = True
            line.tag = bd["tag"]
            line.block = bd["block_number"]

        ev.cache_snapshot = [[ln.to_dict() for ln in self.lines]]
        ev.total_accesses = self.total_accesses
        ev.hits = self.hits
        ev.misses = self.misses
        return ev


# ================================================================
# Fully Associative Cache
# ================================================================
class FullyAssociativeCache:
    def __init__(self, cfg: CacheConfig):
        self.cfg = cfg
        self.cache_set = CacheSet.create(cfg.num_cache_lines)
        self.total_accesses = 0
        self.hits = 0
        self.misses = 0
        self.tick = 0

    def access(self, address: int) -> SimEvent:
        self.tick += 1
        self.total_accesses += 1
        bd = breakdown_address(address, self.cfg)
        ev = SimEvent(
            address=address,
            block_number=bd["block_number"],
            tag=bd["tag"],
            index=0,
            offset=bd["offset"],
            inserted_block=bd["block_number"],
        )
        s = self.cache_set
        # Search all lines (tag for FA == block_number)
        hit_line = -1
        for i, ln in enumerate(s.lines):
            if ln.valid and ln.tag == bd["block_number"]:
                hit_line = i
                break

        if hit_line >= 0:
            ev.hit = True
            ev.event_type = "HIT"
            self.hits += 1
            if self.cfg.replacement == LRU:
                s.lru_time[hit_line] = self.tick
            # FIFO: hit does NOT change insertion order
        else:
            self.misses += 1
            # Find empty slot
            empty_slot = next((i for i, ln in enumerate(s.lines) if not ln.valid), -1)
            if empty_slot >= 0:
                ev.replacement = False
                ev.event_type = "MISS"
                s.lines[empty_slot] = CacheLine(valid=True, tag=bd["block_number"], block=bd["block_number"])
                if self.cfg.replacement == LRU:
                    s.lru_time[empty_slot] = self.tick
                else:
                    s.fifo_order.append(empty_slot)
            else:
                ev.replacement = True
                ev.event_type = "MISS_REPLACE"
                if self.cfg.replacement == FIFO:
                    victim = s.fifo_order.popleft()
                else:
                    victim = min(range(len(s.lines)), key=lambda i: s.lru_time[i] if s.lines[i].valid else float('inf'))
                ev.victim_line = victim
                ev.evicted_block = s.lines[victim].block
                s.lines[victim] = CacheLine(valid=True, tag=bd["block_number"], block=bd["block_number"])
                if self.cfg.replacement == LRU:
                    s.lru_time[victim] = self.tick
                else:
                    s.fifo_order.append(victim)

        ev.cache_snapshot = [[ln.to_dict() for ln in s.lines]]
        ev.total_accesses = self.total_accesses
        ev.hits = self.hits
        ev.misses = self.misses
        return ev


# ================================================================
# Set Associative Cache
# ================================================================
class SetAssociativeCache:
    def __init__(self, cfg: CacheConfig):
        self.cfg = cfg
        self.sets: List[CacheSet] = [CacheSet.create(cfg.associativity) for _ in range(cfg.num_sets)]
        self.total_accesses = 0
        self.hits = 0
        self.misses = 0
        self.tick = 0

    def access(self, address: int) -> SimEvent:
        self.tick += 1
        self.total_accesses += 1
        bd = breakdown_address(address, self.cfg)
        ev = SimEvent(
            address=address,
            block_number=bd["block_number"],
            tag=bd["tag"],
            index=bd["index"],
            offset=bd["offset"],
            inserted_block=bd["block_number"],
        )
        s = self.sets[bd["index"]]
        # Search the target set
        hit_line = -1
        for i, ln in enumerate(s.lines):
            if ln.valid and ln.tag == bd["tag"]:
                hit_line = i
                break

        if hit_line >= 0:
            ev.hit = True
            ev.event_type = "HIT"
            self.hits += 1
            if self.cfg.replacement == LRU:
                s.lru_time[hit_line] = self.tick
        else:
            self.misses += 1
            empty_slot = next((i for i, ln in enumerate(s.lines) if not ln.valid), -1)
            if empty_slot >= 0:
                ev.replacement = False
                ev.event_type = "MISS"
                s.lines[empty_slot] = CacheLine(valid=True, tag=bd["tag"], block=bd["block_number"])
                if self.cfg.replacement == LRU:
                    s.lru_time[empty_slot] = self.tick
                else:
                    s.fifo_order.append(empty_slot)
            else:
                ev.replacement = True
                ev.event_type = "MISS_REPLACE"
                if self.cfg.replacement == FIFO:
                    victim = s.fifo_order.popleft()
                else:
                    victim = min(range(len(s.lines)), key=lambda i: s.lru_time[i] if s.lines[i].valid else float('inf'))
                ev.victim_line = victim
                ev.evicted_block = s.lines[victim].block
                s.lines[victim] = CacheLine(valid=True, tag=bd["tag"], block=bd["block_number"])
                if self.cfg.replacement == LRU:
                    s.lru_time[victim] = self.tick
                else:
                    s.fifo_order.append(victim)

        ev.cache_snapshot = snapshot_sets(self.sets)
        ev.total_accesses = self.total_accesses
        ev.hits = self.hits
        ev.misses = self.misses
        return ev


# ================================================================
# Main simulation entry-point called by Flask
# ================================================================
def run_simulation(config_dict: dict, addresses: List[int]) -> dict:
    cfg = CacheConfig(
        main_memory_size=int(config_dict.get("main_memory_size", 256)),
        cache_size=int(config_dict.get("cache_size", 64)),
        block_size=int(config_dict.get("block_size", 4)),
        mapping=config_dict.get("mapping", DIRECT),
        associativity=int(config_dict.get("associativity", 1)),
        replacement=config_dict.get("replacement", LRU),
    )

    err = validate_config(cfg)
    if err:
        return {"error": err}

    cfg.compute_derived()

    if cfg.mapping == DIRECT:
        sim = DirectMappedCache(cfg)
    elif cfg.mapping == FULLY_ASSOCIATIVE:
        sim = FullyAssociativeCache(cfg)
    else:
        sim = SetAssociativeCache(cfg)

    events = [sim.access(addr) for addr in addresses]

    total = sim.total_accesses
    hits = sim.hits
    misses = sim.misses
    hit_ratio = (hits / total) if total else 0.0
    miss_ratio = (misses / total) if total else 0.0

    return {
        "events": [e.to_dict() for e in events],
        "statistics": {
            "total_accesses": total,
            "hits": hits,
            "misses": misses,
            "hit_ratio": round(hit_ratio, 6),
            "miss_ratio": round(miss_ratio, 6),
            "hit_percentage": round(hit_ratio * 100, 2),
            "miss_percentage": round(miss_ratio * 100, 2),
        },
        "config": {
            "main_memory_size": cfg.main_memory_size,
            "cache_size": cfg.cache_size,
            "block_size": cfg.block_size,
            "mapping": cfg.mapping,
            "associativity": cfg.associativity,
            "replacement": cfg.replacement,
            "num_blocks": cfg.num_blocks,
            "num_cache_lines": cfg.num_cache_lines,
            "num_sets": cfg.num_sets,
            "offset_bits": cfg.offset_bits,
            "index_bits": cfg.index_bits,
            "tag_bits": cfg.tag_bits,
        }
    }
