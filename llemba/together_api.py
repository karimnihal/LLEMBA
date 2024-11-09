import os
import sys
import time
import logging
from termcolor import colored
from datetime import datetime
from together import Together
from dotenv import load_dotenv
import tqdm

load_dotenv()  # Load environment variables from .env

class TogetherApi:
    def __init__(self, verbose=False):
        self.verbose = verbose
        api_key = os.getenv('TOGETHER_API_KEY')
        if not api_key:
            raise ValueError("API key not found. Please set the TOGETHER_API_KEY environment variable.")
        self.client = Together(api_key=api_key)
        logging.getLogger().setLevel(logging.CRITICAL)  # Suppress all HTTP INFO log messages

    # answer_id is used for determining if it was the top answer or how deep in the list it was
    def request(self, prompt, model, parse_response, temperature=0.0, answer_id=-1, cache=None, max_tokens=None):
        if cache is None:
            cache = {}
        request = {"model": model, "temperature": temperature, "prompt": prompt}

        # Convert the request dictionary to a hashable key
        request_key = tuple(sorted(request.items()))

        if request_key in cache and cache[request_key] is not None and len(cache[request_key]) > 0:
            answers = cache[request_key]
        else:
            answers = self.request_api(prompt, model, temperature, max_tokens)
            cache[request_key] = answers

        # There is no valid answer
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
            finish_reason = full_answer["finish_reason"]
            full_answer_text = full_answer["answer"]
            answer_id += 1
            answer = parse_response(full_answer_text)
            if self.verbose or temperature > 0:
                print(f"Answer (t={temperature}): " + colored(answer, "yellow") + " (" + colored(full_answer_text, "blue") + ")", file=sys.stderr)
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

        # There was no valid answer, increase temperature and try again
        if len(parsed_answers) == 0:
            if temperature >= 1.0:
                return []
            new_temperature = min(temperature + 0.1, 1.0)
            return self.request(prompt, model, parse_response, temperature=new_temperature, answer_id=answer_id, cache=cache, max_tokens=max_tokens)

        return parsed_answers

    def request_api(self, prompt, model, temperature=0.0, max_tokens=None):
        if temperature > 1.0:
            return []

        while True:
            try:
                response = self.call_api(prompt, model, temperature, max_tokens)
                break
            except Exception as e:
                # Handle exceptions
                print(colored("Error, retrying...", "red"), file=sys.stderr)
                print(e, file=sys.stderr)
                time.sleep(1)

        answers = []
        # Access the choices attribute directly
        for choice in response.choices:
            # Access the message content directly
            if hasattr(choice, 'message') and choice.message.content is not None:
                answer = choice.message.content.strip()
            elif hasattr(choice, 'delta') and choice.delta.content is not None:
                answer = choice.delta.content.strip()
            else:
                answer = choice.text.strip() if hasattr(choice, 'text') else None

            if not answer:
                continue

            # Check if the response didn't finish due to max token limit
            finish_reason = choice.finish_reason

            # Only increase max_tokens if finish_reason is 'length' (i.e., response was cut off)
            if str(finish_reason).lower() == 'length':
                if self.verbose:
                    print(colored(f"Increasing max tokens to fit answers.", "red") + colored(answer, "blue"), file=sys.stderr)
                    print(f"Finish reason: {finish_reason}", file=sys.stderr)
                if max_tokens is None:
                    max_tokens = 0
                return self.request_api(prompt, model, temperature=temperature, max_tokens=max_tokens + 200)
            else:
                # Acceptable finish reason, proceed
                pass

            answers.append({
                "answer": answer,
                "finish_reason": finish_reason,
            })

        if len(answers) > 1:
            # Remove duplicate answers
            answers = [dict(t) for t in {tuple(d.items()) for d in answers}]

        return answers

    def call_api(self, prompt, model, temperature, max_tokens):
        parameters = {
            "model": model,
            "temperature": temperature,
            "top_p": 1.0,
            "top_k": 50,
            "repetition_penalty": 1.0,
            "stop": ["<|eot_id|>", "<|eom_id|>"],
            "stream": False,
        }

        if max_tokens is not None:
            parameters["max_tokens"] = max_tokens

        if isinstance(prompt, list):
            # Check that prompt contains a list of dictionaries with role and content
            assert all(isinstance(p, dict) for p in prompt), "Prompts must be a list of dictionaries."
            assert all("role" in p and "content" in p for p in prompt), "Prompts must be a list of dictionaries with role and content."
            parameters["messages"] = prompt
        else:
            parameters["messages"] = [{"role": "user", "content": prompt}]

        # Use the correct method for chat completion
        return self.client.chat.completions.create(**parameters)

    def bulk_request(self, df, model, parse_mqm_answer, cache, max_tokens=None):
        answers = []
        for i, row in tqdm.tqdm(df.iterrows(), total=len(df), file=sys.stderr):
            prompt = row["prompt"]
            parsed_answers = self.request(prompt, model, parse_mqm_answer, cache=cache, max_tokens=max_tokens)
            answers += parsed_answers
        return answers