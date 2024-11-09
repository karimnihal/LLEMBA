# LLEMBA

This is a fork of the GEMBA Repository. Acknowledgements below.

Install required packages with python >= 3.8 

```
pip install -r requirements.txt
```

Set up secrets either for Together AI API: 

```
export TOGETHER_API_KEY=
```

## Scoring

It assumes two files with the same number of lines. It prints the score for each line pair:

```
python main.py --source=source.txt --hypothesis=hypothesis.txt --source_lang=English --target_lang=Czech --method="LLEMBA-DA" --model="meta-llama/LLama-3.2-3B-Instruct-Turbo"
```

The main recommended methods:`LLEMBA-DA` with the model `meta-llama/LLama-3.2-3B-Instruct-Turbo`.


## Acknowledgments

This project is an extension on the GEMBA work.

- **[GEMBA Repository](https://github.com/MicrosoftTranslator/GEMBA/)** 

Special thanks to the authors for their contributions and efforts.

If you use this repository, please consider citing their work:

### GEMBA-MQM 

    @inproceedings{kocmi-federmann-2023-gemba-mqm,
        title = {GEMBA-MQM: Detecting Translation Quality Error Spans with GPT-4},
        author = {Kocmi, Tom  and Federmann, Christian},
        booktitle = "Proceedings of the Eighth Conference on Machine Translation",
        month = dec,
        year = "2023",
        address = "Singapore",
        publisher = "Association for Computational Linguistics",
    }

### GEMBA-DA

    @inproceedings{kocmi-federmann-2023-large,
        title = "Large Language Models Are State-of-the-Art Evaluators of Translation Quality",
        author = "Kocmi, Tom and Federmann, Christian",
        booktitle = "Proceedings of the 24th Annual Conference of the European Association for Machine Translation",
        month = jun,
        year = "2023",
        address = "Tampere, Finland",
        publisher = "European Association for Machine Translation",
        url = "https://aclanthology.org/2023.eamt-1.19",
        pages = "193--203",
    }
