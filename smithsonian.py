import streamlit as st
import requests
import math
import pandas as pd

# ================== CONFIG ==================
st.set_page_config(
    page_title="Smithsonian 3D API Query Tool",
    layout="wide"
)

API_BASE_URL = "https://3d-api.si.edu/api/v1.0/content/file/search"
TABLE_PAGE_SIZE = 25
PREVIEW_BATCH_SIZE = 9

# Session keys (SAFE – no collisions)
KEY_RESULTS = "results"
KEY_PREVIEW_ENABLED = "preview_enabled"

# ================== HELPERS ==================
@st.cache_data(show_spinner=False)
def query_api(params: dict):
    r = requests.get(API_BASE_URL, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def first_url(value):
    if not value:
        return None
    if isinstance(value, (list, tuple)):
        for v in value:
            u = first_url(v)
            if u:
                return u
    if isinstance(value, dict):
        for k in ("uri", "url", "href"):
            if k in value:
                return first_url(value[k])
    if isinstance(value, str):
        for p in value.replace(",", " ").split():
            if p.startswith("http://") or p.startswith("https://"):
                return p
    return None

def build_voyager_src(model_url):
    if not model_url:
        return None
    if isinstance(model_url, (list, tuple)):
        model_url = model_url[0]
    if not isinstance(model_url, str):
        return None
    model_url = model_url.strip()
    if model_url.startswith("3d_package:"):
        return f"https://3d-api.si.edu/voyager/{model_url}"
    if model_url.startswith("http"):
        return model_url
    if ":" in model_url:
        return f"https://3d-api.si.edu/voyager/{model_url}"
    return None

# ================== SIDEBAR ==================
st.sidebar.header("API Settings")

api_key = st.sidebar.text_input("API Key (optional)", type="password")
rows = st.sidebar.number_input(
    "Number of results",
    min_value=1,
    max_value=1000,
    value=100,
    step=25
)
type_filter = st.sidebar.selectbox(
    "Filter by Type",
    [
        "all",
        "file_type:glb",
        "file_type:ply",
        "file_type:zip",
        "model_type:gltf",
        "model_type:stl"
    ]
)

# ================== MAIN ==================
st.title("Smithsonian 3D API Query Tool")

query = st.text_input("Search query:", placeholder="e.g. dinosaur, apollo")

if st.button("Search", type="primary"):
    if not query.strip():
        st.warning("Please enter a search query.")
    else:
        params = {"q": query, "rows": rows}
        if api_key:
            params["api_key"] = api_key
        if type_filter != "all":
            k, v = type_filter.split(":", 1)
            params[k] = v

        with st.spinner("Fetching results..."):
            try:
                data = query_api(params)
                st.session_state[KEY_RESULTS] = data.get("rows", [])
                st.session_state[KEY_PREVIEW_ENABLED] = False
                st.success(f"Fetched {len(st.session_state[KEY_RESULTS])} results.")
            except Exception as e:
                st.error(f"API error: {e}")

# ================== TABLE ==================
if st.session_state.get(KEY_RESULTS):
    items = st.session_state[KEY_RESULTS]

    records = []
    for idx, item in enumerate(items):
        c = item.get("content", {}) or {}

        draco = c.get("draco_compressed")
        draco_str = (
            "True" if draco is True else
            "False" if draco is False else
            "N/A"
        )

        records.append({
            "Select": False,
            "Index": idx,
            "Title": str(item.get("title", "Untitled")),
            "File Type": str(c.get("file_type", "N/A")),
            "Quality": str(c.get("quality", "N/A")),
            "Usage": str(c.get("usage", "N/A")),
            "Draco": draco_str,
            "Download": str(first_url(c.get("uri")) or "")
        })

    df = pd.DataFrame(records)

    # ---------- Paging ----------
    total_rows = len(df)
    total_pages = max(1, math.ceil(total_rows / TABLE_PAGE_SIZE))
    table_page = st.number_input(
        "Table page",
        min_value=1,
        max_value=total_pages,
        value=1
    )

    start = (table_page - 1) * TABLE_PAGE_SIZE
    end = start + TABLE_PAGE_SIZE

    st.subheader("Results (check rows to preview)")

    edited_df = st.data_editor(
        df.iloc[start:end],
        width="stretch",
        hide_index=True,
        column_config={
            "Select": st.column_config.CheckboxColumn(),
            "Index": st.column_config.NumberColumn(disabled=True),
            "Download": st.column_config.LinkColumn("Download")
        }
    )

    # Merge checkbox state back
    df.loc[start:end - 1, "Select"] = edited_df["Select"].values

    selected_indices = df[df["Select"]]["Index"].tolist()

    st.info(f"Selected items: {len(selected_indices)}")

    # ---------- Downloads ----------
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download all results (CSV)",
            df.drop(columns=["Select"]).to_csv(index=False),
            file_name="smithsonian_results_all.csv"
        )
    with col2:
        st.download_button(
            "Download selected (CSV)",
            df[df["Select"]].drop(columns=["Select"]).to_csv(index=False),
            file_name="smithsonian_results_selected.csv"
        )

    # ================== PREVIEW ==================
    if st.button("Render Selected Previews"):
        st.session_state[KEY_PREVIEW_ENABLED] = True

    if st.session_state.get(KEY_PREVIEW_ENABLED) and selected_indices:
        total_preview_pages = max(
            1, math.ceil(len(selected_indices) / PREVIEW_BATCH_SIZE)
        )

        preview_page = st.number_input(
            "Preview page",
            min_value=1,
            max_value=total_preview_pages,
            value=1
        ) - 1

        subset = selected_indices[
            preview_page * PREVIEW_BATCH_SIZE:
            (preview_page + 1) * PREVIEW_BATCH_SIZE
        ]

        st.subheader(
            f"3D Previews (Page {preview_page + 1} of {total_preview_pages})"
        )

        for i in range(0, len(subset), 3):
            cols = st.columns(3)
            for col, idx in zip(cols, subset[i:i + 3]):
                with col:
                    item = items[idx]
                    c = item.get("content", {}) or {}

                    title = item.get("title", "Untitled")
                    dl = first_url(c.get("uri"))
                    src = build_voyager_src(c.get("model_url"))

                    st.markdown(f"**{title}**")

                    if src:
                        st.components.v1.html(
                            f"""
                            <div style="position:relative;padding-bottom:66.66%;height:0;">
                              <iframe src="{src}"
                                style="position:absolute;top:0;left:0;width:100%;height:100%;border:none;"
                                loading="lazy"></iframe>
                            </div>
                            """,
                            height=360
                        )
                    else:
                        st.info("Preview not available")

                    if dl:
                        st.markdown(f"[Download file]({dl})")

                    with st.expander("Details"):
                        st.json(item)
else:
    st.info("Enter a query and click Search.")
