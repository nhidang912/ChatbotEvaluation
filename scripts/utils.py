import pandas as pd
import apiKeys
import openai
from google import genai
from openai import OpenAI

def append_to_excel(df, filename):
    try:
        # Check if the file exists
        with pd.ExcelWriter(filename, mode='a', if_sheet_exists='overlay', engine='openpyxl') as writer:
            df.to_excel(writer, index=False, header=writer.sheets['Sheet1'].max_row == 0, startrow=writer.sheets['Sheet1'].max_row)
    except FileNotFoundError:
        # If file doesn't exist, create a new one
        with pd.ExcelWriter(filename, mode='w', engine='openpyxl') as writer:
            df.to_excel(writer, index=False)

def request_LLM(model, prompt):
    response = None
    # Request LLM based on model
    if "gemini" in model:        
        client = genai.Client(api_key=apiKeys.GEMINI_API_KEY)
        # response = client.models.generate_content(model=model, contents=prompt).text.strip()
        try:
            response = client.models.generate_content(model=model, contents=prompt).text.strip()
        except Exception as e:
            response = request_LLM(model, prompt)
    elif ("gpt" in model) or ("o1" in model) or ("o3" in model):
        client = OpenAI(api_key=apiKeys.OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        response = completion.choices[0].message.content
    return response