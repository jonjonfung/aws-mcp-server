from mcp.server.fastmcp import FastMCP
import boto3
import awswrangler as wr
import pandas as pd
import joblib
import tempfile
import os
import json

from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Set AWS credentials
aws_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_DEFAULT_REGION', 'ap-southeast-2')

if aws_key:
    os.environ['AWS_ACCESS_KEY_ID'] = aws_key
if aws_secret:
    os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret
os.environ['AWS_DEFAULT_REGION'] = aws_region

# Create MCP server
mcp = FastMCP("AWS Data Server")

# AWS config
AWS_REGION = "ap-southeast-2"
BUCKET = "olist-ecommerce-pipeline-john"
STOCK_BUCKET = "stock-pipeline-john"

# ---- TOOL 1: Query Athena ----
@mcp.tool()
def query_athena(sql: str, database: str = "olist_silver_db") -> str:
    """
    Run a SQL query against AWS Athena.
    Use this to query any data in the AWS databases.
    Available databases: olist_silver_db, stock_db
    """
    try:
        df = wr.athena.read_sql_query(
            sql,
            database=database,
            s3_output=f"s3://{BUCKET}/output/"
        )
        return df.to_string(index=False)
    except Exception as e:
        return f"Error running query: {str(e)}"

# ---- TOOL 2: List S3 Files ----
@mcp.tool()
def list_s3_files(bucket: str, prefix: str = "") -> str:
    """
    List files in an S3 bucket.
    Available buckets: olist-ecommerce-pipeline-john, stock-pipeline-john
    """
    try:
        s3 = boto3.client('s3', region_name=AWS_REGION)
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        
        if 'Contents' not in response:
            return f"No files found in s3://{bucket}/{prefix}"
        
        files = []
        for obj in response['Contents']:
            files.append(f"{obj['Key']} ({obj['Size']} bytes)")
        
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"

# ---- TOOL 3: Get Stock Data ----
@mcp.tool()
def get_stock_data(days: int = 7) -> str:
    """
    Get recent stock price data from the stock pipeline.
    Returns stock prices for AAPL, GOOGL, MSFT, AMZN, META.
    """
    try:
        df = wr.athena.read_sql_query(
            f"""
            SELECT symbol, date, price, change, change_percent
            FROM stock_db.daily_stocks
            ORDER BY date DESC, symbol
            LIMIT {days * 5}
            """,
            database="stock_db",
            s3_output=f"s3://{STOCK_BUCKET}/output/"
        )
        return df.to_string(index=False)
    except Exception as e:
        return f"Error fetching stock data: {str(e)}"

# ---- TOOL 4: Predict Delivery Time ----
@mcp.tool()
def predict_delivery(
    customer_state: str,
    num_items: int,
    total_price: float,
    total_freight: float,
    purchase_month: int = 6,
    purchase_dayofweek: int = 1,
    purchase_hour: int = 12
) -> str:
    """
    Predict delivery time in days for a Brazilian e-commerce order.
    customer_state: Brazilian state code e.g. SP, RJ, AM, MG
    num_items: number of items in the order
    total_price: total price in BRL
    total_freight: freight value in BRL
    """
    try:
        import numpy as np
        
        s3 = boto3.client('s3', region_name=AWS_REGION)
        
        with tempfile.TemporaryDirectory() as tmp:
            model_path = os.path.join(tmp, 'model.pkl')
            encoder_path = os.path.join(tmp, 'encoder.pkl')
            
            s3.download_file(BUCKET, 'models/delivery_model.pkl', model_path)
            s3.download_file(BUCKET, 'models/label_encoder.pkl', encoder_path)
            
            model = joblib.load(model_path)
            encoder = joblib.load(encoder_path)
        
        try:
            state_encoded = encoder.transform([customer_state])[0]
        except:
            state_encoded = 0
        
        features = np.array([[
            state_encoded,
            num_items,
            total_price,
            total_freight,
            purchase_month,
            purchase_dayofweek,
            purchase_hour
        ]])
        
        prediction = model.predict(features)[0]
        
        return f"""
Delivery prediction for {customer_state}:
  Estimated delivery: {round(float(prediction), 1)} days
  Items: {num_items}
  Total price: R$ {total_price}
  Freight: R$ {total_freight}
        """
    except Exception as e:
        return f"Error predicting delivery: {str(e)}"

# ---- TOOL 5: Get Business Summary ----
@mcp.tool()
def get_business_summary() -> str:
    """
    Get a high level summary of the Olist e-commerce business.
    Returns total orders, revenue, customers and top categories.
    """
    try:
        df = wr.athena.read_sql_query(
            """
            SELECT
                COUNT(DISTINCT o.order_id) as total_orders,
                ROUND(SUM(oi.price), 2) as total_revenue,
                COUNT(DISTINCT o.customer_id) as total_customers,
                ROUND(AVG(oi.price), 2) as avg_order_value
            FROM olist_silver_db.orders o
            JOIN olist_silver_db.order_items oi
            ON o.order_id = oi.order_id
            """,
            database="olist_silver_db",
            s3_output=f"s3://{BUCKET}/output/"
        )
        return df.to_string(index=False)
    except Exception as e:
        return f"Error fetching summary: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport='stdio')