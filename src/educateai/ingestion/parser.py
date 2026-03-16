# parses files that we get in upload endpoint

import os
import pdfplumber


def parse_uploaded_file(file_path: str) -> dict[str, str]:
    """
    Parses the uploaded file and extracts text.

    Args:
        file_path (str): The path to the uploaded file.

    Returns:
        dict[str, str]: {"text": extracted_text}
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    if file_extension == ".txt":
        return {"text": extract_text_from_file(file_path)}
    elif file_extension == ".pdf":
        return {"text": extract_text_from_pdf(file_path)}
    elif file_extension == ".docx":
        return {"text": extract_text_from_docx(file_path)}
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")


def extract_text_from_file(file_path: str) -> str:
    """Extracts text from a plain .txt file."""
    with open(file_path, "r") as f:
        return f.read()


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts text from a PDF file using pdfplumber.

    Detects headers by comparing each line's font size against the most
    common font size on the page (body text). Lines with a larger font
    are prefixed with '## ' so structural_split() can recognise them.
    """
    output = ""

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            # extract_words returns one dict per word with position + font info.
            # extra_attrs=["size"] adds the font size to each word dict.
            words = page.extract_words(extra_attrs=["size"])
            if not words:
                continue

            # Build a list of every font size that appears on this page.
            sizes = [w["size"] for w in words]

            # The body font size is the most frequently used one.
            # max(..., key=sizes.count) picks the value that appears most often.
            body_size = max(set(sizes), key=sizes.count)

            # We group words into lines by watching for font-size changes.
            # When the size changes we know we've moved to a new "run" of text.
            current_line: list[str] = []
            current_size: float | None = None

            for word in words:
                if current_size is None:
                    # first word on the page — start a new line
                    current_size = word["size"]

                if word["size"] != current_size:
                    # font size changed → flush the accumulated line
                    line = " ".join(current_line)
                    prefix = "## " if current_size > body_size else ""
                    output += prefix + line + "\n"
                    # start a fresh line with this word's size
                    current_line = []
                    current_size = word["size"]

                current_line.append(word["text"])

            # flush the last line on this page (loop ends without a size change)
            if current_line:
                line = " ".join(current_line)
                prefix = "## " if current_size > body_size else ""
                output += prefix + line + "\n"

            # blank line between pages so double-newline splitting still works
            output += "\n"

    return output


def extract_text_from_docx(file_path: str) -> str:
    """
    Extracts text from a DOCX file.

    Word's built-in heading styles (Heading 1, Heading 2, etc.) are mapped
    to ## prefixes so structural_split() can recognise them.
    """
    from docx import Document

    document = Document(file_path)
    output = ""

    for paragraph in document.paragraphs:
        if not paragraph.text.strip():
            output += "\n"
            continue

        # paragraph.style.name is "Heading 1", "Heading 2", "Normal", etc.
        if paragraph.style.name.startswith("Heading"):
            output += "## " + paragraph.text + "\n"
        else:
            output += paragraph.text + "\n"

    return output
