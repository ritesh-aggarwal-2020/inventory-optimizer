# Inventory Optimizer

## Overview

Inventory optimization engine that analyzes:

- Demand Variability
- Lead Time Variability
- Safety Stock
- Reorder Level (ROL)
- Economic Order Quantity (EOQ)
- ABC Classification
- XYZ Classification
- Inventory Health Score

## Input Sheets

### Inventory_Master
Current inventory position and cost data

### Sales_History
Historical consumption data

### PO_History
Historical purchase order lead times

### Open_PO
In-transit inventory

## Outputs

- BUY NOW / HOLD Recommendation
- Recommended Order Quantity
- Safety Stock
- Reorder Level
- Inventory Health Score
- Risk Classification

## Installation

```bash
pip install -r requirements.txt
```

## Run Inventory Engine

```bash
python test_inventory.py
```

## Run Dashboard

```bash
streamlit run streamlit_app.py
```

## Technology Stack

- Python
- Pandas
- NumPy
- SciPy
- Streamlit



## Architecture

![Architecture](Docs/architecture_diagram.png)


## Inventory Calculation Flow

![Process Flow](Docs/calculation_flowchart.png)

## Sample Output
![Sample_output](Docs/Sample_output.csv)