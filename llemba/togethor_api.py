import os
import sys
import time
import logging
import requests
import tqdm
from termcolor import colored

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TOGETHER_AI_TOKEN = os.getenv("TOGETHER_AI_TOKEN")
if not TOGETHER_AI_TOKEN:
    raise Exception("Together AI token is not set in the .env file")

class TogethorApi:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.api_url = "https://api.together.xyz/v1/completions"
        self.model_name = "togethercomputer/LLaMA-2-70B-chat"  # Set the Together AI model here
        logging.getLogger().setLevel(logging.CRITICAL)  # Suppress logging info

    def request(self, prompt, model=None, parse_response=lambda x: x, temperature=0, answer_id=-1, cache=None, max_tokens=200):
        request = {"model": self.model_name, "temperature": temperature, "prompt": prompt, "max_tokens": max_tokens}

        if request in cache and cache[request] is not None and len(cache[request]) > 0:
            answers = cache[request]
        else:
            answers = self.request_api(prompt, temperature, max_tokens)
            cache[request] = answers

        if len(answers) == 0:
            return [{
                "temperature": temperature,
                "answer_id": answer_id,
                "answer": None,
                "prompt": prompt,
                "finish_reason": None,
                "model": self.model_name,
            }]

        parsed_answers = []
        for full_answer in answers:
            finish_reason = full_answer["finish_reason"]
            full_answer = full_answer["answer"]
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
                    "model": self.model_name,
                }
            )

        if len(parsed_answers) == 0:
            return self.request(prompt, parse_response, temperature=temperature + 1, answer_id=answer_id, cache=cache)

        return parsed_answers

    def request_api(self, prompt, temperature=0, max_tokens=200):
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
                return [{"answer": choice["text"].strip(), "finish_reason": choice.get("finish_reason", "stop")} for choice in data.get("choices", [])]
            except requests.exceptions.RequestException as e:
                print(colored("Error, retrying...", "red"), file=sys.stderr)
                print(e, file=sys.stderr)
                time.sleep(1)

    def bulk_request(self, df, parse_mqm_answer, cache, max_tokens=200):
        answers = []
        for i, row in tqdm.tqdm(df.iterrows(), total=len(df), file=sys.stderr):
            prompt = row["prompt"]
            parsed_answers = self.request(prompt, parse_mqm_answer, cache=cache, max_tokens=max_tokens)
            answers += parsed_answers
        return answers