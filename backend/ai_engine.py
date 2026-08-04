import re

CLAUSES = {
    "Confidentiality": ["confidential", "confidentiality", "non-disclosure", "nda"],
    "Termination": ["termination", "terminate", "terminated"],
    "Notice Period": ["notice period", "30 days notice", "60 days notice", "notice"],
    "Payment Terms": ["payment", "salary", "rent", "fee", "amount payable", "inr", "rs.", "salary of"],
    "Security Deposit": ["security deposit", "deposit"],
    "Maintenance": ["maintenance"],
    "Warranty": ["warranty"],
    "Liability": ["liability", "liable"],
    "Indemnity": ["indemnity", "indemnify"],
    "Force Majeure": ["force majeure", "force-majeure"],
    "Arbitration": ["arbitration"],
    "Governing Law": ["governing law", "jurisdiction"],
    "Intellectual Property": ["intellectual property", "copyright", "patent"],
    "Renewal": ["renewal", "renew"],
    "Non-Compete": ["non compete", "non-compete"],
    "Probation": ["probation"],
    "Working Hours": ["working hours", "office hours"],
    "Leave Policy": ["leave", "annual leave", "vacation"],
    "Insurance": ["insurance", "benefits"],
    "Penalty": ["penalty", "fine"],
    "Capital Contribution": ["capital contribution", "capital invested", "initial investment", "capital of the firm", "contribution"],
    "Bank Account": ["bank account", "account number", "bank details", "account of the firm", "banking information","Bank accounts"],
    "Books of Accounts": ["books of accounts", "accounting records", "financial statements", "ledger", "account books","books of account"],
    "GST Compliance": ["gst", "goods and services tax", "tax compliance","income tax","tax returns","gst compliance"],
    "Dissolution": ["dissolution", "dissolve", "termination of partnership", "winding up", "partnership termination","dissolution of partnership","dissolved"],
    "Managing Partner": ["managing partner", "partner in charge", "partner responsible", "partner managing the firm","managing partners"],
    "expenses": ["expenses", "operating expenses", "business expenses", "costs", "expenditure","expenses of the firm"],
    "admission of new partners": ["admission of new partners", "admitting new partners"],
    "employment of staff": ["employment of staff", "hiring employees", "staff employment", "employee hiring","employment of employees"],
    "duration": ["duration", "term of partnership", "partnership term", "length of partnership","duration of the partnership"],
}

def _clean_text(text):
    # remove common markdown/bullet artifacts so regexes don't capture section numbers or bullets
    text = re.sub(r"\*+", "", text)               # remove asterisks/bold markers
    text = re.sub(r"•", "-", text)                # normalize bullets
    text = re.sub(r"^\s*\d+\.\s*", "", text, flags=re.MULTILINE)  # remove leading section numbers like "3."
    return text

def detect_clauses(text):
    found = []
    txt = text.lower()
    for clause, keywords in CLAUSES.items():
        for kw in keywords:
            if kw in txt:
                found.append(clause)
                break
    return found

def extract_clause_details(text, clause_name):
   

    if clause_name == "Payment Terms":
        keywords = [
            "salary",
            "monthly salary",
            "salary of",
            "remuneration",
            "compensation",
            "payment",
            "rent",
            "fee",
            "amount payable",
            "inr",
            "rs."
        ]
    else:
        keywords = CLAUSES.get(clause_name, [clause_name])

    lines = text.splitlines()
    for i, line in enumerate(lines):
        for kw in keywords:
            if kw.lower() in line.lower():
                detail = line.strip()
                # include a few following lines for context
                if i + 1 < len(lines):
                    detail += " " + lines[i + 1].strip()
                if i + 2 < len(lines):
                    detail += " " + lines[i + 2].strip()
                return detail
    return "Not Found"

