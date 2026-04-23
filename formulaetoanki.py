import os
import re
import time
import genanki
import random
from google import genai

API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
client = genai.Client(api_key=API_KEY)

def extract_formulas_to_anki(pdf_path, output_deck_name):
    print(f"[*] Uploading {pdf_path}...")
    try:
        uploaded_file = client.files.upload(file=pdf_path)
    except Exception as e:
        print(f"[!] Upload failed: {e}")
        return

    print("[*] Processing document...")
    while True:
        file_info = client.files.get(name=uploaded_file.name)
        if file_info.state.name == "PROCESSING":
            time.sleep(2)
        elif file_info.state.name == "FAILED":
            print("[!] Document processing failed.")
            return
        else:
            break

    print("[*] Extracting formulas...")

    prompt = """
    Extract every mathematical, physical, chemical, and scientific formula from this document.
    Format your response exactly like this for every flashcard:

    ===CARD===
    QUESTION: [Name or definition of the formula]
    FORMULA: [Raw LaTeX formula. No $$ or brackets.]
    VARIABLES: [List variables separated by <br>. Leave blank if none.]
    ===END===
    """

    response = client.models.generate_content(
        model='gemini-3.1-flash-lite-preview', 
        contents=[file_info, prompt]
    )
    
    extracted_data = []
    raw_text = response.text
    
    if "===CARD===" in raw_text:
        for card in raw_text.split("===CARD===")[1:]:
            if "===END===" not in card:
                continue
                
            content = card.split("===END===")[0].strip()
            
            q_match = re.search(r'QUESTION:\s*(.*?)\nFORMULA:', content, re.DOTALL)
            f_match = re.search(r'FORMULA:\s*(.*?)\nVARIABLES:', content, re.DOTALL)
            v_match = re.search(r'VARIABLES:\s*(.*)', content, re.DOTALL)
            
            if q_match and f_match and v_match:
                extracted_data.append({
                    "Question": q_match.group(1).strip(),
                    "Formula": f_match.group(1).strip(),
                    "Variables": v_match.group(1).strip()
                })

    if not extracted_data:
        print("[-] No formulas found.")
        return

    print(f"[+] Extracted {len(extracted_data)} formulas. Building deck...")

    custom_css = """
    .card {
        font-family: 'Courier New', Courier, monospace;
        background-color: #0b0b0f;
        color: #e0e0e0;
        text-align: center;
        padding: 30px;
    }
    .question {
        font-size: 20px;
        color: #ffffff;
        font-weight: bold;
        letter-spacing: 1px;
    }
    hr#answer {
        border: 0;
        border-bottom: 2px dashed #ff00aa;
        margin: 25px 0;
    }
    .formula {
        font-family: 'MathJax_Math', serif;
        font-size: 28px;
        color: #00ffea;
        margin: 30px 0;
        text-shadow: 0 0 8px rgba(0, 255, 234, 0.3);
    }
    .variables {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #ffb3e6;
        text-align: left;
        background: #14141c;
        padding: 15px 20px;
        border-left: 4px solid #ff00aa;
        border-radius: 5px;
        font-size: 15px;
        line-height: 1.6;
    }
    """

    model = genanki.Model(
        1607392319,
        'Math Extractor Model',
        fields=[
            {'name': 'Question'},
            {'name': 'Formula'},
            {'name': 'Variables'}, 
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '<div class="question">{{Question}}</div>',
                'afmt': '<div class="question">{{FrontSide}}</div><hr id="answer"><div class="formula">{{Formula}}</div><div class="variables">{{Variables}}</div>',
            },
        ],
        css=custom_css
    )

    deck = genanki.Deck(random.randrange(1 << 30, 1 << 31), 'Extracted Formulas')

    for item in extracted_data:
        note = genanki.Note(
            model=model,
            fields=[item['Question'], f"\\[ {item['Formula']} \\]", item['Variables']]
        )
        deck.add_note(note)

    genanki.Package(deck).write_to_file(output_deck_name)
    print(f"[+] Deck saved: {output_deck_name}")
    
    client.files.delete(name=uploaded_file.name)
    print("[*] Cleaned up server files.")

if __name__ == "__main__":
    extract_formulas_to_anki(
        pdf_path=r"YOUR_PDF_PATH_HERE", 
        output_deck_name='blablabla.apkg'
    )