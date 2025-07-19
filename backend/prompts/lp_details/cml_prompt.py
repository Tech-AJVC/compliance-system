cml_system_prompt = """Extract specific information fields from a text document called Client Master List for a VC firm. 

The fields to be extracted are:
- Citizenship mentioned as Sub Type
- Client ID 
- Depository mentioned as national securities depository limited in the document but mentioned as NSDL in the JSON output
- DOB (Date of Birth) mentioned as Sole/First Holder DOB
- DOI (Date of Issuance) mentioned as business date in the CML
- DPID (Depository Participant ID) usually mentioned as starting with IN (ex: IN305000). If not mentioned just say "Not found"
- PAN (Permanent Account Number)
- Type
- CLID
- FIRST-HOLDER-PAN
- Client Type
- DP
- Name of the country
- Number of Foreign Investors

# Steps

1. Identify and extract each field mentioned from the document.
2. Ensure no field is missed despite any variations in the field naming or format.
3. For fields like "Country" and "Number of Foreign Investors", ensure they are extracted correctly even if inferred.

# Output Format

The output should be a JSON object with each field as a key and the extracted information as its value. Here is the structure:

```json
{{
  "citizenship": "[Extracted value]",
  "client_id": "[Extracted value]",
  "depository": "[Extracted value]",
  "dob": "[Extracted value]",
  "doi": "[Extracted value]",
  "dpid": "[Extracted value]",
  "pan": "[Extracted value]",
  "type": "[Extracted value]",
  "clid": "[Extracted value]",
  "first_holder_pan": "[Extracted value]",
  "client_type": "[Extracted value]",
  "dp": "[Extracted value]",
  "country": "[Extracted value]",
  "number_of_foreign_investors": "[Extracted value]"
}}
```

# Example:

## Output:
{{
  "citizenship": "USA",
  "client_id": "23567389",
  "depository": "NSDL", 
  "dob": "12-09-1990",
  "doi": "22-Dec-2023",
  "dpid": "US305679",
  "pan": "XYZAB1234P",
  "type": "Resident",
  "clid": "ABC23456",
  "first_holder_pan": "XYZAB1234P",
  "client_type": "Beneficiary",
  "dp": "GLOBAL DISTRIBUTION SERVICES INC",
  "country": "USA",
  "number_of_foreign_investors": "2"
}}



# Notes 

- Ensure consistency in field extraction, especially for repeated fields.
- Consider variations in field naming or spelling differences that may be present in the document.
- For numeric or count fields, ensure numerical accuracy.
- If some values are not found, just say "Not found"
"""

cml_user_prompt = """Given below is the text of CML from which you need to extract these fields
```{cml_text}```"""