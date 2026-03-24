from unittest.mock import patch

from educateai.ingestion.parser import parse_uploaded_file


def test_parse_pdf_returns_string():
    with patch("educateai.ingestion.parser.extract_text_from_pdf", return_value="pdf text") as mock_pdf:
        result = parse_uploaded_file("notes.pdf")
        assert result == "pdf text"
        mock_pdf.assert_called_once_with("notes.pdf")