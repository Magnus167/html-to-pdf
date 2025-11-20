import subprocess
import logging
import re
from typing import Optional
from fastapi import FastAPI, Response, Depends, Request, HTTPException, Body
from pydantic import BaseModel, Field, field_validator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HTML to PDF Service")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


def convert_to_inches(value: str) -> str:
    """Convert mm/cm/in string to inches string."""
    value = value.strip()
    match = re.match(r"^([\d\.]+)(in|mm|cm)$", value.lower())

    if not match:
        raise ValueError("Format must be number followed by 'in', 'mm', or 'cm'")

    num = float(match.group(1))
    unit = match.group(2)

    if unit == "in":
        return f"{num}in"
    elif unit == "mm":
        return f"{num / 25.4:.3f}in"
    elif unit == "cm":
        return f"{num / 2.54:.3f}in"
    return value


class PdfOptions(BaseModel):
    page_size: str = Field("Letter", alias="page-size")
    margin_top: str = Field("0.75in", alias="margin-top")
    margin_bottom: str = Field("0.75in", alias="margin-bottom")
    margin_left: str = Field("0.75in", alias="margin-left")
    margin_right: str = Field("0.75in", alias="margin-right")
    background: bool = True
    encoding: str = "UTF-8"
    orientation: str = "Portrait"

    class Config:
        populate_by_name = True
        extra = "ignore"

    @field_validator(
        "margin_top", "margin_bottom", "margin_left", "margin_right", mode="before"
    )
    @classmethod
    def validate_margins(cls, v):
        if not isinstance(v, str):
            return v  # Should be str, but let pydantic handle type error if not
        try:
            return convert_to_inches(v)
        except ValueError as e:
            raise ValueError(str(e))


# Dependency for Query Params
def get_query_options(
    page_size: str = "Letter",
    margin_top: str = "0.75in",
    margin_bottom: str = "0.75in",
    margin_left: str = "0.75in",
    margin_right: str = "0.75in",
    background: bool = True,
    encoding: str = "UTF-8",
    orientation: str = "Portrait",
) -> PdfOptions:
    return PdfOptions(
        page_size=page_size,
        margin_top=margin_top,
        margin_bottom=margin_bottom,
        margin_left=margin_left,
        margin_right=margin_right,
        background=background,
        encoding=encoding,
        orientation=orientation,
    )


@app.post("/", response_class=Response)
async def generate_pdf(
    request: Request, query_options: PdfOptions = Depends(get_query_options)
):
    """
    Convert HTML to PDF.
    Accepts raw HTML (text/html) or JSON {"html": "...", "options": {...}}.
    Margins accept 'in', 'mm', 'cm' units only.
    """

    html_content = b""
    final_options = query_options

    # Check Content-Type
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            json_payload = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON")

        if not json_payload or "html" not in json_payload:
            raise HTTPException(
                status_code=400, detail="JSON must contain 'html' field"
            )

        html_content = json_payload["html"].encode("utf-8")

        if "options" in json_payload:
            try:
                final_options = PdfOptions(**json_payload["options"])
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid options: {e}")
    else:
        # Raw HTML
        try:
            body = await request.body()
            if not body:
                raise HTTPException(status_code=400, detail="Empty body")
            html_content = body
        except Exception:
            raise HTTPException(status_code=400, detail="Read error")

    # Build Command
    cmd = ["wkhtmltopdf", "--quiet"]

    # Global Options
    cmd.extend(["--page-size", final_options.page_size])
    cmd.extend(["--margin-top", final_options.margin_top])
    cmd.extend(["--margin-bottom", final_options.margin_bottom])
    cmd.extend(["--margin-left", final_options.margin_left])
    cmd.extend(["--margin-right", final_options.margin_right])
    cmd.extend(["--orientation", final_options.orientation])

    if final_options.background:
        cmd.append("--background")
    else:
        cmd.append("--no-background")

    # Object Options (parsing)
    cmd.extend(["--encoding", final_options.encoding])

    # I/O
    cmd.append("-")
    cmd.append("-")

    logger.info(f"Running: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate(input=html_content)

        if process.returncode != 0:
            msg = stderr.decode("utf-8") if stderr else "Unknown error"
            logger.error(f"Error: {msg}")
            raise HTTPException(status_code=500, detail=f"Generation failed: {msg}")

        if not stdout.startswith(b"%PDF-"):
            out_text = stdout.decode("utf-8", errors="replace")
            logger.error(f"Bad Output: {out_text}")
            raise HTTPException(
                status_code=500, detail=f"Invalid PDF output: {out_text}"
            )

        return Response(
            content=stdout,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=generated.pdf"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Server Exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))
