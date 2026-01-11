from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe

import os
import json
import gspread
import pandas as pd


# Schema
class HardWord(BaseModel):
    word: str = Field(description="The English word to learn")
    meaning: str = Field(description="The meaning of the word in **KOREAN**")
    ex_sentence: str = Field(
        description="An example sentence using the word in English"
    )
    ex_sentence_kr: str = Field(
        description="Korean translation of the example sentence"
    )
    Memorize_tip: str = Field(
        description="A helpful tip or mnemonic to memorize this word in **KOREAN**"
    )


class EnglishStudy(BaseModel):
    description: str = Field(
        description="""
        A formatted Markdown string following the 'Clean Header' style. 
        It MUST contain:
        1. `### 🇺🇸 English`: The original text.
        2. `### 🇰🇷 Korean`: Natural Korean translation.
        3. `---`: A horizontal rule separator.
        4. `**💡 Context & Expressions**`: An explanation of the news context AND detailed explanations of any idioms, phrasal verbs, or useful expressions found in the text (in Korean).
        """
    )
    words: list[HardWord]


# Load Enviroment Variable
load_dotenv()

# Read Environment Variable
api_key = os.getenv("GEMINI_API")
sheet_id = os.getenv("GOOGLE_SHEET_ID")

# Script path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
output_dir = os.path.join(project_root, "output", "markdown")
file_path = os.path.join(output_dir, "wsj_article_20260111.md")

# Read An article
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read().split("\n")

all_descriptions = []
all_words = []

# Gemini Client
with genai.Client(api_key=api_key) as client:
    # Create a chat
    chat = client.chats.create(
        model="gemini-3-pro-preview",
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level="low"),
            system_instruction="""
            You are an expert English tutor.
            I will provide segments of English news articles formatted in Markdown.
            
            Your task is to generate a structured JSON response following the schema.
            
            *** IMPORTANT: 'description' Field Formatting Rules ***
            You MUST use the following Markdown structure for the 'description' field:
            
            ### 🇺🇸 English
            [Insert Original Text Here]
            
            ### 🇰🇷 Korean
            [Insert Natural Korean Translation Here]
            
            ---
            **💡 Context & Expressions**
            [First, explain the main context of the news in Korean.]
            [Second, identify and explain any idioms, phrasal verbs, or common expressions used in the text. Explain why they are used here.]
            
            ---------------------------------------------------------
            
            For the 'words' list:
            - Extract key vocabulary words.
            - The 'meaning' and 'Memorize_tip' MUST be in **Korean**.
            - 'Memorize_tip' should be creative, intuitive, and helpful for a Korean learner.
            """,
        ),
    )
    # Translate Headline
    msg = "\n".join(content[0:2]) + "\n해석해주고 어려운 단어 정리해줘"
    response = chat.send_message(
        message=msg,
        config=types.GenerateContentConfig(
            response_mime_type="application/json", response_schema=EnglishStudy
        ),
    )

    data = json.loads(response.text)
    all_descriptions.append(data["description"])
    all_words.extend(data["words"])

    # Translate Body
    for i in range(2, len(content), 3):
        msg = "\n".join(content[i : i + 3]) + "해석해주고 어려운 단어 정리해줘"
        print(f"Waiting for the {i}-th answer")

        response = chat.send_message(
            message=msg,
            config=types.GenerateContentConfig(
                response_mime_type="application/json", response_schema=EnglishStudy
            ),
        )

        data = json.loads(response.text)
        all_descriptions.append(data["description"])
        all_words.extend(data["words"])

with open("description.md", "w", encoding="utf-8") as f:
    for desc in all_descriptions:
        f.write(desc)
        f.write("\n\n---\n\n")

print("description.md 저장 완료!")

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_file(
    "groovy-ego-475711-h5-411f4a8f602e.json", scopes=scopes
)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(sheet_id)

df = pd.DataFrame(all_words)
df.columns = ["Word", "Meaning", "Example Sentence", "Example (Korean)", "Memorize Tip"]
df.to_csv("words.csv", index=False, encoding="utf-8")

worksheet = spreadsheet.sheet1
set_with_dataframe(worksheet, df, include_index=False)
