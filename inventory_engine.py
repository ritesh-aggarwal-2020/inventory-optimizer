import pandas as pd
import numpy as np
from scipy.stats import norm


class InventoryOptimizer:

    def __init__(self):

        self.cv_threshold = 0.20

        self.review_period_days = 30

        self.service_levels = {
            "A": 0.99,
            "B": 0.95,
            "C": 0.90
        }

    # ==================================================
    # ABC Classification
    # ==================================================

    def classify_abc(self, df):

        total_value = (
            df["Annual_Consumption_Value"]
            .sum()
        )

        if total_value <= 0:

            df["ABC"] = "C"

            return df

        df = df.sort_values(
            "Annual_Consumption_Value",
            ascending=False
        )

        df["CumPct"] = (
            df["Annual_Consumption_Value"]
            .cumsum()
            /
            total_value
        )

        df["ABC"] = np.select(
            [
                df["CumPct"] <= 0.70,
                df["CumPct"] <= 0.90
            ],
            [
                "A",
                "B"
            ],
            default="C"
        )

        return df

    # ==================================================
    # XYZ Classification
    # ==================================================

    def classify_xyz(self, demand_cv):

        if demand_cv < 0.25:
            return "X"

        elif demand_cv < 0.50:
            return "Y"

        else:
            return "Z"

    # ==================================================
    # Scenario Classification
    # ==================================================

    def classify_scenario(
        self,
        demand_cv,
        lt_cv
    ):

        t = self.cv_threshold

        if demand_cv <= t and lt_cv <= t:

            return "Stable"

        elif demand_cv > t and lt_cv <= t:

            return "Demand Volatile"

        elif demand_cv <= t and lt_cv > t:

            return "Lead Time Volatile"

        else:

            return "Both Volatile"

    # ==================================================
    # MAIN ENGINE
    # ==================================================

    def optimize(self, excel_file):

        inventory = pd.read_excel(
            excel_file,
            sheet_name="Inventory_Master"
        )

        sales = pd.read_excel(
            excel_file,
            sheet_name="Sales_History"
        )

        po_history = pd.read_excel(
            excel_file,
            sheet_name="PO_History"
        )

        open_po = pd.read_excel(
            excel_file,
            sheet_name="Open_PO"
        )

        sales["Date"] = pd.to_datetime(
            sales["Date"]
        )

        po_history["PO_Date"] = pd.to_datetime(
            po_history["PO_Date"]
        )

        po_history["Receipt_Date"] = pd.to_datetime(
            po_history["Receipt_Date"]
        )

        open_po[
            "Expected_Receipt_Date"
        ] = pd.to_datetime(
            open_po[
                "Expected_Receipt_Date"
            ]
        )

        # =====================================
        # DEMAND STATS
        # =====================================

        demand_stats = (
            sales.groupby("SKU")
            .agg(
                Avg_Daily_Sales=(
                    "Qty_Sold",
                    "mean"
                ),
                Demand_StdDev=(
                    "Qty_Sold",
                    "std"
                ),
                Annual_Demand=(
                    "Qty_Sold",
                    "sum"
                )
            )
            .reset_index()
        )

        demand_stats[
            "Demand_StdDev"
        ] = (
            demand_stats[
                "Demand_StdDev"
            ]
            .fillna(0)
        )

        demand_stats[
            "Demand_CV"
        ] = np.where(
            demand_stats[
                "Avg_Daily_Sales"
            ] > 0,
            demand_stats[
                "Demand_StdDev"
            ]
            /
            demand_stats[
                "Avg_Daily_Sales"
            ],
            0
        )

        # =====================================
        # LEAD TIME STATS
        # =====================================

        po_history["Lead_Time"] = (
            po_history[
                "Receipt_Date"
            ]
            -
            po_history[
                "PO_Date"
            ]
        ).dt.days

        lt_stats = (
            po_history.groupby("SKU")
            .agg(
                Avg_Lead_Time=(
                    "Lead_Time",
                    "mean"
                ),
                LeadTime_StdDev=(
                    "Lead_Time",
                    "std"
                )
            )
            .reset_index()
        )

        lt_stats[
            "LeadTime_StdDev"
        ] = (
            lt_stats[
                "LeadTime_StdDev"
            ]
            .fillna(0)
        )

        lt_stats[
            "LeadTime_CV"
        ] = np.where(
            lt_stats[
                "Avg_Lead_Time"
            ] > 0,
            lt_stats[
                "LeadTime_StdDev"
            ]
            /
            lt_stats[
                "Avg_Lead_Time"
            ],
            0
        )

        # =====================================
        # MERGE
        # =====================================

        df = inventory.merge(
            demand_stats,
            on="SKU",
            how="left"
        )

        df = df.merge(
            lt_stats,
            on="SKU",
            how="left"
        )

        df.fillna(
            {
                "Avg_Daily_Sales": 0,
                "Demand_StdDev": 0,
                "Annual_Demand": 0,
                "Demand_CV": 0,
                "Avg_Lead_Time": 0,
                "LeadTime_StdDev": 0,
                "LeadTime_CV": 0
            },
            inplace=True
        )

        # =====================================
        # INVENTORY VALUE
        # =====================================

        df[
            "Annual_Consumption_Value"
        ] = (
            df["Annual_Demand"]
            *
            df["Unit_Cost"]
        )

        df = self.classify_abc(df)

        today = pd.Timestamp.today()

        results = []

        # =====================================
        # SKU LOOP
        # =====================================

        for _, row in df.iterrows():

            sku = row["SKU"]

            d_avg = row["Avg_Daily_Sales"]
            d_std = row["Demand_StdDev"]

            lt_avg = row["Avg_Lead_Time"]
            lt_std = row["LeadTime_StdDev"]

            demand_cv = row["Demand_CV"]
            lt_cv = row["LeadTime_CV"]

            abc = row["ABC"]

            xyz = self.classify_xyz(
                demand_cv
            )

            scenario = (
                self.classify_scenario(
                    demand_cv,
                    lt_cv
                )
            )

            service_level = (
                self.service_levels[
                    abc
                ]
            )

            z = norm.ppf(
                service_level
            )

            variance = (
                lt_avg
                *
                (d_std ** 2)
            ) + (
                (d_avg ** 2)
                *
                (lt_std ** 2)
            )

            variance = max(
                variance,
                0
            )

            safety_stock = (
                z
                *
                np.sqrt(
                    variance
                )
            )

            lead_time_demand = (
                d_avg
                *
                lt_avg
            )

            rol = (
                lead_time_demand
                +
                safety_stock
            )

            target_stock = (
                rol
                +
                (
                    d_avg
                    *
                    self.review_period_days
                )
            )

            # =================================
            # OPEN PO LOGIC
            # =================================

            sku_po = open_po[
                open_po["SKU"]
                == sku
            ].copy()

            usable_po = 0

            if len(sku_po) > 0:

                sku_po["ETA_Days"] = (
                    sku_po[
                        "Expected_Receipt_Date"
                    ]
                    -
                    today
                ).dt.days

                usable_po = (
                    sku_po[
                        sku_po[
                            "ETA_Days"
                        ].between(
                            -30,
                            lt_avg
                        )
                    ]["PO_Qty"]
                    .sum()
                )

            inventory_position = (
                row["QOH"]
                +
                usable_po
            )

            annual_demand = max(
                row["Annual_Demand"],
                0
            )

            holding_cost = max(
                row["Holding_Cost"],
                0.01
            )

            eoq = np.sqrt(
                (
                    2
                    *
                    annual_demand
                    *
                    row["Ordering_Cost"]
                )
                /
                holding_cost
            )

            days_cover = (
                inventory_position
                /
                d_avg
                if d_avg > 0
                else 999
            )

            inventory_health = (
                inventory_position
                /
                rol
                if rol > 0
                else 999
            )

            inventory_value = (
                row["QOH"]
                *
                row["Unit_Cost"]
            )

            if inventory_health < 0.5:

                risk = "Critical"

            elif inventory_health < 1:

                risk = "Reorder"

            elif inventory_health <= 2:

                risk = "Healthy"

            else:

                risk = "Overstock"

            order_gap = max(
                0,
                target_stock
                -
                inventory_position
            )

            if inventory_position <= rol:

                action = "BUY NOW"

                recommended_order = round(
                    order_gap
                )

            else:

                action = "HOLD"

                recommended_order = 0

            results.append({

                "SKU": sku,
                "Description": row["Description"],
                "Category": row["Category"],

                "ABC": abc,
                "XYZ": xyz,

                "Scenario": scenario,

                "Avg_Daily_Demand":
                    round(d_avg, 2),

                "Avg_Lead_Time":
                    round(lt_avg, 1),

                "Safety_Stock":
                    round(safety_stock),

                "ROL":
                    round(rol),

                "Target_Stock":
                    round(target_stock),

                "Inventory_Position":
                    round(inventory_position),

                "Days_Cover":
                    round(days_cover, 1),

                "EOQ":
                    round(eoq),

                "Inventory_Health":
                    round(
                        inventory_health,
                        2
                    ),

                "Inventory_Value":
                    round(
                        inventory_value,
                        0
                    ),

                "Risk":
                    risk,

                "Action":
                    action,

                "Recommended_Order":
                    recommended_order
            })

        result_df = pd.DataFrame(
            results
        )

        summary = {

            "Total_SKUs":
                len(result_df),

            "Critical_SKUs":
                (
                    result_df["Risk"]
                    == "Critical"
                ).sum(),

            "Reorder_SKUs":
                (
                    result_df["Risk"]
                    == "Reorder"
                ).sum(),

            "Healthy_SKUs":
                (
                    result_df["Risk"]
                    == "Healthy"
                ).sum(),

            "Overstock_SKUs":
                (
                    result_df["Risk"]
                    == "Overstock"
                ).sum(),

            "Total_Inventory_Value":
                round(
                    result_df[
                        "Inventory_Value"
                    ].sum(),
                    0
                )
        }

        return result_df, summary