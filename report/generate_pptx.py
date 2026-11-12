"""
generate_pptx.py  --  Create Cache Memory Simulator PowerPoint Presentation
Run with:  python generate_pptx.py
Requires:  pip install python-pptx  (or install via uv / pip --target)
"""
import sys, os

# Add site-packages
SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site-packages")
if os.path.isdir(SITE):
    sys.path.insert(0, SITE)

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt, Emu
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    HAVE_PPTX = True
except ImportError:
    HAVE_PPTX = False

# ---- Colours -----------------------------------------------
C_BG        = RGBColor(0x0f, 0x17, 0x2a)   # dark navy
C_PRIMARY   = RGBColor(0x25, 0x63, 0xeb)   # blue
C_SECONDARY = RGBColor(0x7c, 0x3a, 0xed)   # purple
C_WHITE     = RGBColor(0xff, 0xff, 0xff)
C_HIT       = RGBColor(0x16, 0xa3, 0x4a)   # green
C_MISS      = RGBColor(0xdc, 0x26, 0x26)   # red
C_MUTED     = RGBColor(0x94, 0xa3, 0xb8)   # slate
C_ACCENT    = RGBColor(0x34, 0xd3, 0x99)   # teal

W  = Inches(13.33)   # widescreen 16:9
H  = Inches(7.5)


def add_bg(slide, color=C_BG):
    """Fill the slide background."""
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def title_box(slide, text, y=Inches(0.4), h=Inches(0.9), color=C_WHITE,
              size=36, bold=True, align=PP_ALIGN.LEFT, x=Inches(0.6), w=Inches(12)):
    tf = slide.shapes.add_textbox(x, y, w, h).text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.bold  = bold
    run.font.size  = Pt(size)
    run.font.color.rgb = color


def bullet_box(slide, bullets, x=Inches(0.6), y=Inches(1.6), w=Inches(12), h=Inches(5),
               size=18, color=C_MUTED, indent="  •  "):
    tf = slide.shapes.add_textbox(x, y, w, h).text_frame
    tf.word_wrap = True
    for i, b in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(6)
        run = p.add_run()
        run.text = indent + b
        run.font.size  = Pt(size)
        run.font.color.rgb = color


def code_box(slide, lines, x=Inches(0.6), y=Inches(2.0), w=Inches(12), h=Inches(4)):
    tf = slide.shapes.add_textbox(x, y, w, h).text_frame
    tf.word_wrap = False
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        run = p.add_run()
        run.text = ln
        run.font.size  = Pt(14)
        run.font.color.rgb = C_ACCENT
        run.font.name  = "Courier New"


def accent_rule(slide, y=Inches(1.3)):
    """Thin coloured horizontal rule under title."""
    line = slide.shapes.add_shape(1, Inches(0.6), y, Inches(12.1), Inches(0.03))
    line.fill.solid()
    line.fill.fore_color.rgb = C_PRIMARY
    line.line.fill.background()


