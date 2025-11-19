import subprocess
import logging
from fastapi import FastAPI, Response, Request, HTTPException
from pydantic import BaseModel, Field

# Set up logging to see the command in Docker logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HTML to PDF Service (Stateful Config)")

# Define Option Model
class PdfOptions(BaseModel):
    page_size: str = Field("Letter", alias="page-size")
    margin_top: str = Field("0.56in", alias="margin-top")
    margin_bottom: str = Field("0.56in", alias="margin-bottom")
    margin_left: str = Field("0.56in", alias="margin-left")
    margin_right: str = Field("0.56in", alias="margin-right")
    background: bool = True
    encoding: str = "UTF-8"
    orientation: str = "Portrait"

    class Config:
        populate_by_name = True
        extra = "ignore"

# Global Configuration Store (Defaults)
global_config = PdfOptions()

@app.post("/config")
async def update_config(options: PdfOptions):
    """
    Update the global configuration for PDF generation.
    All subsequent requests to '/' will use these settings.
    """
    global global_config
    global_config = options
    logger.info(f"Config updated: {global_config}")
    return {"message": "Configuration updated", "config": global_config}

@app.get("/config")
async def get_config():
    """Get current global configuration."""
    return global_config

@app.post("/", response_class=Response)
async def generate_pdf(request: Request):
    """
    Convert HTML to PDF using the current global configuration.
    Expected Body: Raw HTML (text/html)
    """
    # Read raw body
    try:
        html_content = await request.body()
        if not html_content:
            raise HTTPException(status_code=400, detail="No HTML content provided")
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read body")

    # Use current global options
    options = global_config

    # Construct Command
    cmd = ["wkhtmltopdf", "--quiet"]

    # --- Global Options ---
    cmd.extend(["--page-size", options.page_size])
    cmd.extend(["--margin-top", options.margin_top])
    cmd.extend(["--margin-bottom", options.margin_bottom])
    cmd.extend(["--margin-left", options.margin_left])
    cmd.extend(["--margin-right", options.margin_right])
    cmd.extend(["--orientation", options.orientation])
    
    if options.background:
        cmd.append("--background")
    else:
        cmd.append("--no-background")

    # --- Object Options ---
    cmd.extend(["--encoding", options.encoding])
    
    # Input / Output
    cmd.append("-")
    cmd.append("-")

    # Log the command for debugging
    logger.info(f"Executing command: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = process.communicate(input=html_content)
        
        if process.returncode != 0:
            error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
            logger.error(f"wkhtmltopdf failed: {error_msg}")
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {error_msg}")
            
        if not stdout.startswith(b"%PDF-"):
             error_content = stdout.decode('utf-8', errors='replace')
             logger.error(f"Invalid Output: {error_content}")
             raise HTTPException(
                 status_code=500, 
                 detail=f"Invalid PDF Output. Stdout: {error_content}"
             )

        return Response(
            content=stdout,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=generated.pdf"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Server exception: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")
