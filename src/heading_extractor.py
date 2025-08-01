import re
from collections import Counter, defaultdict
from typing import List, Dict, Callable


def merge_adjacent_headings_by_level(ranked: List[Dict], max_y_gap: float = 5.0) -> List[Dict]:
    """
    Merge consecutive headings (H1/H2/H3) on the same page that are close in vertical (Y) space.
    """
    if not ranked:
        return []

    merged = []
    buffer = []
    
    def flush_buffer():
        if buffer:
            base = buffer[0]
            combined_text = ' '.join([b["text"] for b in buffer])
            merged.append({
                "level": base["level"],
                "text": combined_text.strip(),
                "page": base["page"],
                "x": min(b["x"] for b in buffer),
                "y": min(b["y"] for b in buffer),
                "font_size": max(b.get("font_size", 0) for b in buffer),
            })
            buffer.clear()

    prev = ranked[0]
    buffer.append(prev)

    for curr in ranked[1:]:
        same_level = curr["level"] == prev["level"]
        same_page = curr["page"] == prev["page"]
        vertical_proximity = abs(curr["y"] - prev["y"]) <= (curr.get("font_size") + max_y_gap * 0.5)

        if same_level and same_page and vertical_proximity:
            buffer.append(curr)
        else:
            flush_buffer()
            buffer.append(curr)

        prev = curr

    flush_buffer()
    return merged


def clean_heading_text(text: str) -> str:
    """Lowercase, strips punctuation/numbers for deduplication in level normalization."""
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def fix_heading_spacing(text: str) -> str:
    if not text:
        return text
    # Join single-letter/fragment with followers (for both cases)
    fixed = re.sub(r'\b([A-Z])\s+([A-Za-z]{2,})', r'\1\2', text)
    # Fix remaining C Ourse, D ep etc
    fixed = re.sub(r'\b([A-Z])\s+([a-z]+)', r'\1\2', fixed)
    # Collapse space between short single letters [A B C] → [ABC]
    words = fixed.split()
    buffer = ""
    result_words = []
    for word in words:
        if len(word) == 1 and word.isalpha():
            buffer += word
        else:
            if buffer:
                result_words.append(buffer)
                buffer = ""
            result_words.append(word)
    if buffer:
        result_words.append(buffer)
    return " ".join(result_words)

def clean_text_in_data(data_item: Dict) -> Dict:
    if isinstance(data_item, dict) and "text" in data_item:
        data_item["text"] = fix_heading_spacing(data_item["text"])
    return data_item

def process_data_list(data_list: List[Dict]) -> List[Dict]:
    return [clean_text_in_data(item.copy()) for item in data_list]

############# HEADER/FOOTER FILTERING (frequency-based) #############

def filter_repetitive_headings(
    outline: List[Dict], 
    total_pages: int, 
    threshold: float = 1.0,
    normalize_fn: Callable = None,
) -> List[Dict]:
    if normalize_fn is None:
        normalize_fn = lambda x: re.sub(r'\s+', ' ', x.strip().lower())
    
    text_counts = Counter([normalize_fn(entry["text"]) for entry in outline])
    max_allowed = max(1, int(threshold * total_pages))

    filtered = [
        entry for entry in outline
        if text_counts[normalize_fn(entry["text"])] <= max_allowed
    ]

    return filtered

############# HEADING LEVEL CONSISTENCY #############

def normalize_heading_levels(outline: List[Dict]) -> List[Dict]:
    """
    Make sure duplicate headings always have the same level.
    """
    level_map = defaultdict(list)
    for item in outline:
        norm = clean_heading_text(item["text"])
        level_map[norm].append(item["level"])
    most_common_level = {
        norm: Counter(levels).most_common(1)[0][0]
        for norm, levels in level_map.items()
    }
    for item in outline:
        norm = clean_heading_text(item["text"])
        item["level"] = most_common_level[norm]
    return outline


