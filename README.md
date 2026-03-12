# ChatbotEvaluation

This repository provides the code and dataset samples as supporting documents for our paper: **[End-to-End Chatbot Evaluation with Adaptive Reasoning and Uncertainty Filtering](https://arxiv.org/abs/2603.10570)**.

This work is accepted at **ACIIDS 2026** _(18th Asian Conference on Intelligent Information and Database Systems)_.

### About the Project
We propose an end-to-end automatic framework to reliably evaluate domain-specific chatbots (especially those relying on retrieval-augmented generation) with minimal human effort. Our system automatically synthesizes Q&A pairs from underlying knowledge bases, uses an LLM-as-a-judge to evaluate chatbot responses against reference answers, and applies uncertainty filtering to flag edge cases. This repository contains the evaluation pipelines, the generated dataset sample, and the code used to measure evaluation accuracy scaling.

## 1. Create environment
Prompt command line, input below commands:
- `conda create -n "myenv" python>=3.12`
- `conda activate myenv`
- `pip install -r requirement.txt`

## 2. API Keys configuration
**IMPORTANT**: Before running any scripts, please remind to setup and configure your API keys! 
You need to supply your model keys corresponding to the models you wish to use (OpenAI, Gemini, DeepSeek, etc.).

We provide an `apiKeys_sample.py` file. You should:
1. Rename `apiKeys_sample.py` to `apiKeys.py`.
2. Replace the placeholder strings with your actual API keys.
3. Make sure never to commit your real `apiKeys.py` to version control. Uses of `apiKeys.py` are locally imported by our scripts.

## 3. Generate Q&A Dataset
Originally, the generation of Q&A dataset was performed dynamically within a chatbot platform through a user interface connected to a large knowledge base retrieval system. Note that we omit that proprietary implementation.
To simplify the process and allow reproduction, we mimic looking into the original knowledge base by having the `generate_dataset.py` script access data directly from `input/article.xlsx`.

This script will generate only the **question** and **expected_answer** columns.

**Note**: The process of collecting the `received_answer` must be done by the reader themselves! You will need to take the generated questions and feed them into your own knowledge-base/chatbot system, then manually populate the `received_answer` column in the resulting excel file before running the evaluate script. For convenience and reproducibility, readers may alternatively use `input/qa_300.xlsx`, which contains the same dataset used in the publication.

Arguments:
- `-i`: Path to the input excel file (e.g. `input/article.xlsx`).
- `-o`: Output file to save the generated Q&A dataset.
- `-m`: Model to use (default: `gemini-1.5-flash-002`).
- `-n`: Number of questions to generate per article (default: `5`).

```bash
python generate_dataset.py -i input/article.xlsx -o output/generated_qa_pairs.xlsx -m gemini-1.5-flash-002 -n 5
```

## 4. Run evaluate
Use the `evaluate.py` script to run evaluation pipelines on the Q&A dataset.
There are several arguments that need to be provided or adjusted:
- `--type` or `-t`: Evaluation mechanism. Options are:
    - `one_instruction`
    - `decision_chain_2`
    - `k_step_conf`
- `--model` or `-m`: 
    - `gemini-1.5-flash-002`, `gemini-1.5-pro-002`, `gemini-2.0-flash-001`
    - `gpt-4o-2024-08-06`, `gpt-4o-mini-2024-07-18`, `o1-mini-2024-09-12`
    - `DeepSeek-V3`, `DeepSeek-R1`
- `-k`: The specific steps constraint parameter for the k-step confidence model (default is 3).
- `-n`: The starting index. The script will process data starting from this index to the end of the input file. If `0`, it runs on the entire dataset from the beginning (default is 0).
- `--input` or `-i`: path to the input dataset, default is `input/qa_300.xlsx`
- `--output` or `-o`: path to save results, default is `output/qa_300`

### Example
```bash
python evaluate.py -t k_step_conf -m gpt-4o-mini-2024-07-18 -i input/qa_300.xlsx
```

## 5. Filter Uncertain Cases
As mentioned in our paper, we feature uncertainty filtering by setting a confidence threshold. After evaluation, you can run the `filter_uncertainty.py` script to automatically extract uncertain edge cases (responses below the chosen threshold) to a new Excel file. 

The script dynamically detects if the dataset was generated using a `k_step` model (which contains multiple `step_confidence` columns) and calculates the multiplied confidence score to aggregate uncertainty.

### Example
```bash
python filter_uncertainty.py -i output/qa_300/k-step_conf/general/your_evaluated_data.xlsx -o output/uncertain_cases.xlsx -t 0.8
```
- `-i`: Path to the evaluated dataset containing a `confidence` column.
- `-o`: Output file to save the filtered data.
- `-t`: Confidence threshold (default `0.8`).

## 6. Citation
If you find our work helpful for your research, please consider citing our paper:
```bibtex
@misc{dang2026endtoendchatbotevaluationadaptive,
      title={End-to-End Chatbot Evaluation with Adaptive Reasoning and Uncertainty Filtering}, 
      author={Nhi Dang and Tung Le and Huy Tien Nguyen},
      year={2026},
      eprint={2603.10570},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2603.10570}, 
}
```

## 7. Contact
For any questions, discussions, or inquiries, please feel free to reach out to the first author via email: dangmainhi129@gmail.com. You can also contact my supervisor if needed: ntienhuy@fit.hcmus.edu.vn.
