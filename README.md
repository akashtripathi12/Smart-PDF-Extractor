# PDF Outline Extractor

A robust solution for extracting structured outlines (titles and headings) from PDF documents for the Adobe Hackathon Challenge 1A.

Team Details:

1. [Akash Tripathi](https://www.linkedin.com/in/akashtripathi122004/)
2. [Arihant Yadav](https://www.linkedin.com/in/arihant-yadav-07a7a5289/)
3. [Nilanjan Mitra](https://www.linkedin.com/in/nilanjanbmitra/)

## Approach

1. **Text Extraction**

   - Uses **PyMuPDF** to extract text along with positional metadata (`text`, `x`, `y`, `font_size`).
   - Falls back to **Tesseract OCR** when PDF structure is broken or text extraction fails (e.g., scanned documents).
   - Applies smart **clubbing of adjacent lines/fragments** using spatial heuristics (gap thresholds) to handle broken extractions.
   - Produces **clean, consistent metadata** that forms the basis for reliable heading detection.

   > _Future Enhancements:_ Plan to include richer metadata (e.g., font name, font weight) from PyMuPDF to further improve heading distinction and merging accuracy.

2. **Heading Ranking System**

   - Analyzes text metadata with **20+ heuristics** including:
     - Font size prominence
     - Relative positioning
     - Text patterns (using regex)
     - Line spacing and horizontal alignment
   - Applies normalization and de-duplication to ensure headings are **consistently ranked and distributed** throughout the document.

3. **Hierarchical Classification**
   - Classifies detected headings into **H1, H2, H3** levels.
   - Maintains **document hierarchy** and logical flow.
   - Uses relative font size trends and layout structure to infer heading levels.

### Performance Optimizations

- Fast and reliable text extraction using **PyMuPDF**, with fallback to **OCR** only when necessary.
- Single-pass processing for large documents
- Optimized merging logic using spatial clustering and frequency-based filters.
- Minimal memory overhead and efficient use of standard Python data structures.
- Fully **containerized via Docker** for reproducibility and deployment.

## Models and Libraries Used

- **PyMuPDF (v1.23.14)** – High-performance PDF parsing.
- **Pytesseract** – OCR fallback engine.
- **Python Standard Library** – `json`, `re`, `collections`, `time`, `statistics`, `pathlib`, etc.
- **No ML models used** – Fully **rule-based approach** for maximum transparency and control.

## Build and Run Instructions

### Docker Build

```bash
docker build --platform linux/amd64 -t pdf-processor .
```

### Docker Run

```bash
# For Linux
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-processor
```

```bash
# For Windows
docker run --rm -v "${PWD}/input:/app/input" -v "${PWD}/output:/app/output" --network none pdf-processor
```

## Structure of the Code

```
Adobe-1A/
├── app/
│   ├── input/         # Input PDF files
│   └── output/        # JSON files provided as outputs.
├── src/
|   ├── compute_dominant_gaps.py
│   ├── heading_extractor.py
|   ├── heading_merger.py
|   ├── heading_ranker.py
|   ├── ocr_utils.py
|   ├── parallel_heading_merger.py
|   ├── parallel_worker.py
│   └── main.py
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── README.md
```

### Local Development

You need to have the following installed:

1. [uv](https://docs.astral.sh/uv/)
2. [python](https://www.python.org/)
3. [tesseract](https://github.com/tesseract-ocr/tesseract?tab=readme-ov-file#installing-tesseract)

For installing dependencies and running the project:

```bash
uv run poe setup
uv run poe start
```

## Performance Results

- Test PDF: `/sample_dataset/pdfs/file03.pdf`
- Number of Pages: 14
- Processing Time: 1.44 seconds
- Accuracy: 85 % - 90 %

## Key Features

1.  Robust Detection: Handles various PDF layouts and formatting styles
2.  Fast Processing: Well under 10-second constraint for 50-page documents
3.  Hierarchical Classification: Proper H1/H2/H3 level assignment
4.  Error Handling: Graceful handling of malformed PDFs
5.  Offline Operation: No network dependencies
6.  Docker Support: Containerized for consistent environments

Output Format (schema listed under `sample_dataset/schema/output_schema.json`)

```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Main Heading",
      "page": 1
    },
    {
      "level": "H2",
      "text": "Sub Heading",
      "page": 2
    }
  ]
}
```

## Constraints Compliance

- ✅ Execution time: ≤ 10 seconds for 50-page PDF
- ✅ Model size: N/A (rule-based approach)
- ✅ Network: No internet access required
- ✅ Runtime: CPU-only on AMD64 architecture
- ✅ Memory: < 16GB RAM usage

## Future Enhancements

- Multi-language support for international documents
- Machine learning integration for improved accuracy
- Support for additional document formats
- Advanced layout analysis for complex documents
