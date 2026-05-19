import streamlit as st
import pandas as pd
from itertools import combinations
from io import BytesIO

st.set_page_config(page_title="Cashfree Reconciliation", layout="wide")
st.title("💳 Cashfree vs Acme Reconciliation Dashboard")

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

cashfree_file = st.file_uploader("📤 Upload Cashfree File", type=["xlsx", "csv"])
acme_file = st.file_uploader("📤 Upload Acme File", type=["xlsx", "csv"])

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
        cf_phone_col = st.selectbox("Phone Column", cashfree.columns)
        cf_amount_col = st.selectbox("Amount Column", cashfree.columns)
        cf_date_col = st.selectbox("Date Column", cashfree.columns)

    with col2:
        st.markdown("### Acme Columns")
        ac_phone_col = st.selectbox("Phone Column ", acme.columns)
        ac_amount_col = st.selectbox("Amount Column ", acme.columns)
        ac_date_col = st.selectbox("Date Column ", acme.columns)

    # ========================================================
    # STANDARDIZE DATA (DYNAMIC)
    # ========================================================

    cashfree["Customer Phone"] = cashfree[cf_phone_col].apply(clean_mobile)
    acme["mobile"] = acme[ac_phone_col].apply(clean_mobile)

    cashfree["Amount"] = cashfree[cf_amount_col].apply(clean_amount)
    acme["payment_amount"] = acme[ac_amount_col].apply(clean_amount)

    cashfree["MATCH_DATE"] = cashfree[cf_date_col].apply(clean_date)
    acme["MATCH_DATE"] = acme[ac_date_col].apply(clean_date)

    acme["USED"] = False

    # ========================================================
    # DEBUG DATE CHECK
    # ========================================================

    with st.expander("🔍 Debug Date Parsing"):
        st.write(cashfree[[cf_date_col, "MATCH_DATE"]].head())
        st.write(acme[[ac_date_col, "MATCH_DATE"]].head())

    # ========================================================
    # MATCHING LOGIC (UNCHANGED)
    # ========================================================

    results = []
    exact_match_count = 0
    split_match_count = 0
    unmatched_count = 0

    for _, cf_row in cashfree.iterrows():

        phone = cf_row["Customer Phone"]
        amount = cf_row["Amount"]
        date = cf_row["MATCH_DATE"]

        matched = False

        # EXACT MATCH
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
                merged[f"ACME_{col}"] = exact_matches.iloc[0][col]

            merged["MATCH_TYPE"] = "EXACT MATCH"
            results.append(merged)

            exact_match_count += 1
            matched = True

        # SPLIT MATCH
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
                    if round(acme.loc[list(combo), "payment_amount"].sum(), 2) == amount:
                        found_combo = combo
                        break
                if found_combo:
                    break

            if found_combo:
                acme.loc[list(found_combo), "USED"] = True

                for _, row in acme.loc[list(found_combo)].iterrows():
                    merged = {}
                    for col in cashfree.columns:
                        merged[f"CF_{col}"] = cf_row[col]
                    for col in acme.columns:
                        merged[f"ACME_{col}"] = row[col]

                    merged["MATCH_TYPE"] = "SPLIT MATCH"
                    results.append(merged)

                split_match_count += 1
                matched = True

        # UNMATCHED
        if not matched:
            merged = {}
            for col in cashfree.columns:
                merged[f"CF_{col}"] = cf_row[col]

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
    st.dataframe(final_df, use_container_width=True, height=600)

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
