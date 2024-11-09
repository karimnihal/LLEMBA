from llemba.together_api import TogetherApi
from termcolor import colored
from dotenv import load_dotenv
import pandas as pd

load_dotenv()  # Load environment variables from .env

def parse_response(answer):
    # Implement your parsing logic here
    return answer

# Initialize the TogetherApi with verbose output
together_api = TogetherApi(verbose=True)

# List of prompts to process
prompts = [
    "Tell me a joke.",
    "What is the capital of France?",
    "Explain the theory of relativity.",
    "Give me a recipe for pancakes.",
    "How does a plane fly?"
]

# Create a DataFrame with the prompts
df = pd.DataFrame(prompts, columns=['prompt'])

# Model to use from Together AI
model = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"  # Use an available model from Together AI

# Cache dictionary to store responses
cache = {}

# Make a bulk request
answers = together_api.bulk_request(df, model, parse_response, cache=cache)

# Print the answers
for ans in answers:
    print(f"Prompt: {ans['prompt']}")
    print(f"Answer: {ans['answer']}")
    print('-' * 50)