import pdfplumber
import os
import json
from groq import Groq
from dotenv import load_dotenv


def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pdf_text = page.extract_text()
            if pdf_text:
                text += pdf_text + "\n"
    return text


load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def extract_syllabus(text):
    prompt = f"""
            You are a structured data explorer.
            Extract only syllabus unit.
            Each unit should became one JSON subject.

            DON NOT create a seperate object for the lost of all units.
            DO NOT treat unit names as chapters.
            The chapters field should contain only the topics listed under that unit.

            Return ONLY valid JSON.

            Schema:

            [
            {{
                "subject":"string",
                "unit":"string",
                "chapters":["string"],
                "exam_date": "YYYY-MM-DD or null",
                "weightage": "percentage or null"
            }}
            ]

            Syllabus text:

            {text}
        """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=4000
    )
    return response.choices[0].message.content


def clean_json_response(raw):
    start = raw.find("[")
    end = raw.rfind("]")

    if start == -1 or end == -1:
        raise ValueError("No JSON found")

    return raw[start : end + 1]


def main():
    text = extract_text_from_pdf("sample_syllabus_for_studypilot.pdf")
    ## send this text to the AI model
    raw_output = extract_syllabus(text)
    cleaned = clean_json_response(raw_output)
    print(cleaned)
    data = json.loads(cleaned)

    with open("syllabus.json", "w") as f:
        json.dump(data, f, indent=2)

    print("Json has been written properly")


main()