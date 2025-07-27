import pandas as pd
import duckdb
import os

# Load LIC summaries
summary_2023 = pd.read_excel("data/lic_summary_2023.xlsx")
summary_2024 = pd.read_excel("output/lic_summary_2024.xlsx")

# 1. Reconcile total case reserves (2024 input vs 2024 output)
input_df = pd.read_excel("data/claims_triangle.xlsx")
input_df["Valuation_Year"]=input_df["AY"]+input_df["DY"]
input_case_2024 = input_df.loc[input_df["Valuation_Year"] == 2024, "Case_Reserve"].sum()
output_case_2024 = summary_2024["Case_Reserve"].sum()

if abs(input_case_2024 - output_case_2024) > 1:
    print(f"⚠️ WARNING: Case reserve mismatch in 2024 input vs output. Input={input_case_2024:.2f}, Output={output_case_2024:.2f}")
else:
    print(f"✅ 2024 Case reserve reconciles in input and output files: {output_case_2024:.2f}")

# 2. Check discounting reasonableness
summary_2024["LIC_Undiscounted"] = summary_2024["Case_Reserve"] + summary_2024["IBNR"] + summary_2024["RA"]
summary_2024["LIC_Ratio"] = summary_2024["LIC_Discounted"] / summary_2024["LIC_Undiscounted"]
min_ratio = summary_2024["LIC_Ratio"].min()
max_ratio = summary_2024["LIC_Ratio"].max()
if min_ratio < 0.85 or max_ratio > 1.05:
    print(f"⚠️ WARNING: Discounted LIC ratio out of bounds. Range: {min_ratio:.3f} to {max_ratio:.3f}")
else:
    print(f"✅ Discounted LIC ratio is reasonable across LOBs: {min_ratio:.3f} to {max_ratio:.3f}")

# 3. Check RA to BEL ratio
summary_2024["RA_Ratio"] = summary_2024["RA"] / summary_2024["BEL"]
min_ra = summary_2024["RA_Ratio"].min()
max_ra = summary_2024["RA_Ratio"].max()
if min_ra < 0.05 or max_ra > 0.3:
    print(f"⚠️ WARNING: RA to BEL ratio out of bounds. Range: {min_ra:.3f} to {max_ra:.3f}")
else:
    print(f"✅ The ratio of RA/BEL for each LOB is within the expected range: {min_ra:.3f} to {max_ra:.3f}")

# 4. YoY comparison with SQL
con = duckdb.connect()
con.execute("CREATE TABLE summary_2023 AS SELECT * FROM summary_2023")
con.execute("CREATE TABLE summary_2024 AS SELECT * FROM summary_2024")

query = """
SELECT
  s24.LOB,
  SUM(s24.Case_Reserve) AS Case_2024,
  SUM(s23.Case_Reserve) AS Case_2023,
  ROUND((SUM(s24.Case_Reserve) - SUM(s23.Case_Reserve)) / NULLIF(SUM(s23.Case_Reserve), 0), 4) AS change_case,

  SUM(s24.IBNR) AS IBNR_2024,
  SUM(s23.IBNR) AS IBNR_2023,
  ROUND((SUM(s24.IBNR) - SUM(s23.IBNR)) / NULLIF(SUM(s23.IBNR), 0), 4) AS change_ibnr,

  SUM(s24.RA) AS RA_2024,
  SUM(s23.RA) AS RA_2023,
  ROUND((SUM(s24.RA) - SUM(s23.RA)) / NULLIF(SUM(s23.RA), 0), 4) AS change_ra,

  SUM(s24.LIC_Discounted) AS LIC_2024,
  SUM(s23.LIC_Discounted) AS LIC_2023,
  ROUND((SUM(s24.LIC_Discounted) - SUM(s23.LIC_Discounted)) / NULLIF(SUM(s23.LIC_Discounted), 0), 4) AS change_lic,

  ROUND(SUM(s24.RA) / NULLIF(SUM(s24.BEL), 0), 4) AS RA_Ratio_2024,
  ROUND(SUM(s23.RA) / NULLIF(SUM(s23.BEL), 0), 4) AS RA_Ratio_2023,
  ROUND((SUM(s24.RA) / NULLIF(SUM(s24.BEL), 0) - SUM(s23.RA) / NULLIF(SUM(s23.BEL), 0)) / NULLIF(SUM(s23.RA) / NULLIF(SUM(s23.BEL), 0), 0), 4) AS change_ra_ratio
FROM summary_2024 s24
JOIN summary_2023 s23 ON s24.LOB = s23.LOB
GROUP BY s24.LOB
"""

result = con.execute(query).fetchdf()

# Flag large changes
for col in ["change_case", "change_ibnr", "change_ra", "change_lic", "change_ra_ratio"]:
    result[f"flag_{col}"] = result[col].abs() > 0.2

result.to_excel("output/validation_checklist_sql.xlsx", index=False)
print("✅ YoY validation checklist saved to output/validation_checklist_sql.xlsx")
