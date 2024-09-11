from researcher_ai.main.parse_url.html_parser import UrlTextParser


def test_url_text_parser():
    parser = UrlTextParser()

    # Test with a PDF URL
    pdf_urls = ["https://arxiv.org/pdf/2402.15000"]
    pdf_result = parser.parse_html(pdf_urls)
    assert len(pdf_result) == 1, "Expected 1 result for PDF URL"

def test_html_parser():
    parser = UrlTextParser()
    # Test with an HTML URL
    html_urls = ["https://python.langchain.com/v0.2/docs/introduction/"]
    html_result = parser.parse_html(html_urls)
    assert len(html_result) == 1, "Expected 1 result for HTML URL"