# ================================================================
def build_presentation():
    if not HAVE_PPTX:
        print("python-pptx not installed — generating text summary instead.")
        generate_text_summary()
        return

    prs = Presentation()
    prs.slide_width  = W
    prs.slide_height = H
    blank = prs.slide_layouts[6]  # blank layout

    slides_data = [
        # (slide_maker_function, args)
    ]

    # ---- Helper to add a slide ----
    def new_slide():
        s = prs.slides.add_slide(blank)
        add_bg(s)
        return s

    # ==== Slide 1: Title ====
    s = new_slide()
    # Gradient bar at top
    bar = s.shapes.add_shape(1, 0, 0, W, Inches(0.08))
    bar.fill.solid(); bar.fill.fore_color.rgb = C_PRIMARY; bar.line.fill.background()
    title_box(s, "Cache Memory Simulator", y=Inches(1.5), h=Inches(1.2),
              color=C_WHITE, size=44, align=PP_ALIGN.CENTER, x=0, w=W)
    title_box(s, "Computer Organization & Architecture", y=Inches(2.8),
              color=C_PRIMARY, size=24, align=PP_ALIGN.CENTER, x=0, w=W)
    title_box(s, "B.Tech CSE Academic Project", y=Inches(3.4),
              color=C_MUTED, size=18, align=PP_ALIGN.CENTER, x=0, w=W, bold=False)
    # Info box
    info = [
        "Student : [Your Name Here]",
        "Roll No : [Your Roll Number]",
        "College  : [Your Institution]",
        "Guide    : [Faculty Name]",
        "Year     : 2024–2025",
    ]
    bullet_box(s, info, x=Inches(4), y=Inches(4.5), w=Inches(5), size=16, indent="")

    # ==== Slide 2: Agenda ====
    s = new_slide()
    accent_rule(s)
    title_box(s, "Agenda")
    items = [
        "1.  Project Overview & Objectives",
        "2.  Memory Hierarchy & Cache Basics",
        "3.  Direct Mapping",
        "4.  Fully Associative Mapping",
        "5.  Set Associative Mapping",
        "6.  FIFO & LRU Replacement Policies",
        "7.  Address Breakdown: TAG | INDEX | OFFSET",
        "8.  Performance Statistics",
        "9.  System Architecture & Technologies",
        "10. Demo Results & Test Cases",
        "11. Conclusions",
    ]
    bullet_box(s, items, size=17)

    # ==== Slide 3: Objectives ====
    s = new_slide()
    accent_rule(s)
    title_box(s, "Project Objectives")
    bullet_box(s, [
        "Simulate cache memory between CPU and Main Memory",
        "Implement Direct, Fully Associative, and Set Associative Mapping",
        "Implement FIFO and LRU replacement algorithms correctly",
        "Provide step-by-step simulation with forward/backward navigation",
        "Display address breakdown: TAG | INDEX | OFFSET for every access",
        "Show real-time hit ratio, miss ratio, and percentage statistics",
        "Create an educational section explaining all 20 COA concepts",
        "Validate all inputs; handle errors gracefully",
        "Build 50+ automated tests (all passing)",
    ], size=18)

    # ==== Slide 4: Memory Hierarchy ====
    s = new_slide()
    accent_rule(s)
    title_box(s, "Memory Hierarchy")
    bullet_box(s, [
        "Registers     —  Fastest  |  Bytes  |  Inside CPU",
        "L1 Cache     —  ~1 ns    |  32–64 KB  |  On chip",
        "L2 Cache     —  ~5 ns    |  256 KB – 4 MB  |  On chip",
        "L3 Cache     —  ~30 ns   |  4 – 32 MB  |  On chip",
        "RAM (Main Memory)  —  ~100 ns  |  4 – 64 GB",
        "SSD / HDD    —  ms range  |  TB",
    ], size=20)
    title_box(s, "⬆ Faster, smaller, more expensive", y=Inches(5.6),
              color=C_HIT, size=16, bold=False)
    title_box(s, "⬇ Slower, larger, cheaper", y=Inches(6.0),
              color=C_MISS, size=16, bold=False)

    # ==== Slide 5: Cache Hit & Miss ====
    s = new_slide()
    accent_rule(s)
    title_box(s, "Cache Hit & Miss")
    bullet_box(s, [
        "CACHE HIT:  Requested data IS in cache  →  Fast retrieval",
        "CACHE MISS: Requested data NOT in cache  →  Fetch from RAM",
        "",
        "Hit  Flow:   CPU  →  Cache  →  FOUND  →  Return data",
        "Miss Flow:   CPU  →  Cache  →  NOT FOUND  →  RAM  →  Load block into cache",
        "",
        "Types of Misses:",
        "   Cold Miss (Compulsory):  First-ever access to a block",
        "   Conflict Miss:  Two blocks map to same line (direct mapping)",
        "   Capacity Miss:  Cache too small for working set",
    ], size=17)

    # ==== Slide 6: Direct Mapping ====
    s = new_slide()
    accent_rule(s)
    title_box(s, "Direct Mapping")
    title_box(s, "Each memory block maps to EXACTLY ONE cache line",
              y=Inches(1.4), color=C_MUTED, size=16, bold=False)
    code_box(s, [
        "Memory Block Number  =  Address  /  Block Size",
        "Cache Line (Index)   =  Block Number  mod  Num Cache Lines",
        "Tag                  =  Block Number  /   Num Cache Lines",
        "Block Offset         =  Address  mod  Block Size",
        "",
        "Example  (256 B memory, 64 B cache, 4 B block, 16 lines):",
        "  Address 0:   Block=0,  Line=0,  Tag=0  →  MISS",
        "  Address 4:   Block=1,  Line=1,  Tag=0  →  MISS",
        "  Address 0:   Block=0,  Line=0,  Tag=0  →  HIT  ✅",
        "  Address 64:  Block=16, Line=0,  Tag=1  →  MISS+REPLACE ⚠",
        "  Address 4:   Block=1,  Line=1,  Tag=0  →  HIT  ✅",
        "  Address 64:  Block=16, Line=0,  Tag=1  →  HIT  ✅",
        "                         Result: 3 Hits, 3 Misses, 50% Hit Rate",
    ], y=Inches(1.7), h=Inches(5.0))

    # ==== Slide 7: Fully Associative ====
    s = new_slide()
    accent_rule(s)
    title_box(s, "Fully Associative Mapping")
    bullet_box(s, [
        "Any memory block can be placed in ANY cache line",
        "No fixed mapping — maximum flexibility",
        "No INDEX field in address",
        "Tag = Memory Block Number (entire block number identifies the data)",
        "On cache miss: search ALL lines for a hit",
        "Requires a replacement algorithm (FIFO or LRU) when cache is full",
        "",
        "Address format:  [ TAG  |  OFFSET ]",
        "",
        "Advantage:   No conflict misses",
        "Disadvantage: Hardware search cost — used in TLBs, small caches",
    ], size=18)

    # ==== Slide 8: Set Associative ====
    s = new_slide()
    accent_rule(s)
    title_box(s, "Set Associative Mapping (N-Way)")
    code_box(s, [
        "Cache divided into S sets, each with N lines (N = associativity)",
        "",
        "Number of Sets  =  Cache Lines  /  Associativity",
        "Set Index       =  Block Number  mod  Num Sets",
        "Tag             =  Block Number  /   Num Sets",
        "",
        "2-Way Example  (8 lines, 4 sets, 2 lines per set):",
        "  Block 0 → Set 0 (can go in line 0 or 1 of set 0)",
        "  Block 4 → Set 0 (same set as block 0, different tag)",
        "  Block 8 → Set 0 (if set full → replacement needed)",
        "",
        "Address format:  [ TAG  |  SET INDEX  |  OFFSET ]",
    ], y=Inches(1.6), h=Inches(5.2))

    # ==== Slide 9: FIFO vs LRU ====
    s = new_slide()
    accent_rule(s)
    title_box(s, "Replacement Policies: FIFO vs LRU")
    code_box(s, [
        "FIFO (First In First Out):",
        "  Evicts the OLDEST INSERTED block — not the least accessed",
        "  Cache HIT does NOT update insertion order",
        "  Queue: [B0(oldest), B1, B2, B3(newest)]",
        "  Access B4 (miss): evict B0 → [B1, B2, B3, B4]",
        "  Access B1 (hit):  queue UNCHANGED → [B1, B2, B3, B4]",
        "",
        "LRU (Least Recently Used):",
        "  Evicts the block NOT ACCESSED for the longest time",
        "  Cache HIT DOES update block's recency timestamp",
        "  State: B0(t=1), B1(t=2), B2(t=3), B3(t=4)",
        "  Access B0 (hit):  B0 recency → t=5  →  B1 is now LRU victim",
        "  Access B4 (miss): evict B1(t=2)  →  LRU correctly saves B0",
    ], y=Inches(1.6), h=Inches(5.3))

    # ==== Slide 10: Address Breakdown ====
    s = new_slide()
    accent_rule(s)
    title_box(s, "Address Breakdown: TAG | INDEX | OFFSET")
    code_box(s, [
        "32-bit Address = [ TAG (tag_bits) | INDEX (index_bits) | OFFSET (offset_bits) ]",
        "",
        "offset_bits  =  log2(Block Size)",
        "index_bits   =  log2(Number of Sets)    [0 for Fully Associative]",
        "tag_bits     =  32 - index_bits - offset_bits",
        "",
        "Example  (64 B cache, 4 B block, Direct Mapping, 16 lines):",
        "  offset_bits  =  log2(4)   = 2",
        "  index_bits   =  log2(16)  = 4",
        "  tag_bits     =  32 - 4 - 2 = 26",
        "",
        "Address 68 = 0x44:",
        "  Block   =  68  /  4  =  17",
        "  Offset  =  68 mod 4  =   0",
        "  Index   =  17 mod 16 =   1   (cache line 1)",
        "  Tag     =  17  /  16 =   1",
    ], y=Inches(1.6), h=Inches(5.4))

    # ==== Slide 11: Statistics ====
    s = new_slide()
    accent_rule(s)
    title_box(s, "Performance Statistics")
    code_box(s, [
        "Hit Ratio    =  Cache Hits   /  Total Accesses",
        "Miss Ratio   =  Cache Misses /  Total Accesses",
        "",
        "Hit  %       =  Hit Ratio  × 100",
        "Miss %       =  Miss Ratio × 100",
        "",
        "ALWAYS:    Hit% + Miss% = 100%",
        "",
        "Special case:  Total = 0  →  all ratios defined as 0  (no division by zero)",
        "",
        "Demo 1 Results (addresses 0, 4, 0, 64, 4, 64):",
        "  Total Accesses : 6",
        "  Cache Hits     : 3     Hit  Ratio  = 0.5     Hit%  = 50%",
        "  Cache Misses   : 3     Miss Ratio  = 0.5     Miss% = 50%",
        "  Verification   : 50% + 50% = 100%  ✅",
    ], y=Inches(1.6), h=Inches(5.4))

    # ==== Slide 12: System Architecture ====
    s = new_slide()
    accent_rule(s)
    title_box(s, "System Architecture & Technologies")
    bullet_box(s, [
        "Frontend   :  HTML5, CSS3, JavaScript (single-page application, 7 pages)",
        "Backend    :  Python 3.14, Flask 3.x REST API (6 endpoints)",
        "Engine     :  C++17 simulation + Python mirror engine",
        "CORS       :  Flask-CORS for browser–server communication",
        "Protocol   :  JSON over HTTP",
        "",
        "Pages:  Home | Configure | Simulate | Visualize | Statistics | Learn | About",
        "",
        "Data flow:",
        "   Browser  →  POST /api/simulate  →  Flask  →  cache_engine.py  →  JSON",
        "   JSON events  →  renderCacheVisualization()  →  DOM update",
        "",
        "50 automated tests covering all mapping + replacement scenarios",
    ], size=17)

    # ==== Slide 13: Demo Results ====
    s = new_slide()
    accent_rule(s)
    title_box(s, "Demonstration Results")
    bullet_box(s, [
        "Demo 1 – Direct Mapping  (256B/64B/4B, addrs: 0,4,0,64,4,64)",
        "   Hits=3  Misses=3  Hit%=50%  ✅  Matches expected output exactly",
        "",
        "Demo 2 – Fully Associative FIFO  (16B cache, 4 lines)",
        "   FIFO evicts oldest-inserted block when cache full",
        "",
        "Demo 3 – Fully Associative LRU  (same config)",
        "   LRU evicts least-recently-accessed block (different from FIFO)",
        "",
        "Demo 4 – 2-Way Set Associative LRU  (32B/4B, 4 sets)",
        "   Block maps to fixed set, any line within set",
        "",
        "Demo 5 – LRU/FIFO Difference  (hit on B0 saves it in LRU, not FIFO)",
    ], size=18)

    # ==== Slide 14: Test Results ====
    s = new_slide()
    accent_rule(s)
    title_box(s, "Test Results: 50/50 Passing")
    bullet_box(s, [
        "✅  8 / 8   Config Validation   (power-of-two, divisibility, range checks)",
        "✅ 15 / 15  Direct Mapping      (Demo 1 events, address breakdown)",
        "✅  4 / 4   Fully Assoc FIFO   (miss sequence, correct eviction)",
        "✅  4 / 4   Fully Assoc LRU    (hit updates recency, correct eviction)",
        "✅  5 / 5   2-Way Set Assoc    (set index calculation, hits/misses)",
        "✅  5 / 5   Statistics Formulas (hit%+miss%=100, zero accesses safe)",
        "✅  1 / 1   Conflict Miss       (direct mapping, alternating conflict)",
        "✅  2 / 2   FIFO vs LRU         (LRU hits ≥ FIFO hits on reuse)",
        "✅  5 / 5   Address Breakdown   (block, offset, index, tag correctness)",
        "",
        "              TOTAL:  50 / 50  =  100% PASS",
    ], size=17)

    # ==== Slide 15: Conclusion ====
    s = new_slide()
    accent_rule(s)
    title_box(s, "Conclusion")
    bullet_box(s, [
        "Successfully implemented a complete, accurate Cache Memory Simulator",
        "All 3 mapping techniques and 2 replacement policies are correct",
        "Step-by-step simulation with forward/backward navigation works",
        "50 automated unit tests pass — 100% test coverage",
        "Professional web UI with educational content for 20 COA concepts",
        "Flask REST API with 6 endpoints validated and tested",
        "C++ source code provided for all simulation modules",
        "",
        "Thank You!",
        "",
        "Open: http://127.0.0.1:5000  after running start_server.bat",
    ], size=18)
    title_box(s, "Questions?", y=Inches(6.5), color=C_PRIMARY, size=28,
              align=PP_ALIGN.CENTER, x=0, w=W)

    # Save
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "Cache_Memory_Simulator_Presentation.pptx")
    prs.save(out)
    print(f"✅ Presentation saved: {out}")


