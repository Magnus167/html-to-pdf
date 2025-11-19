from flask import Flask, request, Response
import subprocess

app = Flask(__name__)


@app.route("/", methods=["POST"])
def generate_pdf():
    html_content = request.data

    if not html_content:
        return "No HTML content provided", 400

    try:
        cmd = [
            "wkhtmltopdf",
            "--quiet",  # Suppress output to stderr
            "--page-size",
            "Letter",
            "--background",
            "--margin-top",
            "0.56in",
            "--margin-bottom",
            "0.56in",
            "--margin-left",
            "0.56in",
            "--margin-right",
            "0.56in",
            "-",  # Read from stdin
            "-",  # Write to stdout
        ]

        process = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Send HTML to stdin and get PDF from stdout
        stdout, stderr = process.communicate(input=html_content)

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
            return f"PDF generation failed: {error_msg}", 500

        return Response(
            stdout,
            mimetype="application/pdf",
            headers={"Content-Disposition": "attachment; filename=generated.pdf"},
        )

    except Exception as e:
        return f"Server Error: {str(e)}", 500


if __name__ == "__main__":
    # Run on 0.0.0.0 to be accessible outside container
    app.run(host="0.0.0.0", port=5000)
