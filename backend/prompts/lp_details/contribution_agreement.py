contribution_agg_sys_prompt = """Extract specific details from a contribution agreement and present the extracted information in a structured JSON format.

Given an excerpt from a contribution agreement, identify and extract the following information: address, name, contact details, class of units, capital commitment, date of the agreement, and details of the nominee.

# Steps

1. **Identify Sections**: Read through the document carefully and locate the sections that contain the required information.
2. **Extract Information**: For each identified section, extract the specific details relevant to the targeted fields.
3. **Structure in JSON**: Arrange the extracted information in a JSON format using the specified field names.

# Output Format

Output the extracted information as a JSON object with the following fields:

- `address`: Address where the agreement is executed.
- `name`: Name of the entity or individual involved.
- `address_of_contributor`: Address of the contributor.
- `mobile_tel_no`: Contact number of the contributor.
- `details_of_nominee`: A nested JSON with `name`, `date_of_birth`, `relationship_with_contributor`, `pan`, `mobile_no`, and `email_id`.
- `class_subclass_of_units`: Class of units to be issued.
- `amount_of_capital_commitment`: Amount of capital committed in Rs. This is just a number
- `date_of_agreement`: Date when the agreement was executed in YYYY-MM-DD format
- `email_id`: Email address of the contributor.
- `name_of_contributor`: The name of the contributor.
- `address_of_contributor`: The address of the contributor.

The JSON should adhere to this structure precisely and include all specified fields.

# Examples

**Input:** ```# **CONTRIBUTION AGREEMENT FOR AJVC FUND**

(*a scheme of AJVC Trust*)

**THIS CONTRIBUTION AGREEMENT** (hereinafter referred to as this "**Agreement**") is executed at on : Gurugram 8/29/2024

# **BY AND AMONGST:**

1. **"Orbis Trusteeship Services Private Limited"**, a company incorporated under the provisions of the Companies Act, 2013, having its registered office at 4A Ocus Technopolis, Sector 54, Golf Club Road, Gurgaon 122 002, Haryana, India, (hereinafter referred to as the "**Trustee**", which expression shall, unless repugnant to or inconsistent with the context or meaning thereof, be deemed to mean and include its successors and permitted assigns) acting in its capacity as the trustee of "**AJVC Trust**" (hereinafter referred to as the "**Trust**") of the **FIRST PART**;

# **AND**

2. "**Founders Compass Ventures LLP**", a limited liability partnership incorporated under the provisions of the Limited Liability Partnership, 2008 and having its registered office at WeWork Futura, Sr No 133(P), CTS No 4944, Magarpatta Road, Kirtane Baugh, Magarpatta, Hadapsar, Pune – 411013, Maharashtra (hereinafter referred to as the "**Investment Manager**", which expression shall, unless repugnant to or inconsistent with the context or meaning thereof, be deemed to mean and include its successors and assigns) of the **SECOND PART**;

# **AND**

3. **Person named under Annexure A** (hereinafter referred to as the "**Contributor**", which expression shall, unless repugnant to or inconsistent with the context or meaning thereof, be deemed to mean and include their permitted assigns) of the **OTHER PART**.

In this Agreement, unless the context otherwise requires, (i) the Trustee and the Investment Manager shall hereinafter be jointly referred to as the "**Fund Parties**"; and (ii) the Trustee, the Investment Manager and the Contributor shall hereinafter be jointly referred to as the "**Parties**", and individually as a "**Party**".

## **WHEREAS:**

- A. Under the Indenture (*as defined herein below*), the Trustee has been appointed by the Settlor (*as defined herein below*) to act as a trustee to **"***AJVC Trust***",** organized as an irrevocable, contributory, determinate trust, settled in India by the Settlor (with Initial Settlement being irrevocable) under the provisions of the Indian Trusts Act, 1882, pursuant to the Indenture and registered as a Category II AIF (*as defined herein below*) under the Regulations (*as defined herein below*).
- B. The Settlor has set up the Trust, which shall, through Scheme/s launched under the Trust, including the Fund, invest in accordance with the Trust Documents (*as defined herein*)

## **ANNEXURE A**

## **Details of the Contributor, Capital Commitment, Class of Units and Contact details**

# **1. Name and Address of the Contributor**

John Doe

123 Main Street, Apt 4B, Springfield, Kolkata 800096

#### **2. Amount of Capital Commitment**

The Contributor hereby makes Capital Commitment to the Fund of an aggregate amount of INR (Indian Rupees only). 1,00,00,000.00

#### **3. Class / Subclass of Units**

On making Capital Contribution, the Fund will issue fully paid **Class A Units** to the Contributor in accordance with the Agreement.

## **4. Management Fees**

- (a) *During the Commitment Period:* 2% (Two Percent) of the aggregate Capital Commitments of the respective Contributor.
- (b) *Upon expiry of the Commitment Period:* 2% (Two Percent) of the aggregate Capital Contributions of the respective Contributor less the cost of Fund Investments that have been sold, disposed of, written off or otherwise realized. Provided that any such cost of Fund Investments (that have been sold, disposed of or otherwise realized) shall be considered as part of Capital Contributions to the extent the whole or part thereof is utilised towards making reinvestment by the Fund. Accordingly, any such reinvestment shall be considered as part of Fund Investments

#### **5. Set-up Expenses**

At actuals subject to a cap of 0.5% (Zero Point Five Percent) of the Capital Commitment.

## **6. Contact details for communication**

As required under **Clause 19.2** of the Agreement, the contact details of the Contributor for services of notice and other communication is as below:

| S. No | Particulars                              | Details                                  |  |
|-------|------------------------------------------|------------------------------------------|--|
| 1     | Address (if different from (1)<br>above) | 123 Main Street, Apt 4B, Springfield, Kolkata 800096 |  |
| 2     | Email id                                 | johndoe@example.com                      |  |
| 3     | Mobile / Tel. No.                        | 9903403044                               |  |

## **7. Details of Nominee:**

| S. No | Particulars                   | Details                 |
|-------|-------------------------------|-------------------------|
| 1     | Name                          | Rohan Sharma           |
| 2     | Date of Birth                 | 1990-05-15             |
| 3     | Relationship with Contributor | Brother                |
| 4     | PAN (optional)                | ABCDE1234F             |
| 5     | Mobile No.                    | 9876543210             |
| 6     | Email id                      | rohan.sharma@example.com |

## **8. Details for demat account of the Contributor**

(Demat account details not provided in your JSON example, so this section can be customized as necessary.)

**Signature of the Contributor**```

**Output:**
```json
{{
  "address": "4A Ocus Technopolis, Sector 54, Golf Club Road, Gurgaon 122 002, Haryana, India",
  "name": "Orbis Trusteeship Services Private Limited",
  "address_of_contributor": "3rd Floor, Meera Building, 8 Dr Sarat Banerjee Road, kalighat, Kolkata 700029",
  "mobile_tel_no": "9903403044",
  "details_of_nominee": {{
    "name": "Rohan Sharma",
    "date_of_birth": "1990-05-15",
    "relationship_with_contributor": "Brother",
    "pan": "ABCDE1234F",
    "mobile_no": "9876543210",
    "email_id": "rohan.sharma@example.com"
  }},
  "class_subclass_of_units": "Class A Units",
  "amount_of_capital_commitment": "1,00,00,000.00",
  "date_of_agreement": "2024-08-29",
  "email_id": "johndoe@example.com",
  "name_of_contributor": "John Doe",
  "address_of_contributor": "123 Main Street, Apt 4B, Springfield, Kolkata 800096"
}}
```

# Notes

- Consider variations in document format and presentation when identifying sections.
- Ensure every field specified in the JSON structure is included in the output, using empty strings for any missing data.
- Account for potential multiple lines or formatting issues that might obscure data extraction.
"""

contribution_agg_user_prompt = """Given below is the text of Contribution Agreement from which you need to extract these fields
```{ca_text}```"""