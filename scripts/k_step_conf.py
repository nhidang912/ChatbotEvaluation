""" Import punlic libraries"""
import pandas as pd
from datetime import datetime
import progressbar
import os
import json

""" Import functions from private library"""
from scripts.utils import *


""" Define global variables for this script"""
CHATBOT_EVALUATE = """
Bạn là một bộ kiểm thử thông tin có nhiệm vụ đánh giá tính chính xác của câu trả lời do chatbot cung cấp.

### Dữ liệu đầu vào:
- **Câu hỏi (Q)**: "{question}"
- **Câu trả lời mong đợi (A_expected)**: "{expected_answer}"
- **Câu trả lời chatbot đã cung cấp (A_received)**: "{received_answer}"
- **Số bước đánh giá (k)**: {k}

### Nhiệm vụ của bạn:
1. **Phân tích A_received theo {k} bước** để xác định mức độ phù hợp với câu hỏi Q và so sánh với A_expected.  
   Với mỗi bước i (i từ 1 đến k), thực hiện:
   - **Câu hỏi phân tích**: phát sinh một câu hỏi đánh giá rõ ràng cho bước i, tập trung vào một khía cạnh cụ thể (ví dụ: chủ đề, độ đầy đủ, tính chính xác, tính liên quan…).
   - **Phân tích chi tiết**: trả lời ngắn gọn (1-2 câu) dựa trên câu hỏi phân tích, so sánh A_received với Q và A_expected.
   - **Kết luận rõ ràng**: nêu kết luận rõ ràng cho bước i.

2. **Đánh giá mức độ chính xác của nhãn chatbot_label**:
   - **TRUE**: Nếu A_received phản ánh đúng ý nghĩa của A_expected và trả lời chính xác câu hỏi Q.
   - **FALSE**: Nếu A_received có ý định trả lời Q nhưng sai lệch hoặc thiếu sót đáng kể.
   - **NOT GIVEN**: Nếu A_received không cung cấp đủ thông tin để trả lời hoặc không liên quan.

3. **Đánh giá độ tin cậy (confidence)**:  
   - **Confidence không phụ thuộc vào nội dung của A_received**, mà phản ánh mức độ chắc chắn của kết luận từng bước hoặc kết luận cuối cùng.  
   - Nếu kết luận ở từng bước có dấu hiệu **mơ hồ, thiếu chắc chắn, có thể có nhiều cách hiểu khác nhau**, confidence phải giảm xuống đáng kể, ví dụ **dưới 0.5**.  


4. **Xuất kết quả cuối cùng theo cấu trúc JSON để dễ dàng trích xuất**:
{{
    "steps": [
        {{"step": 1, "question": "<Câu hỏi đánh giá bước 1>", "conclusion": "<Kết luận rõ ràng về bước 1>", "confidence": <Độ tin cậy của bước 1>}},
        ...
        {{"step": k, "question": "<Câu hỏi đánh giá bước k>", "conclusion": "<Kết luận rõ ràng về bước k>", "confidence": <Độ tin cậy của bước k>}},
    ],
    "final_evaluation": {{
        "label": "<TRUE/FALSE/NOT GIVEN>",
        "confidence": <Độ tin cậy tổng thể của nhãn cuối cùng>,
        "reason": "<Giải thích ngắn gọn về quyết định cuối cùng, nêu rõ lý do chọn mức confidence>"
    }}
}}

Lưu ý: không sử dụng dấu nháy kép (") trong câu trả lời của bạn.
"""


""" Define functions for this script"""
def evaluate(input, output, model, k, start=0):
    # Load input data and define output path based on model name and current time
    input_df = pd.read_excel(input, sheet_name=0)
    current_time = datetime.now().strftime("%y%m%d_%H%M%S")
    if output[-5:] == ".xlsx":
        output_path = output
    else:
        output_path = f"{output}/{k}-step_conf_{model}_{current_time}.xlsx"
    # Create a progress bar with ETA and other useful widgets    
    bar = progressbar.ProgressBar(
        maxval=len(input_df),
        widgets=[
            ' [', progressbar.Percentage(), '] ',
            progressbar.Bar(), ' (',
            progressbar.ETA(), ') '
        ]
    )
    input_df = input_df[start:]

    # For each row in input data, modify prompt and request LLM
    bar.start()
    for index, row in input_df.iterrows():
        question = row['question']
        expected_answer = row['expected_answer']
        received_answer = row['received_answer']
        human_label = row['human_label']
        prompt = CHATBOT_EVALUATE.format(question=question, expected_answer=expected_answer, received_answer=received_answer, k=k)
        response = request_LLM(model, prompt).replace("`", "").lstrip("json").strip()
        print(f"Response for row {index + 1}:")
        print(response)
        print("-" * 50)
        response = json.loads(response)
        steps = response.get("steps", [])
        questions = [step["question"] for step in steps]
        descriptions = [step["conclusion"] for step in steps]
        confidences = [step["confidence"] for step in steps]
        # Append the result to the output file
        data = {
                'id': [row['id']],  
                'human_label': [human_label],
                'chatbot_label': [response['final_evaluation']['label']],
                'confidence': [response['final_evaluation']['confidence']],
                'reason': [response['final_evaluation']['reason']],
            }
        for i, (q, d, c) in enumerate(zip(questions, descriptions, confidences)):
            data[f'step{i+1}_question'] = [q]
            data[f'step{i+1}_description'] = [d]
            data[f'step{i+1}_confidence'] = [c]
        temporary_df = pd.DataFrame(data)
        append_to_excel(temporary_df, output_path)
        bar.update(index + 1)
    bar.finish()

    # Calculate accuracy for each label and overall accuracy
    output_df = pd.read_excel(output_path, sheet_name=0)
    df_T = output_df[output_df['human_label'] == 'T']
    df_F = output_df[output_df['human_label'] == 'F']
    df_N = output_df[output_df['human_label'] == 'N']
    df_TT = df_T[df_T['chatbot_label'] == 'TRUE']
    df_FF = df_F[df_F['chatbot_label'] == 'FALSE']
    df_NN = df_N[df_N['chatbot_label'] == 'NOT GIVEN']
    acc_T = len(df_TT) / len(df_T) if len(df_T) > 0 else 0
    acc_F = len(df_FF) / len(df_F) if len(df_F) > 0 else 0
    acc_N = len(df_NN) / len(df_N) if len(df_N) > 0 else 0
    acc = (acc_T + acc_F + acc_N) / 3
    print(f"Accuracy of one_instruction for model {model}:")
    print(f"TRUE: {acc_T:.2f}, FALSE: {acc_F:.2f}, NOT GIVEN: {acc_N:.2f}, Average: {acc:.2f}")
    return output_path
