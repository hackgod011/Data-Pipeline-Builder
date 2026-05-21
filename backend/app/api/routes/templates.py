from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])

TEMPLATES = [
    {
        "id": "sales-summary",
        "name": "Sales Summary",
        "category": "Analytics",
        "description": "Aggregate total revenue and order count grouped by product category.",
        "nl_prompt": "Load the sales data, group by product category, and calculate total revenue and order count for each category. Sort by total revenue descending.",
        "required_columns": ["category", "revenue", "order_id"],
    },
    {
        "id": "data-cleaning",
        "name": "Data Cleaning",
        "category": "Data Quality",
        "description": "Drop duplicates, fill missing values, and standardise column names.",
        "nl_prompt": "Clean the dataset by removing duplicate rows, filling missing numeric values with the column mean, filling missing text values with 'Unknown', and converting all column names to lowercase with underscores.",
        "required_columns": [],
    },
    {
        "id": "customer-segmentation",
        "name": "Customer Segmentation",
        "category": "Analytics",
        "description": "Segment customers into High / Medium / Low value tiers based on total spend.",
        "nl_prompt": "Load the customer data, calculate total spend per customer, then segment them into High (top 20%), Medium (middle 50%), and Low (bottom 30%) value tiers. Output the customer ID, total spend, and segment.",
        "required_columns": ["customer_id", "spend"],
    },
    {
        "id": "time-series-resample",
        "name": "Time Series Resample",
        "category": "Transformation",
        "description": "Resample a time series dataset to a weekly frequency and compute the mean.",
        "nl_prompt": "Parse the date column, set it as the index, resample the data to weekly frequency, and compute the mean of all numeric columns for each week.",
        "required_columns": ["date"],
    },
    {
        "id": "join-merge",
        "name": "Join & Merge",
        "category": "Transformation",
        "description": "Left-join two datasets on a common key and drop rows with nulls after join.",
        "nl_prompt": "Merge the two datasets using a left join on the common ID column, then drop any rows that have null values after the merge.",
        "required_columns": ["id"],
    },
    {
        "id": "top-n-report",
        "name": "Top-N Report",
        "category": "Analytics",
        "description": "Find the top 10 records by a numeric metric.",
        "nl_prompt": "Sort the dataset by the main numeric metric column in descending order and return the top 10 rows.",
        "required_columns": [],
    },
]


@router.get("/")
async def list_templates():
    return TEMPLATES


@router.get("/{template_id}")
async def get_template(template_id: str):
    for t in TEMPLATES:
        if t["id"] == template_id:
            return t
    raise HTTPException(status_code=404, detail="Template not found")
