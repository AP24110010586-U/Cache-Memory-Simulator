// ============================================================
// DirectMapping.cpp
// Direct-Mapped Cache implementation
// ============================================================
#include "cache.h"
#include <vector>

class DirectMappedCache {
public:
    CacheConfig             cfg;
    std::vector<CacheLine>  lines;
    Stats                   stats;
    uint64_t                tick = 0;

    explicit DirectMappedCache(const CacheConfig& c) : cfg(c) {
        lines.resize(cfg.num_cache_lines);
    }

    SimEvent access(uint32_t address) {
        ++tick;
        ++stats.total_accesses;

        auto bd = breakdown_address(address, cfg);

        SimEvent ev;
        ev.address        = address;
        ev.block_number   = bd.block_number;
        ev.tag            = bd.tag;
        ev.index          = bd.index;
        ev.offset         = bd.offset;
        ev.inserted_block = bd.block_number;

        CacheLine& line = lines[bd.index];

        if (line.valid && line.tag == bd.tag) {
            // ---- CACHE HIT ----
            ev.hit         = true;
            ev.replacement = false;
            ev.event_type  = "HIT";
            ++stats.hits;
        } else {
            // ---- CACHE MISS ----
            ev.hit = false;
            ++stats.misses;

            if (line.valid) {
                // Another block was here — natural direct-map replacement
                ev.replacement = true;
                ev.victim_line = (int)bd.index;
                ev.evicted_block = line.block;
                ev.event_type = "MISS_REPLACE";
            } else {
                ev.replacement = false;
                ev.event_type  = "MISS";
            }
            line.valid = true;
            line.tag   = bd.tag;
            line.block = bd.block_number;
        }

        // Snapshot
        ev.cache_snapshot.resize(1);
        ev.cache_snapshot[0] = lines;

        ev.total_accesses = stats.total_accesses;
        ev.hits           = stats.hits;
        ev.misses         = stats.misses;
        return ev;
    }
};
