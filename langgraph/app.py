from langchain.agents import create_agent
from langchain_docling import DoclingLoader
from pydantic import BaseModel
from match_debit_row import match_debit_row
from dotenv import load_dotenv
import asyncio
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

pipeline_options = PdfPipelineOptions()
pipeline_options.allow_external_plugins = True

load_dotenv()

class PhytoExtraction(BaseModel):
    current_certificate_number: str
    replaced_certificate_number: str
    debit_rows: str
    
instructions = """
        You extract structured data from a California Phytosanitary Certificate packet.
        The packet contains: the certificate itself (page 1), an inspection log,
        a Debit Transaction report, and possibly supporting docs (pick ticket, email).

        ── CERTIFICATE NUMBERS ─────────────────────────────────────────────
        There are TWO distinct certificate numbers on the certificate page and
        you MUST NOT confuse them:

        1. current_certificate_number
           - This is the number printed in the "NO." field in the TOP-RIGHT
             header of page 1, directly to the right of the "PHYTOSANITARY
             CERTIFICATE" title block and to the left of the state seal.
           - It is the ONLY certificate number that appears in the header.
           - Format example: "S-C-06019-14089360-CA".
           - This is the certificate being issued right now.

        2. replaced_certificate_number
           - This appears INSIDE the "ADDITIONAL DECLARATION" free-text block
             near the bottom of page 1, in a sentence such as:
               "This certificate replaces and cancels <NUMBER>, issued on
                <date>, due to <reason>."
           - It is the OLD certificate that this new one supersedes.
           - Any certificate number preceded by words like "replaces",
             "cancels", "cancelled", "supersedes", or "amended from" is the
             REPLACED one, never the current one.
           - If the Additional Declaration does NOT contain a
             "replaces and cancels" (or equivalent) phrase, return an empty
             string "" for this field. Do NOT invent one and do NOT copy
             the current_certificate_number into it.

        CRITICAL: The number in the "NO." header field is ALWAYS the current
        one. The number inside the "replaces and cancels" sentence is ALWAYS
        the replaced one. Never swap them. Never use a number from the
        Debit Transaction table, the inspection log, the pick ticket, or
        the email as the current_certificate_number.

        ── DEBIT ROWS ──────────────────────────────────────────────────────
        Extract EVERY row from the "Debit Transaction" / "Report Detail"
        table exactly as written. Include rows whose certificate number does
        not look related to this certificate — do not filter.

        For each row capture:
          - certificate_number  (verbatim, preserve dashes and case)
          - date                (verbatim string as shown)
          - debit_amount        (numeric, no $ sign; null if blank)

        ── RULES ───────────────────────────────────────────────────────────
        - Do NOT decide which debit row matches the certificate.
        - Do NOT perform any matching logic.
        - Do NOT normalize, reformat, or "clean up" certificate numbers.
        - Return data exactly as written on the document.
    """
    
agent = create_agent(
    name="phyto_match_agent",
    model="openai:gpt-5.5",
    system_prompt=instructions,
    response_format=PhytoExtraction
)
async def main():
    FILE_PATH = "../file.pdf"
    
    custom_converter = DocumentConverter(
        format_options = {
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    
    loader = DoclingLoader(file_path=FILE_PATH, converter=custom_converter)
    
    document = loader.load()
    document_text = "\n\n".join([doc.page_content for doc in document])
    
    result = agent.invoke(
        {"messages": [
            {"role": "user", "content": f"""
                                    Extract structured data from this phytosanitary certificate packet.

                                    Return:
                                    - current_certificate_number: ONLY the number shown
                                    in the "NO." header field at the top-right of the
                                    certificate page (next to the state seal). Never
                                    use a number that appears after the words
                                    "replaces", "cancels", "cancelled", or
                                    "supersedes" — those identify the OLD certificate.
                                    - replaced_certificate_number: the number that
                                    appears inside the "ADDITIONAL DECLARATION" block
                                    after "replaces and cancels" (or similar). Use
                                    "" if no such sentence is present.
                                    - debit_rows: every row from the Debit Transaction
                                    table, verbatim. Do not filter.

                                    Do not choose the matching debit row.
                                    Do not perform any debit matching.
                                    
                                    Perform the action on this document: {document_text}
                                    """}
            ]
        }
    )
    result = result["structured_response"]
    
    matched = match_debit_row(
        result.current_certificate_number,
        result.debit_rows
    )
    print(matched)

if __name__ == '__main__':
    asyncio.run(main())