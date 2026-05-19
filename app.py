import streamlit as st
import pandas as pd
from itertools import combinations
from io import BytesIO
import base64

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Cashfree Reconciliation Suite",
    page_icon="💳",
    layout="wide"
)

# ============================================================
# ADVANCED UI CSS (Merged with Modern Design)
# ============================================================

st.markdown("""
<style>
/* Import Google Font */
@import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,500;14..32,600;14..32,700&display=swap');

/* Main container styling */
.stApp {
    background: linear-gradient(135deg, #f5f7fb 0%, #f0f4fa 100%);
}

.main {
    background-color: transparent;
    font-family: 'Inter', sans-serif;
}

/* Hero Section */
.hero-title {
    background: linear-gradient(135deg, #1A2A3F, #2C3E66);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    letter-spacing: -0.3px;
}

.hero-subtitle {
    color: #5b6e8c;
    font-size: 1rem;
    margin-bottom: 2rem;
}

/* Modern Card Styling */
.modern-card {
    background: rgba(255, 255, 255, 0.98);
    border-radius: 28px;
    padding: 1.5rem;
    box-shadow: 0 12px 30px rgba(0,0,0,0.05);
    border: 1px solid rgba(230, 240, 255, 0.8);
    margin-bottom: 1.5rem;
    transition: transform 0.2s, box-shadow 0.2s;
}

.modern-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 18px 35px rgba(0,0,0,0.08);
}

/* Upload Section */
.upload-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-bottom: 1rem;
}

.upload-box {
    background: white;
    border-radius: 24px;
    padding: 1.8rem;
    text-align: center;
    border: 2px dashed #e0e8f2;
    transition: all 0.2s;
}

.upload-box:hover {
    border-color: #2c7da0;
    background: #fafcff;
}

.upload-icon {
    font-size: 2.5rem;
    color: #2c7da0;
    margin-bottom: 1rem;
}

/* Metric Cards */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

.metric-card {
    background: linear-gradient(135deg, #ffffff, #f8fafd);
    padding: 1.8rem;
    border-radius: 24px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    border: 1px solid #eef2f8;
    transition: all 0.2s;
}

.metric-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}

.metric-icon {
    font-size: 2.2rem;
    margin-bottom: 0.8rem;
}

.metric-title {
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #5e6f8d;
    margin-bottom: 0.5rem;
}

.metric-value {
    font-size: 2.8rem;
    font-weight: 800;
    color: #1e2f41;
    line-height: 1.1;
}

/* Button Styling */
.stButton > button {
    background: linear-gradient(95deg, #1c3f5c, #2c6285);
    border: none;
    color: white;
    font-weight: 600;
    padding: 0.75rem 1.5rem;
    border-radius: 40px;
    font-size: 1rem;
    transition: all 0.2s;
    width: 100%;
    font-family: 'Inter', sans-serif;
}

.stButton > button:hover {
    background: linear-gradient(95deg, #153448, #235574);
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(28,63,92,0.3);
}

/* Selectbox Styling */
.stSelectbox label {
    font-weight: 600;
    color: #2c3e66;
    font-size: 0.85rem;
}

.stSelectbox > div {
    border-radius: 16px;
}

/* DataFrame Styling */
div[data-testid="stDataFrame"] {
    border-radius: 20px;
    overflow: hidden;
    border: 1px solid #e6e6e6;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

/* Expander Styling */
.streamlit-expanderHeader {
    background: #f8fafd;
    border-radius: 12px;
    font-weight: 600;
    color: #2c3e66;
}

/* Download Buttons */
.download-section {
    display: flex;
    gap: 1rem;
    margin-top: 1.5rem;
}

/* Badge Colors */
.exact-badge {
    background: #e1f7e6;
    color: #1e7e34;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.75rem;
}

.split-badge {
    background: #fff1cf;
    color: #b66d0d;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.75rem;
}

.unmatched-badge {
    background: #ffe8e3;
    color: #bc3900;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.75rem;
}

/* Divider */
.custom-divider {
    height: 2px;
    background: linear-gradient(90deg, transparent, #2c7da0, transparent);
    margin: 2rem 0;
}

/* Footer */
.footer {
    text-align: center;
    padding: 2rem;
    color: #8ba0bc;
    font-size: 0.8rem;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HERO SECTION
# ============================================================

st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 class="hero-title">
        <span style="background: linear-gradient(135deg, #1A2A3F, #2C3E66); -webkit-background-clip: text; background-clip: text; color: transparent;">
            💳 Cashfree Reconciliation Studio
        </span>
    </h1>
    <p class="hero-subtitle">
        Smart matching — exact & split reconciliation · Advanced dashboard
    </p>
</div>
""", unsafe_allow_html=True)

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
# FILE UPLOAD SECTION (Modern Grid)
# ============================================================

