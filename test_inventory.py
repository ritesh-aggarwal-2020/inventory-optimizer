from inventory_engine import InventoryOptimizer

optimizer = InventoryOptimizer()

result_df, summary = optimizer.optimize(
    "sample_inventory.xlsx"
)

print(summary)

print(result_df.head())