# IFRS 17 Gross LIC Computation and YoY Checks

This project demonstrates how to calculate the Liability for Incurred Claims (LIC) under IFRS 17 and validate the result using a combination of Python and SQL.

## 🔍 Purpose
To simulate a real-world actuarial workflow for a P&C (General Insurance) company, including:
- Reading claim triangle data and assumptions
- Calculate IBNR using Chain Ladder method
- Computing discounted LIC per line of business and AY
- Validating results with SQL-based reconciliation and YoY checks

## 💻 Tech Stack
- Python (pandas, duckdb)
- SQLite-style SQL (via DuckDB)
- VS Code
- Excel input/output for easy review

## 💻 Definition/Assumptions of input data
- claims_triangle: Reported - cumulative incurred; Case_Reserve - outstanding case reserve as of end of the DY.
- dev_factors: development factors to ultimate
- payment_pattern: 1/2/3/4 - assuming payment at end of 1/2/3/4 year(s). Assuming same payment pattern for BEL across AYs. 

## 📁 Project Structure
- data/ # Input files
- output/ # Output files: LIC summary and validation checklist
- main.py # Core LIC calculation logic
- validate.py # Validation and YoY comparison logic using SQL. Vaildation results will be displayed in Interactive console.
- requirements.txt # Python dependencies
- README.md # Project summary