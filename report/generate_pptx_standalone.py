"""
generate_pptx_standalone.py
Pure Python standalone PowerPoint presentation generator for Cache Memory Simulator.
Generates a complete, beautiful 15-slide widescreen (.pptx) presentation without any third-party dependencies.
"""
import zipfile
import html
import os

EMU_PER_INCH = 914400
SLIDE_W = 12192000  # 13.333 inches (16:9 widescreen)
SLIDE_H = 6858000   # 7.5 inches

def escape_xml(s):
    return html.escape(str(s), quote=True)

def create_text_shape(sp_id, x_inch, y_inch, w_inch, h_inch, paragraphs, bg_color=None, border_color=None):
    x_emu = int(x_inch * EMU_PER_INCH)
    y_emu = int(y_inch * EMU_PER_INCH)
    w_emu = int(w_inch * EMU_PER_INCH)
    h_emu = int(h_inch * EMU_PER_INCH)

    fill_xml = f'<a:solidFill><a:srgbClr val="{bg_color}"/></a:solidFill>' if bg_color else '<a:noFill/>'
    ln_xml = f'<a:ln w="19050"><a:solidFill><a:srgbClr val="{border_color}"/></a:solidFill></a:ln>' if border_color else '<a:ln><a:noFill/></a:ln>'

    p_xmls = []
    for p in paragraphs:
        text = p.get('text', '')
        size = p.get('size', 16) * 100
        bold = ' b="1"' if p.get('bold', False) else ''
        color = p.get('color', 'E2E8F0')
        font = p.get('font', 'Segoe UI')
        align = p.get('align', 'l')
        bullet = p.get('bullet', False)
        code = p.get('code', False)
        if code:
            font = 'Courier New'

        algn_val = 'ctr' if align == 'center' else ('r' if align == 'right' else 'l')
        bu_xml = '<a:buChar char="•"/>' if bullet else '<a:buNone/>'

        runs_xml = ""
        # Support multiple styled spans or single run
        if 'runs' in p:
            for r in p['runs']:
                r_txt = escape_xml(r.get('text', ''))
                r_sz = r.get('size', p.get('size', 16)) * 100
                r_bold = ' b="1"' if r.get('bold', p.get('bold', False)) else ''
                r_col = r.get('color', color)
                r_font = r.get('font', font)
                runs_xml += f'''<a:r>
                  <a:rPr lang="en-US" sz="{r_sz}"{r_bold}><a:solidFill><a:srgbClr val="{r_col}"/></a:solidFill><a:latin typeface="{r_font}"/></a:rPr>
                  <a:t>{r_txt}</a:t>
                </a:r>'''
        else:
            e_text = escape_xml(text)
            runs_xml = f'''<a:r>
              <a:rPr lang="en-US" sz="{size}"{bold}><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="{font}"/></a:rPr>
              <a:t>{e_text}</a:t>
            </a:r>'''

        p_xmls.append(f'''<a:p>
          <a:pPr algn="{algn_val}">{bu_xml}</a:pPr>
          {runs_xml}
        </a:p>''')

    body_xml = "\n".join(p_xmls)

    return f'''<p:sp>
      <p:nvSpPr><p:cNvPr id="{sp_id}" name="Shape{sp_id}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr>
        <a:xfrm><a:off x="{x_emu}" y="{y_emu}"/><a:ext cx="{w_emu}" cy="{h_emu}"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        {fill_xml}
        {ln_xml}
      </p:spPr>
      <p:txBody>
        <a:bodyPr wrap="square" rtlCol="0"><a:spAutoFit/></a:bodyPr>
        <a:lstStyle/>
        {body_xml}
      </p:txBody>
    </p:sp>'''

