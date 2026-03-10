import argparse
from scripts import one_instruction, decision_chain_2, k_step_conf

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--type', type=str, required=True, choices=["one_instruction", "decision_chain_2", "k_step_conf"])
    parser.add_argument('-m', '--model', type=str, required=True)
    parser.add_argument('-k', type=int, default=3)
    parser.add_argument('-n', type=int, default=0)
    parser.add_argument('-i', '--input', type=str, default="input/qa_300.xlsx")
    parser.add_argument('-o', '--output', type=str, default="output/qa_300")
    args = parser.parse_args()

    # NOTE: Ensure you have populated your API keys properly before running the evaluation.
    # Check apiKeys.py or your environment variables.

    if args.type == "one_instruction":
        output = one_instruction.evaluate(args.input, args.output, args.model, args.n)
    elif args.type == "decision_chain_2":
        output = decision_chain_2.evaluate(args.input, args.output, args.model, args.n) 
    elif args.type == "k_step_conf":
        output = k_step_conf.evaluate(args.input, args.output, args.model, args.k, args.n)

if __name__ == "__main__":
    main()
