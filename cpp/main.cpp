// ============================================================
// main.cpp  –  Cache Memory Simulator C++ Engine
// Accepts JSON on stdin, writes JSON results on stdout.
// Protocol: single JSON object in, array of SimEvent JSON out.
// ============================================================
#include "cache.h"
#include "cache.cpp"
#include "ReplacementPolicy.cpp"
#include "DirectMapping.cpp"
#include "FullyAssociative.cpp"
#include "SetAssociative.cpp"

#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <stdexcept>

// ---- Minimal JSON serialiser (no external dependencies) ----

static std::string json_bool(bool b) { return b ? "true" : "false"; }
static std::string json_str(const std::string& s) { return "\"" + s + "\""; }

static std::string json_cache_line(const CacheLine& l) {
    std::ostringstream o;
    o << "{\"valid\":" << json_bool(l.valid)
      << ",\"tag\":"   << l.tag
      << ",\"block\":" << l.block << "}";
    return o.str();
}

static std::string json_event(const SimEvent& ev) {
    std::ostringstream o;
    o << "{"
      << "\"address\":"        << ev.address        << ","
      << "\"block_number\":"   << ev.block_number   << ","
      << "\"tag\":"            << ev.tag            << ","
      << "\"index\":"          << ev.index          << ","
      << "\"offset\":"         << ev.offset         << ","
      << "\"hit\":"            << json_bool(ev.hit) << ","
      << "\"replacement\":"    << json_bool(ev.replacement) << ","
      << "\"victim_line\":"    << ev.victim_line    << ","
      << "\"evicted_block\":"  << ev.evicted_block  << ","
      << "\"inserted_block\":" << ev.inserted_block << ","
      << "\"event_type\":"     << json_str(ev.event_type) << ","
      << "\"total_accesses\":" << ev.total_accesses << ","
      << "\"hits\":"           << ev.hits           << ","
      << "\"misses\":"         << ev.misses         << ","
      << "\"cache_snapshot\":[";

    for (size_t si = 0; si < ev.cache_snapshot.size(); ++si) {
        if (si) o << ",";
        o << "[";
        for (size_t li = 0; li < ev.cache_snapshot[si].size(); ++li) {
            if (li) o << ",";
            o << json_cache_line(ev.cache_snapshot[si][li]);
        }
        o << "]";
    }
    o << "]}";
    return o.str();
}

// ---- Tiny JSON parser for input ----
// We only parse a flat object with known keys.

static std::string find_value(const std::string& json, const std::string& key) {
    std::string search = "\"" + key + "\"";
    size_t pos = json.find(search);
    if (pos == std::string::npos) return "";
    pos = json.find(':', pos + search.size());
    if (pos == std::string::npos) return "";
    ++pos;
    while (pos < json.size() && (json[pos] == ' ' || json[pos] == '\t')) ++pos;
    if (pos >= json.size()) return "";
    if (json[pos] == '"') {
        size_t end = json.find('"', pos + 1);
        return json.substr(pos + 1, end - pos - 1);
    }
    // number or array start
    size_t end = json.find_first_of(",}]", pos);
    std::string val = json.substr(pos, end - pos);
    // trim
    while (!val.empty() && (val.back() == ' ' || val.back() == '\n')) val.pop_back();
    return val;
}

static std::vector<uint32_t> parse_addresses(const std::string& json) {
    std::vector<uint32_t> addrs;
    size_t arr_start = json.find("\"addresses\"");
    if (arr_start == std::string::npos) return addrs;
    size_t bracket = json.find('[', arr_start);
    if (bracket == std::string::npos) return addrs;
    size_t bracket_end = json.find(']', bracket);
    std::string arr = json.substr(bracket + 1, bracket_end - bracket - 1);
    std::istringstream ss(arr);
    std::string token;
    while (std::getline(ss, token, ',')) {
        // trim
        while (!token.empty() && (token.front() == ' ' || token.front() == '\n')) token.erase(token.begin());
        while (!token.empty() && (token.back()  == ' ' || token.back()  == '\n')) token.pop_back();
        if (!token.empty())
            addrs.push_back((uint32_t)std::stoul(token));
    }
    return addrs;
}

int main() {
    std::string line, input;
    while (std::getline(std::cin, line)) input += line + "\n";

    CacheConfig cfg;
    std::string err;

    // Parse config
    std::string mm_str   = find_value(input, "main_memory_size");
    std::string cs_str   = find_value(input, "cache_size");
    std::string bs_str   = find_value(input, "block_size");
    std::string map_str  = find_value(input, "mapping");
    std::string assoc_str= find_value(input, "associativity");
    std::string rep_str  = find_value(input, "replacement");

    try {
        cfg.main_memory_size = mm_str.empty()  ? 256 : std::stoull(mm_str);
        cfg.cache_size       = cs_str.empty()  ? 64  : std::stoull(cs_str);
        cfg.block_size       = bs_str.empty()  ? 4   : (uint32_t)std::stoull(bs_str);
        cfg.associativity    = assoc_str.empty()? 1  : std::stoi(assoc_str);
    } catch (...) {
        std::cout << "{\"error\":\"Invalid numeric parameter.\"}" << std::endl;
        return 1;
    }

    if (map_str == "direct")            cfg.mapping = MappingType::DIRECT;
    else if (map_str == "fully_associative") cfg.mapping = MappingType::FULLY_ASSOCIATIVE;
    else                                cfg.mapping = MappingType::SET_ASSOCIATIVE;

    if (rep_str == "fifo") cfg.replacement = ReplacementPolicy::FIFO;
    else                   cfg.replacement = ReplacementPolicy::LRU;

    if (!validate_config(cfg, err)) {
        std::cout << "{\"error\":\"" << err << "\"}" << std::endl;
        return 1;
    }
    compute_derived(cfg);

    auto addresses = parse_addresses(input);

    // Run simulation
    std::vector<SimEvent> events;

    if (cfg.mapping == MappingType::DIRECT) {
        DirectMappedCache sim(cfg);
        for (auto addr : addresses) events.push_back(sim.access(addr));
    } else if (cfg.mapping == MappingType::FULLY_ASSOCIATIVE) {
        FullyAssociativeCache sim(cfg);
        for (auto addr : addresses) events.push_back(sim.access(addr));
    } else {
        SetAssociativeCache sim(cfg);
        for (auto addr : addresses) events.push_back(sim.access(addr));
    }

    // Output JSON array of events
    std::cout << "[";
    for (size_t i = 0; i < events.size(); ++i) {
        if (i) std::cout << ",";
        std::cout << json_event(events[i]);
    }
    std::cout << "]" << std::endl;
    return 0;
}
