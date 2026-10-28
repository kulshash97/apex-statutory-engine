from pydantic import BaseModel, Field
from typing import List, Optional

class InvoiceItem(BaseModel):
    description: str
    hsn_sac_code: Optional[str] = Field(default=None, description="Harmonized System of Nomenclature code")
    taxable_amount: float = Field(..., ge=0.0)
    gst_rate_percent: float = Field(..., ge=0.0, le=28.0)
    cgst: float = 0.0
    sgst: float = 0.0
    igst: float = 0.0

class ComplianceExtraction(BaseModel):
    vendor_gstin: str = Field(..., description="15-character GSTIN")
    client_gstin: str = Field(..., description="15-character GSTIN")
    invoice_number: str
    invoice_date: str
    is_interstate: bool
    items: List[InvoiceItem]

class AuditIssue(BaseModel):
    severity: str
    field: str
    message: str
    statutory_reference: str

class VerificationResult(BaseModel):
    is_compliant: bool
    computed_taxable_total: float
    computed_tax_total: float
    discrepancy_amount: float
    audit_issues: List[AuditIssue]
    raw_extraction: ComplianceExtraction
