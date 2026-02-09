""" Import punlic libraries"""
import pandas as pd
from datetime import datetime
import progressbar
import os

""" Import functions from private library"""
from scripts.utils import *


""" Define global variables for this script"""
NOTGIVEN_CHECK = """Phân tích A_received bên dưới để xác định xem nó có từ chối trả lời câu hỏi Q bằng cách khẳng định thiếu các thông tin cần thiết hay không. Nếu A_received nêu rõ rằng thông tin cần thiết không đủ để trả lời Q hoặc cho rằng không thể cung cấp câu trả lời đầy đủ, trả lời "có". Ngược lại, nếu A_received cung cấp bất kỳ nội dung có ý nghĩa liên quan đến Q, trả lời "không".
Chỉ trả lời ngắn gọn "có" hoặc "không" mà không thêm lời giải thích hay định dạng:
- Q: "{question}"
- A_received: "{received_answer}"
"""
CONTENT_COMPARE = """Bỏ qua các chi tiết phụ như tiêu đề bài báo, hãy so sánh A_received với A_expected dựa trên các thông tin cốt lõi cần thiết. Xác định như sau:
1. Nếu A_received truyền đạt đầy đủ ý chính của A_expected, kể cả khi có thêm chi tiết phụ không làm thay đổi ý nghĩa, trả lời "tương đương".
2. Nếu A_received mâu thuẫn hoặc sai lệch các thông tin chủ chốt so với A_expected, trả lời "sai".
3. Nếu A_received thiếu các thông tin cốt lõi cần thiết, làm giảm tính đầy đủ của câu trả lời, trả lời "thiếu".
4. Nếu A_received chỉ bổ sung các chi tiết vượt quá cần thiết nhưng không gây nhầm lẫn hoặc lệch hướng nội dung cốt lõi, vẫn trả lời "tương đương". Chỉ trả lời một trong bốn từ: "sai", "thiếu", "dư thừa", "tương đương" mà không thêm lời giải thích hay định dạng:
- A_expected: "{expected_answer}"
- A_received: "{received_answer}"
"""
EXTRA_CHECK = """So sánh A_received với A_expected, tập trung vào các thông tin bổ sung không có trong A_expected. Xác định xem các chi tiết phụ đó có làm thay đổi hoặc gây hiểu nhầm ý nghĩa cốt lõi của A_expected hay không:
- Nếu có bất kỳ thông tin bổ sung nào khiến nội dung chính bị lệch hướng hoặc gây nhầm lẫn, trả lời "có".
- Nếu các thông tin thêm chỉ là chi tiết phụ không ảnh hưởng đến ý chính, trả lời "không".
Chỉ trả lời ngắn gọn "có" hoặc "không" mà không thêm lời giải thích hay định dạng:
- Q: "{question}"
- A_expected: "{expected_answer}"
- A_received: "{received_answer}"
"""
MISSING_CHECK = """So sánh A_received với A_expected, tập trung vào các thông tin cốt lõi cần có trong A_expected. Xác định xem A_received có bị thiếu những thông tin chủ chốt nào làm giảm tính đầy đủ hoặc làm sai lệch ý nghĩa chính của câu trả lời hay không:
- Nếu thiếu bất kỳ thông tin quan trọng nào khiến nội dung cốt lõi bị ảnh hưởng, trả lời "có".
- Nếu những thiếu sót chỉ là chi tiết phụ không làm mất đi ý chính, trả lời "không".
Chỉ trả lời ngắn gọn "có" hoặc "không" mà không thêm lời giải thích hay định dạng:
- Q: "{question}"
- A_expected: "{expected_answer}"
- A_received: "{received_answer}"
"""


""" Define functions for this script"""
def evaluate(input, output, model, start):
    # Load input data and define output path based on model name and current time
    input_df = pd.read_excel(input, sheet_name=0)
    current_time = datetime.now().strftime("%y%m%d_%H%M%S")
    if output[-5:] == ".xlsx":
        output_path = output
    else:
        output_path = output +"/decision-chain_2_" + model + "_" + current_time + ".xlsx"
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
        # Request LLM for each step of the decision chain
        notgiven_check = request_LLM(model, prompt=NOTGIVEN_CHECK.format(question=question, received_answer=received_answer))
        notgiven_check = str(notgiven_check).lower()        
        content_compare, extra_check, missing_check = "", "", ""
        if 'có' in notgiven_check:
            chatbot_label = 'NOT GIVEN'
        else:
            content_compare = request_LLM(model, prompt=CONTENT_COMPARE.format(expected_answer=expected_answer, received_answer=received_answer))
            content_compare = str(content_compare).lower()
            match content_compare:
                case 'sai':
                    chatbot_label = 'FALSE'
                case 'tương đương':
                    chatbot_label = 'TRUE'
                case 'dư thừa':
                    extra_check = request_LLM(model, prompt=EXTRA_CHECK.format(question=question, expected_answer=expected_answer, received_answer=received_answer))
                    extra_check = str(extra_check).lower()
                    chatbot_label = 'FALSE' if 'có' in extra_check else 'TRUE'
                case 'thiếu':
                    missing_check = request_LLM(model, prompt=MISSING_CHECK.format(question=question, expected_answer=expected_answer, received_answer=received_answer))
                    missing_check = str(missing_check).lower()
                    chatbot_label = 'FALSE' if 'có' in missing_check else 'TRUE'
        # Append the result to the output file
        temporary_df = pd.DataFrame({
                'id': [row['id']],  
                'human_label': [human_label],
                'notgiven_check': [notgiven_check],
                'content_compare': [content_compare],
                'extra_check': [extra_check],
                'missing_check': [missing_check],
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
    print(f"Accuracy of decision_chain_2 for model {model}:")
    print(f"TRUE: {acc_T:.2f}, FALSE: {acc_F:.2f}, NOT GIVEN: {acc_N:.2f}, Average: {acc:.2f}")
    return output_path