// ============================================================
// ReplacementPolicy.cpp
// FIFO and LRU replacement algorithms
// ============================================================
#include "cache.h"
#include <algorithm>
#include <limits>

// ---- FIFO replacement inside a CacheSet --------------------
// Returns the index of the line to evict.
int fifo_pick_victim(const CacheSet& set) {
    // fifo_order holds indices of valid lines in insertion order.
    // The front of the deque is the oldest.
    if (!set.fifo_order.empty())
        return set.fifo_order.front();
    return 0; // fallback (should not happen)
}

void fifo_on_insert(CacheSet& set, int line_idx) {
    // Remove the line from fifo_order if already tracked (re-use on eviction)
    auto it = std::find(set.fifo_order.begin(), set.fifo_order.end(), line_idx);
    if (it != set.fifo_order.end())
        set.fifo_order.erase(it);
    set.fifo_order.push_back(line_idx);
}

// IMPORTANT: A FIFO hit does NOT update insertion order.
// Only called when a NEW block is loaded.

// ---- LRU replacement inside a CacheSet --------------------
int lru_pick_victim(const CacheSet& set) {
    // Find the line with the smallest (oldest) lru_time among valid lines.
    uint64_t min_time = std::numeric_limits<uint64_t>::max();
    int victim = 0;
    for (int i = 0; i < (int)set.lines.size(); ++i) {
        if (set.lines[i].valid && set.lru_time[i] < min_time) {
            min_time = set.lru_time[i];
            victim   = i;
        }
    }
    return victim;
}

void lru_on_access(CacheSet& set, int line_idx, uint64_t timestamp) {
    set.lru_time[line_idx] = timestamp;
}
