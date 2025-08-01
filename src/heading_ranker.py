from typing import List, Dict, Tuple
import re

def extract_possible_heading(text: str) -> str:
    bullet_heading = re.match(r"^[\u2022\-\*•]\s*([^:]+?)\s*:\s*(.*)", text)
    if bullet_heading:
        heading = bullet_heading.group(1).strip()
        return heading
    return text

def _calculate_statistics(data: List[float]) -> Tuple[float, float, float]:
    if not data:
        return 0.0, 0.0, 0.0

    max_value = max(data)
    sum_data = sum(data)
    count_data = len(data)
    
    mean_value = sum_data / count_data

    if count_data > 1:
        sum_sq_diff = sum([(x - mean_value) ** 2 for x in data])
        std_dev = (sum_sq_diff / (count_data - 1)) ** 0.5
    else:
        std_dev = 0.0
        
    return max_value, mean_value, std_dev

def rank_all_headings(lines: List[Dict], debug=False) -> List[Dict]:
    font_sizes = [line["font_size"] for line in lines if line.get("font_size") is not None]
    
    if not font_sizes:
        return []

    max_font, font_mean, font_std = _calculate_statistics(font_sizes)

    # unique_sorted is not directly used in the threshold calculations,
    # but kept for future implementation
    unique_sorted = sorted(set(font_sizes), reverse=True) 

    title_threshold = max_font
    h1_threshold = max_font - 0.5 * font_mean
    h2_threshold = font_mean + 0.2 * font_std
    h3_threshold = font_mean - font_mean * 0.2

    lines_sorted = sorted(lines, key=lambda x: (x["page"], x.get("y", float("inf"))))
    y_by_page = {}
    for line in lines_sorted:
        y_by_page.setdefault(line["page"], []).append(line)

    ranked = []
    title_assigned = False

    for page, page_lines in y_by_page.items():
        for idx, line in enumerate(page_lines):
            text = line.get("text", "").strip()
            font_size = line.get("font_size")
            x = line.get("x", 0)
            y = line.get("y", 0)
            
            

            if not text or font_size is None:
                continue
            
            heading_candidate = extract_possible_heading(text)
            # For caution, only replace with heading_candidate if shortening
            text = heading_candidate if len(heading_candidate) < len(text) else text

            if len(text) > 120 or len(text.split()) > 15:
                continue
            
            # Normalize trailing punctuation if safe
            if text.strip().endswith('.') and re.match(r'.*\b(Inc|Ltd|Co|etc)\.$', text):
                text = text.rstrip('.')
                
            if re.search(r'[-–—()]?\s*\d+\s*of\s*\d+', text):  # e.g., "- 4 of 9", "(2 of 10)"
                continue

            if re.search(r'page\s*\d+', text):  # e.g., "Page 3"
                continue

            if re.search(r'[-–—]\s*\d+\s*$', text):  # e.g., "- 4" at end
                continue

            if re.match(r'^\d+\s*/\s*\d+\s*$', text):  # e.g., "3/9"
                continue

            if re.fullmatch(r'\(?\s*\d+\s*\)?', text):  # e.g., "5", "(6)"
                continue
            
            if re.search(r'[\.\-\_\*=\s]{3,}', text):
                continue

            words = text.strip().split()
            if text.strip().endswith(';'):
                continue
            
            if text.strip().endswith('.') and len(words) == 1 and len(text.strip()) <= 12:
                continue

            if not (text[0].isupper() or text[0].isdigit()) and len(text) >= 10:
                continue

            if re.match(r'^\d{1,2}([/-])\d{1,2}([/-])\d{2,4}$', text):
                continue
            if re.match(r'^[A-Z][a-z]+\s\d{1,2},\s\d{4}$', text):
                continue

            if re.search(r'page\s*\d+', text.lower()):
                continue

            if re.search(r'\b\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?\b', text):
                continue
            if re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2},? \d{2,4}\b', text, re.IGNORECASE):
                continue
            if re.search(r'\b(19|20)\d{2}\b', text) and len(text.strip().split()) <= 3:
                continue

            if re.search(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', text):
                continue

            if re.search(r'http[s]?://', text, re.IGNORECASE) or 'www.' in text.lower():
                continue

            if len(text.strip()) < 3 and re.match(r'^\s*(\d{1,3}|[a-zA-Z])[\.\)]?\s*$', text.strip()):
                continue

            common_verbs = r"\b(is|are|was|were|be|being|been|will|shall|have|has|had|should|would|could|may|might|must|do|does|did)\b"
            if len(text.split()) > 12 and re.search(common_verbs, text, flags=re.IGNORECASE):
                continue
            
            if len(text.split()) >= 2 and re.search(r'\b(Board|Tel|Committee|Version|Organization|Published|©|All rights reserved)\b', text, re.I):
                continue
            
            if re.search(r'\b(Tel|Phone|Fax|Email|E-mail|Signature|Location|Class|Room)\b', text, re.I):
                continue
            
            if re.match(r"(?i)^\s*\d{1,2}:\d{2}\s*(AM|PM|–|-|to)?\s*\d{1,2}:\d{2}", text):
                continue
            
            if re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text):  # phone number pattern
                continue
                
            stripped_text = re.sub(r'[^A-Za-z0-9 ]', '', text).strip()
            tokens = stripped_text.split()
            if (
                len(stripped_text.replace(" ", "")) <= 4
                or (0 < len(tokens) <= 3 and all(len(tok) <= 2 for tok in tokens))
            ):
                continue

            level = None

            if not title_assigned and abs(font_size - title_threshold) < 0.1:
                level = "Title"
                title_assigned = True
            elif font_size >= h1_threshold:
                level = "H1"
            elif font_size >= h2_threshold:
                level = "H2"
            elif font_size >= h3_threshold:
                level = "H3"
            else:
                continue

            ranked.append({
                "text": text,
                "level": level,
                "page": page,
                "font_size": font_size,
                "x": x,
                "y": y
            })
            

    return ranked