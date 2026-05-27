from dotenv import load_dotenv
from openai import OpenAI
from agents import Agent, Runner, function_tool
import asyncio
import boto3
from botocore.config import Config
_ = load_dotenv()
client = OpenAI()

s3 = boto3.client(service_name='s3', 
                    endpoint_url = 'https://bf914ef906c6a775e774544cd8dbe689.r2.cloudflarestorage.com',
                    aws_access_key_id = '8f53fdaab37d463b569b10554eaa3efe',
                    aws_secret_access_key = '32b14c5f5258bd18eebe6eeade4da047f67cac0d2e9bd309bce3d8fb8ef88783',
                    region_name="auto",
                    config = Config(signature_version="s3v4")
                    )

print(s3.list_objects_v2(Bucket="documentanaylsiscandidates"))

s3.download_file("documentanaylsiscandidates", 
                 r"Phyto #S-C-06019-14089360-CA Order #76410 PO #AW-1671120 (Arizona).pdf",
                 "file.pdf")

file = client.files.create(
    file = open("file.pdf", "rb"),
    purpose = "user_data"
)

prompt = """
    Extract the current phytosanitary certificate debit transaction.

    Important:
    The first page may mention an old certificate number in an Additional Declaration such as
    "replaces and cancels ...". That is NOT the current certificate number.

    Task:
    1. Identify the CURRENT certificate number for this PDF.
    - Prefer the certificate number shown in the document/file title or main certificate identifier.
    - Do NOT use any certificate number that appears after "replaces and cancels".
    2. Find the Debit Transaction Log table.
    3. Search every row for an EXACT match to the CURRENT certificate number.
    4. Do NOT select the first row unless it exactly matches the current certificate number.
    5. If no exact match exists, return matched=false.

    Return the matched certificate number, date, and debit amount only.
    """

response = client.responses.create(
    model = "gpt-5.4-mini",
    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_file",
                    "file_id": file.id
                },
                {
                    "type": "input_text",
                    "text": prompt
                },
            ]
        }
    ],
    text = {
        "format": {
            "type": "json_schema",
            "name": "phyto_debit_match",
            "strict": True,
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "matched": {"type": "boolean"},
                    "header_certificate_number": {"type": "string"},
                    "matched_certificate_number":{"type":["string", "null"]},
                    "date": {"type": ["string", "null"]},
                    "debit_amount": {"type": ["number", "null"]},
                    "reason": {"type": "string"}
                },
                "required": [
                    "matched",
                    "header_certificate_number",
                    "matched_certificate_number",
                    "date",
                    "debit_amount",
                    "reason"
                ]
            }
            
        }
    }
)

print(response.output_text)