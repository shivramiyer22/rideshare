"""
File Upload Endpoints - Handle historical data and competitor data uploads.

These endpoints accept CSV, JSON, and Excel files for:
1. Historical ride data (for Prophet ML training)
2. Competitor pricing data (for competitive analysis)

Files are validated, processed with pandas, and stored in MongoDB.
"""

import pandas as pd
import io
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse

from app.database import get_database
from app.config import settings

router = APIRouter(prefix="/upload", tags=["upload"])


async def validate_historical_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate historical data DataFrame with new data model.
    
    Requirements:
    - Minimum 300 total rows
    - Required columns: Order_Date, Historical_Cost_of_Ride, Pricing_Model, Expected_Ride_Duration
    - Optional but recommended: All other fields for comprehensive analysis
    - Order_Date must be datetime
    - Historical_Cost_of_Ride must be numeric
    - Expected_Ride_Duration must be numeric
    - Pricing_Model must be CONTRACTED, STANDARD, or CUSTOM
    - Time_of_Ride must be Morning, Afternoon, Evening, or Night
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Dictionary with validation result and error message if invalid
    """
    # Check minimum rows
    if len(df) < 300:
        return {
            "valid": False,
            "error": f"Insufficient data: {len(df)} rows. Minimum 300 rows required for Prophet ML training."
        }
    
    # Check required columns (case-insensitive matching)
    df.columns = df.columns.str.strip()  # Remove whitespace
    required_columns = ["Order_Date", "Historical_Cost_of_Ride", "Pricing_Model", "Expected_Ride_Duration"]
    missing_columns = []
    
    for col in required_columns:
        # Try exact match first, then case-insensitive
        if col not in df.columns:
            # Try case-insensitive match
            matching_cols = [c for c in df.columns if c.lower() == col.lower()]
            if not matching_cols:
                missing_columns.append(col)
            else:
                # Rename to standard format
                df.rename(columns={matching_cols[0]: col}, inplace=True)
    
    if missing_columns:
        return {
            "valid": False,
            "error": f"Missing required columns: {missing_columns}. Required: {required_columns}"
        }
    
    # Validate data types
    try:
        # Convert Order_Date to datetime
        df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
        if df["Order_Date"].isna().any():
            return {
                "valid": False,
                "error": "Column 'Order_Date' contains invalid datetime values"
            }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Error converting 'Order_Date' to datetime: {str(e)}"
        }
    
    # Validate Historical_Cost_of_Ride is numeric
    try:
        # Store original values for error reporting
        original_cost_values = df["Historical_Cost_of_Ride"].copy()
        
        # First, convert to string and clean the values
        cost_series = df["Historical_Cost_of_Ride"].astype(str)
        
        # Remove common currency symbols and whitespace
        cost_series = cost_series.str.replace('$', '', regex=False)
        cost_series = cost_series.str.replace('€', '', regex=False)
        cost_series = cost_series.str.replace('£', '', regex=False)
        cost_series = cost_series.str.replace(',', '', regex=False)  # Remove thousand separators
        cost_series = cost_series.str.strip()
        
        # Replace empty strings with NaN
        cost_series = cost_series.replace('', pd.NA)
        cost_series = cost_series.replace('nan', pd.NA)
        cost_series = cost_series.replace('None', pd.NA)
        cost_series = cost_series.replace('null', pd.NA)
        cost_series = cost_series.replace('NULL', pd.NA)
        
        # Convert to numeric
        df["Historical_Cost_of_Ride"] = pd.to_numeric(cost_series, errors="coerce")
        
        # Check for invalid values
        invalid_mask = df["Historical_Cost_of_Ride"].isna()
        if invalid_mask.any():
            # Get original invalid values for error message
            invalid_indices = df.index[invalid_mask].tolist()
            invalid_count = invalid_mask.sum()
            
            # Get sample invalid values (first 5)
            sample_invalid_values = original_cost_values[invalid_mask].head(5).tolist()
            sample_indices = invalid_indices[:5]
            
            # Format error message with examples
            examples = ", ".join([f"row {idx+1}: '{val}'" for idx, val in zip(sample_indices, sample_invalid_values)])
            
            error_msg = (
                f"Column 'Historical_Cost_of_Ride' contains {invalid_count} invalid numeric value(s). "
                f"All values must be numbers (currency symbols like $, €, £ and commas are automatically removed). "
                f"Example invalid values: {examples}. "
                f"Please check your CSV file and ensure all cost values are numeric."
            )
            
            return {
                "valid": False,
                "error": error_msg
            }
        
        # Check for negative values (warn but don't fail)
        negative_count = (df["Historical_Cost_of_Ride"] < 0).sum()
        if negative_count > 0:
            # Allow negative values but log a warning (could be refunds)
            pass
        
        # Check for zero values (warn but don't fail)
        zero_count = (df["Historical_Cost_of_Ride"] == 0).sum()
        if zero_count > 0:
            # Allow zero values but log a warning (could be free rides)
            pass
            
    except Exception as e:
        return {
            "valid": False,
            "error": f"Error converting 'Historical_Cost_of_Ride' to numeric: {str(e)}"
        }
    
    # Validate Expected_Ride_Duration is numeric
    try:
        df["Expected_Ride_Duration"] = pd.to_numeric(df["Expected_Ride_Duration"], errors="coerce")
        if df["Expected_Ride_Duration"].isna().any() or (df["Expected_Ride_Duration"] <= 0).any():
            return {
                "valid": False,
                "error": "Column 'Expected_Ride_Duration' must contain positive numeric values"
            }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Error converting 'Expected_Ride_Duration' to numeric: {str(e)}"
        }
    
    # Validate Pricing_Model values
    valid_models = ["CONTRACTED", "STANDARD", "CUSTOM"]
    df["Pricing_Model"] = df["Pricing_Model"].str.upper().str.strip()
    invalid_models = df[~df["Pricing_Model"].isin(valid_models)]["Pricing_Model"].unique()
    
    if len(invalid_models) > 0:
        return {
            "valid": False,
            "error": f"Invalid Pricing_Model values: {list(invalid_models)}. Must be one of: {valid_models}"
        }
    
    # Validate Time_of_Ride if present
    if "Time_of_Ride" in df.columns:
        valid_times = ["Morning", "Afternoon", "Evening", "Night"]
        df["Time_of_Ride"] = df["Time_of_Ride"].str.strip()
        invalid_times = df[~df["Time_of_Ride"].isin(valid_times)]["Time_of_Ride"].dropna().unique()
        if len(invalid_times) > 0:
            return {
                "valid": False,
                "error": f"Invalid Time_of_Ride values: {list(invalid_times)}. Must be one of: {valid_times}"
            }
    
    # Check pricing model distribution (informational, not blocking)
    pricing_counts = df["Pricing_Model"].value_counts().to_dict()
    min_count = min(pricing_counts.values()) if pricing_counts else 0
    
    return {
        "valid": True,
        "pricing_model_counts": pricing_counts,
        "total_rows": len(df),
        "warning": f"Minimum orders per pricing model: {min_count}" if min_count < 300 else None
    }


async def validate_competitor_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate competitor data DataFrame.
    
    Requirements:
    - Required columns: Rideshare_Company (or competitor_name), Order_Date (or timestamp), Historical_Cost_of_Ride (or price)
    - Optional: All other fields matching historical rides format
    - Historical_Cost_of_Ride/price must be numeric
    - Order_Date/timestamp must be datetime
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Dictionary with validation result and error message if invalid
    """
    # Normalize column names (case-insensitive, handle both old and new formats)
    df.columns = df.columns.str.strip()
    
    # Map old column names to new ones for backward compatibility
    column_mapping = {
        "competitor_name": "Rideshare_Company",
        "timestamp": "Order_Date",
        "price": "Historical_Cost_of_Ride"
    }
    
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns and new_name not in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)
    
    # Check required columns (accept either new or old names)
    required_columns_new = ["Rideshare_Company", "Order_Date", "Historical_Cost_of_Ride"]
    required_columns_old = ["competitor_name", "timestamp", "price"]
    
    # Check if we have new format or old format
    has_new_format = all(col in df.columns for col in required_columns_new)
    has_old_format = all(col in df.columns for col in required_columns_old)
    
    if not (has_new_format or has_old_format):
        missing_new = [col for col in required_columns_new if col not in df.columns]
        missing_old = [col for col in required_columns_old if col not in df.columns]
        return {
            "valid": False,
            "error": f"Missing required columns. Need either: {required_columns_new} OR {required_columns_old}"
        }
    
    # Validate data types
    date_col = "Order_Date" if "Order_Date" in df.columns else "timestamp"
    price_col = "Historical_Cost_of_Ride" if "Historical_Cost_of_Ride" in df.columns else "price"
    
    try:
        # Convert date column to datetime
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        if df[date_col].isna().any():
            return {
                "valid": False,
                "error": f"Column '{date_col}' contains invalid datetime values"
            }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Error converting '{date_col}' to datetime: {str(e)}"
        }
    
    # Validate price is numeric
    try:
        # Clean price column: remove dollar signs, commas, percentage signs, and whitespace
        # This handles formats like: "$888.88 ", "$5.42 ", "67.02%", etc.
        if df[price_col].dtype == 'object':  # Only clean if it's a string column
            df[price_col] = df[price_col].str.replace('$', '', regex=False)
            df[price_col] = df[price_col].str.replace(',', '', regex=False)
            df[price_col] = df[price_col].str.replace('%', '', regex=False)
            df[price_col] = df[price_col].str.strip()
        
        df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
        if df[price_col].isna().any():
            return {
                "valid": False,
                "error": f"Column '{price_col}' contains invalid numeric values"
            }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Error converting '{price_col}' to numeric: {str(e)}"
        }
    
    return {
        "valid": True,
        "total_rows": len(df)
    }