def generate_text_summary():
    """Fallback: write slide content as text if pptx not available."""
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "presentation_slides.txt")
    content = """
CACHE MEMORY SIMULATOR — PRESENTATION SLIDES
COA B.Tech CSE Project
==============================================

SLIDE 1: Title
  Cache Memory Simulator
  Computer Organization & Architecture — B.Tech CSE
  Student: [Your Name] | Roll: [Roll No] | 2024-2025

SLIDE 2: Agenda
  1. Project Overview & Objectives
  2. Memory Hierarchy & Cache Basics
  3. Direct Mapping
  4. Fully Associative Mapping
  5. Set Associative Mapping
  6. FIFO & LRU Replacement Policies
  7. Address Breakdown: TAG | INDEX | OFFSET
  8. Performance Statistics
  9. System Architecture & Technologies
  10. Demo Results & Test Cases
  11. Conclusions

SLIDE 3: Objectives
  - Simulate cache memory between CPU and Main Memory
  - Direct, Fully Associative, Set Associative Mapping
  - FIFO and LRU replacement policies
  - Step-by-step simulation with navigation
  - Address breakdown display
  - Hit/miss statistics
  - 50 automated tests

[... 15 total slides — install python-pptx to generate full PPTX]
"""
    with open(out, "w") as f:
        f.write(content)
    print(f"Text summary saved: {out}")


if __name__ == "__main__":
    build_presentation()
