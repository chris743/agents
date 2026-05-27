from agents import function_tool
from typing import Optional
from pydantic import BaseModel

class DebitRow(BaseModel):
    certificate_number: str
    date: Optional[str]
    debit_amount: Optional[float]
    

def match_debit_row(
    current_certificate_number: str,
    debit_rows: list[DebitRow]
    ) -> dict:
    def norm(value: str) -> str:
        return value.strip().replace(" ", ""). replace("-", "").upper()
    
    target = norm(current_certificate_number)
    
    for row in debit_rows:
        row_cert = row.get("certificate_number", "")
        if norm(row_cert) == target:
            return {
                "matched": True,
                "current_certificate_number": current_certificate_number,
                "matched_certificate_number": row_cert,
                "date": row.get("date"),
                "debit_amount": row.get("debit_amount"),
                "reason": "Exact certificate match found"
            }
            
    return {
        "matched": False,
        "current_certificate_number": current_certificate_number,
        "matched_certificate_number": None,
        "date": None,
        "debit_amount": None,
        "reason": "No Exact Match found"
    }