def preprocess_pdf(pdf_path):
    import fitz  # PyMuPDF
    from ocr_utils import render_page_to_image, is_broken_text

    # Helper: is the inner bbox fully inside outer bbox (with tolerance)?
    def bbox_inside(inner, outer, tol=2):
        ix0, iy0, ix1, iy1 = inner
        ox0, oy0, ox1, oy1 = outer
        return (
            ix0 + tol >= ox0 and iy0 + tol >= oy0 and
            ix1 - tol <= ox1  and iy1 - tol <= oy1
        )

    doc = fitz.open(pdf_path)
    pre_data = []

    for i, page in enumerate(doc):
        # --- Find tables and optionally filter boxes ---
        try:
            tables = page.find_tables()
            table_bboxes = [table.bbox for table in tables.tables]
        except Exception:
            table_bboxes = []
        # Table box post-filtering: exclude very odd/small/huge bboxes
        page_width, page_height = page.rect.width, page.rect.height
        filtered_table_bboxes = []
        for tb in table_bboxes:
            x0, y0, x1, y1 = tb
            width = x1 - x0
            height = y1 - y0
            # Filter: minimum height, max width percent (adjust as needed)
            if height > 40 and width/page_width < 0.98:
                filtered_table_bboxes.append(tb)
        table_bboxes = filtered_table_bboxes

        # --- Extract lines, skip those fully inside table boxes ---
        lines = []
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue

                # --- Break long-spaced spans into multiple virtual lines ---
                virtual_lines = []
                current_line = []
                prev_x1 = None

                for span in spans:
                    x0 = span["bbox"][0]
                    x1 = span["bbox"][2]
                    if prev_x1 is not None and (x0 - prev_x1) > 50:  # gap threshold
                        if current_line:
                            virtual_lines.append(current_line)
                        current_line = [span]
                    else:
                        current_line.append(span)
                    prev_x1 = x1

                if current_line:
                    virtual_lines.append(current_line)

                # --- Now process each virtual line separately ---
                for vspans in virtual_lines:
                    line_text = " ".join([s["text"].strip() for s in vspans])
                    if not line_text.strip():
                        continue

                    x0 = min(s["bbox"][0] for s in vspans)
                    y0 = min(s["bbox"][1] for s in vspans)
                    x1 = max(s["bbox"][2] for s in vspans)
                    y1 = max(s["bbox"][3] for s in vspans)
                    line_bbox = (x0, y0, x1, y1)

                    # --- Skip if inside any table bbox (unless it's a heading-like label) ---
                    in_table = False
                    for tbbox in table_bboxes:
                        if bbox_inside(line_bbox, tbbox, tol=2):
                            avg_font_size = sum(s["size"] for s in vspans) / len(vspans)
                            if (
                                avg_font_size > 12 and
                                line_text.isupper() and
                                len(line_text.split()) <= 5
                            ):
                                continue  # allow this line
                            in_table = True
                            break
                    if in_table:
                        continue

                    # --- Save cleaned line ---
                    lines.append({
                        "text": line_text,
                        "x": x0,
                        "y": y0,
                        "font_size": vspans[0]["size"],
                        "page": i + 1
                    })


        # --- Detect broken text, render page as needed ---
        cleaned_lines = [
            l["text"] for l in lines
            if not re.fullmatch(r'[\.\-\_\*=\s]{6,}', l["text"].strip())
        ]
        page_text = "\n".join(cleaned_lines)
        is_broken = is_broken_text(page_text)
        img = render_page_to_image(page) if is_broken else None

        pre_data.append((i, lines, img, is_broken))

    return pre_data



def extract_headings_hybrid(pdf_path):
    from multiprocessing import Pool
    from parallel_worker import process_page_with_optional_ocr
    from parallel_heading_merger import merge_headings_worker
    from compute_dominant_gaps import compute_dynamic_thresholds_from_raw_lines

    # --- PASS 1: Extract raw lines (parallel) ---
    pre_data = preprocess_pdf(pdf_path)
    args1 = [(i, lines, img, is_broken) for (i, lines, img, is_broken) in pre_data]

    with Pool(8) as pool:
        all_raw_lines_per_page = pool.map(process_page_with_optional_ocr, args1)

    # --- Compute Dynamic Thresholds ---
    thresholds = compute_dynamic_thresholds_from_raw_lines(all_raw_lines_per_page)
    max_y_gap = thresholds["dyn_y_gap"]
    max_x_gap = thresholds["dyn_x_gap"]

    # --- PASS 2: Merge Headings (parallel) ---
    args2 = [(i, raw_lines, max_y_gap, max_x_gap) for i, raw_lines in enumerate(all_raw_lines_per_page)]

    with Pool(8) as pool:
        merged_lists = pool.map(merge_headings_worker, args2)
        

    merged_headings = [heading for page_list in merged_lists for heading in page_list]

    # --- Rank & Post-process ---
    from heading_ranker import rank_all_headings

    ranked = rank_all_headings(merged_headings, debug=False)
    merged = merge_adjacent_headings_by_level(ranked)
    merged.sort(key=lambda r: r["page"])

    outline = []
    title = None
    total_pages = len(all_raw_lines_per_page)

    for heading in merged:
        level = heading["level"]
        text = heading["text"]

        if level.lower() == "title" and not title:
            title = text
        elif level.lower().startswith("h"):
            outline.append({
                "level": level.upper(),
                "text": text,
                "page": heading["page"]
            })

    outline = filter_repetitive_headings(
        outline,
        total_pages=total_pages,
        threshold=0.7,
    )
    outline = normalize_heading_levels(outline)

    return {
        "title": title if title else "Untitled Document",
        "outline": outline
    }