st.markdown('<div class="upload-container">', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    with st.container():
        st.markdown("""
        <div class="upload-box">
            <div class="upload-icon">📤</div>
            <h3 style="margin-bottom: 1rem;">Cashfree File</h3>
        </div>
        """, unsafe_allow_html=True)
        cashfree_file = st.file_uploader(
            "Upload Cashfree File",
            type=["xlsx", "csv"],
            key="cashfree",
            label_visibility="collapsed"
        )

with col2:
    with st.container():
        st.markdown("""
        <div class="upload-box">
            <div class="upload-icon">📥</div>
            <h3 style="margin-bottom: 1rem;">Internal File</h3>
        </div>
        """, unsafe_allow_html=True)
        acme_file = st.file_uploader(
            "Upload Internal File",
            type=["xlsx", "csv"],
            key="internal",
            label_visibility="collapsed"
        )

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# MAIN PROCESS
# ============================================================

if cashfree_file and acme_file:

    cashfree = read_file(cashfree_file)
    acme = read_file(acme_file)

    st.success("✅ Files Uploaded Successfully")

    # ========================================================
    # COLUMN MAPPING UI (Modern Styled)
    # ========================================================

    with st.container():
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        st.markdown("### 🧩 Column Mapping")
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📊 Cashfree Columns")
            cf_phone_col = st.selectbox(
                "Phone Column",
                cashfree.columns,
                key="cf_phone"
            )
            cf_amount_col = st.selectbox(
                "Amount Column",
                cashfree.columns,
                key="cf_amount"
            )
            cf_date_col = st.selectbox(
                "Date Column",
                cashfree.columns,
                key="cf_date"
            )

        with col2:
            st.markdown("#### 🏢 Internal File Columns")
            ac_phone_col = st.selectbox(
                "Phone Column",
                acme.columns,
                key="ac_phone"
            )
            ac_amount_col = st.selectbox(
                "Amount Column",
                acme.columns,
                key="ac_amount"
            )
            ac_date_col = st.selectbox(
                "Date Column",
                acme.columns,
                key="ac_date"
            )

        st.markdown('</div>', unsafe_allow_html=True)

    # ========================================================
    # AUTO MAPPING BUTTON
    # ========================================================

    start_mapping = st.button(
        "🚀 Start Auto Mapping & Reconciliation",
        type="primary",
        use_container_width=True
    )

    # ========================================================
    # START PROCESS ONLY AFTER BUTTON CLICK
    # ========================================================

    if start_mapping:

        with st.spinner("🔄 Processing reconciliation..."):
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
            # DEBUG DATE CHECK (Collapsible)
            # ====================================================

            with st.expander("🔍 Debug Date Parsing (Click to expand)"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Cashfree Date Preview**")
                    st.dataframe(
                        cashfree[[cf_date_col, "MATCH_DATE"]].head(),
                        use_container_width=True
                    )
                with col2:
                    st.markdown("**Internal Date Preview**")
                    st.dataframe(
                        acme[[ac_date_col, "MATCH_DATE"]].head(),
                        use_container_width=True
                    )

            # ====================================================
            # MATCHING LOGIC
            # ====================================================

            results = []
            exact_match_count = 0
            split_match_count = 0
            unmatched_count = 0

            progress_bar = st.progress(0)
            total_rows = len(cashfree)

            for idx, (_, cf_row) in enumerate(cashfree.iterrows()):
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
                    idx_match = exact_matches.index[0]
                    acme.loc[idx_match, "USED"] = True

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

                # Update progress
                progress_bar.progress((idx + 1) / total_rows)

            # Clear progress bar
            progress_bar.empty()

        # ====================================================
        # FINAL DATAFRAME
        # ====================================================

        final_df = pd.DataFrame(results)

        # ====================================================
        # ADVANCED DASHBOARD (Modern Metrics)
        # ====================================================

        st.markdown('<div class="metric-grid">', unsafe_allow_html=True)

        # Metric 1: Exact Matches
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">✅</div>
            <div class="metric-title">Exact Matches</div>
            <div class="metric-value">{exact_match_count}</div>
        </div>
        """, unsafe_allow_html=True)

        # Metric 2: Split Matches
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🔗</div>
            <div class="metric-title">Split Matches</div>
            <div class="metric-value">{split_match_count}</div>
        </div>
        """, unsafe_allow_html=True)

        # Metric 3: Unmatched
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">❌</div>
            <div class="metric-title">Unmatched Records</div>
            <div class="metric-value">{unmatched_count}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # ====================================================
        # RESULT TABLE
        # ====================================================

        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        st.markdown("### 📄 Reconciliation Results")
        st.markdown("---")

        # Add match type badges for better visualization
        def add_badges(df):
            if not df.empty and "MATCH_TYPE" in df.columns:
                df_display = df.copy()
                df_display["MATCH_TYPE"] = df_display["MATCH_TYPE"].apply(
                    lambda x: f'<span class="{"exact-badge" if x == "EXACT MATCH" else "split-badge" if x == "SPLIT MATCH" else "unmatched-badge"}">{x}</span>'
                )
                return df_display
            return df

        final_df_display = add_badges(final_df)
        st.dataframe(
            final_df,
            use_container_width=True,
            height=500
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # ====================================================
        # EXPORT SECTION
        # ====================================================

        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        st.markdown("### 💾 Export Results")
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                final_df.to_excel(writer, index=False)
            
            st.download_button(
                "📊 Download Excel Report",
                data=output.getvalue(),
                file_name="reconciliation_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col2:
            st.download_button(
                "📄 Download CSV Report",
                data=final_df.to_csv(index=False).encode('utf-8'),
                file_name="reconciliation_output.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

        # ====================================================
        # SUMMARY STATISTICS
        # ====================================================

        with st.expander("📈 Detailed Statistics"):
            total_transactions = len(cashfree)
            matched_total = exact_match_count + split_match_count
            match_rate = (matched_total / total_transactions * 100) if total_transactions > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Transactions", total_transactions)
            with col2:
                st.metric("Matched Transactions", matched_total)
            with col3:
                st.metric("Match Rate", f"{match_rate:.1f}%")

elif cashfree_file or acme_file:
    st.warning("⚠️ Please upload both files (Cashfree and Internal) to proceed.")

# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div class="footer">
    <hr class="custom-divider">
    <p>🔐 Secure Reconciliation • Smart Split Matching • Real-time Processing</p>
    <p style="font-size: 0.7rem;">Cashfree Reconciliation Suite v2.0</p>
</div>
""", unsafe_allow_html=True)
