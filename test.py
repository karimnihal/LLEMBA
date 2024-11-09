
from llemba.together_api import TogetherApi
import pandas as pd
from dotenv import load_dotenv
import os
import sys
import time
import logging
import requests  # Import requests to handle HTTP requests
import tqdm
from termcolor import colored
from dotenv import load_dotenv
from together import Together

# Load environment variables from .env file
load_dotenv()

# Define a simple parsing function
def parse_mqm_answer(answer):
    return answer

# Sample DataFrame for testing
data = {
    "prompt": [
        "Tell me a fun fact about space.",
        "What is the capital of France?",
        "Who wrote 'To Kill a Mockingbird'?"
    ]
}
df = pd.DataFrame(data)

# Initialize TogetherApi and test bulk_request
together_api = TogetherApi(verbose=True)
responses = together_api.bulk_request(df, parse_mqm_answer, max_tokens=100)

# Print responses
for i, response in enumerate(responses):
    print(f"Response {i+1}: {response}")