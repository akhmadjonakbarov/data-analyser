import os

import uvicorn as uvicorn
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from apps.analyser.routes import router as analyser_routes

app = FastAPI(
    title="Data Analysis",
    description="A simple API for data analysis tasks."
)
# # Mount the 'output-images' directory to be served at '/ds_files' URL path

# Serve static files from the output-images directory
# Serve static files from the output-images directory
app.mount("/output-images", StaticFiles(directory="ds_files/output-images"), name="output-images")

# Serve static files from the processed_data directory
app.mount("/processed_data", StaticFiles(directory="ds_files/processed_data"), name="process")

app.include_router(
    analyser_routes
)

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
