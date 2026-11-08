
import logging

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.database.connection import get_db_connection
from app.schemas.health import HealthResponse, DatabaseHealthResponse
from app.schemas.data_profile import DataProfileResponse
from app.schemas.upload import CSVUploadResponse
from app.services.data_profiling import profile_csv, profile_dataframe
from app.services.data_cleaning import clean_dataframe
from app.services.eda import generate_eda_summary
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO, StringIO
from app.services.data_validation import validate_dataframe
from fastapi.responses import StreamingResponse
from app.services.cleaning_summary import generate_cleaning_summary
from app.database.csv_storage import store_dataframe
from app.database.dataset_registry import (
    initialize_dataset_registry,
    list_registered_datasets,
)

from pydantic import BaseModel, Field

from app.services.sql_assistant import (
    get_table_schema,
    generate_sql,
    validate_sql,
    execute_sql,
)


class DataQueryRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=1000,
        description="Ask a question about your uploaded CSV data.",
    )
    dataset_name: str = Field(
        min_length=1,
        max_length=100,
        description="Name of the selected uploaded CSV dataset.",
    )


MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="AI-powered Multi-Agent Data Analytics Platform",
    version="0.1.0",
    debug=settings.debug,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://datapilot-ai-frontend-a123.onrender.com",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    initialize_dataset_registry()
    logger.info("Dataset registry initialized successfully")

@app.get("/")
def home():
    logger.info("Home endpoint accessed")

    return {
        "message": f"Welcome to {settings.app_name}!",
        "status": "running",
        "environment": settings.app_env,
    }


@app.get("/health", response_model=HealthResponse)
def health_check():
    logger.info("Health check requested")

    return {
        "status": "healthy",
        "application": settings.app_name,
    }


@app.get("/db-health", response_model=DatabaseHealthResponse)
def database_health_check():
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            database_name = cursor.fetchone()[0]

        logger.info("Database health check successful")

        return {
            "status": "healthy",
            "database": database_name,
        }

    except Exception:
        logger.exception("Database health check failed")

        return {
            "status": "unhealthy",
            "database": None,
        }

    finally:
        if connection is not None:
            connection.close()


@app.get(
    "/profile-sample",
    response_model=DataProfileResponse,
)
def profile_sample_csv():
    return profile_csv("data/sample/students.csv")


@app.post(
    "/upload-csv",
    response_model=CSVUploadResponse,
)
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file.",
        )

    file_size = 0

    try:
        # Read the upload in chunks and enforce the 5 MB limit.
        while True:
            chunk = await file.read(1024 * 1024)

            if not chunk:
                break

            file_size += len(chunk)

            if file_size > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail="File too large. Maximum upload size is 5 MB.",
                )

        # Rewind the file so pandas can read it from the beginning.
        await file.seek(0)

        df = pd.read_csv(file.file)

        if df.empty or len(df.columns) == 0:
            raise HTTPException(
                status_code=400,
                detail="The CSV file is empty or contains no columns.",
            )

        profile = profile_dataframe(df)

        logger.info(
            "CSV uploaded and profiled successfully: %s",
            file.filename,
        )

        return {
            "filename": file.filename,
            "message": "CSV uploaded and analyzed successfully.",
            **profile,
        }

    except HTTPException:
        raise

    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError):
        raise HTTPException(
            status_code=400,
            detail="Unable to read the CSV file. Please check its format and encoding.",
        ) from None

    except Exception:
        logger.exception("Unexpected error while processing CSV upload")

        raise HTTPException(
            status_code=400,
            detail="Unable to process the CSV file.",
        ) from None

    finally:
        await file.close()

