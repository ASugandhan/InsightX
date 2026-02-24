import pandas as pd
import sys

print("=" * 60)
print("DATASET VERIFICATION")
print("=" * 60)

try:
    df = pd.read_csv("data/upi_transactions_2024.csv")

    print("\n✓ Dataset loaded successfully!")
    print(f"  Rows: {len(df):,}")
    print(f"  Columns: {len(df.columns)}")

    print("\n✓ Column names:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2}. {col}")

    print("\n✓ Sample data (first row):")
    print(df.iloc[0])

    print("\n✓ Data types:")
    print(df.dtypes)

    print("\n✓ Missing values:")
    null_counts = df.isnull().sum()
    if null_counts.sum() == 0:
        print("  No NULL values!")
    else:
        for col, nulls in null_counts[null_counts > 0].items():
            print(f"  {col}: {nulls}")

    print("\n✓ Basic stats:")
    print(f"  Transaction types: {df['transaction_type'].unique()}")
    print(f"  Success rate: {(df['transaction_status']=='SUCCESS').mean()*100:.2f}%")
    print(f"  Avg amount: ₹{df['amount_inr'].mean():.2f}")

    print("\n" + "=" * 60)
    print("✓ DATASET VERIFICATION COMPLETE!")
    print("=" * 60)

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    sys.exit(1)