@router.post("/historical-data")
async def upload_historical_data(file: UploadFile = File(...)):
    """
    Upload historical ride data for Prophet ML training.
    
    This endpoint accepts CSV or JSON files containing historical ride orders.
    The data is used to train Prophet ML forecasting models.
    
    Requirements:
    - File format: CSV or JSON
    - Minimum 300 rows total
    - Required columns: Order_Date (datetime), Pricing_Model (string), Historical_Cost_of_Ride (numeric), Expected_Ride_Duration (numeric)
    - Optional columns: All other fields for comprehensive analysis
    - Pricing_Model must be: CONTRACTED, STANDARD, or CUSTOM
    - Time_of_Ride must be: Morning, Afternoon, Evening, or Night (if provided)
    
    Derived fields calculated automatically:
    - Historical_Unit_Price = Historical_Cost_of_Ride / Expected_Ride_Duration
    - Supply_By_Demand = (Number_of_Drivers / Number_Of_Riders) * 100 (if both provided)
    - Demand_Profile = High (<34%), Medium (34-66%), Low (>=66%) (if Supply_By_Demand provided)
    
    Example CSV format:
        Order_Date,Customer_Id,Number_Of_Riders,Number_of_Drivers,Location_Category,Customer_Loyalty_Status,Number_of_Past_Rides,Average_Ratings,Time_of_Ride,Vehicle_Type,Expected_Ride_Duration,Historical_Cost_of_Ride,Pricing_Model
        2024-01-01,12345,2,5,Urban,Gold,50,4.8,Morning,Sedan,30,45.50,STANDARD
        2024-01-01,12346,1,3,Suburban,Silver,25,4.5,Evening,SUV,45,60.00,CUSTOM
    
    Args:
        file: Uploaded file (CSV or JSON)
        
    Returns:
        JSON response with:
            - success: bool
            - rows_count: int
            - pricing_model_counts: dict (counts per pricing model)
            - message: str
    """
    try:
        # Read file content
        contents = await file.read()
        
        # Determine file type
        filename = file.filename.lower()
        is_csv = filename.endswith('.csv')
        is_json = filename.endswith('.json')
        
        if not (is_csv or is_json):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Must be CSV or JSON file."
            )
        
        # Read file with pandas
        try:
            if is_csv:
                # Try different encodings for CSV
                try:
                    df = pd.read_csv(io.BytesIO(contents), encoding='utf-8')
                except UnicodeDecodeError:
                    # Try latin-1 if UTF-8 fails
                    df = pd.read_csv(io.BytesIO(contents), encoding='latin-1')
            else:  # JSON
                df = pd.read_json(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error reading file: {str(e)}"
            )
        
        # Clean numeric columns BEFORE validation
        # Remove dollar signs, commas, percentage signs, and whitespace from potential numeric columns
        numeric_columns = [
            "Historical_Cost_of_Ride", "Historical_Unit_Price", "Expected_Ride_Duration",
            "Number_Of_Riders", "Number_of_Drivers", "Supply_By_Demand",
            "Number_of_Past_Rides", "Average_Ratings", "price"
        ]
        
        for col in numeric_columns:
            if col in df.columns and df[col].dtype == 'object':  # Only clean string columns
                df[col] = df[col].astype(str).str.replace('$', '', regex=False)
                df[col] = df[col].str.replace(',', '', regex=False)
                df[col] = df[col].str.replace('%', '', regex=False)
                df[col] = df[col].str.strip()
                # Replace empty strings with NaN
                df[col] = df[col].replace('', pd.NA)
                df[col] = df[col].replace('nan', pd.NA)
        
        # Validate data
        validation = await validate_historical_data(df)
        
        if not validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation["error"]
            )
        
        # Clean data (remove any rows with NaN in required columns)
        df = df.dropna(subset=["Order_Date", "Historical_Cost_of_Ride", "Pricing_Model", "Expected_Ride_Duration"])
        
        # Calculate derived fields
        # Historical_Unit_Price = Historical_Cost_of_Ride / Expected_Ride_Duration
        df["Historical_Unit_Price"] = df["Historical_Cost_of_Ride"] / df["Expected_Ride_Duration"]
        
        # Supply_By_Demand = (Number_of_Drivers / Number_Of_Riders) * 100 (as percentage)
        if "Number_of_Drivers" in df.columns and "Number_Of_Riders" in df.columns:
            # Handle division by zero
            df["Number_Of_Riders"] = df["Number_Of_Riders"].replace(0, 1)  # Avoid division by zero
            df["Supply_By_Demand"] = (df["Number_of_Drivers"] / df["Number_Of_Riders"]) * 100
        else:
            df["Supply_By_Demand"] = None
        
        # Demand_Profile: High if Supply_By_Demand < 34%, Medium if 34-66%, Low if >=66%
        if "Supply_By_Demand" in df.columns:
            def calculate_demand_profile(supply_demand):
                if pd.isna(supply_demand):
                    return None
                if supply_demand < 34:
                    return "High"
                elif supply_demand < 66:
                    return "Medium"
                else:
                    return "Low"
            
            df["Demand_Profile"] = df["Supply_By_Demand"].apply(calculate_demand_profile)
        else:
            df["Demand_Profile"] = None
        
        # Standardize column names (keep original names but ensure consistency)
        # Map old names to new names for backward compatibility
        column_mapping = {
            "completed_at": "Order_Date",
            "actual_price": "Historical_Cost_of_Ride",
            "pricing_model": "Pricing_Model"
        }
        
        # Rename columns if old names exist
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns and new_name not in df.columns:
                df[new_name] = df[old_name]
        
        # Convert to dictionary for MongoDB insertion
        records = df.to_dict("records")
        
        # Process records for MongoDB
        for record in records:
            # Ensure Order_Date is datetime
            if isinstance(record.get("Order_Date"), str):
                record["Order_Date"] = pd.to_datetime(record["Order_Date"])
            # Ensure datetime is timezone-aware or convert to UTC
            if hasattr(record.get("Order_Date"), "tz_localize"):
                if record["Order_Date"].tz is None:
                    record["Order_Date"] = record["Order_Date"].tz_localize("UTC")
            
            # Convert numeric fields
            numeric_fields = ["Historical_Cost_of_Ride", "Historical_Unit_Price", "Expected_Ride_Duration", 
                            "Number_Of_Riders", "Number_of_Drivers", "Supply_By_Demand", 
                            "Number_of_Past_Rides", "Average_Ratings"]
            for field in numeric_fields:
                if field in record and record[field] is not None:
                    try:
                        record[field] = float(record[field]) if not pd.isna(record[field]) else None
                    except (ValueError, TypeError):
                        record[field] = None
            
            # Add metadata
            record["uploaded_at"] = datetime.now(timezone.utc)
            
            # Keep backward compatibility: also store as completed_at and actual_price
            if "Order_Date" in record:
                record["completed_at"] = record["Order_Date"]
            if "Historical_Cost_of_Ride" in record:
                record["actual_price"] = record["Historical_Cost_of_Ride"]
            if "Pricing_Model" in record:
                record["pricing_model"] = record["Pricing_Model"]
        
        # Store in MongoDB
        database = get_database()
        if database is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        collection = database["historical_rides"]
        result = await collection.insert_many(records)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "rows_count": len(records),
                "pricing_model_counts": validation.get("pricing_model_counts", {}),
                "inserted_ids": len(result.inserted_ids),
                "message": f"Successfully uploaded {len(records)} historical ride records"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )


