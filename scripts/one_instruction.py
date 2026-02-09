""" Import punlic libraries"""
import pandas as pd
from datetime import datetime
import progressbar
import os

""" Import functions from private library"""
from scripts.utils import *


""" Define global variables for this script"""
CHATBOT_EVALUATE = """
Bạn đang đóng vai trò là một bộ kiểm thử thông tin. Tôi sẽ cung cấp cho bạn các thông tin sau:

- Q: "{question}"  
- A_expected: "{expected_answer}"  
- A_received: "{received_answer}"

Nhiệm vụ của bạn là **đánh giá sự phù hợp của A_received dựa trên câu hỏi Q** và so sánh với A_expected. Bạn cần đánh giá dựa trên nội dung, không phụ thuộc vào cách diễn đạt, chỉ cần đảm bảo rằng câu trả lời có phản ánh đúng nội dung yêu cầu của câu hỏi.

Hãy trả lời ngắn gọn theo một trong các kết quả sau:

- TRUE: nếu A_received phù hợp và trả lời chính xác nội dung yêu cầu của câu hỏi Q so với A_expected.
- FALSE: nếu A_received có ý định trả lời câu hỏi Q nhưng thông tin không khớp với A_expected.
- NOT GIVEN: nếu A_received từ chối trả lời câu hỏi hoặc cho biết không biết, không đủ thông tin để trả lời hoặc chỉ cung cấp các thông tin khác mà không liên quan trực tiếp đến câu hỏi Q.
"""

NOTE_NORMAL = """\n\nLưu ý: Bạn chỉ được trả lời ngắn gọn với một trong ba kết quả trên mà không giải thích gì thêm và không tạo thêm định dạng."""

NOTE_W_CONFIDENT = """\n\nLưu ý: Hãy trả lời theo định dạng 'kết quả đánh giá; độ tin cậy của đánh giá (theo thang điểm từ 0.0 đến 1.0); giải thích ngắn gọn kết quả đánh giá' và không tạo thêm định dạng nào khác."""

""" Define functions for this script"""
def evaluate(input, output, model, start=0):
    # Load input data and define output path based on model name and current time
    input_df = pd.read_excel(input, sheet_name=0)
    current_time = datetime.now().strftime("%y%m%d_%H%M%S")
    if output[-5:] == ".xlsx":
        output_path = output
    else:
        output_path = output +"/one-instruction_" + model + "_" + current_time + ".xlsx"
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
        prompt = CHATBOT_EVALUATE.format(question=question, expected_answer=expected_answer, received_answer=received_answer) + NOTE_NORMAL
        chatbot_label = request_LLM(model, prompt)
        # Append the result to the output file
        temporary_df = pd.DataFrame({
                'id': [row['id']],  
                'human_label': [human_label],
                'chatbot_label': [chatbot_label],
            })
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


def evaluate_with_confident(input, output, model, start=0):
    # Load input data and define output path based on model name and current time
    input_df = pd.read_excel(input, sheet_name=0)
    current_time = datetime.now().strftime("%y%m%d_%H%M%S")
    if output[-5:] == ".xlsx":
        output_path = output
    else:
        output_path = output +"/one-instruction_wconf_" + model + "_" + current_time + ".xlsx"
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
        prompt = CHATBOT_EVALUATE.format(question=question, expected_answer=expected_answer, received_answer=received_answer) + NOTE_W_CONFIDENT
        response = request_LLM(model, prompt)
        chatbot_label, confident, explanation = response.split(";")
        # Append the result to the output file
        temporary_df = pd.DataFrame({
                'id': [row['id']],  
                'human_label': [human_label],
                'chatbot_label': [chatbot_label],
                'confident': [confident],
                'explanation': [explanation],
            })
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