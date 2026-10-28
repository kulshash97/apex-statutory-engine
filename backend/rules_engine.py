import re
from schemas import ComplianceExtraction, VerificationResult, AuditIssue

def validate_gstin_format(gstin: str) -> bool:
    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    return bool(re.match(pattern, gstin.strip()))

def run_statutory_audit(data: ComplianceExtraction) -> VerificationResult:
    issues = []
    
    if not validate_gstin_format(data.vendor_gstin):
        issues.append(AuditIssue(
            severity="CRITICAL",
            field="vendor_gstin",
            message=f"Vendor GSTIN '{data.vendor_gstin}' is syntactically invalid.",
            statutory_reference="Section 25 of CGST Act / Rule 8"
        ))
    if not validate_gstin_format(data.client_gstin):
        issues.append(AuditIssue(
            severity="CRITICAL",
            field="client_gstin",
            message=f"Client GSTIN '{data.client_gstin}' is syntactically invalid.",
            statutory_reference="Section 25 of CGST Act / Rule 8"
        ))

    vendor_state = data.vendor_gstin[:2] if len(data.vendor_gstin) >= 2 else ""
    client_state = data.client_gstin[:2] if len(data.client_gstin) >= 2 else ""
    should_be_interstate = (vendor_state != client_state)

    if should_be_interstate != data.is_interstate:
        issues.append(AuditIssue(
            severity="CRITICAL",
            field="is_interstate",
            message=f"Interstate flag mismatch: Vendor state ({vendor_state}) vs Client state ({client_state}). Expected is_interstate={should_be_interstate}.",
            statutory_reference="Section 7 & 8 of IGST Act"
        ))

    computed_taxable = 0.0
    computed_tax = 0.0
    discrepancy = 0.0

    for idx, item in enumerate(data.items, start=1):
        computed_taxable += item.taxable_amount
        expected_tax = round((item.taxable_amount * item.gst_rate_percent) / 100.0, 2)
        
        if should_be_interstate:
            actual_tax = item.igst
            if item.cgst > 0 or item.sgst > 0:
                issues.append(AuditIssue(
                    severity="CRITICAL",
                    field=f"items[{idx}]",
                    message="Inter-state supplies cannot claim CGST/SGST. Must be booked under IGST.",
                    statutory_reference="Section 5(1) IGST Act"
                ))
        else:
            actual_tax = item.cgst + item.sgst
            half_tax = round(expected_tax / 2.0, 2)
            if abs(item.cgst - half_tax) > 0.05 or abs(item.sgst - half_tax) > 0.05:
                issues.append(AuditIssue(
                    severity="WARNING",
                    field=f"items[{idx}]",
                    message=f"CGST/SGST split deviation. Expected ~{half_tax} each.",
                    statutory_reference="Section 9 CGST Act"
                ))
            if item.igst > 0:
                issues.append(AuditIssue(
                    severity="CRITICAL",
                    field=f"items[{idx}]",
                    message="Intra-state transaction contains IGST.",
                    statutory_reference="Section 9 CGST Act"
                ))

        computed_tax += expected_tax
        discrepancy += abs(actual_tax - expected_tax)

    is_compliant = len([i for i in issues if i.severity == "CRITICAL"]) == 0 and discrepancy < 1.0

    return VerificationResult(
        is_compliant=is_compliant,
        computed_taxable_total=round(computed_taxable, 2),
        computed_tax_total=round(computed_tax, 2),
        discrepancy_amount=round(discrepancy, 2),
        audit_issues=issues,
        raw_extraction=data
    )