def _extract_parties(text):
    txt = _clean_text(text)

    # Partnership - prefer explicit "NAME OF PARTNERSHIP FIRM" or a heading followed by firm name
    if re.search(r"\bPARTNERSHIP\b|\bDEED OF PARTNERSHIP\b", txt, re.IGNORECASE):
            m = re.search(r"NAME OF PARTNERSHIP FIRM\s*(?:SHALL BE)?\s*[:\-]?\s*(?P<firm>[^\n]+)", txt, re.IGNORECASE)
            if m:
                firm = m.group("firm").strip()
                firm = re.sub(r"\s+firm$", "", firm, flags=re.IGNORECASE).strip()
            if not firm:
                # fallback: find the first title-case line that looks like a firm name
                lines = [l.strip() for l in txt.splitlines() if l.strip()]
                for ln in lines[:40]:
                    if len(ln.split()) <= 6 and re.search(r"(Traders|Industries|Technologies|Enterprises|Private|Limited|LLP|Co\.|Company|Firm)", ln, re.IGNORECASE):
                        firm = ln.strip()
                        break
            # partners - capture Mr/Ms blocks with PAN if present
            partners = []
            for m in re.finditer(r"(Mr\.|Ms\.|Mrs\.)\s*([A-Z][A-Za-z'`\-\s]+)[\.,\n].*?PAN\s*Number\s*[:\-]?\s*([A-Z0-9]+)", txt, re.IGNORECASE | re.DOTALL):
                partners.append(f"{m.group(2).strip()} (PAN {m.group(3)})")
            if not partners:
                # simple fallback: names appearing in first section
                for m in re.finditer(r"(Mr\.|Ms\.|Mrs\.)\s*([A-Z][A-Za-z'`\-\s]+)", txt[:2000], re.IGNORECASE):
                    partners.append(m.group(2).strip())
            if not partners:
                partners = ["Not Found"]
            return {"type": "Partnership Deed", "firm": (firm or "Not Found"), "partners": partners}

    # Employment
    if re.search(r"\bEMPLOYMENT AGREEMENT\b|\bEMPLOYER\b.*\bEMPLOYEE\b", txt, re.IGNORECASE):
        m_employer = re.search(r"(?P<employer>[A-Z][A-Za-z0-9&,\.\- ]{3,}?(?:Private Limited|Limited|LLP|Company|Technologies|Enterprises|Inc\.))", txt)
        employer = m_employer.group("employer").strip() if m_employer else "Not Found"
        m_employee = re.search(r"(Mr\.|Ms\.|Mrs\.)\s*(?P<employee>[A-Z][A-Za-z'\.\- ]+?),\s*(?:Employee ID\s*(?P<id>[A-Z0-9\-]+))", txt, re.IGNORECASE)
        if m_employee:
            employee = f"{m_employee.group('employee').strip()} (ID {m_employee.group('id').strip()})"
        else:
            m_emp2 = re.search(r"(?P<employee>[A-Z][A-Za-z'\.\- ]+?)\s*,\s*hereinafter referred to as the\s*\"Employee\"", txt, re.IGNORECASE | re.DOTALL)
            employee = m_emp2.group("employee").strip() if m_emp2 else "Not Found"
        return {"type": "Employment Agreement", "party_a": employer, "party_b": employee}

     # Lease Agreement
    if re.search(r"\bLEASE AGREEMENT\b", txt, re.IGNORECASE):

    # LESSOR
      m_lessor = re.search(
        r"by\s+and\s+between:\s*(?:Sri|Mr\.|Mrs\.|Ms\.)\s+([A-Za-z ]+),",
        txt,
        re.IGNORECASE,
    )
      
      if m_lessor:
        lessor = "Sri " + m_lessor.group(1).strip()
      else:
        lessor = "Not Found"

    # LESSEE
      m_lessee = re.search(
        r"AND\s+(?:Sri|Mr\.|Mrs\.|Ms\.)\s+([A-Za-z ]+),",
        txt,
        re.IGNORECASE,
    )

      if m_lessee:
        lessee = "Sri " + m_lessee.group(1).strip()
      else:
        lessee = "Not Found"

      return {
        "type": "Lease Agreement",
        "party_a": lessor,
        "party_b": lessee,
    }
    # Service Agreement - try BETWEEN ... AND ... block or Provider/Client labels
    # Service Agreement
    if re.search(r"\bSERVICE AGREEMENT\b", txt, re.IGNORECASE):

      m_client = re.search(
        r"by\s+and\s+between:\s*([A-Za-z0-9 &]+?Private Limited)",
        txt,
        re.IGNORECASE,
    )

      m_provider = re.search(
        r"AND\s*([A-Za-z0-9 &]+?Private Limited)",
        txt,
        re.IGNORECASE,
    )

      client = m_client.group(1).strip() if m_client else "Not Found"
      provider = m_provider.group(1).strip() if m_provider else "Not Found"

      return {
        "type": "Service Agreement",
        "party_a": client,
        "party_b": provider,
    }

    # Generic fallback by keywords
    if "employee" in txt.lower() or "employer" in txt.lower() or "salary" in txt.lower():
        m_em = re.search(r"(Employer|Company)\s*[:\-]?\s*(?P<c>.+)", txt, re.IGNORECASE)
        m_emp = re.search(r"(Employee)\s*[:\-]?\s*(?P<p>.+)", txt, re.IGNORECASE)
        return {"type": "Employment Agreement", "party_a": (m_em.group("c").strip() if m_em else "Not Found"), "party_b": (m_emp.group("p").strip() if m_emp else "Not Found")}

    return {"type": "Unknown Agreement", "party_a": "Not Found", "party_b": "Not Found"}

