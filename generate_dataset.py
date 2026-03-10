import pandas as pd
import argparse
import time
import os
import re

# Load prompts from the others directory or define them here
from others.prompt import CHATBOT_QUESTION

def extract_qa_pairs(text):
    qa_pairs = re.findall(r'(Q: .*?)(A: .*?)(?=Q:|$)', text, re.DOTALL)    
    return [{"question": q.strip(), "expected_answer": a.strip()} for q, a in qa_pairs]

def get_model(model_name):
    # Initialize the specific model
    # Reminder: Setup your API keys in apiKeys.py or your environment variables!
    import apiKeys
    
    if "gemini" in model_name.lower():
        import google.generativeai as genai
        genai.configure(api_key=apiKeys.GEMINI_API_KEY)
        return genai.GenerativeModel(model_name)
    elif "gpt" in model_name.lower():
        from openAI import OpenAI
        # pseudo code for tracking API client setup
        pass
    else:
        raise ValueError(f"Model {model_name} not supported for dataset generation script.")

def main():
    parser = argparse.ArgumentParser(description="Mimic the process of creating a Q&A dataset from articles.")
    parser.add_argument('-i', '--input', type=str, default="input/article.xlsx", help="Path to input articles Excel file")
    parser.add_argument('-o', '--output', type=str, default="output/generated_qa.xlsx", help="Path to output QA Excel file")
    parser.add_argument('-m', '--model', type=str, default="gemini-1.5-flash-002", help="Model to generate QA pairs")
    parser.add_argument('-n', '--num_questions', type=int, default=5, help="Number of questions to generate per article")
    args = parser.parse_args()

    print(f"Loading articles from {args.input}...")
    try:
        articles_df = pd.read_excel(args.input)
    except Exception as e:
        print(f"Error loading {args.input}: {e}")
        return

    model = get_model(args.model)
    
    eval_df = pd.DataFrame(columns=['title', 'url', 'question', 'expected_answer'])

    print(f"Generating questions using {args.model}...")
    for idx, row in articles_df.iterrows():
        title = row.get('title', f"Article_{idx}")
        url = row.get('url', "")
        content = row.get('content', row.get('text', ''))
        
        if not content:
            continue
            
        print(f"Processing: {title}")
        
        prompt = CHATBOT_QUESTION.format(
            information=content, 
            number_of_question=args.num_questions
        )
        
        try:
            # Note: adjust this according to the exact model library invocation
            response = model.generate_content(prompt) 
            qa_pairs = extract_qa_pairs(response.text)
            
            for qa in qa_pairs:
                article_qa_data = {
                    'title': title,
                    'url': url,
                    'question': qa['question'],
                    'expected_answer': qa['expected_answer'],
                    'received_answer': '' # Placeholder for the reader to fill
                }
                eval_df = pd.concat([eval_df, pd.DataFrame([article_qa_data])], ignore_index=True)
                
            time.sleep(2) # rate limit mitigation
        except Exception as e:
            print(f"Error generating QA for {title}: {e}")

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    eval_df.to_excel(args.output, index=False)
    print(f"Generation complete. Saved {len(eval_df)} Q&A pairs to {args.output}")
    print("\nIMPORTANT: the 'received_answer' column in the output file is left intentionally blank.")
    print("The original implementation tests the knowledge retrieval system and LLMs within a Chatbot platform UI.")
    print("You must supply the generated questions to your own system and input the replies into the 'received_answer' column before running the evaluate function.")

if __name__ == "__main__":
    main()
