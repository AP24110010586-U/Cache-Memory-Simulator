// ============================================================
// SetAssociative.cpp
// N-Way Set Associative Cache with FIFO / LRU replacement
// ============================================================
#include "cache.h"
#include <vector>
#include <algorithm>
#include <limits>

class SetAssociativeCache {
public:
    CacheConfig           cfg;
    std::vector<CacheSet> sets;
    Stats                 stats;
    uint64_t              tick = 0;

    explicit SetAssociativeCache(const CacheConfig& c)
        : cfg(c) {
        for (uint32_t i = 0; i < cfg.num_sets; ++i)
            sets.emplace_back(cfg.associativity);
    }

    SimEvent access(uint32_t address) {
        ++tick;
        ++stats.total_accesses;

        auto bd = breakdown_address(address, cfg);

        SimEvent ev;
        ev.address        = address;
        ev.block_number   = bd.block_number;
        ev.tag            = bd.tag;
        ev.index          = bd.index;   // set index
        ev.offset         = bd.offset;
        ev.inserted_block = bd.block_number;

        CacheSet& s = sets[bd.index];

        // --- Search the target set ---
        int hit_line = -1;
        for (int i = 0; i < cfg.associativity; ++i) {
            if (s.lines[i].valid && s.lines[i].tag == bd.tag) {
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
                s.lru_time[hit_line] = tick;
            // FIFO: hit does NOT change insertion order
        } else {
            // CACHE MISS
            ev.hit = false;
            ++stats.misses;

            // Look for an empty line in this set
            int empty_slot = -1;
            for (int i = 0; i < cfg.associativity; ++i) {
                if (!s.lines[i].valid) { empty_slot = i; break; }
            }

            if (empty_slot >= 0) {
                ev.replacement = false;
                ev.event_type  = "MISS";
                s.lines[empty_slot].valid = true;
                s.lines[empty_slot].tag   = bd.tag;
                s.lines[empty_slot].block = bd.block_number;
                if (cfg.replacement == ReplacementPolicy::LRU)
                    s.lru_time[empty_slot] = tick;
                else
                    s.fifo_order.push_back(empty_slot);
            } else {
                // Eviction required
                ev.replacement = true;
                ev.event_type  = "MISS_REPLACE";

                int victim = -1;
                if (cfg.replacement == ReplacementPolicy::FIFO) {
                    victim = s.fifo_order.front();
                    s.fifo_order.pop_front();
                } else {
                    uint64_t min_t = std::numeric_limits<uint64_t>::max();
                    for (int i = 0; i < cfg.associativity; ++i) {
                        if (s.lines[i].valid && s.lru_time[i] < min_t) {
                            min_t  = s.lru_time[i];
                            victim = i;
                        }
                    }
                }
                ev.victim_line   = victim;
                ev.evicted_block = s.lines[victim].block;

                s.lines[victim].valid = true;
                s.lines[victim].tag   = bd.tag;
                s.lines[victim].block = bd.block_number;
                if (cfg.replacement == ReplacementPolicy::LRU)
                    s.lru_time[victim] = tick;
                else
                    s.fifo_order.push_back(victim);
            }
        }

        // Build snapshot
        ev.cache_snapshot.resize(cfg.num_sets);
        for (uint32_t i = 0; i < cfg.num_sets; ++i)
            ev.cache_snapshot[i] = sets[i].lines;

        ev.total_accesses = stats.total_accesses;
        ev.hits           = stats.hits;
        ev.misses         = stats.misses;
        return ev;
    }
};
