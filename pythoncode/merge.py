import pandas as pd

# Load the two CSV files
test_df = pd.read_csv('test.csv')
data_geo_df = pd.read_csv('data_geo_epc_ltv_loss.csv')

# Select specific columns from data_geo_epc_ltv_loss
columns_to_merge = ['ID', 'Energieklasse', 'Quadratmeterpreise', 'aktuelles_LtV', 'darlehenbetrag', 'aktueller_immobilienwert', 'wohnflaeche', 'Schadensfaktor']
data_geo_selected = data_geo_df[columns_to_merge]

# Concatenate the two dataframes based on their index
merged_df = pd.concat([test_df.reset_index(drop=True), data_geo_selected.reset_index(drop=True)], axis=1)

# Reorder columns to have 'ID' as the first column
cols = ['ID'] + [col for col in merged_df.columns if col != 'ID']
merged_df = merged_df[cols]

# Save the merged dataframe to a new CSV file
merged_df.to_csv('hypothekendata.csv', index=False)
