import argparse
import pandas as pd
import re
from pathlib import Path

STEP_RE = re.compile(r"^step\d+_confidence$")

def main():
    parser = argparse.ArgumentParser(description="Filter uncertain Q&A pairs based on a confidence threshold.")
    parser.add_argument('-i', '--input', type=str, required=True, help="Path to the evaluated Excel dataset")
    parser.add_argument('-o', '--output', type=str, default="output/uncertain_cases.xlsx", help="Path to save the filtered Excel file")
    parser.add_argument('-t', '--threshold', type=float, default=0.8, help="Confidence threshold to filter uncertain cases (default: 0.8)")
    
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file {args.input} does not exist.")
        return

    print(f"Loading data from {args.input}...")
    df = pd.read_excel(input_path)

    if "confidence" not in df.columns:
        print("Error: The input file does not contain a 'confidence' column. Make sure you run evaluation first.")
        return

    df_clean = df.dropna(subset=["confidence"]).copy()

    # Calculate multiplied confidence if step confidence columns exist (from k-step model)
    step_cols = [c for c in df_clean.columns if STEP_RE.match(c)]
    if step_cols:
        df_clean["final_confidence"] = df_clean[step_cols].prod(axis=1) * df_clean["confidence"]
        print(f"Found step confidence columns: {step_cols}. Using multiplied confidence for filtering.")
    else:
        df_clean["final_confidence"] = df_clean["confidence"]
        print("No step confidence columns found. Using base 'confidence' for filtering.")

    # Filter rows below the given threshold
    uncertain_df = df_clean[df_clean["final_confidence"] < args.threshold].copy()

    print(f"Total samples with confidence score: {len(df_clean)}")
    print(f"Uncertain samples flagged (confidence < {args.threshold}): {len(uncertain_df)}")

    # Save output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    uncertain_df.to_excel(output_path, index=False)
    print(f"Filtered uncertain cases successfully saved to {output_path}")

if __name__ == "__main__":
    main()