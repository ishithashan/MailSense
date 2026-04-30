import html
from bs4 import BeautifulSoup
import re


def clean_email_body(raw_body: str) -> str:
    """
    Convert HTML email body to clean plain text
    """
    if not raw_body:
        return ""

    # Decode HTML entities (&nbsp;, &amp;, etc.)
    text = html.unescape(raw_body)

    # Parse HTML
    soup = BeautifulSoup(text, "html.parser")

    # Remove scripts and styles
    for tag in soup(["script", "style"]):
        tag.decompose()

    # Extract visible text
    text = soup.get_text(separator=" ")

    # Normalize whitespace
    text = text.lower()

    # remove urls
    text = re.sub(r'http\S+', ' ', text)

    # remove special chars
    text = re.sub(r'[^a-z\s]', ' ', text)

    # remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text
