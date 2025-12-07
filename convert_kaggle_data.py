import pandas as pd
from datetime import datetime, timedelta

print("Loading Kaggle PaySim dataset...")
df = pd.read_csv('data/raw/PS_20174392719_1491204439457_log.csv')

print(f"Original dataset: {len(df):,} transactions")

# Take a sample for testing (10,000 transactions)
sample_size = 10000
df_sample = df.sample(n=min(sample_size, len(df)), random_state=42)

# Convert step (hours) to actual dates
base_date = datetime(2017, 1, 1)
df_sample['Date'] = df_sample['step'].apply(
    lambda x: (base_date + timedelta(hours=x)).strftime('%Y-%m-%d')
)

# Convert to your parser's format
converted = pd.DataFrame({
    'Date': df_sample['Date'],
    'Merchant': df_sample['nameDest'],
    'Amount': df_sample['amount'],
    'Category': df_sample['type']
})

# Save converted data
output_file = 'data/raw/kaggle_converted.csv'
converted.to_csv(output_file, index=False)

print(f"✅ Converted {len(converted):,} transactions")
print(f"📁 Saved to: {output_file}")
print(f"\nSample data:")
print(converted.head())
print(f"\nTransaction types:")
print(converted['Category'].value_counts())