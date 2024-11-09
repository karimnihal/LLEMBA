import os
import sys
import time
import logging
import tqdm
from termcolor import colored
from dotenv import load_dotenv
from together import Together  # Import Together client library

# Load environment variables from .env file
load_dotenv()

TOGETHER_AI_TOKEN = os.getenv("TOGETHER_AI_TOKEN")
if not TOGETHER_AI_TOKEN:
    raise Exception("Together AI token is not set in the .env file")

class TogetherApi:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.model_name = "meta-llama/Llama-3-70b-chat-hf"  # Updated model name
        self.client = Together(api_key=TOGETHER_AI_TOKEN)  # Initialize Together client with API key
        logging.getLogger().setLevel(logging.CRITICAL)  # Suppress logging info

    def request(self, prompt, model=None, parse_response=lambda x: x, temperature=0, answer_id=-1, cache=None, max_tokens=None, stream=False):
        # Use provided model or default to self.model_name
        model = model or self.model_name

        # If streaming is enabled, handle it here
        if stream:
            return self.request_stream(prompt, model, max_tokens)

        # Convert request dictionary to a tuple of sorted items for hashing
        request_key = tuple(sorted({"model": model, "temperature": temperature, "prompt": prompt, "max_tokens": max_tokens}.items()))

        # Initialize cache if it's None
        if cache is None:
            cache = {}

        if request_key in cache and cache[request_key] is not None and len(cache[request_key]) > 0:
            answers = cache[request_key]
        else:
            answers = self.request_api(prompt, temperature, max_tokens)
            cache[request_key] = answers

        if len(answers) == 0:
            return [{
                "temperature": temperature,
                "answer_id": answer_id,
                "answer": None,
                "prompt": prompt,
                "finish_reason": None,
                "model": model,
            }]

        parsed_answers = []
        for full_answer in answers:
            finish_reason = full_answer.get("finish_reason", "stop")
            full_answer = full_answer.get("answer", "")
            answer_id += 1
            answer = parse_response(full_answer)
            if self.verbose or temperature > 0:
                print(f"Answer (t={temperature}): " + colored(answer, "yellow") + " (" + colored(full_answer, "blue") + ")", file=sys.stderr)
            if answer is None:
                continue
            parsed_answers.append(
                {
                    "temperature": temperature,
                    "answer_id": answer_id,
                    "answer": answer,
                    "prompt": prompt,
                    "finish_reason": finish_reason,
                    "model": model,
                }
            )

        if len(parsed_answers) == 0:
            return self.request(prompt, parse_response, temperature=temperature + 1, answer_id=answer_id, cache=cache)

        return parsed_answers

    def request_stream(self, prompt, model, max_tokens):
        # Stream responses from Together API with updated parameters
        stream = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1,
            stop=["<|eot_id|>"],
            stream=True
        )

        # Print each chunk as it streams in
        for chunk in stream:
            if hasattr(chunk, 'choices'):
                content = chunk.choices[0].delta.content or ""
                print(content, end='', flush=True)

    def request_api(self, prompt, temperature=0, max_tokens=200):
        # This function is kept for non-streaming API calls, if needed
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature / 10,
            "top_p": 1,
            "n": 1,
            "stop": ["</s>"]
        }

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {TOGETHER_AI_TOKEN}"
        }

        while True:
            try:
                response = requests.post(self.api_url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                # Ensure choices exist in the response, else return empty list
                if "choices" not in data or data["choices"] is None:
                    print("No choices found in the response.")
                    return []

                # Extract answers, handling cases where "text" might not be present
                return [{"answer": choice.get("text", "").strip(), "finish_reason": choice.get("finish_reason", "stop")}
                        for choice in data["choices"]]
            except requests.exceptions.RequestException as e:
                print(colored("Error, retrying...", "red"), file=sys.stderr)
                print(e, file=sys.stderr)
                time.sleep(1)

    def bulk_request(self, df, parse_mqm_answer, cache=None, max_tokens=200):
        if cache is None:
            cache = {}
        answers = []
        for i, row in tqdm.tqdm(df.iterrows(), total=len(df), file=sys.stderr):
            prompt = row["prompt"]
            parsed_answers = self.request(prompt, parse_mqm_answer, cache=cache, max_tokens=max_tokens)
            answers += parsed_answers
        return answers