from export_utils import markdown_to_pdf
import io

def test_crash():
    print("Testing for crash...")
    # 1. Test with long links in bullet points
    md_links = """
    - Link: [This is a very long link text that might cause wrapping issues when combined with the indentation logic in the PDF generator](https://example.com)
    """
    try:
        markdown_to_pdf(md_links)
        print("Links test passed")
    except Exception as e:
        print(f"Links test failed: {e}")

    # 2. Test with long single word
    md_long_word = """
    - ThisIsAVeryLongWordThatMightNotFitOnTheLineAndCouldCauseIssuesIfTheWidthCalculationIsWrongOrIfMarginsAreTooTight
    """
    try:
        markdown_to_pdf(md_long_word)
        print("Long word test passed")
    except Exception as e:
        print(f"Long word test failed: {e}")

    # 3. Test with narrow margins logic (if any)
    # 4. Test with mixed content
    md_mixed = """
    # Name
    - [Link](url)
    """
    try:
        markdown_to_pdf(md_mixed)
        print("Mixed test passed")
    except Exception as e:
        print(f"Mixed test failed: {e}")

if __name__ == "__main__":
    test_crash()