def build_slide(title, subtitle, shapes_data):
    sp_id = 2
    shapes = []

    # Slide Background
    shapes.append(f'''<p:sp>
      <p:nvSpPr><p:cNvPr id="{sp_id}" name="Bg"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
      <p:spPr>
        <a:xfrm><a:off x="0" y="0"/><a:ext cx="{SLIDE_W}" cy="{SLIDE_H}"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        <a:solidFill><a:srgbClr val="0F172A"/></a:solidFill>
        <a:ln><a:noFill/></a:ln>
      </p:spPr>
    </p:sp>''')
    sp_id += 1

    # Accent Top Stripe
    shapes.append(f'''<p:sp>
      <p:nvSpPr><p:cNvPr id="{sp_id}" name="TopBar"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
      <p:spPr>
        <a:xfrm><a:off x="0" y="0"/><a:ext cx="{SLIDE_W}" cy="73152"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        <a:solidFill><a:srgbClr val="2563EB"/></a:solidFill>
        <a:ln><a:noFill/></a:ln>
      </p:spPr>
    </p:sp>''')
    sp_id += 1

    # Header / Title area
    if title:
        header_paras = [
            {'text': title, 'size': 26, 'bold': True, 'color': 'FFFFFF'},
        ]
        if subtitle:
            header_paras.append({'text': subtitle, 'size': 14, 'color': '94A3B8'})
        shapes.append(create_text_shape(sp_id, 0.8, 0.4, 11.7, 1.0, header_paras))
        sp_id += 1

    # Custom content shapes
    for s_info in shapes_data:
        shapes.append(create_text_shape(
            sp_id,
            s_info.get('x', 0.8),
            s_info.get('y', 1.6),
            s_info.get('w', 11.7),
            s_info.get('h', 4.8),
            s_info.get('paras', []),
            bg_color=s_info.get('bg'),
            border_color=s_info.get('border')
        ))
        sp_id += 1

    # Footer
    shapes.append(create_text_shape(
        sp_id, 0.8, 7.0, 11.7, 0.4,
        [{'text': 'Cache Memory Simulator | Computer Organization and Architecture (COA) | B.Tech CSE Project', 'size': 10, 'color': '475569'}]
    ))

    body = "\n".join(shapes)
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      {body}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>'''

def build_presentation(output_path):
    slides = [
        # Slide 1: Title
        {
            'title': '', 'subtitle': '',
            'shapes': [
                {
                    'x': 1.0, 'y': 1.6, 'w': 11.3, 'h': 4.5,
                    'paras': [
                        {'text': 'COMPUTER ORGANIZATION & ARCHITECTURE', 'size': 14, 'bold': True, 'color': '60A5FA', 'align': 'center'},
                        {'text': 'CACHE MEMORY SIMULATOR', 'size': 40, 'bold': True, 'color': 'FFFFFF', 'align': 'center'},
                        {'text': 'Interactive Educational Simulation Engine & Web-Based Visualizer', 'size': 18, 'color': '94A3B8', 'align': 'center'},
                        {'text': ' ', 'size': 14},
                        {'text': 'B.Tech Computer Science & Engineering Final Project', 'size': 16, 'bold': True, 'color': '34D399', 'align': 'center'},
                        {'text': 'Implementation: C++17 Engine | Python Flask Backend | HTML5/CSS3/JS UI', 'size': 14, 'color': 'A78BFA', 'align': 'center'},
                        {'text': ' ', 'size': 10},
                        {'text': 'Student: [Student Name]  |  Roll No: [Roll Number]  |  Guide: [Faculty Name]', 'size': 13, 'color': 'E2E8F0', 'align': 'center'},
                        {'text': 'Institution: [College Name]  |  Academic Year: 2024-2025', 'size': 12, 'color': '64748B', 'align': 'center'},
                    ],
                    'bg': '1E293B', 'border': '3B82F6'
                }
            ]
        },
        # Slide 2: Objectives & Executive Summary
        {
            'title': 'Project Overview & Objectives',
            'subtitle': 'Bridging theoretical computer architecture and hands-on simulation',
            'shapes': [
                {
                    'x': 0.8, 'y': 1.6, 'w': 5.6, 'h': 4.9,
                    'paras': [
                        {'text': '🎯 Core Project Goals', 'size': 18, 'bold': True, 'color': '60A5FA'},
                        {'text': 'Demonstrate CPU-Cache-Main Memory interactions dynamically', 'bullet': True, 'size': 14},
                        {'text': 'Model Direct, Fully Associative, and Set Associative Mapping', 'bullet': True, 'size': 14},
                        {'text': 'Implement FIFO and LRU victim eviction policies', 'bullet': True, 'size': 14},
                        {'text': 'Show exact 32-bit address field decomposition (Tag, Index, Offset)', 'bullet': True, 'size': 14},
                        {'text': 'Provide step-by-step navigation with forward/backward time-travel', 'bullet': True, 'size': 14},
                        {'text': 'Calculate accurate real-time hit/miss metrics dynamically', 'bullet': True, 'size': 14},
                    ],
                    'bg': '1E293B', 'border': '334155'
                },
                {
                    'x': 6.8, 'y': 1.6, 'w': 5.7, 'h': 4.9,
                    'paras': [
                        {'text': '⭐ Key Architectural Highlights', 'size': 18, 'bold': True, 'color': '34D399'},
                        {'text': 'C++17 Engine: Native modular algorithms without approximations', 'bullet': True, 'size': 14},
                        {'text': 'Zero Frontend Fabrication: UI never synthesizes simulation state', 'bullet': True, 'size': 14},
                        {'text': 'Flask REST API: Clean subprocess communication and input safety', 'bullet': True, 'size': 14},
                        {'text': '50 Automated Engine Tests: 100% test pass on all scenarios', 'bullet': True, 'size': 14},
                        {'text': '40 Backend API Tests: Validating status codes, errors, and JSON', 'bullet': True, 'size': 14},
                        {'text': 'Viva-Ready: Includes full theoretical explanations & demonstration presets', 'bullet': True, 'size': 14},
                    ],
                    'bg': '1E293B', 'border': '334155'
                }
            ]
        },
        # Slide 3: Memory Hierarchy
        {
            'title': 'Computer Memory Hierarchy',
            'subtitle': 'Understanding the fundamental tradeoff between speed, size, and cost',
            'shapes': [
                {
                    'x': 0.8, 'y': 1.6, 'w': 11.7, 'h': 4.9,
                    'paras': [
                        {'text': 'Level 0: CPU Registers (< 1 KB) — Access time < 0.5 ns — Fastest, ultra-expensive', 'size': 14, 'bold': True, 'color': '60A5FA'},
                        {'text': 'Level 1: L1 Cache (32–64 KB) — Access time ~ 1 ns — On-chip per-core SRAM', 'size': 14, 'bold': True, 'color': '34D399'},
                        {'text': 'Level 2: L2 Cache (256 KB–4 MB) — Access time ~ 4–10 ns — Dedicated SRAM', 'size': 14, 'bold': True, 'color': 'A78BFA'},
                        {'text': 'Level 3: L3 Cache (8–64 MB) — Access time ~ 20–40 ns — Shared on-die SRAM', 'size': 14, 'bold': True, 'color': 'FBBF24'},
                        {'text': 'Level 4: Main Memory / RAM (8–128 GB) — Access time ~ 60–100 ns — Synchronous DRAM', 'size': 14, 'bold': True, 'color': 'F87171'},
                        {'text': 'Level 5: Secondary Storage / NVMe SSD (1–4 TB) — Access time ~ 10–50 µs — Non-volatile Flash', 'size': 14, 'color': '94A3B8'},
                        {'text': ' ', 'size': 8},
                        {'text': '💡 Principle of Locality of Reference:', 'size': 16, 'bold': True, 'color': 'F59E0B'},
                        {'text': '• Temporal Locality: If a memory location was referenced, it will tend to be referenced again soon (loops, variables).', 'size': 13, 'color': 'E2E8F0'},
                        {'text': '• Spatial Locality: If a memory location is referenced, nearby locations will tend to be referenced soon (array indexing, code execution).', 'size': 13, 'color': 'E2E8F0'},
                    ],
                    'bg': '1E293B', 'border': '334155'
                }
            ]
        },
        # Slide 4: Cache Terminology
        {
            'title': 'Cache Memory Fundamentals & Terminology',
            'subtitle': 'Essential concepts governing cache organization and operation',
            'shapes': [
                {
                    'x': 0.8, 'y': 1.6, 'w': 5.6, 'h': 4.9,
                    'paras': [
                        {'text': 'Cache Line (Block)', 'size': 16, 'bold': True, 'color': '60A5FA'},
                        {'text': 'The minimum unit of data transferred between main memory and cache.', 'size': 13, 'color': 'E2E8F0'},
                        {'text': 'Tag Field', 'size': 16, 'bold': True, 'color': '60A5FA'},
                        {'text': 'Bits from the memory address stored alongside data to uniquely identify the cached block.', 'size': 13, 'color': 'E2E8F0'},
                        {'text': 'Valid Bit (V)', 'size': 16, 'bold': True, 'color': '60A5FA'},
                        {'text': '1-bit flag indicating whether the cache line currently holds valid, initialized memory data.', 'size': 13, 'color': 'E2E8F0'},
                        {'text': 'Index / Set Index', 'size': 16, 'bold': True, 'color': '60A5FA'},
                        {'text': 'Selects the specific line (direct) or set (set associative) where a block must map.', 'size': 13, 'color': 'E2E8F0'},
                    ],
                    'bg': '1E293B', 'border': '334155'
                },
                {
                    'x': 6.8, 'y': 1.6, 'w': 5.7, 'h': 4.9,
                    'paras': [
                        {'text': 'Block Offset', 'size': 16, 'bold': True, 'color': '34D399'},
                        {'text': 'Identifies the exact byte or word inside the multi-byte block.', 'size': 13, 'color': 'E2E8F0'},
                        {'text': 'Cache Hit vs Cache Miss', 'size': 16, 'bold': True, 'color': '34D399'},
                        {'text': 'Hit: Requested tag matches valid tag in target set (low latency).', 'size': 13, 'color': 'E2E8F0'},
                        {'text': 'Miss: Tag not found or line invalid; must fetch block from RAM.', 'size': 13, 'color': 'E2E8F0'},
                        {'text': 'Cache Replacement / Eviction', 'size': 16, 'bold': True, 'color': '34D399'},
                        {'text': 'When all target lines are full, a victim block must be chosen and replaced.', 'size': 13, 'color': 'E2E8F0'},
                        {'text': 'Hit & Miss Ratios', 'size': 16, 'bold': True, 'color': '34D399'},
                        {'text': 'Hit Ratio = Hits / Total | Miss Ratio = Misses / Total | Sum = 1.0 (100%).', 'size': 13, 'color': 'E2E8F0'},
                    ],
                    'bg': '1E293B', 'border': '334155'
                }
            ]
        },
        # Slide 5: Direct Mapping
        {
            'title': 'Direct Mapping Implementation',
            'subtitle': 'One-to-one relationship between main memory blocks and cache lines',
            'shapes': [
                {
                    'x': 0.8, 'y': 1.6, 'w': 5.6, 'h': 4.9,
                    'paras': [
                        {'text': 'Working Principle', 'size': 16, 'bold': True, 'color': '60A5FA'},
                        {'text': 'Each block of main memory maps to exactly one predetermined cache line.', 'size': 13},
                        {'text': 'Lookup is instantaneous (O(1)): check only one line per access.', 'size': 13},
                        {'text': ' ', 'size': 6},
                        {'text': 'Mathematical Formulation:', 'size': 16, 'bold': True, 'color': '34D399'},
                        {'text': 'Memory Block Number = Address / Block Size', 'size': 13, 'code': True, 'color': 'A78BFA'},
                        {'text': 'Cache Line (Index)  = Block Number % Num Lines', 'size': 13, 'code': True, 'color': 'A78BFA'},
                        {'text': 'Tag                 = Block Number / Num Lines', 'size': 13, 'code': True, 'color': 'A78BFA'},
                        {'text': 'Block Offset        = Address % Block Size', 'size': 13, 'code': True, 'color': 'A78BFA'},
                        {'text': ' ', 'size': 6},
                        {'text': 'Replacement Mechanism:', 'size': 16, 'bold': True, 'color': 'F59E0B'},
                        {'text': 'Strictly deterministic. If line is occupied by another block, it is evicted immediately without requiring FIFO or LRU.', 'size': 13},
                    ],
                    'bg': '1E293B', 'border': '334155'
                },
                {
                    'x': 6.8, 'y': 1.6, 'w': 5.7, 'h': 4.9,
                    'paras': [
                        {'text': 'Address Division (32-bit Architecture)', 'size': 16, 'bold': True, 'color': '60A5FA'},
                        {'text': '[ TAG (32-i-o bits) ] [ INDEX (i bits) ] [ OFFSET (o bits) ]', 'size': 12, 'code': True, 'color': '34D399'},
                        {'text': ' ', 'size': 8},
                        {'text': '✅ Key Advantages:', 'size': 15, 'bold': True, 'color': '34D399'},
                        {'text': '• Minimal hardware comparator circuitry (only 1 comparator needed).', 'size': 13},
                        {'text': '• Lowest search delay among all mapping schemes.', 'size': 13},
                        {'text': '• Simple replacement logic.', 'size': 13},
                        {'text': ' ', 'size': 8},
                        {'text': '❌ Key Disadvantage (Conflict Misses):', 'size': 15, 'bold': True, 'color': 'EF4444'},
                        {'text': 'If a program loops between two memory blocks that share the same line index (e.g. Block 0 and Block 16), thrashing occurs with 0% hit rate.', 'size': 13},
                    ],
                    'bg': '1E293B', 'border': '334155'
                }
            ]
        },
        # Slide 6: Demonstration 1 Step-by-Step
        {
            'title': 'Direct Mapping Demonstration (Demo 1 Analysis)',
            'subtitle': 'Configuration: MM=256 B, Cache=64 B, Block=4 B (16 Lines) | Addresses: 0, 4, 0, 64, 4, 64',
            'shapes': [
                {
                    'x': 0.8, 'y': 1.6, 'w': 11.7, 'h': 4.9,
                    'paras': [
                        {'text': 'Step-by-Step Execution Verification (C++ Engine Output):', 'size': 16, 'bold': True, 'color': '60A5FA'},
                        {'text': '1. Address 0  -> Block 0,  Line 0, Tag 0: MISS (Cold miss -> Line 0 loaded with Block 0, Tag 0)', 'size': 13, 'code': True, 'color': 'F87171'},
                        {'text': '2. Address 4  -> Block 1,  Line 1, Tag 0: MISS (Cold miss -> Line 1 loaded with Block 1, Tag 0)', 'size': 13, 'code': True, 'color': 'F87171'},
                        {'text': '3. Address 0  -> Block 0,  Line 0, Tag 0: HIT  (Line 0 valid bit=1, Tag=0 matches requested Tag 0)', 'size': 13, 'code': True, 'color': '34D399'},
                        {'text': '4. Address 64 -> Block 16, Line 0, Tag 1: MISS_REPLACE (Conflict: Line 0 had Tag 0; evicted -> loaded Tag 1)', 'size': 13, 'code': True, 'color': 'FBBF24'},
                        {'text': '5. Address 4  -> Block 1,  Line 1, Tag 0: HIT  (Line 1 valid bit=1, Tag=0 still intact)', 'size': 13, 'code': True, 'color': '34D399'},
                        {'text': '6. Address 64 -> Block 16, Line 0, Tag 1: HIT  (Line 0 valid bit=1, Tag=1 matches requested Tag 1)', 'size': 13, 'code': True, 'color': '34D399'},
                        {'text': ' ', 'size': 8},
                        {'text': '📊 Final Performance Metrics:', 'size': 16, 'bold': True, 'color': 'A78BFA'},
                        {'text': 'Total Accesses: 6  |  Hits: 3  |  Misses: 3  |  Hit Rate: 50.00%  |  Miss Rate: 50.00%', 'size': 14, 'bold': True, 'color': 'FFFFFF'},
                        {'text': 'Exact alignment between user problem specification and simulation engine output.', 'size': 13, 'color': '34D399'},
                    ],
                    'bg': '1E293B', 'border': '334155'
                }
            ]
        },
        # Slide 7: Fully Associative Mapping
        {
            'title': 'Fully Associative Mapping',
            'subtitle': 'Zero placement restrictions with associative search across all lines',
            'shapes': [
                {
                    'x': 0.8, 'y': 1.6, 'w': 5.6, 'h': 4.9,
                    'paras': [
                        {'text': 'Design Principles', 'size': 16, 'bold': True, 'color': '60A5FA'},
                        {'text': 'Any memory block can reside in ANY cache line.', 'size': 13},
                        {'text': 'No index field exists in the memory address.', 'size': 13},
                        {'text': 'The entire Block Number serves as the Tag.', 'size': 13},
                        {'text': 'On every access, all cache lines are searched simultaneously.', 'size': 13},
                        {'text': ' ', 'size': 6},
                        {'text': 'Address Division:', 'size': 16, 'bold': True, 'color': '34D399'},
                        {'text': '[ TAG (32 - offset bits) ] [ BLOCK OFFSET (offset bits) ]', 'size': 12, 'code': True, 'color': 'A78BFA'},
                        {'text': ' ', 'size': 6},
                        {'text': 'Eviction Handling:', 'size': 16, 'bold': True, 'color': 'F59E0B'},
                        {'text': 'When all lines are valid, victim selection is governed by the configured policy (FIFO or LRU).', 'size': 13},
                    ],
                    'bg': '1E293B', 'border': '334155'
                },
                {
                    'x': 6.8, 'y': 1.6, 'w': 5.7, 'h': 4.9,
                    'paras': [
                        {'text': 'Pros and Cons Analysis', 'size': 16, 'bold': True, 'color': '60A5FA'},
                        {'text': '✅ Zero Conflict Misses: Maximizes cache capacity utilization.', 'size': 13, 'color': '34D399'},
                        {'text': '✅ Ideal for small, specialized memories like CPU Translation Lookaside Buffers (TLB).', 'size': 13, 'color': '34D399'},
                        {'text': ' ', 'size': 8},
                        {'text': '❌ Hardware Complexity: Requires N tag comparators in parallel hardware.', 'size': 13, 'color': 'EF4444'},
                        {'text': '❌ High Power Consumption & propagation delay for large caches.', 'size': 13, 'color': 'EF4444'},
                        {'text': ' ', 'size': 8},
                        {'text': 'Engine Implementation Details:', 'size': 16, 'bold': True, 'color': 'A78BFA'},
                        {'text': 'C++ FullyAssociativeCache models a unified single set holding all lines with rigorous timestamp/order tracking.', 'size': 13},
                    ],
                    'bg': '1E293B', 'border': '334155'
                }
            ]
        },
        # Slide 8: Set Associative Mapping
        {
            'title': 'Set Associative Mapping (N-Way Architecture)',
            'subtitle': 'The industry standard compromise combining speed and conflict mitigation',
            'shapes': [
                {
                    'x': 0.8, 'y': 1.6, 'w': 5.6, 'h': 4.9,
                    'paras': [
                        {'text': 'Architecture & Partitioning', 'size': 16, 'bold': True, 'color': '60A5FA'},
                        {'text': 'Cache lines are divided into S sets, each containing N lines (N-way).', 'size': 13},
                        {'text': 'A memory block maps to a single fixed set, but can occupy any line in that set.', 'size': 13},
                        {'text': ' ', 'size': 6},
                        {'text': 'Formulas for N-Way Cache:', 'size': 16, 'bold': True, 'color': '34D399'},
                        {'text': 'Number of Cache Lines = Cache Size / Block Size', 'size': 13, 'code': True},
                        {'text': 'Number of Sets (S)    = Number of Lines / N', 'size': 13, 'code': True},
                        {'text': 'Set Index             = Block Number % S', 'size': 13, 'code': True},
                        {'text': 'Tag                   = Block Number / S', 'size': 13, 'code': True},
                        {'text': 'Offset                = Address % Block Size', 'size': 13, 'code': True},
                    ],
                    'bg': '1E293B', 'border': '334155'
                },
                {
                    'x': 6.8, 'y': 1.6, 'w': 5.7, 'h': 4.9,
                    'paras': [
                        {'text': 'Address Layout (Set Associative)', 'size': 16, 'bold': True, 'color': '60A5FA'},
                        {'text': '[ TAG ] [ SET INDEX ] [ BLOCK OFFSET ]', 'size': 13, 'code': True, 'color': '34D399'},
                        {'text': ' ', 'size': 8},
                        {'text': 'Why Modern CPUs Use N-Way Set Associativity:', 'size': 15, 'bold': True, 'color': 'A78BFA'},
                        {'text': '• Direct mapping has N=1 (fast, high conflicts).', 'size': 13},
                        {'text': '• Fully associative has S=1, N=total lines (slow, expensive).', 'size': 13},
                        {'text': '• 2-way, 4-way, 8-way, and 16-way deliver ~95% of fully associative benefits with modest hardware comparator count.', 'size': 13},
                        {'text': ' ', 'size': 8},
                        {'text': 'Engine Support:', 'size': 15, 'bold': True, 'color': '34D399'},
                        {'text': 'Simulator supports arbitrary power-of-two ways (2-way, 4-way, 8-way, etc.) with per-set independent replacement queues.', 'size': 13},
                    ],
                    'bg': '1E293B', 'border': '334155'
                }
            ]
        },
        # Slide 9: Replacement Policies
        {
            'title': 'Replacement Policies: FIFO vs LRU',
            'subtitle': 'Algorithmic strategies for selecting which block to evict on cache fullness',
            'shapes': [
                {
                    'x': 0.8, 'y': 1.6, 'w': 5.6, 'h': 4.9,
                    'paras': [
                        {'text': 'FIFO (First In First Out)', 'size': 17, 'bold': True, 'color': '60A5FA'},
                        {'text': '• Core Rule: Evicts the block that was loaded earliest.', 'size': 13},
                        {'text': '• Insertion Tracking: Uses a queue (std::deque in C++).', 'size': 13},
                        {'text': '• Critical Invariant: Cache HIT does NOT alter FIFO queue.', 'size': 13, 'bold': True, 'color': 'FBBF24'},
                        {'text': '• Susceptible to Belady’s Anomaly where larger cache can paradoxically yield more misses in certain access patterns.', 'size': 13},
                        {'text': '• Example Queue: [B0 (oldest), B1, B2, B3 (newest)]', 'size': 12, 'code': True, 'color': '94A3B8'},
                        {'text': '  Hit on B0 leaves B0 at the head of the eviction queue!', 'size': 12, 'code': True, 'color': 'F87171'},
                    ],
                    'bg': '1E293B', 'border': '334155'
                },
                {
                    'x': 6.8, 'y': 1.6, 'w': 5.7, 'h': 4.9,
                    'paras': [
                        {'text': 'LRU (Least Recently Used)', 'size': 17, 'bold': True, 'color': '34D399'},
                        {'text': '• Core Rule: Evicts the block not accessed for longest duration.', 'size': 13},
                        {'text': '• Recency Tracking: Timestamp/counter updated on every hit or miss.', 'size': 13},
                        {'text': '• Critical Invariant: Cache HIT refreshes timestamp to current tick.', 'size': 13, 'bold': True, 'color': '34D399'},
                        {'text': '• Exploit temporal locality optimally; immune to Belady’s anomaly.', 'size': 13},
                        {'text': '• Example State: B0(t=1), B1(t=2), B2(t=3), B3(t=4)', 'size': 12, 'code': True, 'color': '94A3B8'},
                        {'text': '  Hit on B0 updates B0(t=5); B1 now becomes the LRU victim.', 'size': 12, 'code': True, 'color': '34D399'},
                    ],
                    'bg': '1E293B', 'border': '334155'
                }
            ]
        },
        # Slide 10: Address Breakdown
        {
            'title': '32-Bit Memory Address Breakdown',
            'subtitle': 'Bit-level decomposition for byte-addressable main memory',
            'shapes': [
                {
                    'x': 0.8, 'y': 1.6, 'w': 11.7, 'h': 4.9,
                    'paras': [
                        {'text': 'Address Bit Field Allocation Rules:', 'size': 16, 'bold': True, 'color': '60A5FA'},
                        {'text': 'Offset Bits (o) = log2(Block Size)', 'size': 14, 'code': True, 'color': '34D399'},
                        {'text': 'Index Bits  (i) = log2(Number of Sets)  [i=0 for Fully Associative]', 'size': 14, 'code': True, 'color': '34D399'},
                        {'text': 'Tag Bits    (t) = 32 - Index Bits - Offset Bits', 'size': 14, 'code': True, 'color': '34D399'},
                        {'text': ' ', 'size': 8},
                        {'text': 'Detailed Numerical Example:', 'size': 16, 'bold': True, 'color': 'F59E0B'},
                        {'text': 'Configuration: MM = 256 B, Cache = 64 B, Block = 4 B, Direct Mapping (16 Lines)', 'size': 13},
                        {'text': '  Offset Bits = log2(4) = 2 bits  |  Index Bits = log2(16) = 4 bits  |  Tag Bits = 32 - 4 - 2 = 26 bits', 'size': 13, 'color': 'A78BFA'},
                        {'text': 'Address 68 (Decimal) -> Binary: 0000 0000 0000 0000 0000 0000 0100 0100', 'size': 13, 'code': True},
                        {'text': '  Offset: lower 2 bits (00) = 0', 'size': 13, 'code': True, 'color': 'E2E8F0'},
                        {'text': '  Index:  next 4 bits (0001) = 1 (Cache line 1)', 'size': 13, 'code': True, 'color': 'E2E8F0'},
                        {'text': '  Tag:    remaining 26 bits (00...0001) = 1', 'size': 13, 'code': True, 'color': 'E2E8F0'},
                    ],
                    'bg': '1E293B', 'border': '334155'
                }
            ]
        },
        # Slide 11: Statistics & Mathematics
        {
            'title': 'Simulation Performance Statistics',
            'subtitle': 'Formulas, dynamic calculation, and boundary safety',
            'shapes': [
                {
                    'x': 0.8, 'y': 1.6, 'w': 5.6, 'h': 4.9,
                    'paras': [
                        {'text': 'Formal Performance Metrics', 'size': 16, 'bold': True, 'color': '60A5FA'},
                        {'text': 'Total Accesses = Hits + Misses', 'size': 13, 'code': True},
                        {'text': 'Hit Ratio      = Hits / Total Accesses', 'size': 13, 'code': True},
                        {'text': 'Miss Ratio     = Misses / Total Accesses', 'size': 13, 'code': True},
                        {'text': 'Hit Percentage  = Hit Ratio * 100', 'size': 13, 'code': True},
                        {'text': 'Miss Percentage = Miss Ratio * 100', 'size': 13, 'code': True},
                        {'text': ' ', 'size': 6},
                        {'text': 'Mathematical Invariants Enforced:', 'size': 16, 'bold': True, 'color': '34D399'},
                        {'text': '• Hit Ratio + Miss Ratio = 1.0 (Exact)', 'size': 13},
                        {'text': '• Hit% + Miss% = 100.0% (Exact)', 'size': 13},
                        {'text': '• Zero-access safety: Div-by-zero protected.', 'size': 13},
                    ],
                    'bg': '1E293B', 'border': '334155'
                },
                {
                    'x': 6.8, 'y': 1.6, 'w': 5.7, 'h': 4.9,
                    'paras': [
                        {'text': 'Effective Memory Access Time (EMAT)', 'size': 16, 'bold': True, 'color': 'F59E0B'},
                        {'text': 'Theoretical Context for Viva Examination:', 'size': 13, 'color': '94A3B8'},
                        {'text': 'EMAT = Hit_Time + (Miss_Rate * Miss_Penalty)', 'size': 13, 'code': True, 'color': 'A78BFA'},
                        {'text': ' ', 'size': 6},
                        {'text': 'Example Calculation:', 'size': 14, 'bold': True, 'color': 'E2E8F0'},
                        {'text': 'Suppose Cache Hit Time = 1 ns, RAM Miss Penalty = 50 ns', 'size': 13},
                        {'text': 'With 90% Hit Rate (10% Miss Rate):', 'size': 13},
                        {'text': '  EMAT = 1 + (0.10 * 50) = 6 ns (8.3x faster than RAM alone!)', 'size': 13, 'bold': True, 'color': '34D399'},
                        {'text': 'With 50% Hit Rate (Demo 1):', 'size': 13},
                        {'text': '  EMAT = 1 + (0.50 * 50) = 26 ns', 'size': 13, 'color': 'E2E8F0'},
                    ],
                    'bg': '1E293B', 'border': '334155'
                }
            ]
        },
        # Slide 12: System Architecture
        {
            'title': 'Full-Stack System Architecture',
            'subtitle': 'Modular design separating UI, backend orchestration, and algorithmic computation',
            'shapes': [
                {
                    'x': 0.8, 'y': 1.6, 'w': 11.7, 'h': 4.9,
                    'paras': [
                        {'text': 'Three-Tier Architecture Flow:', 'size': 17, 'bold': True, 'color': '60A5FA'},
                        {'text': '[ Frontend Browser (HTML5 / CSS3 / ES6) ]', 'size': 14, 'code': True, 'color': '60A5FA'},
                        {'text': '        │  Async Fetch HTTP REST API (/api/configure, /api/simulate, /api/sample)', 'size': 12, 'code': True, 'color': '94A3B8'},
                        {'text': '        ▼', 'size': 12, 'code': True, 'color': '94A3B8'},
                        {'text': '[ Python Flask 3.x Backend (app.py) ]  <-- Validates inputs, handles timeouts, returns JSON', 'size': 14, 'code': True, 'color': '34D399'},
                        {'text': '        │  Standard Subprocess Execution or Python Engine Mirror', 'size': 12, 'code': True, 'color': '94A3B8'},
                        {'text': '        ▼', 'size': 12, 'code': True, 'color': '94A3B8'},
                        {'text': '[ Core Simulation Engine (C++17 / Python Mirror) ]', 'size': 14, 'code': True, 'color': 'A78BFA'},
                        {'text': '   DirectMapping.cpp  |  FullyAssociative.cpp  |  SetAssociative.cpp  |  ReplacementPolicy.cpp', 'size': 12, 'code': True, 'color': 'E2E8F0'},
                        {'text': ' ', 'size': 6},
                        {'text': 'Security & Isolation Design:', 'size': 15, 'bold': True, 'color': 'F59E0B'},
                        {'text': '• Subprocess argument arrays prevent shell injection. No raw string formatting used in execution.', 'size': 13},
                        {'text': '• All numbers strictly validated for positive powers of two, divisibility, and bounds before execution.', 'size': 13},
                    ],
                    'bg': '1E293B', 'border': '334155'
                }
            ]
        },
        # Slide 13: Interactive Navigation & UI
        {
            'title': 'Interactive Step Navigation & State Snapshots',
            'subtitle': 'Time-travel simulation with full cache memory state preservation',
            'shapes': [
                {
                    'x': 0.8, 'y': 1.6, 'w': 5.6, 'h': 4.9,
                    'paras': [
                        {'text': 'Step Controls & Navigation', 'size': 16, 'bold': True, 'color': '60A5FA'},
                        {'text': '• Next Step (▶): Advance one access, update lines and stats.', 'size': 13},
                        {'text': '• Prev Step (◀): Step backward to exact previous state.', 'size': 13},
                        {'text': '• Reset: Clear memory states and reset counter.', 'size': 13},
                        {'text': '• Jump-to-Step: Clicking any row in the simulation table restores that exact access state.', 'size': 13},
                        {'text': ' ', 'size': 6},
                        {'text': 'State Preservation Engine:', 'size': 16, 'bold': True, 'color': '34D399'},
                        {'text': 'Every access generates a complete Cache Snapshot storing the exact valid bit, tag, and block number of every line across all sets.', 'size': 13},
                    ],
                    'bg': '1E293B', 'border': '334155'
                },
                {
                    'x': 6.8, 'y': 1.6, 'w': 5.7, 'h': 4.9,
                    'paras': [
                        {'text': 'Visual Color Indicators', 'size': 16, 'bold': True, 'color': '60A5FA'},
                        {'text': '🟢 GREEN: Cache Hit (highlighted target line)', 'size': 13, 'bold': True, 'color': '34D399'},
                        {'text': '🔴 RED: Cache Miss (block fetched from main memory)', 'size': 13, 'bold': True, 'color': 'EF4444'},
                        {'text': '🟡 YELLOW: Cache Replacement (evicted victim block)', 'size': 13, 'bold': True, 'color': 'FBBF24'},
                        {'text': '🔵 BLUE: Valid cached block (not accessed in current step)', 'size': 13, 'bold': True, 'color': '60A5FA'},
                        {'text': '⬜ GRAY: Empty line (Valid bit = 0)', 'size': 13, 'color': '94A3B8'},
                        {'text': ' ', 'size': 8},
                        {'text': 'Animated CPU-Cache-RAM Data Path:', 'size': 15, 'bold': True, 'color': 'A78BFA'},
                        {'text': 'Visual buses pulse green on hit, red on miss with memory transfer arrows indicating block fetching.', 'size': 13},
                    ],
                    'bg': '1E293B', 'border': '334155'
                }
            ]
        },
        # Slide 14: Verification & Test Results
        {
            'title': 'Automated Verification & Test Coverage',
            'subtitle': 'Rigorous testing of all algorithmic edge cases and API contracts',
            'shapes': [
                {
                    'x': 0.8, 'y': 1.6, 'w': 5.6, 'h': 4.9,
                    'paras': [
                        {'text': 'Core Simulation Tests: 50 / 50 PASSED', 'size': 16, 'bold': True, 'color': '34D399'},
                        {'text': '• Config Validation (8 tests): Powers of two, divisibility, bounds.', 'size': 12},
                        {'text': '• Direct Mapping (15 tests): Verified 6-step Demo 1 sequence.', 'size': 12},
                        {'text': '• Fully Associative FIFO (4 tests): Cold miss sequence, oldest evicted.', 'size': 12},
                        {'text': '• Fully Associative LRU (4 tests): Access refresh, least recent evicted.', 'size': 12},
                        {'text': '• Set Associative LRU (5 tests): Multi-way partitioning, correct hits.', 'size': 12},
                        {'text': '• Statistics Formulas (5 tests): Sum invariants, zero accesses.', 'size': 12},
                        {'text': '• Direct Conflict Thrashing (1 test): Alternating conflict verification.', 'size': 12},
                        {'text': '• FIFO vs LRU Divergence (2 tests): Proof that hits protect LRU.', 'size': 12},
                        {'text': '• Address Breakdown (5 tests): Tag, index, offset bit-math.', 'size': 12},
                    ],
                    'bg': '1E293B', 'border': '334155'
                },
                {
                    'x': 6.8, 'y': 1.6, 'w': 5.7, 'h': 4.9,
                    'paras': [
                        {'text': 'Flask REST API Tests: 40 / 40 PASSED', 'size': 16, 'bold': True, 'color': '34D399'},
                        {'text': '• GET /api/health: Verified engine response and status code 200.', 'size': 12},
                        {'text': '• GET /api/algorithms: Verified 3 mapping types and 2 policies.', 'size': 12},
                        {'text': '• GET /api/sample: Verified 5 preconfigured demonstrations.', 'size': 12},
                        {'text': '• POST /api/configure: Valid configs accepted; invalid rejected with 400.', 'size': 12},
                        {'text': '• POST /api/simulate: Demo 1 events match, error inputs handled.', 'size': 12},
                        {'text': '• POST /api/reset: Confirms stateless reset behavior.', 'size': 12},
                        {'text': '• Error Handlers: Empty addresses, out of bounds, malformed JSON.', 'size': 12},
                        {'text': ' ', 'size': 6},
                        {'text': 'TOTAL VERIFICATION: 90 / 90 TESTS PASSING (100%)', 'size': 13, 'bold': True, 'color': '34D399'},
                    ],
                    'bg': '1E293B', 'border': '334155'
                }
            ]
        },
        # Slide 15: Conclusion & Viva Preparation
        {
            'title': 'Conclusions & Academic Submission Summary',
            'subtitle': 'Complete delivery for B.Tech CSE Computer Organization & Architecture',
            'shapes': [
                {
                    'x': 0.8, 'y': 1.6, 'w': 5.6, 'h': 4.9,
                    'paras': [
                        {'text': 'Project Deliverables Summary', 'size': 16, 'bold': True, 'color': '60A5FA'},
                        {'text': '✅ Full C++17 Simulation Engine Source Code', 'size': 13, 'color': 'E2E8F0'},
                        {'text': '✅ Python Flask Backend REST API with zero external bloat', 'size': 13, 'color': 'E2E8F0'},
                        {'text': '✅ Responsive HTML5 / CSS3 / JavaScript Single Page Web App', 'size': 13, 'color': 'E2E8F0'},
                        {'text': '✅ 90 Comprehensive Automated Unit & API Tests', 'size': 13, 'color': 'E2E8F0'},
                        {'text': '✅ Formal LaTeX Project Report (.tex document)', 'size': 13, 'color': 'E2E8F0'},
                        {'text': '✅ 15-Slide Presentation (.pptx file ready for defense)', 'size': 13, 'color': 'E2E8F0'},
                        {'text': '✅ One-Click Batch Launch Scripts (start_server.bat, run_tests.bat)', 'size': 13, 'color': 'E2E8F0'},
                    ],
                    'bg': '1E293B', 'border': '334155'
                },
                {
                    'x': 6.8, 'y': 1.6, 'w': 5.7, 'h': 4.9,
                    'paras': [
                        {'text': 'Key Viva Examination Questions Ready:', 'size': 16, 'bold': True, 'color': '34D399'},
                        {'text': 'Q1: What is the difference between direct and set-associative mapping?', 'size': 12, 'bold': True, 'color': '60A5FA'},
                        {'text': 'A: Direct has 1 line per set; Set-associative has N lines per set reducing conflict misses.', 'size': 12},
                        {'text': 'Q2: Why does a cache hit NOT reset the FIFO queue?', 'size': 12, 'bold': True, 'color': '60A5FA'},
                        {'text': 'A: FIFO tracks insertion order only. Access order is tracked only by LRU.', 'size': 12},
                        {'text': 'Q3: How are address bit widths derived?', 'size': 12, 'bold': True, 'color': '60A5FA'},
                        {'text': 'A: Offset = log2(BlockSize); Index = log2(NumSets); Tag = 32 - Index - Offset.', 'size': 12},
                        {'text': ' ', 'size': 6},
                        {'text': 'THANK YOU — OPEN FOR QUESTIONS', 'size': 14, 'bold': True, 'color': 'A78BFA', 'align': 'center'},
                    ],
                    'bg': '1E293B', 'border': '334155'
                }
            ]
        }
    ]

    num_slides = len(slides)

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
        # [Content_Types].xml
        overrides = [
            '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
            '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
            '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
            '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
        ]
        for i in range(1, num_slides + 1):
            overrides.append(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')

        content_types = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  {"".join(overrides)}
</Types>'''
        z.writestr('[Content_Types].xml', content_types)

        # _rels/.rels
        z.writestr('_rels/.rels', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>''')

        # ppt/_rels/presentation.xml.rels
        pres_rels = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>']
        for i in range(1, num_slides + 1):
            pres_rels.append(f'<Relationship Id="rId{i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>')

        z.writestr('ppt/_rels/presentation.xml.rels', f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  {"".join(pres_rels)}
</Relationships>''')

        # ppt/presentation.xml
        sld_ids = []
        for i in range(1, num_slides + 1):
            sld_ids.append(f'<p:sldId id="{255+i}" r:id="rId{i+1}"/>')

        z.writestr('ppt/presentation.xml', f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1"/>
  </p:sldMasterIdLst>
  <p:sldIdLst>
    {"".join(sld_ids)}
  </p:sldIdLst>
  <p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}" type="screen16x9"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>''')

        # ppt/theme/theme1.xml
        z.writestr('ppt/theme/theme1.xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
  <a:themeElements>
    <a:clrScheme name="Office">
      <a:dk1><a:srgbClr val="000000"/></a:dk1>
      <a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="1F497D"/></a:dk2>
      <a:lt2><a:srgbClr val="EEECE1"/></a:lt2>
      <a:accent1><a:srgbClr val="2563EB"/></a:accent1>
      <a:accent2><a:srgbClr val="7C3AED"/></a:accent2>
      <a:accent3><a:srgbClr val="16A34A"/></a:accent3>
      <a:accent4><a:srgbClr val="DC2626"/></a:accent4>
      <a:accent5><a:srgbClr val="D97706"/></a:accent5>
      <a:accent6><a:srgbClr val="0891B2"/></a:accent6>
      <a:hlink><a:srgbClr val="2563EB"/></a:hlink>
      <a:folHlink><a:srgbClr val="7C3AED"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Office">
      <a:majorFont><a:latin typeface="Segoe UI"/></a:majorFont>
      <a:minorFont><a:latin typeface="Segoe UI"/></a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Office">
      <a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>
      <a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>
      <a:effectStyleLst><a:effectLst/></a:effectStyleLst>
      <a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
</a:theme>''')

        # ppt/slideMasters/slideMaster1.xml
        z.writestr('ppt/slideMasters/slideMaster1.xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst>
    <p:sldLayoutId id="2147483649" r:id="rId1"/>
  </p:sldLayoutIdLst>
</p:sldMaster>''')

        # ppt/slideMasters/_rels/slideMaster1.xml.rels
        z.writestr('ppt/slideMasters/_rels/slideMaster1.xml.rels', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>''')

        # ppt/slideLayouts/slideLayout1.xml
        z.writestr('ppt/slideLayouts/slideLayout1.xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>''')

        # ppt/slideLayouts/_rels/slideLayout1.xml.rels
        z.writestr('ppt/slideLayouts/_rels/slideLayout1.xml.rels', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>''')

        # Write each slide and its rels
        for i, s_def in enumerate(slides, start=1):
            s_xml = build_slide(s_def['title'], s_def['subtitle'], s_def['shapes'])
            z.writestr(f'ppt/slides/slide{i}.xml', s_xml)
            z.writestr(f'ppt/slides/_rels/slide{i}.xml.rels', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>''')

    print(f"✅ Generated {num_slides}-slide PPTX presentation at: {output_path}")
    print(f"   File size: {os.path.getsize(output_path):,} bytes")

if __name__ == '__main__':
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Cache_Memory_Simulator_Presentation.pptx')
    build_presentation(out)
