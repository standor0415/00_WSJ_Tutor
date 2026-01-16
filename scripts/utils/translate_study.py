from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe
from pathlib import Path

import os
import json
import gspread
import pandas as pd
import time

# Load Enviroment Variable
load_dotenv()

# Read Environment Variable
API_KEY = os.getenv("GEMINI_API")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")


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


def translate_stduy(file_path: Path | str, cfg) -> None:
    path = Path(file_path)
    content = path.read_text().split("\n")

    all_descriptions = []
    all_words = []

    with genai.Client(api_key=API_KEY) as client:
        # Create a chat
        chat = client.chats.create(
            model=cfg.model.name,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_level=cfg.model.thinking_config.thinking_level
                ),
                system_instruction=cfg.prompt.system_instruction,
            ),
        )
        # Translate Headline
        msg = cfg.prompt.user_message_template.format(content="\n".join(content[0:2]))
        response = chat.send_message(
            message=msg,
            config=types.GenerateContentConfig(
                response_mime_type=cfg.model.response_config.response_mime_type,
                response_schema=EnglishStudy,
            ),
        )

        data = json.loads(response.text)
        all_descriptions.append(data["description"])
        all_words.extend(data["words"])

        chunk_size = cfg.chunk_size
        # Translate Body
        for i in range(2, len(content), chunk_size):
            msg = cfg.prompt.user_message_template.format(
                content="\n".join(content[i : i + chunk_size])
            )
            start_time = time.time()

            response = chat.send_message(
                message=msg,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json", response_schema=EnglishStudy
                ),
            )

            data = json.loads(response.text)
            all_descriptions.append(data["description"])
            all_words.extend(data["words"])
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"{i}번째 응답 완료 - 소요 시간: {elapsed_time:.2f}초")
    output_path = path.parent.parent
    project_path = output_path.parent
    translate_path = output_path / "translations"
    vocab_path = output_path / "vocabulary"

    translate_path.mkdir(parents=True, exist_ok=True)
    vocab_path.mkdir(parents=True, exist_ok=True)

    filename = path.stem.replace("article", "translations")

    with open(translate_path / f"{filename}.md", "w", encoding="utf-8") as f:
        for desc in all_descriptions:
            f.write(desc)
            f.write("\n\n---\n\n")

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    service_account_file = project_path / "credentials/google_service_account.json"

    creds = Credentials.from_service_account_file(service_account_file, scopes=scopes)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SHEET_ID)

    df = pd.DataFrame(all_words)
    df.columns = [
        "Word",
        "Meaning",
        "Example Sentence",
        "Example (Korean)",
        "Memorize Tip",
    ]

    vocab_name = path.stem.replace("article", "vocabs")
    df_path = vocab_path / f"{vocab_name}.csv"
    df.to_csv(df_path, index=False, encoding="utf-8")

    sheet_name = f"{vocab_name}"

    try:
        worksheet = spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=400, cols=10)

    set_with_dataframe(worksheet, df, include_index=False)
