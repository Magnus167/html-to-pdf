# HTML to PDF Service

A simple microservice that converts HTML to PDF using `wkhtmltopdf` and FastAPI.

## Getting Started

Build and run the service:

```bash
docker compose up --build
```

Access API docs at `http://localhost:5000/docs`.

## Usage

Send a `POST` request to `/` with either Raw HTML or a JSON payload.

### Check if the service is running

```bash
curl http://localhost:5000/health
```

### Simple run - no additional options

```bash
curl -X POST -d "<h1>Hello</h1>" \
  -H "Content-Type: text/html" \
  --output result.pdf \
  http://localhost:5000
```

### Passing options as a JSON payload

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "html": "<h1>Hello</h1>",
    "options": {
      "page-size": "Letter",
      "margin-top": "0.5in",
      "background": true
    }
  }' \
  --output result.pdf \
  http://localhost:5000
```

### Passing options as query parameters

```bash
curl -X POST -d "<h1>Hello</h1>" \
  -H "Content-Type: text/html" \
  --output result.pdf \
  "http://localhost:5000?page-size=A4&margin-top=20mm&background=true"
```

### Available Options

- `page-size` (e.g., A4, Letter)
- `orientation` (Portrait, Landscape)
- `background` (true/false)
- `margin-top`, `margin-bottom`, `margin-left`, `margin-right`
  - **Accepted Units**: `in`, `mm`, `cm` ONLY.
  - **Note**: Inputting `20mm` auto-converts to inches.
