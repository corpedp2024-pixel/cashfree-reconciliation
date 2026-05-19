import streamlit as st
import pandas as pd
from itertools import combinations
from io import BytesIO

st.set_page_config(page_title="Payment Reconciliation", layout="wide")
st.title("💳 External vs Internal Payment Reconciliation Dashboard")

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
        return pd.to_datetime(x, dayfirst=True, errors="coerce").date()
    except:
        return None

# ============================================================
# FILE UPLOAD
# ============================================================

external_file = st.file_uploader(
    "📤 Upload External Payment File",
    type=["xlsx", "csv"]
)

internal_file = st.file_uploader(
    "📤 Upload Internal Payment File",
    type=["xlsx", "csv"]
)

# ============================================================
# MAIN PROCESS
# ============================================================

if external_file and internal_file:

    external_payment = read_file(external_file)
    internal_payment = read_file(internal_file)

    st.success("✅ Files Uploaded Successfully")

    # ========================================================
    # COLUMN MAPPING UI
    # ========================================================

    st.subheader("🧩 Column Mapping")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### External Payment Columns")
        ext_phone_col = st.selectbox("Phone Column", external_payment.columns)
        ext_amount_col = st.selectbox("Amount Column", external_payment.columns)
        ext_date_col = st.selectbox("Date Column", external_payment.columns)

    with col2:
        st.markdown("### Internal Payment Columns")
        int_phone_col = st.selectbox("Phone Column ", internal_payment.columns)
        int_amount_col = st.selectbox("Amount Column ", internal_payment.columns)
        int_date_col = st.selectbox("Date Column ", internal_payment.columns)

    # ========================================================
    # STANDARDIZE DATA
    # ========================================================

    external_payment["Customer Phone"] = external_payment[ext_phone_col].apply(clean_mobile)
    internal_payment["mobile"] = internal_payment[int_phone_col].apply(clean_mobile)

    external_payment["Amount"] = external_payment[ext_amount_col].apply(clean_amount)
    internal_payment["payment_amount"] = internal_payment[int_amount_col].apply(clean_amount)

    external_payment["MATCH_DATE"] = external_payment[ext_date_col].apply(clean_date)
    internal_payment["MATCH_DATE"] = internal_payment[int_date_col].apply(clean_date)

    internal_payment["USED"] = False

    # ========================================================
    # DEBUG DATE CHECK
    # ========================================================

    with st.expander("🔍 Debug Date Parsing"):
        st.write(external_payment[[ext_date_col, "MATCH_DATE"]].head())
        st.write(internal_payment[[int_date_col, "MATCH_DATE"]].head())

    # ========================================================
    # MATCHING LOGIC
    # ========================================================

    results = []
    exact_match_count = 0
    split_match_count = 0
    unmatched_count = 0

    for _, ext_row in external_payment.iterrows():

        phone = ext_row["Customer Phone"]
        amount = ext_row["Amount"]
        date = ext_row["MATCH_DATE"]

        matched = False

        # EXACT MATCH
        exact_matches = internal_payment[
            (internal_payment["mobile"] == phone) &
            (internal_payment["payment_amount"] == amount) &
            (internal_payment["MATCH_DATE"] == date) &
            (internal_payment["USED"] == False)
        ]

        if not exact_matches.empty:

            idx = exact_matches.index[0]
            internal_payment.loc[idx, "USED"] = True

            merged = {}

            for col in external_payment.columns:
                merged[f"EXT_{col}"] = ext_row[col]

            for col in internal_payment.columns:
                merged[f"INT_{col}"] = exact_matches.iloc[0][col]

            merged["MATCH_TYPE"] = "EXACT MATCH"

            results.append(merged)

            exact_match_count += 1
            matched = True

        # SPLIT MATCH
        if not matched:

            candidates = internal_payment[
                (internal_payment["mobile"] == phone) &
                (internal_payment["MATCH_DATE"] == date) &
                (internal_payment["USED"] == False)
            ]

            indices = list(candidates.index)
            found_combo = None

            for r in range(2, min(6, len(indices) + 1)):

                for combo in combinations(indices, r):

                    if round(
                        internal_payment.loc[list(combo), "payment_amount"].sum(),
                        2
                    ) == amount:

                        found_combo = combo
                        break

                if found_combo:
                    break

            if found_combo:

                internal_payment.loc[list(found_combo), "USED"] = True

                for _, row in internal_payment.loc[list(found_combo)].iterrows():

                    merged = {}

                    for col in external_payment.columns:
                        merged[f"EXT_{col}"] = ext_row[col]

                    for col in internal_payment.columns:
                        merged[f"INT_{col}"] = row[col]

                    merged["MATCH_TYPE"] = "SPLIT MATCH"

                    results.append(merged)

                split_match_count += 1
                matched = True

        # UNMATCHED
        if not matched:

            merged = {}

            for col in external_payment.columns:
                merged[f"EXT_{col}"] = ext_row[col]

            merged["MATCH_TYPE"] = "UNMATCHED"

            results.append(merged)

            unmatched_count += 1

    final_df = pd.DataFrame(results)

    # ========================================================
    # DASHBOARD
    # ========================================================

    st.subheader("📊 Dashboard")

    c1, c2, c3 = st.columns(3)

    c1.metric("✅ Exact Matches", exact_match_count)
    c2.metric("🔗 Split Matches", split_match_count)
    c3.metric("❌ Unmatched", unmatched_count)

    st.divider()

    # ========================================================
    # TABLE
    # ========================================================

    st.subheader("📄 Reconciliation Result")

    st.dataframe(
        final_df,
        use_container_width=True,
        height=600
    )

    # ========================================================
    # EXPORT
    # ========================================================

    output = BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        final_df.to_excel(writer, index=False)

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
