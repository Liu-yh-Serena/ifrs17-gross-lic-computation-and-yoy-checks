import pandas as pd
import os

# Ensure output folder exists
os.makedirs("output", exist_ok=True)

# Load input files from 'data' subfolder
claims_df = pd.read_excel("data/claims_triangle.xlsx")
ldf_df = pd.read_excel("data/dev_factors.xlsx")
ra_df = pd.read_excel("data/risk_adjustment.xlsx")
discount_df = pd.read_excel("data/discount_factors.xlsx")
payment_pattern_df = pd.read_excel("data/payment_pattern.xlsx")

# Step 1: Get latest development year rows for valuation year
valuation_year = 2024
claims_df["Valuation_Year"] = claims_df["AY"] + claims_df["DY"]
latest_df = claims_df[claims_df["Valuation_Year"] == valuation_year].copy()

# Step 2: Estimate Ultimate, IBNR, and BEL
ldf_df = ldf_df.rename(columns={"From_DY": "DY"})
latest_df = latest_df.merge(ldf_df[["LOB", "DY", "LDF"]], on=["LOB", "DY"], how="left")
latest_df["LDF"] = latest_df["LDF"].fillna(1.0)
latest_df["Ultimate"] = latest_df["Reported"] * latest_df["LDF"]
latest_df["IBNR"] = latest_df["Ultimate"] - latest_df["Reported"]
latest_df["BEL"] = latest_df["IBNR"] + latest_df["Case_Reserve"]

# Step 3: Add Risk Adjustment
ra_df = ra_df.rename(columns={"RA %": "RA_Percent"})
latest_df = latest_df.merge(ra_df, on="LOB", how="left")
latest_df["RA"] = latest_df["BEL"] * latest_df["RA_Percent"] / 100

# Step 4: Expand payment pattern as direct proportions
payment_pattern_df.columns = [str(col) if col != "LOB" else col for col in payment_pattern_df.columns]
payment_long = payment_pattern_df.melt(id_vars="LOB", var_name="DY", value_name="Payment_Pct")
payment_long["DY"] = pd.to_numeric(payment_long["DY"], errors="coerce")
payment_long = payment_long.dropna(subset=["DY"])
payment_long["DY"] = payment_long["DY"].astype(int)

# Step 5: Expand discounting assuming a single rate per LOB
discount_df.columns = ["LOB", "Discount_Rate"]
discount_df["Discount_Rate"] = discount_df["Discount_Rate"] / 100  # convert % to decimal

# Create discount years 1-10 for each LOB
discount_expanded = []
for dy in range(1, 11):
    temp = discount_df.copy()
    temp["DY"] = dy
    discount_expanded.append(temp)

discount_long = pd.concat(discount_expanded, ignore_index=True)

# Step 6: Merge and calculate discounted cashflows
expanded = latest_df[["LOB", "AY", "Case_Reserve", "IBNR", "RA"]].merge(
    payment_long, on="LOB", how="left"
).merge(
    discount_long, on=["LOB", "DY"], how="left"
)

# Apply payment pattern to total LIC (Case + IBNR + RA)
expanded["Total_LIC_Undiscounted"] = expanded["Case_Reserve"] + expanded["IBNR"] + expanded["RA"]
expanded["Discount_Years"] = expanded["DY"]  # DY means how many years after valuation
discount_base = 1 + expanded["Discount_Rate"]
expanded["Discount_Factor"] = 1 / (discount_base ** expanded["Discount_Years"])
expanded["Cashflow_Undiscounted"] = expanded["Total_LIC_Undiscounted"] * expanded["Payment_Pct"]
expanded["Discounted_Cashflow"] = expanded["Cashflow_Undiscounted"] * expanded["Discount_Factor"]

# Step 7: Aggregate LIC result
summary = expanded.groupby(["LOB", "AY"]).agg({
    "Case_Reserve": "first",
    "IBNR": "first",
    "RA": "first",
    "Discounted_Cashflow": "sum"
}).reset_index()

summary["BEL"] = summary["IBNR"] + summary["Case_Reserve"]
summary = summary.rename(columns={"Discounted_Cashflow": "LIC_Discounted"})
summary = summary[["LOB", "AY", "Case_Reserve", "IBNR", "RA", "BEL", "LIC_Discounted"]]

# Export to Excel
summary.to_excel("output/lic_summary_2024.xlsx", index=False)
print("LIC calculation completed and exported to 'output/lic_summary_2024.xlsx'")
