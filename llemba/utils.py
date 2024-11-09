import ipdb
import pandas as pd
import diskcache as dc

from llemba.together_api import TogetherApi
from llemba.llemba_mqm_utils import TEMPLATE_LLEMBA_MQM, apply_template, parse_mqm_answer
from llemba.prompt import prompts, validate_number


def get_llemba_scores(source, hypothesis, source_lang, target_lang, method, model):
    df = pd.DataFrame({'source_seg': source, 'target_seg': hypothesis})
    df['source_lang'] = source_lang
    df['target_lang'] = target_lang

    cache = dc.Cache(f'cache/{model}_{method}', expire=None, size_limit=int(10e10), cull_limit=0, eviction_policy='none')
    togetherapi = TogetherApi()

    if method == "LLEMBA-MQM":
        # df["prompt"] = df.apply(lambda x: apply_template(TEMPLATE_LLEMBA_MQM, x), axis=1)
        # parse_answer = lambda x: parse_mqm_answer(x, list_mqm_errors=False, full_desc=True)
        # answers = togetherapi.bulk_request(df, model, parse_answer, cache=cache, max_tokens=500)
        raise Exception(f"Method {method} not supported.")
    elif method in ["LLEMBA-DA", "LLEMBA-DA_ref", "LLEMBA-SQM", "LLEMBA-SQM_ref", "LLEMBA-stars", "LLEMBA-stars_ref", "LLEMBA-classes", "LLEMBA-classes_ref"]:
        df["prompt"] = df.apply(lambda x: apply_template(prompts[method]['prompt'], x), axis=1)
        parse_answer = prompts[method]["validate_answer"]
        answers = togetherapi.bulk_request(df, model, parse_answer, cache=cache, max_tokens=500)
    else:
        raise Exception(f"Method {method} not supported.")

    return list(pd.DataFrame(answers)['answer'])
