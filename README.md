# museumVR

Smithsonian 3D API Query Tool (Streamlit app)

This repository contains a small Streamlit application (smithsonian.py) that queries the Smithsonian Institution's 3D API and provides a table-based interface to browse results, download CSVs, and render embeddable 3D previews.

Key features

- Search the Smithsonian 3D API by free-text query.
- Optional API key support for rate-limited endpoints.
- Filter results by file type or model type (GLB, PLY, ZIP, GLTF, STL).
- Paginated results table with selectable rows.
- Download all results or selected rows as CSV.
- Render selected 3D previews in batches using embedded Voyager frames when available.
- Uses Streamlit session state to persist results and preview state.

Files

- smithsonian.py — Main Streamlit application.

Requirements

- Python 3.8+
- Packages: streamlit, requests, pandas

Install

1. Create a virtual environment (recommended):

   python -m venv .venv
   source .venv/bin/activate  # macOS / Linux
   .venv\Scripts\activate     # Windows (PowerShell)

2. Install dependencies:

   pip install streamlit requests pandas

Usage

From the repository root run:

   streamlit run smithsonian.py

When the app opens in your browser you can:

- Enter a search query (e.g. "dinosaur", "apollo"), choose the number of results and an optional filter.
- (Optional) Provide an API key if you have one — the app will pass it to the Smithsonian API.
- Click Search to fetch results. Results are cached per query using Streamlit's cache_data decorator.
- Use the table to select rows you want to preview. The table is paginated; adjust "Table page" to see other rows.
- Click "Render Selected Previews" to enable the preview area. Previews are shown in pages and loaded in batches.
- Download either all results or only the selected rows as CSV files.

Implementation notes

- API endpoint: https://3d-api.si.edu/api/v1.0/content/file/search
- The app uses requests.get(..., timeout=15) and will raise an error on non-2xx responses.
- A small helper, first_url, extracts the first HTTP URL from nested structures returned by the API.
- build_voyager_src converts model identifiers (or full URLs) into embeddable Voyager iframe URLs when possible.
- Results are stored in Streamlit session state under keys "results" and "preview_enabled".
- The table uses st.data_editor so selection state is merged back into the DataFrame before previewing/downloading.
- Preview embedding uses st.components.v1.html with an iframe that points to the Voyager URL if available.

Limitations and tips

- The Smithsonian API enforces rate limits; providing an API key may increase allowed usage.
- Not all items have downloadable files or previewable Voyager models — the UI will indicate when a preview is not available.
- The app currently uses a simple heuristic for the Voyager URL (e.g. prepends https://3d-api.si.edu/voyager/ for package-style identifiers). If the Smithsonian changes their URL patterns, build_voyager_src may need updates.
- For large result sets consider increasing the TABLE_PAGE_SIZE or modifying PREVIEW_BATCH_SIZE in the script.

Contributing

If you'd like to extend this tool, consider:

- Adding authentication and secure storage for API keys.
- Improving error handling and retry logic for transient network errors.
- Adding more robust parsing of model URIs and handling additional file/model types.

No license is included in this repository.