@app.post("/clean-csv")
async def clean_csv(file: UploadFile = File(...)):
    """Clean an uploaded CSV and return it as a downloadable file."""

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file.",
        )

    
    try:
        # Check the uploaded file size in chunks.
        file_size = 0

        while True:
            chunk = await file.read(1024 * 1024)

            if not chunk:
                break

            file_size += len(chunk)

            if file_size > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail="File too large. Maximum upload size is 5 MB.",
                )

        # Reset file position before pandas reads the CSV.
        await file.seek(0)

        # Read the uploaded CSV.
        df = pd.read_csv(file.file)


        if df.empty or len(df.columns) == 0:
            raise HTTPException(
                status_code=400,
                detail="The CSV file is empty or contains no columns.",
            )

        # Clean duplicate rows and handle missing values.
        cleaned_df = clean_dataframe(df)

        # Convert the cleaned DataFrame into CSV text in memory.
        csv_buffer = StringIO()
        cleaned_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        # Build a safe download filename.
        output_filename = "cleaned_" + file.filename.replace("\\", "_").replace("/", "_")

        logger.info("CSV cleaned successfully: %s", file.filename)

        return StreamingResponse(
            iter([csv_buffer.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{output_filename}"'
                )
            },
        )

    except HTTPException:
        raise

    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError):
        raise HTTPException(
            status_code=400,
            detail="Unable to read the CSV file. Please check its format and encoding.",
        ) from None

    except Exception:
        logger.exception("Unexpected error while cleaning CSV")

        raise HTTPException(
            status_code=400,
            detail="Unable to clean the CSV file.",
        ) from None

    finally:
        await file.close()


@app.post("/cleaning-summary")
async def cleaning_summary(file: UploadFile = File(...)):
    """Return a before-and-after summary of CSV cleaning."""

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file.",
        )

    try:
        # Check file size before parsing.
        file_size = 0

        while True:
            chunk = await file.read(1024 * 1024)

            if not chunk:
                break

            file_size += len(chunk)

            if file_size > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail="File too large. Maximum upload size is 5 MB.",
                )

        await file.seek(0)

        # Read and validate the CSV.
        df = pd.read_csv(file.file)

        if df.empty or len(df.columns) == 0:
            raise HTTPException(
                status_code=400,
                detail="The CSV file is empty or contains no columns.",
            )

        # Generate the before-and-after cleaning summary.
        summary = generate_cleaning_summary(df)

        logger.info(
            "Cleaning summary generated successfully: %s",
            file.filename,
        )

        return {
            "filename": file.filename,
            "message": "Cleaning summary generated successfully.",
            **summary,
        }

    except HTTPException:
        raise

    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
    ):
        raise HTTPException(
            status_code=400,
            detail="Unable to read the CSV file. Please check its format and encoding.",
        ) from None

    except Exception:
        logger.exception("Unexpected error while generating cleaning summary")

        raise HTTPException(
            status_code=400,
            detail="Unable to generate the cleaning summary.",
        ) from None

    finally:
        await file.close()


@app.post("/validate-csv")
async def validate_csv(file: UploadFile = File(...)):
    """Validate a CSV file and report suspicious data values."""

    # Check file extension.
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are allowed.",
        )

    # Read uploaded file and enforce the 5 MB size limit.
    contents = await file.read()

    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds the 5 MB limit.",
        )

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded CSV file is empty.",
        )

    # Parse and validate the CSV.
    try:
        import io

        df = pd.read_csv(io.BytesIO(contents))

        if df.empty and len(df.columns) == 0:
            raise HTTPException(
                status_code=400,
                detail="CSV file contains no columns.",
            )

        validation_result = validate_dataframe(df)

        return {
            "filename": file.filename,
            "message": "Data validation completed.",
            **validation_result,
        }

    except HTTPException:
        raise

    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid or unreadable CSV file.",
        )


@app.post("/eda")
async def analyze_csv(file: UploadFile = File(...)):
    """Generate an exploratory data analysis summary for a CSV file."""

    import io

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are allowed.",
        )

    contents = await file.read()

    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds the 5 MB limit.",
        )

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded CSV file is empty.",
        )

    try:
        df = pd.read_csv(io.BytesIO(contents))

        if df.empty:
            raise HTTPException(
                status_code=400,
                detail="CSV contains no data rows.",
            )

        result = generate_eda_summary(df)

        return {
            "filename": file.filename,
            "message": "EDA summary generated successfully.",
            **result,
        }

    except HTTPException:
        raise

    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=400,
            detail="CSV file contains no readable data.",
        )

    except pd.errors.ParserError:
        raise HTTPException(
            status_code=400,
            detail="CSV file format is invalid.",
        )

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="CSV file encoding is not supported.",
        )


@app.post("/store-csv")
async def store_csv_endpoint(file: UploadFile = File(...)):
    """Store an uploaded CSV as a new PostgreSQL table."""

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file.",
        )

    try:
        contents = await file.read(MAX_UPLOAD_SIZE + 1)

        if len(contents) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File too large. Maximum upload size is 5 MB.",
            )

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="Uploaded CSV file is empty.",
            )

        try:
            df = pd.read_csv(BytesIO(contents))
        except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError):
            raise HTTPException(
                status_code=400,
                detail="Unable to read the CSV file. Please check its format and encoding.",
            ) from None

        if df.empty or len(df.columns) == 0:
            raise HTTPException(
                status_code=400,
                detail="The CSV must contain column names and at least one data row.",
            )

        result = store_dataframe(df, file.filename)

        logger.info(
            "CSV stored in PostgreSQL: table=%s, rows=%s",
            result["table_name"],
            result["row_count"],
        )

        return {
            "message": "CSV stored successfully in PostgreSQL.",
            **result,
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from None

    except Exception:
        logger.exception("Failed to store CSV in PostgreSQL")
        raise HTTPException(
            status_code=500,
            detail="Unable to store CSV in PostgreSQL.",
        ) from None

    finally:
        await file.close()


@app.get("/datasets")
async def list_datasets_endpoint():
    """List registered CSV datasets stored in PostgreSQL."""

    try:
        datasets = list_registered_datasets()

        return {
            "count": len(datasets),
            "datasets": [
                {
                    "table_name": dataset["table_name"],
                    "original_filename": dataset["original_filename"],
                    "columns": dataset["columns"],
                    "column_count": dataset["column_count"],
                    "row_count": dataset["row_count"],
                }
                for dataset in datasets
            ],
        }

    except Exception:
        logger.exception("Unable to list registered datasets")
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve datasets. Please try again.",
        ) from None

    

@app.post("/query-data")
async def query_data_endpoint(request: DataQueryRequest):
    """Answer questions using the selected uploaded CSV table."""

    
    try:
        registered_datasets = list_registered_datasets()

        if not registered_datasets:
            raise HTTPException(
                status_code=400,
                detail="No registered datasets found. Upload a CSV first.",
            )

        schema = get_table_schema()

        registered_table_names = {
            dataset["table_name"]
            for dataset in registered_datasets
        }

        schema = [
            table
            for table in schema
            if table["table_name"] in registered_table_names
        ]

        question = request.question.strip()
        dataset_name = request.dataset_name.strip()


        if len(question) < 3:
            raise HTTPException(
                status_code=422,
                detail="Please enter a meaningful question.",
            )

        selected_dataset = next(
            (
                table
                for table in schema
                if table["table_name"] == dataset_name
            ),
            None,
        )

        if selected_dataset is None:
            raise HTTPException(
                status_code=400,
                detail="Selected dataset was not found. Please select an available dataset.",
            )

        # Only the selected dataset's schema is sent to SQL generation.
        selected_schema = [selected_dataset]
        allowed_tables = {dataset_name}

        generated_sql = generate_sql(question, selected_schema)

        validated_sql = validate_sql(
            generated_sql,
            allowed_tables,
        )

        # Enforce that the query references only the selected dataset.
        from sqlglot import exp, parse

        parsed_statements = parse(validated_sql, read="postgres")
        referenced_tables = {
            table.name.lower()
            for table in parsed_statements[0].find_all(exp.Table)
        }

        if referenced_tables != {dataset_name.lower()}:
            raise ValueError(
                "Generated SQL must reference only the selected dataset."
            )

        result = execute_sql(
            validated_sql,
            allowed_tables,
        )

        return {
            "question": question,
            "dataset_name": dataset_name,
            "sql": validated_sql,
            "columns": result["columns"],
            "rows": result["rows"],
            "row_count": result["row_count"],
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from None

    except Exception:
        logger.exception("Natural-language data query failed")
        raise HTTPException(
            status_code=500,
            detail="Unable to answer the data question. Please try again.",
        ) from None

