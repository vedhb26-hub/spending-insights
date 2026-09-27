import io
import pandas as pd

REQUIRED = {"date", "description", "amount"}
RULES = {
    "Groceries": ("grocery", "market", "supermarket", "whole foods"),
    "Dining": ("restaurant", "cafe", "coffee", "pizza", "takeout"),
    "Transport": ("uber", "lyft", "metro", "bus", "gas", "fuel"),
    "Housing": ("rent", "landlord", "utilities", "electric", "internet"),
    "Shopping": ("amazon", "store", "clothing", "electronics"),
    "Entertainment": ("cinema", "movie", "streaming", "concert"),
    "Health": ("pharmacy", "doctor", "clinic", "gym"),
    "Income": ("salary", "payroll", "freelance", "refund"),
}


def category_for(description):
    value = str(description).lower()
    for category, words in RULES.items():
        if any(word in value for word in words):
            return category
    return "Other"


def load_transactions(source):
    df = pd.read_csv(source)
    df.columns = df.columns.str.strip().str.lower()
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"].astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce")
    df["description"] = df["description"].fillna("").astype(str).str.strip()
    invalid = df["date"].isna() | df["amount"].isna() | df["description"].eq("")
    discarded = int(invalid.sum())
    df = df.loc[~invalid].drop_duplicates(subset=["date", "description", "amount"]).copy()
    if "category" not in df:
        df["category"] = ""
    df["category"] = df["category"].fillna("").astype(str).str.strip()
    inferred = df["category"].eq("")
    df.loc[inferred, "category"] = df.loc[inferred, "description"].map(category_for)
    df["month"] = df["date"].dt.to_period("M").astype(str)
    return df.sort_values("date"), discarded


def summarize(df):
    # Positive amounts are income; negative amounts are spending.
    income = df.loc[df.amount > 0, "amount"].sum()
    expenses = -df.loc[df.amount < 0, "amount"].sum()
    by_category = (df[df.amount < 0].assign(spend=lambda x: -x.amount)
                   .groupby("category", as_index=False)["spend"].sum()
                   .sort_values("spend", ascending=False))
    monthly = (df.assign(income=df.amount.clip(lower=0),
                         spending=-df.amount.clip(upper=0))
               .groupby("month", as_index=False)[["income", "spending"]].sum())
    monthly["net"] = monthly.income - monthly.spending
    return {"income": float(income), "spending": float(expenses),
            "net": float(income - expenses), "categories": by_category, "monthly": monthly}