def _extract_dates(text):
    txt = _clean_text(text)

    start = "Not Found"
    end = "Not Found"

    # Format: 15/08/2026
    dates = re.findall(r"\b(\d{1,2}/\d{1,2}/\d{4})\b", txt)
    if len(dates) >= 2:
        return dates[0], dates[1]
    elif len(dates) == 1:
        start = dates[0]

    # Format: Start Date: 01 August 2026
    m_start = re.search(
        r"(?:Start Date|Effective Date|Commencement Date)\s*[:\-]?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
        txt,
        re.IGNORECASE,
    )
    if m_start:
        start = m_start.group(1)

    # Format: commence on 01 August 2026
    if start == "Not Found":
        m_start = re.search(
            r"commence(?:s|d)?\s+on\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
            txt,
            re.IGNORECASE,
        )
        if m_start:
            start = m_start.group(1)

    # Format: made and executed on this 15th day of August, 2026
    if start == "Not Found":
        s = re.search(
            r"(\d{1,2})(?:st|nd|rd|th)?\s+day\s+of\s+([A-Za-z]+),?\s+(\d{4})",
            txt,
            re.IGNORECASE,
        )
        if s:
            start = f"{s.group(1)} {s.group(2)} {s.group(3)}"

    # Partnership at Will
    if "partnership at will" in txt.lower():
        end = "Not Specified (Partnership at Will)"
    else:

        # Service Agreement:
        # remain valid until 31 July 2027
        m_end = re.search(
            r"valid\s+until\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
            txt,
            re.IGNORECASE,
        )
        if m_end:
            end = m_end.group(1)

        # Completion Date: 31 July 2027
        if end == "Not Found":
            m_end = re.search(
                r"Completion Date\s*[:\-]?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
                txt,
                re.IGNORECASE,
            )
            if m_end:
                end = m_end.group(1)

        # End Date / Expiry Date / Termination Date
        if end == "Not Found":
            m_end = re.search(
                r"(?:End Date|Expiry Date|Termination Date|Expires On|Expire On)\s*[:\-]?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
                txt,
                re.IGNORECASE,
            )
            if m_end:
                end = m_end.group(1)

    return start, end
def _extract_payment(text):
    txt = _clean_text(text)
    # robust currency pattern - require currency symbol or word immediately before number
    m = re.search(r"(?:INR|Rs\.?|₹)\s*([0-9][0-9,\.]*)", txt, re.IGNORECASE)
    if m:
        val = m.group(1).replace(",", "").strip()
        # format with commas for readability
        try:
            if "." in val:
                num = float(val)
                return f"INR {num:,.2f}"
            else:
                num = int(val)
                return f"INR {num:,}"
        except Exception:
            return f"INR {m.group(1)}"
    # look for "basic salary of 40000 per month" style
    m2 = re.search(r"basic salary of\s*([0-9][0-9,\.]*)", txt, re.IGNORECASE)
    if m2:
        val = m2.group(1).replace(",", "")
        try:
            num = int(val) if "." not in val else float(val)
            return f"INR {num:,}" if isinstance(num, int) else f"INR {num:,.2f}"
        except Exception:
            return f"INR {m2.group(1)}"
    # look for "advance amount of INR 50,000" captured above; if no currency symbol, avoid false positives
    return "Not Found"

