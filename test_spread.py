import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# 인증
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# 서비스 계정 파일 경로 (프로젝트 루트 기준)
service_account_file = "credentials/google_service_account.json"

creds = Credentials.from_service_account_file(service_account_file, scopes=scopes)
gc = gspread.authorize(creds)

# 스프레드시트 열기
sheet_id = os.getenv("GOOGLE_SHEET_ID")
spreadsheet = gc.open_by_key(sheet_id)

print(f"📊 스프레드시트: {spreadsheet.title}")
print(f"🔗 URL: {spreadsheet.url}")

# 테스트 데이터 생성
test_data = {
    "Name": ["Alice", "Bob", "Charlie", "David"],
    "Age": [25, 30, 35, 28],
    "City": ["Seoul", "Busan", "Incheon", "Daegu"],
    "Score": [95, 87, 92, 88],
}

df = pd.DataFrame(test_data)

# 시트 이름 (날짜 포함)
today = datetime.now().strftime("%Y-%m-%d")
sheet_name = f"Test_{today}"

print(f"\n🎯 타겟 시트: {sheet_name}")

# 시트 생성 또는 가져오기
try:
    worksheet = spreadsheet.worksheet(sheet_name)
    print(f"✅ 기존 시트 사용: {sheet_name}")
except gspread.exceptions.WorksheetNotFound:
    worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=10)
    print(f"✨ 새 시트 생성: {sheet_name}")

# 데이터 업로드
set_with_dataframe(worksheet, df, include_index=False)

print(f"\n✅ 업로드 완료!")
print(f"   - 행 수: {len(df)}")
print(f"   - 열 수: {len(df.columns)}")
print(f"   - 시트 URL: {spreadsheet.url}#gid={worksheet.id}")