@router.post("/competitor-data")
async def upload_competitor_data(file: UploadFile = File(...)):
    """
    Upload competitor pricing data for competitive analysis.
    
    This endpoint accepts CSV or Excel files containing competitor pricing information.
    The data is used by the Recommendation Agent for competitive intelligence.
    
    Requirements:
    - File format: CSV, XLS, or XLSX
    - Required columns: competitor_name (string), route (string), price (numeric), timestamp (datetime)
    
    Example CSV format:
        competitor_name,route,price,timestamp
        Uber,Downtown to Airport,45.50,2024-01-01 08:30:00
        Lyft,Downtown to Airport,44.00,2024-01-01 08:30:00
    
    Args:
        file: Uploaded file (CSV or Excel)
        
    Returns:
        JSON response with:
            - success: bool
            - rows_count: int
            - message: str
    """
    try:
        # Read file content
        contents = await file.read()
        
        # Determine file type
        filename = file.filename.lower()
        is_csv = filename.endswith('.csv')
        is_excel = filename.endswith(('.xls', '.xlsx'))
        
        if not (is_csv or is_excel):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Must be CSV or Excel file (.csv, .xls, .xlsx)."
            )
        
        # Read file with pandas
        try:
            if is_csv:
                # Try different encodings for CSV
                try:
                    df = pd.read_csv(io.BytesIO(contents), encoding='utf-8')
                except UnicodeDecodeError:
                    # Try latin-1 if UTF-8 fails
                    df = pd.read_csv(io.BytesIO(contents), encoding='latin-1')
            else:  # Excel
                df = pd.read_excel(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error reading file: {str(e)}"
            )
        
        # Clean numeric columns BEFORE validation
        # Remove dollar signs, commas, percentage signs, and whitespace from potential numeric columns
        numeric_columns = [
            "Historical_Cost_of_Ride", "Historical_Unit_Price", "Expected_Ride_Duration",
            "Number_Of_Riders", "Number_of_Drivers", "Supply_By_Demand",
            "Number_of_Past_Rides", "Average_Ratings", "price"
        ]
        
        for col in numeric_columns:
            if col in df.columns and df[col].dtype == 'object':  # Only clean string columns
                df[col] = df[col].astype(str).str.replace('$', '', regex=False)
                df[col] = df[col].str.replace(',', '', regex=False)
                df[col] = df[col].str.replace('%', '', regex=False)
                df[col] = df[col].str.strip()
                # Replace empty strings with NaN
                df[col] = df[col].replace('', pd.NA)
                df[col] = df[col].replace('nan', pd.NA)
        
        # Validate data
        validation = await validate_competitor_data(df)
        
        if not validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation["error"]
            )
        
        # Clean data (remove any rows with NaN after validation)
        date_col = "Order_Date" if "Order_Date" in df.columns else "timestamp"
        price_col = "Historical_Cost_of_Ride" if "Historical_Cost_of_Ride" in df.columns else "price"
        company_col = "Rideshare_Company" if "Rideshare_Company" in df.columns else "competitor_name"
        
        required_cols = [company_col, date_col, price_col]
        df = df.dropna(subset=required_cols)
        
        # Calculate derived fields if we have the necessary columns
        if "Expected_Ride_Duration" in df.columns:
            df["Historical_Unit_Price"] = df[price_col] / df["Expected_Ride_Duration"]
        
        if "Number_of_Drivers" in df.columns and "Number_Of_Riders" in df.columns:
            df["Number_Of_Riders"] = df["Number_Of_Riders"].replace(0, 1)
            df["Supply_By_Demand"] = (df["Number_of_Drivers"] / df["Number_Of_Riders"]) * 100
            
            def calculate_demand_profile(supply_demand):
                if pd.isna(supply_demand):
                    return None
                if supply_demand < 34:
                    return "High"
                elif supply_demand < 66:
                    return "Medium"
                else:
                    return "Low"
            
            df["Demand_Profile"] = df["Supply_By_Demand"].apply(calculate_demand_profile)
        
        # Convert to dictionary for MongoDB insertion
        records = df.to_dict("records")
        
        # Process records for MongoDB
        for record in records:
            # Ensure date is datetime
            date_field = record.get(date_col) or record.get("Order_Date") or record.get("timestamp")
            if isinstance(date_field, str):
                date_field = pd.to_datetime(date_field)
            if hasattr(date_field, "tz_localize") and date_field.tz is None:
                date_field = date_field.tz_localize("UTC")
            
            # Store both old and new field names for backward compatibility
            if date_col == "timestamp":
                record["Order_Date"] = date_field
            record["timestamp"] = date_field
            
            if price_col == "price":
                record["Historical_Cost_of_Ride"] = record.get(price_col)
            record["price"] = record.get(price_col)
            
            if company_col == "competitor_name":
                record["Rideshare_Company"] = record.get(company_col)
            record["competitor_name"] = record.get(company_col)
            
            record["uploaded_at"] = datetime.now(timezone.utc)
        
        # Store in MongoDB
        database = get_database()
        if database is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        collection = database["competitor_prices"]
        result = await collection.insert_many(records)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "rows_count": len(records),
                "inserted_ids": len(result.inserted_ids),
                "message": f"Successfully uploaded {len(records)} competitor pricing records"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )
