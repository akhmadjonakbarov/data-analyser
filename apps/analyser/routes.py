import os
import shutil
import uuid
from typing import List

from fastapi import APIRouter, Request, File, UploadFile
import pandas as pd
import matplotlib
from fastapi.params import Query
from starlette import status
from starlette.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from features.data_scienses.process_data import process_data

matplotlib.use('Agg')  # Use Agg backend for headless environments
import matplotlib.pyplot as plt

router = APIRouter()

UPLOAD_DIR = "uploads/"
PROCESSED_DIR = "ds_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(f"{PROCESSED_DIR}/processed_data", exist_ok=True)
os.makedirs(f"{PROCESSED_DIR}/output-images", exist_ok=True)

templates = Jinja2Templates(directory="templates")


@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})


@router.get('/upload')
async def upload_file(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


# Route to handle file upload
@router.post("/upload")
async def handle_upload(file: UploadFile = File(...)):
    upload_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process the file (optional)
    process_data(upload_path)

    # Redirect to the view route
    return RedirectResponse(url=f"/view/{file.filename}", status_code=302)


def check_numeric_type(column):
    non_numeric_data = []
    for row in column:
        if not str(row).isnumeric():
            non_numeric_data.append(row)
    return non_numeric_data


def generate_price_overview(file_name, columns, chart, title="Overview"):
    processed_file_path = os.path.join(f'{PROCESSED_DIR}/processed_data/', file_name)

    try:
        # Read CSV
        df = pd.read_csv(processed_file_path)

        x_label = columns[0]
        y_label = columns[1]

        # Sort by x_label and get the top 20 entries
        df = df.sort_values(by=x_label, ascending=False).head(20)

        # Convert the y-axis column to numeric (if needed)
        df[y_label] = pd.to_numeric(df[y_label], errors='coerce')

        # Drop rows with missing values
        df = df.dropna(subset=[x_label, y_label])

        # Ensure the chart type is valid
        if chart not in ['line', 'bar', 'barh', 'hist', 'box', 'kde', 'area', 'pie']:
            raise ValueError(f"Invalid chart type: {chart}")

        # Create a larger figure for many labels
        fig, ax = plt.subplots(figsize=(22, 15))  # Larger figure for many labels
        df.plot(x=x_label, y=y_label, kind=chart, ax=ax)

        ax.set_title(label=title)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

        # Save the plot
        os.makedirs(f"{PROCESSED_DIR}/output-images", exist_ok=True)
        unique_filename = f"price_overview_{uuid.uuid4().hex}.png"
        output_image_path = os.path.join(f"{PROCESSED_DIR}/output-images", unique_filename)

        plt.savefig(output_image_path, dpi=150)
        plt.close()

        return unique_filename
    except FileNotFoundError:
        raise FileNotFoundError(f"File {processed_file_path} not found.")
    except KeyError as e:
        raise KeyError(f"Missing required column: {e}")


@router.get('/view/{file_name}')
async def view_data(
        request: Request, file_name: str,
):
    processed_file_path = os.path.join(f'{PROCESSED_DIR}/processed_data/', file_name)
    df = pd.read_csv(processed_file_path)

    columns = df.columns.values.tolist()

    html_table = df.to_html(classes='table table-striped')

    return templates.TemplateResponse(
        "view_data.html",
        {
            "request": request,
            "html_table": html_table,
            "file_name": file_name,
            "columns": columns,
        }
    )


@router.get('/prepare-overview/{file_name}')
async def prepare_overview(
        request: Request, file_name: str, columns: List[str] = Query(), chart: str = Query(),
        title: str = Query()
):
    columns = columns[0].split(',')
    image_of_overview = generate_price_overview(file_name, columns, chart, title)
    return {"image_of_overview": image_of_overview}


@router.get('/overview')
async def overview(request: Request, file_name: str):
    processed_file_path = os.path.join(f'{PROCESSED_DIR}/output-images/', file_name)
    new_name = processed_file_path.removeprefix(f"{PROCESSED_DIR}/")
    return templates.TemplateResponse(
        "overview.html",
        {"request": request, "file_name": file_name, "image_url": new_name}
    )
