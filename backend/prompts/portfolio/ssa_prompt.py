sha_system_prompt = """Extract specific information from SHARE SUBSCRIPTION AGREEMENT (SHA) documents and output it as a JSON object.

Identify and extract the following information:
- **Execution Date**: The date the SHA is executed, usually formatted as in the example provided.
- **Founder Names**: List all founders mentioned in the document, identified by associated details and the term "Founder".
- **Company Name**: The official company name mentioned, often stated in initial sections.
- **Company Address**: The registered office address of the company, typically located in the document's introduction.

Adhere to the format of the given examples without generalizing since document structures may vary.

# Steps

1. **Execution Date Extraction**: Locate the sentence containing "SHAREHOLDERS AGREEMENT" and capture the date formatted as "on the [day] of [Month] [year]".
2. **Founder Names Identification**: Search for sections detailing individuals with terms like “Founder”, noting their names.
3. **Company Name Identification**: Check initial sections for the company name, often introduced with the legal description.
4. **Company Address Extraction**: Find the company's registered address, commonly near the beginning or in legal descriptions.

# Output Format

Output the extracted details as a JSON object with keys in snake_case:

```json
{{
  "execution_date": "YYYY-MM-DD",
  "founder_names": ["founder_1", "founder_2", "founder_3"],
  "company_name": "COMPANY NAME",
  "company_address": "COMPANY ADDRESS"
}}
```

# Examples

**Example 1: Extraction from an SHA Document**

_Input:_

```
This SHAREHOLDERS’ AGREEMENT is entered into on this 17th day of March 2025 (“Execution Date”):...
...ABC TECH PRIVATE LIMITED , a company incorporated under...and having its registered office at C/O- Priya Verma, Shyam Nagar Colony,
Greenfields, Near Sun Temple, Jamshedpur, Jharkhand, India, 832101...
...SHUBHAM PATIL, an Indian resident...
...ABHINAV KUMAR, an Indian resident...
...AJAY KUMAR, an Indian resident...
```

_Expected JSON Output:_

```json
{{
  "execution_date": "2025-03-17",
  "founder_names": ["Shubham Patil", "Abhinav Kumar", "Ajay Kumar"],
  "company_name": "ABC Tech Private Limited",
  "company_address": "C/O- Priya Verma, Shyam Nagar Colony,Greenfields, Near Sun Temple, Jamshedpur, Jharkhand, India, 832101"
}}
```

# Notes

- Focus on identifying precise keywords and context such as "Execution Date", "Founder", and introductory company details.
- Consider document structure variations and validate the section from where data is extracted.
- Ensure all extracted fields are accurately formatted in snake_case in the JSON output.
"""

sha_user_prompt = """Given below is the text of SHA from which you need to extract these fields
```{sha_text}```"""