# proposal-checker

Grade an Upwork proposal from 0 to 100 before you send it, and get the three fixes that matter most.

A client sees the first two lines of your proposal in the applicant list and decides in seconds. This checker reads your proposal in that same order: the opening first, then whether it talks about their job, then proof, then the ask.

```
14/100  [D]  54 words

  hook       #####...........   10/30  opens with a stock line: "Dear Hiring Manager, I am an expert developer..."
  relevance  ##..............    2/20  reuses 1 of 20 key words from the post; not mentioned: conversion, mobile, shopify
  proof      ................    0/20  no numbers: add one result with a figure; no link to similar work
  ask        ................    0/15  no question or next step at the end
  length     ###.............    2/10  54 words: too short
  clean      ................    0/5   filler: 'i am the best fit', 'kindly', '100% satisfaction', ...

  Fix first:
  1. End with one specific question about their project.
  2. Delete the stock phrases. Say the specific thing instead.
  3. Reuse the post's own words for the task, the stack and the outcome.
```

The same job, answered well ([examples/good.txt](examples/good.txt)), scores 100.

## The checks

| Check | Points | Passes when |
|---|---|---|
| Hook | 30 | The first two lines name the client's problem, with no "Dear Sir" or "I am an expert" opener |
| Relevance | 20 | The proposal reuses the key words of the job post |
| Proof | 20 | At least one result with a number, and a link to similar work |
| Ask | 15 | It ends with a question or a clear next step |
| Length | 10 | 80 to 220 words |
| Clean | 5 | None of the stock phrases every other bidder sends |

Grades: A 85+, B 70 to 84, C 55 to 69, D below 55.

## Install

```bash
pip install git+https://github.com/abhishek-growth-dev/proposal-checker
```

Python 3.10+, no dependencies.

## Command line

```bash
proposal-checker my-proposal.txt --job job-post.txt
proposal-checker my-proposal.txt --job job-post.txt --json
proposal-checker my-proposal.txt --min 70   # exit code 1 below 70, for scripts and pipelines
```

## Python

```python
from proposal_checker import check_proposal

report = check_proposal(proposal_text, job_text)
print(report.total, report.grade)
for fix in report.fixes:
    print("-", fix)
```

## Pair it with the job scorer

Score the job with [upwork-job-scorer](https://github.com/abhishek-growth-dev/upwork-job-scorer) first, so you only write proposals for jobs worth winning. Then check the proposal here before it goes out.

## Tests

```bash
python -m unittest discover -s tests -v
```

MIT licensed. Built by [Abhishek Bhambhana](https://github.com/abhishek-growth-dev), founder of [Upwork Growth Desk](https://upgrowthdesk.com).
