from statistics import mode

def compute_dynamic_thresholds_from_raw_lines(all_raw_lines_per_page):
    y_diffs = []
    x_diffs = []
    font_sizes = []

    for lines in all_raw_lines_per_page:
        sorted_lines = sorted(lines, key=lambda l: (l["y"], l["x"]))
        for i in range(1, len(sorted_lines)):
            dy = abs(sorted_lines[i]["y"] - sorted_lines[i - 1]["y"])
            dx = abs(sorted_lines[i]["x"] - sorted_lines[i - 1]["x"])

            if dy > 0:
                y_diffs.append(round(dy, 2))
            if dx > 0:
                x_diffs.append(round(dx, 2))

        font_sizes.extend(round(line["font_size"], 2) for line in lines if "font_size" in line)

    return {
        "dyn_y_gap": mode(y_diffs) if y_diffs else 5,
        "dyn_x_gap": mode(x_diffs) if x_diffs else 5,
        "common_font": mode(font_sizes) if font_sizes else 12
    }
