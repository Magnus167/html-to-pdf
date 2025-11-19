# HTML to PDF Service

A simple microservice that converts HTML to PDF using `wkhtmltopdf` and FastAPI.

## Getting Started

### Using Docker Compose

Build and run the service:

```bash
docker compose up --build
```

The service will be available at `http://localhost:5000`.

### Usage

The service configuration is stateful. You configure it once using the `/config` endpoint, and then render PDFs using the `/` endpoint.

#### 1. Configure (Optional)

Set the global options for all future PDF generation requests.
(all margin values need to be in inches, e.g., "1.5in")

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "page-size": "A4",
    "margin-top": "1.5in",
    "margin-bottom": "2.0in",
    "background": false
  }' \
  http://localhost:5000/config
```

#### 2. Generate PDF

Send raw HTML content to generate the PDF using the current configuration.

```bash
curl -X POST -d "<h1>Hello World</h1>" \
  -H "Content-Type: text/html" \
  --output result.pdf \
  http://localhost:5000
```

### API Documentation

You can access the interactive API documentation at `http://localhost:5000/docs` once the service is running.
