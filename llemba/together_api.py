import os
import sys
import time
import logging
import tqdm
from termcolor import colored
from together import Together

# class for calling Together AI API and handling cache
class TogetherApi:
    def __init__(self, api_key=None, verbose=False):
        # Check if api_key is provided or fall back to environment variable
        self.api_key = api_key or os.getenv("TOGETHER_API_KEY")
        
        if not self.api_key:
            raise ValueError("API key is required. Set it as an argument or in the environment variable 'TOGETHER_API_KEY'.")

        self.verbose = verbose
        self.client = Together(self.api_key)
        
        # Set logging level
        logging.getLogger().setLevel(logging.CRITICAL)  # Suppress HTTP INFO log messages

    # answer_id is used for determining if it was the top answer or how deep in the list it was
    def request(self, prompt, model, parse_response, temperature=0.0, answer_id=-1, cache=None, max_tokens=None):
        request = {"model": model, "temperature": temperature, "prompt": prompt}

        if request in cache and cache[request] is not None and len(cache[request]) > 0:
            answers = cache[request]
        else:
            answers = self.request_api(prompt, model, temperature, max_tokens)
            cache[request] = answers

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
                    "model": model,
                }
            )

        # There was no valid answer, increase temperature and try again
        if len(parsed_answers) == 0 and temperature < 1.0:
            return self.request(prompt, model, parse_response, temperature=temperature + 0.1, answer_id=answer_id, cache=cache)

        return parsed_answers

    def request_api(self, prompt, model, temperature=0.0, max_tokens=None):
        if temperature > 1.0:
            return []

        while True:
            try:
                answers = self.call_api(prompt, model, temperature, max_tokens)
                break
            except Exception as e:
                # Handle exceptions and retry
                print(colored("Error, retrying...", "red"), file=sys.stderr)
                print(e, file=sys.stderr)
                time.sleep(1)

        return answers

    def call_api(self, prompt, model, temperature, max_tokens):
        parameters = {
            "model": model,
            "temperature": temperature,
            "top_p": 1,
            "top_k": 50,
            "repetition_penalty": 1,
            "stop": None,
            "stream": False
        }

        if max_tokens is not None:
            parameters["max_tokens"] = max_tokens

        if isinstance(prompt, list):
            parameters["messages"] = prompt
        else:
            parameters["messages"] = [{
                "role": "user",
                "content": prompt,
            }]

        response = self.client.chat.completions.create(**parameters)

        answers = []
        if hasattr(response, 'choices'):
            for choice in response.choices:
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    answer = choice.message.content.strip()
                elif hasattr(choice, 'text'):
                    answer = choice.text.strip()
                else:
                    answer = ''
                finish_reason = getattr(choice, 'finish_reason', None)

                if finish_reason != "stop":
                    if self.verbose:
                        print(colored(f"Increasing max tokens to fit answers.", "red") + colored(answer, "blue"), file=sys.stderr)
                    print(f"Finish reason: {finish_reason}", file=sys.stderr)
                    if max_tokens is None:
                        return []
                    return self.request_api(prompt, model, temperature=temperature, max_tokens=max_tokens + 200)

                answers.append({
                    "answer": answer,
                    "finish_reason": finish_reason,
                })
        else:
            # Handle unexpected response format
            print("No 'choices' in response.", file=sys.stderr)
            return []

        if len(answers) > 1:
            # Remove duplicate answers
            answers = [dict(t) for t in {tuple(d.items()) for d in answers}]

        return answers

    def bulk_request(self, df, model, parse_mqm_answer, cache, max_tokens=None):
        answers = []
        for i, row in tqdm.tqdm(df.iterrows(), total=len(df), file=sys.stderr):
            prompt = row["prompt"]
            parsed_answers = self.request(prompt, model, parse_mqm_answer, cache=cache, max_tokens=max_tokens)
            answers += parsed_answers
        return answers
