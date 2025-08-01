from heading_merger import merge_candidate_headings

def merge_headings_worker(args):
    page_index, raw_lines, max_y_gap, max_x_gap = args
    merged = merge_candidate_headings(raw_lines, max_y_gap=max_y_gap, max_x_gap=max_x_gap)
    for heading in merged:
        heading["page"] = page_index + 1

    return merged