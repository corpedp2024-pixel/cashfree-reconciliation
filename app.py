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
        elif len(x) < 10 and len(x) > 0:
            # Handle cases where leading zeros might be missing
            x = x.zfill(10)

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
        # Try multiple date formats
        if pd.isna(x):
            return None
        
        # If it's already a datetime
        if isinstance(x, (pd.Timestamp, pd.datetime)):
            return x.date()
        
        # Try different formats
        for date_format in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"]:
            try:
                return pd.to_datetime(x, format=date_format).date()
            except:
                continue
        
        # Last resort - let pandas infer
        return pd.to_datetime(x, dayfirst=True, errors="coerce").date()
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
    
    # Show sample data
    with st.expander("📊 Preview Uploaded Data"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Cashfree File (First 5 rows)**")
            st.dataframe(cashfree.head())
        with col2:
            st.write("**Internal File (First 5 rows)**")
            st.dataframe(acme.head())

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
    
    # Matching tolerance options
    st.subheader("⚙️ Matching Settings")
    
    match_settings = st.columns(3)
    with match_settings[0]:
        amount_tolerance = st.number_input(
            "Amount Tolerance (₹)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.5,
            help="Allow small differences in amount (e.g., 0.5 for 50 paise difference)"
        )
    
    with match_settings[1]:
        date_tolerance_days = st.number_input(
            "Date Tolerance (Days)",
            min_value=0,
            max_value=30,
            value=1,
            help="Allow date differences within X days"
        )
    
    with match_settings[2]:
        enable_split_matching = st.checkbox(
            "Enable Split Matching",
            value=True,
            help="Match one Cashfree transaction with multiple internal transactions"
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

        with st.spinner("Processing reconciliation..."):
            
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

            # Remove rows with missing critical data
            cashfree_clean = cashfree[
                (cashfree["Customer Phone"] != "") & 
                (cashfree["Amount"] > 0)
            ].copy()
            
            acme_clean = acme[
                (acme["mobile"] != "") & 
                (acme["payment_amount"] > 0)
            ].copy()

            # ====================================================
            # DEBUG DATE CHECK
            # ====================================================

            with st.expander("🔍 Debug Data Processing"):
                st.write("**Cashfree Processed Data Sample:**")
                st.dataframe(cashfree_clean[[cf_phone_col, cf_amount_col, cf_date_col, "Customer Phone", "Amount", "MATCH_DATE"]].head())
                
                st.write("**Internal Processed Data Sample:**")
                st.dataframe(acme_clean[[ac_phone_col, ac_amount_col, ac_date_col, "mobile", "payment_amount", "MATCH_DATE"]].head())

            # ====================================================
            # MATCHING LOGIC (IMPROVED)
            # ====================================================

            results = []

            exact_match_count = 0
            fuzzy_match_count = 0
            split_match_count = 0
            unmatched_count = 0

            for idx, cf_row in cashfree_clean.iterrows():

                phone = cf_row["Customer Phone"]
                amount = cf_row["Amount"]
                date = cf_row["MATCH_DATE"]

                matched = False

                # =================================================
                # 1. EXACT MATCH (All fields match exactly)
                # =================================================

                exact_matches = acme_clean[
                    (acme_clean["mobile"] == phone) &
                    (acme_clean["payment_amount"] == amount) &
                    (acme_clean["MATCH_DATE"] == date) &
                    (acme_clean["USED"] == False)
                ]

                if not exact_matches.empty:

                    idx_match = exact_matches.index[0]

                    acme_clean.loc[idx_match, "USED"] = True

                    merged = {}

                    for col in cashfree.columns:
                        merged[f"CF_{col}"] = cf_row[col]

                    for col in acme.columns:
                        merged[f"INTERNAL_{col}"] = exact_matches.iloc[0][col]

                    merged["MATCH_TYPE"] = "EXACT MATCH"
                    merged["MATCH_SCORE"] = "100%"

                    results.append(merged)

                    exact_match_count += 1
                    matched = True

                # =================================================
                # 2. FUZZY MATCH (With tolerance)
                # =================================================

                if not matched and (amount_tolerance > 0 or date_tolerance_days > 0):
                    
                    # Find candidates with phone match
                    fuzzy_candidates = acme_clean[
                        (acme_clean["mobile"] == phone) &
                        (acme_clean["USED"] == False)
                    ]
                    
                    if not fuzzy_candidates.empty:
                        
                        best_match = None
                        best_score = 0
                        
                        for candidate_idx, candidate in fuzzy_candidates.iterrows():
                            score = 0
                            
                            # Check amount difference
                            amount_diff = abs(candidate["payment_amount"] - amount)
                            if amount_diff <= amount_tolerance:
                                score += 50
                            
                            # Check date difference
                            if date and candidate["MATCH_DATE"]:
                                date_diff = abs((date - candidate["MATCH_DATE"]).days)
                                if date_diff <= date_tolerance_days:
                                    score += 50
                            elif not date and not candidate["MATCH_DATE"]:
                                score += 50  # Both have no date
                            
                            if score > best_score:
                                best_score = score
                                best_match = candidate_idx
                        
                        if best_match and best_score >= 70:  # At least 70% match
                            acme_clean.loc[best_match, "USED"] = True
                            
                            merged = {}
                            for col in cashfree.columns:
                                merged[f"CF_{col}"] = cf_row[col]
                            for col in acme.columns:
                                merged[f"INTERNAL_{col}"] = acme_clean.loc[best_match, col]
                            
                            merged["MATCH_TYPE"] = "FUZZY MATCH"
                            merged["MATCH_SCORE"] = f"{best_score}%"
                            
                            results.append(merged)
                            fuzzy_match_count += 1
                            matched = True

                # =================================================
                # 3. SPLIT MATCH (If enabled)
                # =================================================

                if not matched and enable_split_matching:

                    candidates = acme_clean[
                        (acme_clean["mobile"] == phone) &
                        (acme_clean["USED"] == False)
                    ]

                    # Apply date tolerance for split matching
                    if date_tolerance_days > 0 and date:
                        candidates = candidates[
                            candidates["MATCH_DATE"].apply(
                                lambda x: abs((date - x).days) <= date_tolerance_days if pd.notna(x) else False
                            )
                        ]

                    indices = list(candidates.index)

                    found_combo = None

                    # Limit combinations for performance
                    max_split = min(10, len(indices))
                    
                    for r in range(2, max_split + 1):
                        
                        # Only check if r is reasonable (max 3-4 splits typically)
                        if r > 5:
                            break
                            
                        for combo in combinations(indices, r):

                            total = round(
                                acme_clean.loc[
                                    list(combo),
                                    "payment_amount"
                                ].sum(),
                                2
                            )

                            # Check amount with tolerance
                            if abs(total - amount) <= amount_tolerance:
                                found_combo = combo
                                break

                        if found_combo:
                            break

                    if found_combo:

                        acme_clean.loc[
                            list(found_combo),
                            "USED"
                        ] = True

                        for _, row in acme_clean.loc[
                            list(found_combo)
                        ].iterrows():

                            merged = {}

                            for col in cashfree.columns:
                                merged[f"CF_{col}"] = cf_row[col]

                            for col in acme.columns:
                                merged[f"INTERNAL_{col}"] = row[col]

                            merged["MATCH_TYPE"] = "SPLIT MATCH"
                            merged["MATCH_SCORE"] = "N/A"

                            results.append(merged)

                        split_match_count += 1
                        matched = True

                # =================================================
                # 4. UNMATCHED
                # =================================================

                if not matched:

                    merged = {}

                    for col in cashfree.columns:
                        merged[f"CF_{col}"] = cf_row[col]

                    merged["MATCH_TYPE"] = "UNMATCHED"
                    merged["MATCH_SCORE"] = "0%"

                    results.append(merged)

                    unmatched_count += 1

            # ====================================================
            # FIND ORPHANED INTERNAL TRANSACTIONS
            # ====================================================
            
            orphaned = acme_clean[acme_clean["USED"] == False].copy()
            
            for _, row in orphaned.iterrows():
                merged = {}
                for col in acme.columns:
                    merged[f"INTERNAL_{col}"] = row[col]
                merged["MATCH_TYPE"] = "ORPHANED (Not in Cashfree)"
                merged["MATCH_SCORE"] = "0%"
                results.append(merged)

            # ====================================================
            # FINAL DATAFRAME
            # ====================================================

            final_df = pd.DataFrame(results)

            # ====================================================
            # ADVANCED DASHBOARD
            # ====================================================

            st.subheader("📊 Reconciliation Dashboard")
            
            total_matched = exact_match_count + fuzzy_match_count + split_match_count
            total_cf_transactions = len(cashfree_clean)
            orphaned_count = len(orphaned)
            
            match_percentage = (total_matched / total_cf_transactions * 100) if total_cf_transactions > 0 else 0

            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric("✅ Exact Matches", exact_match_count)
            
            with col2:
                st.metric("🟡 Fuzzy Matches", fuzzy_match_count)
            
            with col3:
                st.metric("🔗 Split Matches", split_match_count)
            
            with col4:
                st.metric("❌ Unmatched", unmatched_count)
            
            with col5:
                st.metric("📊 Match Rate", f"{match_percentage:.1f}%")

            st.divider()
            
            # Summary statistics
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"💰 **Cashfree Total Amount:** ₹{cashfree_clean['Amount'].sum():,.2f}")
            with col2:
                st.info(f"💰 **Internal Total Amount:** ₹{acme_clean['payment_amount'].sum():,.2f}")

            # ====================================================
            # RESULT TABLE WITH FILTERS
            # ====================================================

            st.subheader("📄 Reconciliation Result")
            
            # Add filters
            filter_type = st.multiselect(
                "Filter by Match Type",
                options=final_df["MATCH_TYPE"].unique(),
                default=final_df["MATCH_TYPE"].unique()
            )
            
            filtered_df = final_df[final_df["MATCH_TYPE"].isin(filter_type)]
            
            st.dataframe(
                filtered_df,
                use_container_width=True,
                height=500
            )

            # ====================================================
            # EXPORT
            # ====================================================

            st.subheader("💾 Export Results")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                output = BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    filtered_df.to_excel(writer, index=False, sheet_name="Reconciliation")
                    
                    # Add summary sheet
                    summary_data = {
                        "Metric": ["Exact Matches", "Fuzzy Matches", "Split Matches", "Unmatched", "Orphaned", "Match Rate", "Cashfree Total", "Internal Total"],
                        "Value": [exact_match_count, fuzzy_match_count, split_match_count, unmatched_count, orphaned_count, f"{match_percentage:.1f}%", 
                                 f"₹{cashfree_clean['Amount'].sum():,.2f}", f"₹{acme_clean['payment_amount'].sum():,.2f}"]
                    }
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, index=False, sheet_name="Summary")
                
                st.download_button(
                    "📊 Download Excel Report",
                    data=output.getvalue(),
                    file_name="reconciliation_report.xlsx",
                    type="primary"
                )
            
            with col2:
                st.download_button(
                    "📄 Download CSV",
                    data=filtered_df.to_csv(index=False).encode(),
                    file_name="reconciliation_output.csv"
                )
            
            with col3:
                st.download_button(
                    "📋 Download Unmatched Only",
                    data=filtered_df[filtered_df["MATCH_TYPE"] == "UNMATCHED"].to_csv(index=False).encode(),
                    file_name="unmatched_transactions.csv"
                )

else:
    st.info("👈 Please upload both Cashfree and Internal files to begin reconciliation")
