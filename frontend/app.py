import streamlit as st
import requests
import os

st.set_page_config(page_title="Apex Statutory Engine", page_icon="⚖️", layout="wide")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("⚖️ Apex Statutory & Audit Engine")
st.caption("Deterministic Regulatory Validation & Automated Invoicing Reconciliation")

with st.sidebar:
    st.header("Engine Configuration")
    backend_input = st.text_input("Backend Endpoint", value=BACKEND_URL)
    st.markdown("---")
    st.markdown("**Compliance Scope:**")
    st.markdown("- CGST/SGST/IGST Act Rules\n- Input Tax Credit (ITC) Verification\n- Tolerance: ₹0.00")

uploaded_file = st.file_uploader("Upload Tax Invoice / Statutory Receipt", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file and st.button("Execute Statutory Audit", type="primary"):
    with st.spinner("Parsing document & validating statutory rules..."):
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            res = requests.post(f"{backend_input}/api/v1/audit-invoice", files=files, timeout=60)
            
            if res.status_code != 200:
                st.error(f"Error {res.status_code}: {res.text}")
            else:
                data = res.json()
                
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    status = "✅ PASSED" if data["is_compliant"] else "❌ REJECTED"
                    st.metric("Statutory Status", status)
                with m2:
                    st.metric("Taxable Base", f"₹{data['computed_taxable_total']:,.2f}")
                with m3:
                    st.metric("Computed Tax", f"₹{data['computed_tax_total']:,.2f}")
                with m4:
                    st.metric("Variance Discrepancy", f"₹{data['discrepancy_amount']:,.2f}")

                st.markdown("---")

                issues = data.get("audit_issues", [])
                st.subheader(f"Statutory Audit Findings ({len(issues)})")
                if not issues:
                    st.success("Zero statutory or mathematical infractions found. Safe for ITC claiming and GSTR filing.")
                else:
                    for issue in issues:
                        sev_color = "red" if issue["severity"] == "CRITICAL" else "orange"
                        st.markdown(
                            f":{sev_color}[**[{issue['severity']}] {issue['field']}**]: {issue['message']}  \n"
                            f"*Legal Reference: {issue['statutory_reference']}*"
                        )

                st.markdown("---")
                st.subheader("Reconciled Line Items")
                raw = data.get("raw_extraction", {})
                st.write(f"**Vendor GSTIN:** {raw.get('vendor_gstin')} | **Client GSTIN:** {raw.get('client_gstin')}")
                st.dataframe(raw.get("items", []), use_container_width=True)

        except requests.exceptions.RequestException as e:
            st.error(f"Failed to communicate with backend: {str(e)}")
