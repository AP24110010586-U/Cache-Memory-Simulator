/**
 * engine.js – Cache Memory Simulation Engine (Pure JavaScript)
 * Mirrors cache_engine.py and the C++ engine logic exactly.
 * Enables 100% client-side execution for GitHub Pages and offline web use.
 */

const CacheEngineJS = {
  DIRECT: "direct",
  FULLY_ASSOCIATIVE: "fully_associative",
  SET_ASSOCIATIVE: "set_associative",
  FIFO: "fifo",
  LRU: "lru",

  isPowerOfTwo(n) {
    return n > 0 && (n & (n - 1)) === 0;
  },

  validateConfig(cfg) {
    const mm = Number(cfg.main_memory_size);
    const cs = Number(cfg.cache_size);
    const bs = Number(cfg.block_size);
    const assoc = Number(cfg.associativity);

    if (mm <= 0) return "Main memory size must be positive.";
    if (cs <= 0) return "Cache size must be positive.";
    if (bs <= 0) return "Block size must be positive.";
    if (!this.isPowerOfTwo(bs)) return "Block size must be a power of two.";
    if (!this.isPowerOfTwo(mm)) return "Main memory size must be a power of two.";
    if (!this.isPowerOfTwo(cs)) return "Cache size must be a power of two.";
    if (cs < bs) return "Cache size must be greater than or equal to block size.";
    if (cs % bs !== 0) return "Cache size must be divisible by block size.";
    if (assoc <= 0) return "Associativity must be a positive integer.";

    const num_lines = Math.floor(cs / bs);
    if (num_lines % assoc !== 0) return "Number of cache lines must be divisible by associativity.";
    if (assoc > num_lines) return "Associativity cannot exceed the number of cache lines.";
    if (mm < cs) return "Main memory size must be >= cache size.";
    return null;
  },

  computeDerived(cfg) {
    const main_memory_size = Number(cfg.main_memory_size);
    const cache_size = Number(cfg.cache_size);
    const block_size = Number(cfg.block_size);
    const mapping = cfg.mapping || this.DIRECT;
    const associativity = Number(cfg.associativity) || 1;
    const replacement = cfg.replacement || this.LRU;

    const num_blocks = Math.floor(main_memory_size / block_size);
    const num_cache_lines = Math.floor(cache_size / block_size);
    const offset_bits = Math.round(Math.log2(block_size));
    let num_sets = 0;
    let index_bits = 0;

    if (mapping === this.DIRECT) {
      num_sets = num_cache_lines;
      index_bits = Math.round(Math.log2(num_cache_lines));
    } else if (mapping === this.FULLY_ASSOCIATIVE) {
      num_sets = 1;
      index_bits = 0;
    } else {
      num_sets = Math.floor(num_cache_lines / associativity);
      index_bits = num_sets > 1 ? Math.round(Math.log2(num_sets)) : 0;
    }
    const tag_bits = Math.max(0, 32 - index_bits - offset_bits);

    return {
      main_memory_size,
      cache_size,
      block_size,
      mapping,
      associativity,
      replacement,
      num_blocks,
      num_cache_lines,
      num_sets,
      offset_bits,
      index_bits,
      tag_bits,
    };
  },

  breakdownAddress(address, derived) {
    const block_number = Math.floor(address / derived.block_size);
    const offset = address % derived.block_size;
    let index = 0;
    let tag = 0;
    let has_index = true;

    if (derived.mapping === this.DIRECT) {
      index = block_number % derived.num_cache_lines;
      tag = Math.floor(block_number / derived.num_cache_lines);
      has_index = true;
    } else if (derived.mapping === this.FULLY_ASSOCIATIVE) {
      index = 0;
      tag = block_number;
      has_index = false;
    } else {
      index = block_number % derived.num_sets;
      tag = Math.floor(block_number / derived.num_sets);
      has_index = true;
    }

    return {
      address,
      block_number,
      tag,
      index,
      offset,
      has_index,
      offset_bits: derived.offset_bits,
      index_bits: derived.index_bits,
      tag_bits: derived.tag_bits,
    };
  },

  runSimulation(configDict, addresses) {
    const err = this.validateConfig(configDict);
    if (err) return { error: err };
    const cfg = this.computeDerived(configDict);

    const events = [];
    let hits = 0;
    let misses = 0;
    let total_accesses = 0;
    let tick = 0;

    if (cfg.mapping === this.DIRECT) {
      const lines = Array.from({ length: cfg.num_cache_lines }, () => ({ valid: false, tag: 0, block: 0 }));
      for (const addr of addresses) {
        total_accesses++;
        const bd = this.breakdownAddress(addr, cfg);
        const line = lines[bd.index];
        const ev = {
          address: addr,
          block_number: bd.block_number,
          tag: bd.tag,
          index: bd.index,
          offset: bd.offset,
          hit: false,
          replacement: false,
          victim_line: -1,
          evicted_block: 0,
          inserted_block: bd.block_number,
          event_type: "",
          cache_snapshot: [],
          total_accesses,
          hits: 0,
          misses: 0,
        };

        if (line.valid && line.tag === bd.tag) {
          ev.hit = true;
          ev.event_type = "HIT";
          hits++;
        } else {
          misses++;
          if (line.valid) {
            ev.replacement = true;
            ev.victim_line = bd.index;
            ev.evicted_block = line.block;
            ev.event_type = "MISS_REPLACE";
          } else {
            ev.replacement = false;
            ev.event_type = "MISS";
          }
          line.valid = true;
          line.tag = bd.tag;
          line.block = bd.block_number;
        }

        ev.cache_snapshot = [lines.map(l => ({ ...l }))];
        ev.hits = hits;
        ev.misses = misses;
        events.push(ev);
      }
    } else if (cfg.mapping === this.FULLY_ASSOCIATIVE) {
      const lines = Array.from({ length: cfg.num_cache_lines }, () => ({ valid: false, tag: 0, block: 0 }));
      const fifo_order = [];
      const lru_time = new Array(cfg.num_cache_lines).fill(0);

      for (const addr of addresses) {
        tick++;
        total_accesses++;
        const bd = this.breakdownAddress(addr, cfg);
        const ev = {
          address: addr,
          block_number: bd.block_number,
          tag: bd.tag,
          index: 0,
          offset: bd.offset,
          hit: false,
          replacement: false,
          victim_line: -1,
          evicted_block: 0,
          inserted_block: bd.block_number,
          event_type: "",
          cache_snapshot: [],
          total_accesses,
          hits: 0,
          misses: 0,
        };

        const hit_line = lines.findIndex(ln => ln.valid && ln.tag === bd.block_number);
        if (hit_line >= 0) {
          ev.hit = true;
          ev.event_type = "HIT";
          hits++;
          if (cfg.replacement === this.LRU) {
            lru_time[hit_line] = tick;
          }
        } else {
          misses++;
          const empty_slot = lines.findIndex(ln => !ln.valid);
          if (empty_slot >= 0) {
            ev.replacement = false;
            ev.event_type = "MISS";
            lines[empty_slot] = { valid: true, tag: bd.block_number, block: bd.block_number };
            if (cfg.replacement === this.LRU) {
              lru_time[empty_slot] = tick;
            } else {
              fifo_order.push(empty_slot);
            }
          } else {
            ev.replacement = true;
            ev.event_type = "MISS_REPLACE";
            let victim = -1;
            if (cfg.replacement === this.FIFO) {
              victim = fifo_order.shift();
            } else {
              let minT = Infinity;
              for (let i = 0; i < lines.length; i++) {
                if (lru_time[i] < minT) {
                  minT = lru_time[i];
                  victim = i;
                }
              }
            }
            ev.victim_line = victim;
            ev.evicted_block = lines[victim].block;
            lines[victim] = { valid: true, tag: bd.block_number, block: bd.block_number };
            if (cfg.replacement === this.LRU) {
              lru_time[victim] = tick;
            } else {
              fifo_order.push(victim);
            }
          }
        }
        ev.cache_snapshot = [lines.map(l => ({ ...l }))];
        ev.hits = hits;
        ev.misses = misses;
        events.push(ev);
      }
    } else {
      // Set Associative
      const sets = Array.from({ length: cfg.num_sets }, () => ({
        lines: Array.from({ length: cfg.associativity }, () => ({ valid: false, tag: 0, block: 0 })),
        fifo_order: [],
        lru_time: new Array(cfg.associativity).fill(0),
      }));

      for (const addr of addresses) {
        tick++;
        total_accesses++;
        const bd = this.breakdownAddress(addr, cfg);
        const s = sets[bd.index];
        const ev = {
          address: addr,
          block_number: bd.block_number,
          tag: bd.tag,
          index: bd.index,
          offset: bd.offset,
          hit: false,
          replacement: false,
          victim_line: -1,
          evicted_block: 0,
          inserted_block: bd.block_number,
          event_type: "",
          cache_snapshot: [],
          total_accesses,
          hits: 0,
          misses: 0,
        };

        const hit_line = s.lines.findIndex(ln => ln.valid && ln.tag === bd.tag);
        if (hit_line >= 0) {
          ev.hit = true;
          ev.event_type = "HIT";
          hits++;
          if (cfg.replacement === this.LRU) {
            s.lru_time[hit_line] = tick;
          }
        } else {
          misses++;
          const empty_slot = s.lines.findIndex(ln => !ln.valid);
          if (empty_slot >= 0) {
            ev.replacement = false;
            ev.event_type = "MISS";
            s.lines[empty_slot] = { valid: true, tag: bd.tag, block: bd.block_number };
            if (cfg.replacement === this.LRU) {
              s.lru_time[empty_slot] = tick;
            } else {
              s.fifo_order.push(empty_slot);
            }
          } else {
            ev.replacement = true;
            ev.event_type = "MISS_REPLACE";
            let victim = -1;
            if (cfg.replacement === this.FIFO) {
              victim = s.fifo_order.shift();
            } else {
              let minT = Infinity;
              for (let i = 0; i < s.lines.length; i++) {
                if (s.lru_time[i] < minT) {
                  minT = s.lru_time[i];
                  victim = i;
                }
              }
            }
            ev.victim_line = victim;
            ev.evicted_block = s.lines[victim].block;
            s.lines[victim] = { valid: true, tag: bd.tag, block: bd.block_number };
            if (cfg.replacement === this.LRU) {
              s.lru_time[victim] = tick;
            } else {
              s.fifo_order.push(victim);
            }
          }
        }

        ev.cache_snapshot = sets.map(st => st.lines.map(l => ({ ...l })));
        ev.hits = hits;
        ev.misses = misses;
        events.push(ev);
      }
    }

    const hit_ratio = total_accesses ? hits / total_accesses : 0;
    const miss_ratio = total_accesses ? misses / total_accesses : 0;

    return {
      events,
      statistics: {
        total_accesses,
        hits,
        misses,
        hit_ratio: Number(hit_ratio.toFixed(6)),
        miss_ratio: Number(miss_ratio.toFixed(6)),
        hit_percentage: Number((hit_ratio * 100).toFixed(2)),
        miss_percentage: Number((miss_ratio * 100).toFixed(2)),
      },
      config: cfg,
    };
  },

  samples: [
    {
      id: 1,
      name: "Demo 1 – Direct Mapping",
      description: "Classic direct mapping with 256B main memory, 64B cache, 4B blocks.",
      config: {
        main_memory_size: 256,
        cache_size: 64,
        block_size: 4,
        mapping: "direct",
        associativity: 1,
        replacement: "lru",
      },
      addresses: [0, 4, 0, 64, 4, 64],
      expected: {
        total_accesses: 6,
        hits: 3,
        misses: 3,
        hit_percentage: 50.0,
        miss_percentage: 50.0,
      },
    },
    {
      id: 2,
      name: "Demo 2 – Fully Associative (FIFO)",
      description: "Small 4-line cache with FIFO replacement.",
      config: {
        main_memory_size: 256,
        cache_size: 16,
        block_size: 4,
        mapping: "fully_associative",
        associativity: 4,
        replacement: "fifo",
      },
      addresses: [0, 4, 8, 12, 0, 16, 4],
    },
    {
      id: 3,
      name: "Demo 3 – Fully Associative (LRU)",
      description: "Same config as Demo 2 but with LRU to show different eviction.",
      config: {
        main_memory_size: 256,
        cache_size: 16,
        block_size: 4,
        mapping: "fully_associative",
        associativity: 4,
        replacement: "lru",
      },
      addresses: [0, 4, 8, 12, 0, 16, 4],
    },
    {
      id: 4,
      name: "Demo 4 – 2-Way Set Associative (LRU)",
      description: "2-way set associative with LRU replacement.",
      config: {
        main_memory_size: 256,
        cache_size: 32,
        block_size: 4,
        mapping: "set_associative",
        associativity: 2,
        replacement: "lru",
      },
      addresses: [0, 4, 8, 0, 12, 4],
    },
    {
      id: 5,
      name: "Demo 5 – LRU vs FIFO Difference",
      description: "Sequence to show that FIFO evicts oldest insertion, LRU evicts least recently used.",
      config: {
        main_memory_size: 256,
        cache_size: 16,
        block_size: 4,
        mapping: "fully_associative",
        associativity: 4,
        replacement: "lru",
      },
      addresses: [0, 4, 8, 12, 0, 4, 8, 16],
    },
  ],
};

window.CacheEngineJS = CacheEngineJS;
