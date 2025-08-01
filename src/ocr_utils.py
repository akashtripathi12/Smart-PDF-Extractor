from PIL import Image
import io

def is_broken_text(text: str, debug=False):
    if not text or text.strip() == "":
        return True

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    total_chars = sum(len(line.replace(" ", "")) for line in lines)

    # Character ratio stats
    norm_text = ''.join(lines)
    digit_count = sum(c.isdigit() for c in norm_text)
    alpha_count = sum(c.isalpha() for c in norm_text)
    digit_ratio = digit_count / total_chars
    alpha_ratio = alpha_count / total_chars

    if alpha_ratio < 0.75 or digit_ratio > 0.25:
        return True

    return False

def render_page_to_image(page):
    pix = page.get_pixmap(dpi=150)
    mode = "RGB" if pix.alpha == 0 else "RGBA"
    return Image.frombytes(mode, [pix.width, pix.height], pix.samples)

def perform_ocr_data(image: Image.Image, page_num: int = 1):
    import pytesseract
    from pytesseract import Output, image_to_data
    from collections import defaultdict

    data = image_to_data(image, output_type=Output.DICT)
    if not data or "text" not in data:
        return []

    line_map = defaultdict(list)

    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        if text:
            line_num = data["line_num"][i]
            line_map[line_num].append({
                "text": text,
                "left": data["left"][i],
                "top": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i]
            })

    lines = []
    for words in line_map.values():
        line_text = " ".join(w["text"] for w in sorted(words, key=lambda w: w["left"]))
        x = min(w["left"] for w in words)
        y = min(w["top"] for w in words)
        font_size = max(w["height"] for w in words)  # estimate from height

        lines.append({
            "text": line_text,
            "x": x,
            "y": y,
            "font_size": font_size,
            "page_num": page_num
        })

    return lines