def analyze_contract(text):
    txt = _clean_text(text)
    parties = _extract_parties(txt)
    contract_type = parties.get("type") if isinstance(parties, dict) else "Unknown Agreement"

    # canonicalize if heading present
    hmatch = re.search(r"^\s*(EMPLOYMENT AGREEMENT|PARTNERSHIP DEED|DEED OF PARTNERSHIP|LEASE AGREEMENT|SERVICE AGREEMENT|NON[- ]DISCLOSURE AGREEMENT)", text, re.IGNORECASE | re.MULTILINE)
    if hmatch:
        contract_type = hmatch.group(1).title()

    if contract_type.lower().startswith("partnership"):
        company_name = parties.get("firm", "Not Found")
        person_name = ", ".join(parties.get("partners", ["Not Found"]))
    else:
        company_name = parties.get("party_a") or parties.get("provider") or parties.get("firm") or "Not Found"
        person_name = parties.get("party_b") or parties.get("client") or "Not Found"

    payment_value = _extract_payment(text)
    start, end = _extract_dates(text)
    important_clauses = detect_clauses(text)
    clause_details = {c: extract_clause_details(text, c) for c in important_clauses}

     #Simple risk heuristic
    risk_score = 0

    if payment_value == "Not Found":
     risk_score += 1

    if start == "Not Found":
      risk_score += 1

# Skip end-date check for Partnership Deed (Partnership at Will)
    if "Partnership" not in contract_type:
      if start == "Not Found" or end == "Not Found":
        risk_score += 1

    for required in ("Termination", "Liability", "Confidentiality"):
      if required not in important_clauses:
        risk_score += 1

    risk = "Low" if risk_score == 0 else "Medium" if risk_score <= 2 else "High"

    # Tailored summary
    summary = f"This is a {contract_type}."
    if contract_type.lower().startswith("partnership"):
        summary += f" Firm: {company_name}. Partners: {person_name}. "
    else:
        summary += f" Parties: {company_name} and {person_name}. "
    summary += (f"Payment: {payment_value}. " if payment_value != "Not Found" else "Payment details not clearly mentioned. ")
    summary += (f"Duration: {start} to {end}. " if start != "Not Found" and end != "Not Found" else "Contract duration missing or incomplete. ")
    summary += f"Overall Risk Level: {risk}."

    recommendations = []
    if payment_value == "Not Found":
        recommendations.append("Provide clear payment terms.")
    else:
        recommendations.append("Review payment terms carefully.")
    if start == "Not Found" or end == "Not Found":
        recommendations.append("Specify clear start and end dates.")
    if contract_type.lower().startswith("partnership"):
        recommendations.append("Ensure registration/stamp duty and explicit profit sharing details are present.")
    if "Governing Law" in important_clauses:
        recommendations.append("Verify governing law implications.")
    report = f"""
    ========== EASYLEGAL AI REPORT ==========

    Contract Type: {contract_type}

    Company/Firm:
    {company_name}

    Second Party:
    {person_name}

    Payment:
    {payment_value}

    Start Date:
    {start}

    End Date:
    {end}

    Risk Level:
    {risk}

    Summary:
    {summary}

     Important Clauses:
     """

    for clause in important_clauses:
      report += f"\n- {clause}: {clause_details[clause]}"

      report += "\n\nRecommendations:\n"

    for rec in recommendations:
       report += f"- {rec}\n"

    with open("analysis_report.txt", "w", encoding="utf-8") as f:
      f.write(report)

    return {
        "contract_type": contract_type,
        "company": company_name,
        "employee": person_name,
        "payment": payment_value,
        "start_date": start,
        "end_date": end,
        "risk": risk,
        "important_clauses": important_clauses,
        "clause_details": clause_details,
        "summary": summary,
        "recommendations": recommendations
    }
