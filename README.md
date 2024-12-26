# LEVF Robust Mouse Rejuvenation 1 Project

This repository contains tools and scripts for importing, cleaning, and visualizing data from the LEVF Robust Mouse Rejuvenation 1 project. The project focuses on processing and analyzing mouse-related data, including image processing and management.

## Features

- Image storage and retrieval system supporting both local and Google Cloud Storage
- Mouse image data processing and organization
- OCR text extraction from mouse images
- Data visualization capabilities

## Setup

### Prerequisites

- Python 3.x
- Google Cloud SDK (if using GCS storage)
- Required Python packages (install via pip):
  - google-cloud-storage
  - pandas
  - other dependencies as needed

### Environment Variables

The following environment variables can be configured:

- `USE_GCS`: Set to 'true' to use Google Cloud Storage, otherwise defaults to local storage
- `GCS_BUCKET_NAME`: Required when using GCS storage, specifies the bucket name

### Local Development

1. Clone the repository
2. Install dependencies
3. Configure environment variables as needed
4. Ensure proper access to image directories or GCS bucket

## Usage

### Image Storage

The system supports two storage backends:

1. Local Storage: Images are stored in a local directory
2. Google Cloud Storage: Images are stored in a GCS bucket

The storage backend can be switched using the `USE_GCS` environment variable.

### Data Processing

- Image data is processed and organized by mouse ear tags
- OCR results are stored in CSV format
- Images can be retrieved and processed based on mouse identification

## Project Structure

- `image_storage.py`: Handles image storage and retrieval
- `data/ocr/`: Contains OCR processing results
- Additional project files and directories

## Contributing

Please follow the project's coding standards and submit pull requests for any enhancements.

## License

[Add appropriate license information] 