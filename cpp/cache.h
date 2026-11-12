// ============================================================
// cache.h  –  Cache Memory Simulator
// Core data structures and declarations
// COA B.Tech Project
// ============================================================
#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <deque>
#include <unordered_map>
#include <limits>

// ---- Mapping Techniques ------------------------------------
enum class MappingType { DIRECT, FULLY_ASSOCIATIVE, SET_ASSOCIATIVE };

// ---- Replacement Policies ----------------------------------
enum class ReplacementPolicy { FIFO, LRU };

// ---- A single cache line -----------------------------------
struct CacheLine {
    bool     valid   = false;
    uint32_t tag     = 0;
    uint32_t block   = 0;   // which memory block is stored
};

// ---- One cache set (used in Fully-Associative and N-Way SA)
struct CacheSet {
    std::vector<CacheLine> lines;
    std::deque<int>        fifo_order;  // indices in insertion order
    std::vector<uint64_t>  lru_time;    // last-access timestamps

    explicit CacheSet(int ways) : lines(ways), lru_time(ways, 0) {}
};

// ---- Configuration -----------------------------------------
struct CacheConfig {
    uint64_t        main_memory_size  = 256;
    uint64_t        cache_size        = 64;
    uint32_t        block_size        = 4;
    MappingType     mapping           = MappingType::DIRECT;
    int             associativity     = 1;
    ReplacementPolicy replacement     = ReplacementPolicy::LRU;

    // Derived (computed after validation)
    uint32_t num_blocks      = 0;  // main memory blocks
    uint32_t num_cache_lines = 0;  // total cache lines
    uint32_t num_sets        = 0;  // sets (SA) or 1 (FA)
    int      offset_bits     = 0;
    int      index_bits      = 0;
    int      tag_bits        = 0;
};

// ---- One simulation step result ----------------------------
struct SimEvent {
    uint32_t    address        = 0;
    uint32_t    block_number   = 0;
    uint32_t    tag            = 0;
    uint32_t    index          = 0;   // cache line (DM) or set (SA)
    uint32_t    offset         = 0;
    bool        hit            = false;
    bool        replacement    = false;
    int         victim_line    = -1;  // which line in set was replaced
    uint32_t    evicted_block  = 0;
    uint32_t    inserted_block = 0;
    std::string event_type;           // "HIT" / "MISS" / "MISS_REPLACE"
    // snapshot of entire cache after this access
    std::vector<std::vector<CacheLine>> cache_snapshot;
    // stats at this moment
    uint64_t total_accesses = 0;
    uint64_t hits           = 0;
    uint64_t misses         = 0;
};

// ---- Statistics --------------------------------------------
struct Stats {
    uint64_t total_accesses = 0;
    uint64_t hits           = 0;
    uint64_t misses         = 0;

    double hit_ratio()  const { return total_accesses ? (double)hits   / total_accesses : 0.0; }
    double miss_ratio() const { return total_accesses ? (double)misses / total_accesses : 0.0; }
    double hit_pct()    const { return hit_ratio()  * 100.0; }
    double miss_pct()   const { return miss_ratio() * 100.0; }
};

// ---- Validation helpers ------------------------------------
bool is_power_of_two(uint64_t n);
int  log2_int(uint64_t n);
bool validate_config(const CacheConfig& cfg, std::string& error);
void compute_derived(CacheConfig& cfg);

// ---- Address breakdown -------------------------------------
struct AddressBreakdown {
    uint32_t address;
    uint32_t block_number;
    uint32_t tag;
    uint32_t index;    // 0 for fully associative
    uint32_t offset;
    int      tag_bits;
    int      index_bits;
    int      offset_bits;
    bool     has_index;
};

AddressBreakdown breakdown_address(uint32_t address, const CacheConfig& cfg);
