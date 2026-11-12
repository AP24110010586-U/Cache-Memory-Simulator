// ============================================================
// AddressCalculation.cpp
// Memory address decomposition for all mapping techniques
// ============================================================
// This module is used by the C++ engine's main.cpp.
// The logic mirrors cache.cpp's breakdown_address().
// Kept as a separate file for modularity and grading.
// ============================================================
#include "cache.h"

// Decompose a 32-bit address into TAG / INDEX / OFFSET fields
// given a fully computed CacheConfig.
AddressBreakdown decompose(uint32_t address, const CacheConfig& cfg) {
    return breakdown_address(address, cfg);
}

// Utility: print a human-readable breakdown
#include <iostream>
void print_breakdown(const AddressBreakdown& bd) {
    std::cout << "Address     : " << bd.address       << "\n"
              << "Block Number: " << bd.block_number   << "\n"
              << "Tag         : " << bd.tag            << "\n";
    if (bd.has_index)
        std::cout << "Index       : " << bd.index     << "\n";
    std::cout << "Offset      : " << bd.offset        << "\n"
              << "Bit widths  : TAG=" << bd.tag_bits
              << " IDX=" << bd.index_bits
              << " OFF=" << bd.offset_bits << "\n";
}
