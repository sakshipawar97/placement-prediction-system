import pandas as pd

# Load your dataset (CSV file)
df = pd.read_csv('Placement_Prediction_data.csv')  # Replace with your dataset's file path

# Drop the 'placement_Status' and 'id' columns
df_modified = df.drop(columns=['PlacementStatus', 'StudentId'])

# Save the modified dataset back to a new CSV file
df_modified.to_csv('modified_dataset.csv', index=False)

print("Modified dataset saved as 'modified_dataset.csv'")
