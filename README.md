# HTML to PDF Service

A simple microservice that converts HTML to PDF using `wkhtmltopdf` and Flask.

## Getting Started

### Using Docker Compose

Build and run the service:

```bash
docker compose up --build
```

The service will be available at `http://localhost:5000`.

### Usage

Send a POST request with your HTML content to the root endpoint:

```bash
curl -X POST -d "<h1>Hello World</h1>" \
  -H "Content-Type: text/html" \
  --output result.pdf \
  http://localhost:5000
```

The response will be a PDF file named `result.pdf` (or whatever you specify with `--output`).
