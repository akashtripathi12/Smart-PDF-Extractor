def process_page_with_optional_ocr(args):
    page_index, raw_lines, image, is_broken = args
    page_number = page_index + 1

    if is_broken and image:
        from ocr_utils import perform_ocr_data

        ocr_words = perform_ocr_data(image)
        if ocr_words:
            for line in ocr_words:
                raw_lines.append({
                    "text": line["text"],
                    "x": line["x"],
                    "y": line["y"],
                    "font_size": line["font_size"],
                    "page": page_number
                })

    return raw_lines