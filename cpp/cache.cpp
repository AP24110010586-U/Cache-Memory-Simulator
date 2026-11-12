// ============================================================
// cache.cpp  –  Validation and address-breakdown helpers
// ============================================================
#include "cache.h"
#include <cmath>
#include <sstream>
#include <stdexcept>

bool is_power_of_two(uint64_t n) {
    return n > 0 && (n & (n - 1)) == 0;
}

int log2_int(uint64_t n) {
    int r = 0;
    while (n > 1) { n >>= 1; ++r; }
    return r;
}

bool validate_config(const CacheConfig& cfg, std::string& error) {
    if (cfg.main_memory_size == 0) { error = "Main memory size must be positive."; return false; }
    if (cfg.cache_size == 0)       { error = "Cache size must be positive."; return false; }
    if (cfg.block_size == 0)       { error = "Block size must be positive."; return false; }
    if (!is_power_of_two(cfg.block_size))        { error = "Block size must be a power of two."; return false; }
    if (!is_power_of_two(cfg.main_memory_size))  { error = "Main memory size must be a power of two."; return false; }
    if (!is_power_of_two(cfg.cache_size))        { error = "Cache size must be a power of two."; return false; }
    if (cfg.cache_size < cfg.block_size)         { error = "Cache size must be >= block size."; return false; }
    if (cfg.cache_size % cfg.block_size != 0)    { error = "Cache size must be divisible by block size."; return false; }
    if (cfg.associativity <= 0)                  { error = "Associativity must be a positive integer."; return false; }

    uint32_t num_lines = (uint32_t)(cfg.cache_size / cfg.block_size);
    if (num_lines % cfg.associativity != 0) {
        error = "Number of cache lines must be divisible by associativity.";
        return false;
    }
    if ((uint32_t)cfg.associativity > num_lines) {
        error = "Associativity cannot exceed the number of cache lines.";
        return false;
    }
    if (cfg.main_memory_size < cfg.cache_size) {
        error = "Main memory must be >= cache size.";
        return false;
    }
    return true;
}

void compute_derived(CacheConfig& cfg) {
    cfg.num_blocks      = (uint32_t)(cfg.main_memory_size / cfg.block_size);
    cfg.num_cache_lines = (uint32_t)(cfg.cache_size / cfg.block_size);
    cfg.offset_bits     = log2_int(cfg.block_size);

    if (cfg.mapping == MappingType::DIRECT) {
        cfg.num_sets   = cfg.num_cache_lines;
        cfg.index_bits = log2_int(cfg.num_cache_lines);
    } else if (cfg.mapping == MappingType::FULLY_ASSOCIATIVE) {
        cfg.num_sets   = 1;
        cfg.index_bits = 0;
    } else { // SET_ASSOCIATIVE
        cfg.num_sets   = cfg.num_cache_lines / cfg.associativity;
        cfg.index_bits = log2_int(cfg.num_sets);
    }
    cfg.tag_bits = 32 - cfg.index_bits - cfg.offset_bits;
    if (cfg.tag_bits < 0) cfg.tag_bits = 0;
}

AddressBreakdown breakdown_address(uint32_t address, const CacheConfig& cfg) {
    AddressBreakdown bd;
    bd.address       = address;
    bd.block_number  = address / cfg.block_size;
    bd.offset        = address % cfg.block_size;
    bd.offset_bits   = cfg.offset_bits;
    bd.index_bits    = cfg.index_bits;
    bd.tag_bits      = cfg.tag_bits;
    bd.has_index     = (cfg.mapping != MappingType::FULLY_ASSOCIATIVE);

    if (cfg.mapping == MappingType::DIRECT) {
        bd.index = bd.block_number % cfg.num_cache_lines;
        bd.tag   = bd.block_number / cfg.num_cache_lines;
    } else if (cfg.mapping == MappingType::FULLY_ASSOCIATIVE) {
        bd.index = 0;
        bd.tag   = bd.block_number;
    } else {
        bd.index = bd.block_number % cfg.num_sets;
        bd.tag   = bd.block_number / cfg.num_sets;
    }
    return bd;
}
