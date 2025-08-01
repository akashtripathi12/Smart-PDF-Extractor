import re
from collections import defaultdict

def clean_spaced_text(text):
    """Clean spaced text while preserving word boundaries."""
    if not text or not isinstance(text, str):
        return text
    
    original = text.strip()
    if not original:
        return original
    
    # Split into parts
    parts = original.split()
    if len(parts) <= 1:
        return original
    
    # Reconstruct by identifying word boundaries
    result_words = []
    current_word = ""
    
    for i, part in enumerate(parts):
        # If it's a single letter, it's likely part of a spaced word
        if len(part) == 1 and part.isalpha():
            current_word += part
        else:
            # This is a complete part or word fragment
            if len(part) <= 4 and part.isalpha() and current_word:
                # Short fragment likely belongs to current word
                current_word += part
            else:
                # This starts a new word
                if current_word:
                    result_words.append(current_word)
                    current_word = ""
                
                # Check if this part itself needs reconstruction
                if len(part) <= 4 and part.isalpha() and i < len(parts) - 1:
                    # Might be start of a spaced word
                    current_word = part
                else:
                    result_words.append(part)
    
    # Don't forget the last word
    if current_word:
        result_words.append(current_word)
    
    return " ".join(result_words)

# Alternative simpler approach for your specific pattern
def fix_heading_spacing(text):
    """Fix spacing in headings like 'C OURSE O BJECTIVE' -> 'COURSE OBJECTIVE'."""
    if not text:
        return text
    
    # Use regex to find and fix spaced patterns
    # Pattern: single letter + space + letters (word fragment)
    fixed = re.sub(r'\b([A-Z])\s+([A-Z]+)', r'\1\2', text)
    
    
    # Handle remaining single letters followed by lowercase
    fixed = re.sub(r'\b([A-Z])\s+([a-z]+)', r'\1\2', fixed)
    
    # Clean up multiple spaces
    fixed = re.sub(r'\s+', ' ', fixed).strip()
    
    return fixed

def clean_text_in_data(data_item):
    """Clean the text field in a data item (JSON object)."""
    if isinstance(data_item, dict) and "text" in data_item:
        data_item["text"] = fix_heading_spacing(data_item["text"])
    return data_item

def process_data_list(data_list):
    return [clean_text_in_data(item.copy()) for item in data_list]


def merge_candidate_headings(data, max_y_gap, max_x_gap):
    cleaned_data = process_data_list(data)
    
    merged = merge_lines_by_xy(cleaned_data, max_y_gap, max_x_gap)
    merged = merge_lines_by_vertical_blocks(merged, max_y_gap, max_x_gap)

    return merged

# ------------------ Horizontal Line Merge (Same Y) ------------------ #
def merge_lines_by_xy(lines, max_y_gap, max_x_gap):
    y_buckets = defaultdict(list)
    for item in lines:
        y_key = round(item["y"] / max_y_gap)
        y_buckets[y_key].append(item)

    merged_output = []

    def smart_stitch_fragments(fragments):
        result = ""
        seen = set()

        def find_overlap(a, b):
            """Return the length of the max overlap where b starts with end of a."""
            max_overlap = 0
            min_len = min(len(a), len(b))
            for i in range(1, min_len + 1):
                if a[-i:] == b[:i]:
                    max_overlap = i
            return max_overlap

        for frag in fragments:
            if not frag or "text" not in frag or frag["text"] is None:
                continue

            text = frag["text"].strip()
        
            if not text or text in seen:
                continue

            seen.add(text)

            if not result:
                result = text
                continue

            overlap_len = find_overlap(result, text)

            if overlap_len > 0:
                result += text[overlap_len:]
            else:
                if result[-1:].islower() and text[0].islower():
                    result += text
                else:
                    result += " " + text

        result = re.sub(r'\s+', ' ', result)
        return result.strip()


    for group in y_buckets.values():
        sorted_group = sorted(group, key=lambda x: x["x"])
        filtered_group = [item for item in sorted_group if item["text"].strip()]
        if not filtered_group:
            continue
        base = filtered_group[0]
        stitched_text = smart_stitch_fragments(filtered_group)
        merged_output.append({
            "text": stitched_text,
            "x": base["x"],
            "y": base["y"],
            "font_size": base["font_size"],
            "page": base["page"]
        })

    return merged_output

# ------------------ Vertical Block Merge (Same X + Font Size) ------------------ #
def merge_lines_by_vertical_blocks(lines, max_y_gap, max_x_gap):
    x_font_buckets = defaultdict(list)
    for item in lines:
        x_key = round(item["x"] / (max_x_gap + 2))
        fs_key = round(item["font_size"], 1)
        bucket_key = (x_key, fs_key)
        x_font_buckets[bucket_key].append(item)

    merged_output = []

    def smart_stitch_fragments(fragments):
        result = ""
       
        for frag in fragments:
            text = frag["text"].strip()
            if re.search(r'[\.\-\_\*=\s]{3,}', line["text"].strip()):
                continue
            if not text:
                continue
            if text in result:
                continue
            max_overlap = 0
            min_len = min(len(text), len(result))
            for i in range(1, min_len + 1):
                if result.endswith(text[:i]):
                    max_overlap = i
            new_part = text[max_overlap:]
            if new_part and new_part in result:
                continue
            result += " " + new_part
        result = re.sub(r'(\b\w{3,}?)\1{2,}', r'\1', result)
        return result.strip()

    def flush_group(group):
        if not group:
            return
        stitched_text = smart_stitch_fragments(group)
        base = group[0]
        merged_output.append({
            "text": stitched_text,
            "x": base["x"],
            "y": base["y"],
            "font_size": base["font_size"],
            "page": base["page"]
        })

    for (_, _), group in x_font_buckets.items():
        sorted_group = sorted(group, key=lambda x: x["y"])
        curr_group = []
        prev_y = None

        for line in sorted_group:
            if re.search(r'[\.\-\_\*=\s]{3,}', line["text"].strip()):
                continue
            if not curr_group:
                curr_group.append(line)
                prev_y = line["y"]
            else:
                gap = abs(line["y"] - prev_y)

                # Merge if y-gap is small OR font size is large (likely heading)
                if gap <= (max_y_gap + max_y_gap * 0.2) :
                    curr_group.append(line)
                    prev_y = line["y"]
                else:
                    flush_group(curr_group)
                    curr_group = [line]
                    prev_y = line["y"]

        flush_group(curr_group)

    return merged_output
