from heading_extractor import extract_headings_hybrid
import time
import json
import os

# Define the primary input directory and the fallback directory
PRIMARY_INPUT_DIR = "/app/input"
FALLBACK_INPUT_DIR = "/app/sample_dataset/pdfs"

# Define the primary output directory and the fallback output directory
PRIMARY_OUTPUT_DIR = "/app/output"
FALLBACK_OUTPUT_DIR = "/app/sample_dataset/outputs"


def get_dirs_to_use():
    """
    Determines the correct input and output directories to use.
    It prioritizes primary directories. If primary input is used, primary output
    is also prioritized. If fallback input is used, fallback output is also used,
    ensuring primary and fallback directories are never combined.
    """
    use_primary_set = False

    if os.path.isdir(PRIMARY_INPUT_DIR):
        pdf_files_in_primary = [
            f for f in os.listdir(PRIMARY_INPUT_DIR) if f.lower().endswith(".pdf")
        ]
        if pdf_files_in_primary:
            use_primary_set = True

    if use_primary_set:
        print(f"Using primary input directory: {PRIMARY_INPUT_DIR}")
        print(f"Using primary output directory: {PRIMARY_OUTPUT_DIR}")
        return PRIMARY_INPUT_DIR, PRIMARY_OUTPUT_DIR
    else:
        print(
            f"Falling back to sample dataset directory for input: {FALLBACK_INPUT_DIR}"
        )
        print(
            f"Falling back to sample dataset directory for output: {FALLBACK_OUTPUT_DIR}"
        )
        return FALLBACK_INPUT_DIR, FALLBACK_OUTPUT_DIR


def process_all_pdfs():
    """
    Processes all PDF files found in the determined input directory
    and saves the output to the determined output directory.
    """
    input_dir_to_use, output_dir_to_use = get_dirs_to_use()

    # Ensure the output directory exists
    os.makedirs(output_dir_to_use, exist_ok=True)

    pdf_files = [
        f for f in os.listdir(input_dir_to_use) if f.lower().endswith(".pdf")
    ]

    if not pdf_files:
        print(f"No PDF files found in {input_dir_to_use}. Exiting.")
        return

    for pdf_file in pdf_files:
        input_path = os.path.join(input_dir_to_use, pdf_file)
        base_name = os.path.splitext(pdf_file)[0]
        output_path = os.path.join(output_dir_to_use, f"{base_name}.json")

        try:
            print(f"\n[+] Processing: {pdf_file}")
            start = time.perf_counter()

            result = extract_headings_hybrid(input_path)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            end = time.perf_counter()
            elapsed = end - start
            print(f"[✓] Saved to: {output_path}  ⏱ {elapsed:.2f} seconds")

        except Exception as e:
            print(f"[!] Failed to process {pdf_file}: {e}")


if __name__ == "__main__":
    process_all_pdfs()