from crewai.tools import tool
import json
import os
import shutil
import subprocess
from db.state_store import append_raw_data

PIPELINE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
UI_DIR = os.path.join(PIPELINE_ROOT, "ui")
STAGEHAND_SCRIPT = os.path.join(UI_DIR, "scripts", "stagehand_qa_runner.mjs")


def _resolve_codex_binary():
    override = os.environ.get("CODEX_CLI_PATH")
    if override:
        if os.path.isabs(override) and os.path.isfile(override):
            return override
        resolved = shutil.which(override)
        if resolved:
            return resolved
        return None
    return shutil.which("codex")


def _format_stagehand_output(stdout: str, stderr: str) -> str:
    lines = (stdout or stderr).splitlines()
    if not lines:
        return "Stagehand QA finished without textual output."
    snippet = "\n".join(lines[-5:])
    return f"Stagehand QA runner output:\n{snippet}"


@tool("Load Local CSV or JSON")
def load_local_data_tool(file_path: str) -> str:
    """Useful to read in local CSV or JSON data and store it into the raw_data database."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = f.read()
            # In a real app, you might want to chunk this or parse it first.
            append_raw_data(source=file_path, data=data)
            return f"Successfully loaded data from {file_path} and saved to database."
    except Exception as e:
        return f"Error loading data: {e}"

@tool("Fetch API Data")
def fetch_api_data_tool(api_url: str) -> str:
    """Useful to fetch data from an external API URL and store it into the raw_data database."""
    import requests
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.text
        append_raw_data(source=api_url, data=data)
        return f"Successfully fetched data from {api_url} and saved to database."
    except Exception as e:
        return f"Error fetching data: {e}"


@tool("Scrape Web Data")
def scrape_web_data_tool(
    url: str,
    selector: str = "body",
    max_blocks: int = 3
) -> str:
    """Scrape text from a web page, cleanse it, and stash it in the raw_data table."""
    try:
        import requests
        from bs4 import BeautifulSoup

        response = requests.get(url, timeout=15)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        if "html" not in content_type.lower():
            return f"URL {url} did not return HTML content; Content-Type={content_type}"

        soup = BeautifulSoup(response.text, "html.parser")
        elements = soup.select(selector)
        if not elements:
            elements = [soup]

        blocks = []
        for element in elements[:max_blocks]:
            text = element.get_text(" ", strip=True)
            if text:
                blocks.append(text)
        if not blocks:
            blocks = [soup.get_text(" ", strip=True)]

        data = "\n\n".join(blocks).strip()
        append_raw_data(source=url, data=data)
        return (
            f"Scraped {len(blocks)} block(s) from {url} using selector '{selector}' "
            "and saved them to the database."
        )
    except Exception as e:
        return f"Web scraping failed for {url}: {e}"

@tool("Codex CLI Patch")
def codex_patch_tool(description: str, file_path: str) -> str:
    """
    Useful to use your local Codex CLI credits to automatically patch a file. 
    Pass a description of the fix needed and the target file path.
    """
    try:
        codex_binary = _resolve_codex_binary()
        if not codex_binary:
            return (
                "Codex CLI binary not found in PATH. "
                "Install it or set the CODEX_CLI_PATH environment variable to the executable."
            )
        result = subprocess.run(
            [codex_binary, "patch", file_path, "-m", description],
            capture_output=True,
            text=True,
            check=True
        )
        return f"Codex CLI successfully patched {file_path}. Result: {result.stdout}"
    except Exception as e:
        return f"Codex CLI execution failed: {e}"

@tool("Codex CLI Rewrite")
def codex_rewrite_tool(json_data: str, target_path: str) -> str:
    """
    Useful to use your local Codex CLI credits to automatically transform/rewrite Interpreter JSON into a UI component.
    """
    try:
        codex_binary = _resolve_codex_binary()
        if not codex_binary:
            return (
                "Codex CLI binary not found in PATH. "
                "Install it or set the CODEX_CLI_PATH environment variable to the executable."
            )
        result = subprocess.run(
            [codex_binary, "rewrite", target_path, "--from", "json", "-d", json_data],
            capture_output=True,
            text=True,
            check=True
        )
        return f"Codex CLI successfully rewrote {target_path}. Result: {result.stdout}"
    except Exception as e:
        return f"Codex CLI rewrite failed: {e}"


@tool("Stagehand UI QA Runner")
def stagehand_ui_qa_tool(
    url: str = "http://127.0.0.1:5173",
    selector: str = "#root"
) -> str:
    """Run the Stagehand QA script to verify the UI renders correctly."""
    if not os.path.exists(STAGEHAND_SCRIPT):
        return (
            "Stagehand QA script missing. Run `npx stagehand` inside the ui/ folder "
            "or create ui/scripts/stagehand_qa_runner.mjs."
        )
    node_binary = shutil.which("node")
    if not node_binary:
        return "Node.js runtime not found in PATH; install Node 20+ to run Stagehand."

    args = [node_binary, STAGEHAND_SCRIPT, url, selector]
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=UI_DIR,
            check=True,
            env=os.environ
        )
        return _format_stagehand_output(result.stdout, result.stderr)
    except subprocess.CalledProcessError as err:
        details = err.stderr.strip() or err.stdout.strip() or str(err)
        return f"Stagehand UI QA failed (exit {err.returncode}): {details}"
