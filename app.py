import streamlit as st
import pandas as pd
from itertools import combinations
from io import BytesIO

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Cashfree Reconciliation",
    layout="wide"
)

# ============================================================
# ADVANCED UI CSS
# ============================================================

st.markdown("""
<style>

.main {
    background-color: #f5f7fb;
}

.metric-card {
    background: linear-gradient(135deg, #ffffff, #f0f2f6);
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.08);
    text-align: center;
    margin-bottom: 10px;
}

.metric-title {
    font-size: 18px;
    color: #555;
    font-weight: 600;
}

.metric-value {
    font-size: 38px;
    font-weight: 700;
    color: #111;
}

.stButton>button {
    width: 100%;
    border-radius: 10px;
    height: 50px;
    font-size: 18px;
    font-weight: bold;
}

div[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid #e6e6e6;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# TITLE
# ============================================================

st.title("💳 Cashfree vs Internal File Reconciliation Dashboard")

# ============================================================
# HELPERS
# ============================================================

def read_file(uploaded_file):
    if uploaded_file.name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)

def clean_mobile(x):
    try:
        x = str(x)
        x = x.replace(".0", "").replace(" ", "").replace("-", "").replace("+91", "")
        x = ''.join(filter(str.isdigit, x))

        if len(x) > 10:
            x = x[-10:]

        return x
    except:
        return ""

def clean_amount(x):
    try:
        return round(float(x), 2)
    except:
        return 0.0

def clean_date(x):
    try:
        return pd.to_datetime(
            x,
            dayfirst=True,
            errors="coerce"
        ).date()
    except:
        return None

# ============================================================
# FILE UPLOAD
# ============================================================

cashfree_file = st.file_uploader(
    "📤 Upload Cashfree File",
    type=["xlsx", "csv"]
)

acme_file = st.file_uploader(
    "📤 Upload Internal File",
    type=["xlsx", "csv"]
)

# ============================================================
# MAIN PROCESS
# ============================================================

if cashfree_file and acme_file:

    cashfree = read_file(cashfree_file)
    acme = read_file(acme_file)

    st.success("✅ Files Uploaded Successfully")

    # ========================================================
    # COLUMN MAPPING UI
    # ========================================================

    st.subheader("🧩 Column Mapping")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### Cashfree Columns")

        cf_phone_col = st.selectbox(
            "Phone Column",
            cashfree.columns
        )

        cf_amount_col = st.selectbox(
            "Amount Column",
            cashfree.columns
        )

        cf_date_col = st.selectbox(
            "Date Column",
            cashfree.columns
        )

    with col2:

        st.markdown("### Internal File Columns")

        ac_phone_col = st.selectbox(
            "Phone Column ",
            acme.columns
        )

        ac_amount_col = st.selectbox(
            "Amount Column ",
            acme.columns
        )

        ac_date_col = st.selectbox(
            "Date Column ",
            acme.columns
        )

    # ========================================================
    # AUTO MAPPING BUTTON
    # ========================================================

    start_mapping = st.button(
        "🚀 Start Auto Mapping",
        type="primary"
    )

    # ========================================================
    # START PROCESS ONLY AFTER BUTTON CLICK
    # ========================================================

    if start_mapping:

        # ====================================================
        # STANDARDIZE DATA
        # ====================================================

        cashfree["Customer Phone"] = cashfree[
            cf_phone_col
        ].apply(clean_mobile)

        acme["mobile"] = acme[
            ac_phone_col
        ].apply(clean_mobile)

        cashfree["Amount"] = cashfree[
            cf_amount_col
        ].apply(clean_amount)

        acme["payment_amount"] = acme[
            ac_amount_col
        ].apply(clean_amount)

        cashfree["MATCH_DATE"] = cashfree[
            cf_date_col
        ].apply(clean_date)

        acme["MATCH_DATE"] = acme[
            ac_date_col
        ].apply(clean_date)

        acme["USED"] = False

        # ====================================================
        # DEBUG DATE CHECK
        # ====================================================

        with st.expander("🔍 Debug Date Parsing"):

            st.write(
                cashfree[
                    [cf_date_col, "MATCH_DATE"]
                ].head()
            )

            st.write(
                acme[
                    [ac_date_col, "MATCH_DATE"]
                ].head()
            )

        # ====================================================
        # MATCHING LOGIC
        # ====================================================

        results = []

        exact_match_count = 0
        split_match_count = 0
        unmatched_count = 0

        for _, cf_row in cashfree.iterrows():

            phone = cf_row["Customer Phone"]
            amount = cf_row["Amount"]
            date = cf_row["MATCH_DATE"]

            matched = False

            # =================================================
            # EXACT MATCH
            # =================================================

            exact_matches = acme[
                (acme["mobile"] == phone) &
                (acme["payment_amount"] == amount) &
                (acme["MATCH_DATE"] == date) &
                (acme["USED"] == False)
            ]

            if not exact_matches.empty:

                idx = exact_matches.index[0]

                acme.loc[idx, "USED"] = True

                merged = {}

                for col in cashfree.columns:
                    merged[f"CF_{col}"] = cf_row[col]

                for col in acme.columns:
                    merged[f"INTERNAL_{col}"] = exact_matches.iloc[0][col]

                merged["MATCH_TYPE"] = "EXACT MATCH"

                results.append(merged)

                exact_match_count += 1

                matched = True

            # =================================================
            # SPLIT MATCH
            # =================================================

            if not matched:

                candidates = acme[
                    (acme["mobile"] == phone) &
                    (acme["MATCH_DATE"] == date) &
                    (acme["USED"] == False)
                ]

                indices = list(candidates.index)

                found_combo = None

                for r in range(2, min(6, len(indices) + 1)):

                    for combo in combinations(indices, r):

                        total = round(
                            acme.loc[
                                list(combo),
                                "payment_amount"
                            ].sum(),
                            2
                        )

                        if total == amount:

                            found_combo = combo
                            break

                    if found_combo:
                        break

                if found_combo:

                    acme.loc[
                        list(found_combo),
                        "USED"
                    ] = True

                    for _, row in acme.loc[
                        list(found_combo)
                    ].iterrows():

                        merged = {}

                        for col in cashfree.columns:
                            merged[f"CF_{col}"] = cf_row[col]

                        for col in acme.columns:
                            merged[f"INTERNAL_{col}"] = row[col]

                        merged["MATCH_TYPE"] = "SPLIT MATCH"

                        results.append(merged)

                    split_match_count += 1

                    matched = True

            # =================================================
            # UNMATCHED
            # =================================================

            if not matched:

                merged = {}

                for col in cashfree.columns:
                    merged[f"CF_{col}"] = cf_row[col]

                merged["MATCH_TYPE"] = "UNMATCHED"

                results.append(merged)

                unmatched_count += 1

        # ====================================================
        # FINAL DATAFRAME
        # ====================================================

        final_df = pd.DataFrame(results)

        # ====================================================
        # ADVANCED DASHBOARD
        # ====================================================

        st.subheader("📊 Advanced Dashboard")

        c1, c2, c3 = st.columns(3)

        with c1:

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">
                    ✅ Exact Matches
                </div>
                <div class="metric-value">
                    {exact_match_count}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c2:

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">
                    🔗 Split Matches
                </div>
                <div class="metric-value">
                    {split_match_count}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c3:

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">
                    ❌ Unmatched
                </div>
                <div class="metric-value">
                    {unmatched_count}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # ====================================================
        # RESULT TABLE
        # ====================================================

        st.subheader("📄 Reconciliation Result")

        st.dataframe(
            final_df,
            use_container_width=True,
            height=600
        )

        # ====================================================
        # EXPORT
        # ====================================================

        output = BytesIO()

        with pd.ExcelWriter(
            output,
            engine="xlsxwriter"
        ) as writer:

            final_df.to_excel(
                writer,
                index=False
            )

        st.download_button(
            "⬇ Download Excel",
            data=output.getvalue(),
            file_name="reconciliation_output.xlsx"
        )

        st.download_button(
            "⬇ Download CSV",
            data=final_df.to_csv(index=False).encode(),
            file_name="reconciliation_output.csv"
        )