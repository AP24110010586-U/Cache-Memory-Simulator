// ============================================================
// FullyAssociative.cpp
// Fully Associative Cache — FIFO and LRU replacement
// ============================================================
#include "cache.h"
#include <vector>
#include <algorithm>
#include <limits>

class FullyAssociativeCache {
public:
    CacheConfig  cfg;
    CacheSet     cache_set;      // one single set containing all lines
    Stats        stats;
    uint64_t     tick = 0;

    explicit FullyAssociativeCache(const CacheConfig& c)
        : cfg(c), cache_set(c.num_cache_lines) {}

    SimEvent access(uint32_t address) {
        ++tick;
        ++stats.total_accesses;

        auto bd = breakdown_address(address, cfg);

        SimEvent ev;
        ev.address        = address;
        ev.block_number   = bd.block_number;
        ev.tag            = bd.tag;
        ev.index          = 0;    // no index in FA
        ev.offset         = bd.offset;
        ev.inserted_block = bd.block_number;

        // --- Search all lines for the block tag ---
        int hit_line = -1;
        for (int i = 0; i < (int)cache_set.lines.size(); ++i) {
            if (cache_set.lines[i].valid && cache_set.lines[i].tag == bd.block_number) {
                hit_line = i;
                break;
            }
        }

        if (hit_line >= 0) {
            // CACHE HIT
            ev.hit        = true;
            ev.event_type = "HIT";
            ++stats.hits;
            if (cfg.replacement == ReplacementPolicy::LRU)
                cache_set.lru_time[hit_line] = tick;
            // FIFO: hit does NOT change insertion order
        } else {
            // CACHE MISS
            ev.hit = false;
            ++stats.misses;

            // Find an empty slot
            int empty_slot = -1;
            for (int i = 0; i < (int)cache_set.lines.size(); ++i) {
                if (!cache_set.lines[i].valid) { empty_slot = i; break; }
            }

            if (empty_slot >= 0) {
                ev.replacement = false;
                ev.event_type  = "MISS";
                cache_set.lines[empty_slot].valid = true;
                cache_set.lines[empty_slot].tag   = bd.block_number;
                cache_set.lines[empty_slot].block = bd.block_number;
                if (cfg.replacement == ReplacementPolicy::LRU)
                    cache_set.lru_time[empty_slot] = tick;
                // For FIFO, track insertion order
                cache_set.fifo_order.push_back(empty_slot);
            } else {
                // Need to evict
                ev.replacement = true;
                ev.event_type  = "MISS_REPLACE";

                int victim = -1;
                if (cfg.replacement == ReplacementPolicy::FIFO) {
                    victim = cache_set.fifo_order.front();
                    cache_set.fifo_order.pop_front();
                } else {
                    // LRU
                    uint64_t min_t = std::numeric_limits<uint64_t>::max();
                    for (int i = 0; i < (int)cache_set.lines.size(); ++i) {
                        if (cache_set.lines[i].valid && cache_set.lru_time[i] < min_t) {
                            min_t  = cache_set.lru_time[i];
                            victim = i;
                        }
                    }
                }
                ev.victim_line   = victim;
                ev.evicted_block = cache_set.lines[victim].block;

                cache_set.lines[victim].valid = true;
                cache_set.lines[victim].tag   = bd.block_number;
                cache_set.lines[victim].block = bd.block_number;
                if (cfg.replacement == ReplacementPolicy::LRU)
                    cache_set.lru_time[victim] = tick;
                else
                    cache_set.fifo_order.push_back(victim);
            }
        }

        // Build snapshot: one set, all lines
        ev.cache_snapshot.resize(1);
        ev.cache_snapshot[0] = cache_set.lines;
        ev.total_accesses = stats.total_accesses;
        ev.hits           = stats.hits;
        ev.misses         = stats.misses;
        return ev;
    }
};
