"""Grade an Upwork proposal the way a busy client reads it.

A client sees the first two lines in the applicant list, decides in seconds,
and opens only the proposals that talk about their job. The checks follow
that order:

- hook      (30): do the first two lines talk about the client's job?
- relevance (20): does the proposal reuse the words of the job post?
- proof     (20): numbers, named results, links to real work
- ask       (15): does it end with a question or a clear next step?
- length    (10): short enough to finish (about 80 to 220 words)
- clean     ( 5): no filler phrases that every other bidder sends
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

WORD = re.compile(r"[A-Za-z0-9$%+#.'-]+")
STOP = set(
    """a an and are as at be but by for from has have i in is it its of on or our that the
    this to was we were will with you your my me us they them their there here what which
    who can could would should need needs looking want wants also just very more some any
    all into about than then so if do does not no""".split()
)
WEAK_OPENERS = [
    r"^\s*(dear|hello|hi|hey|greetings)\b[^\n]{0,40}(sir|madam|hiring manager|there|client)",
    r"^\s*(i am|i'm|my name is)\b",
    r"^\s*i (have|hold) (read|gone through|reviewed) (your|the) (job|post|description)",
    r"^\s*i am (a|an) (expert|experienced|professional|senior)",
    r"^\s*(with|having) \d+\+? years",
]
FILLER = [
    "i am the best fit", "perfect fit for this job", "i can do this job", "i have read your job",
    "kindly", "do the needful", "hope you are doing well", "hope this finds you well",
    "100% satisfaction", "look forward to hearing from you", "thanks in advance",
    "i am an expert", "i'm an expert", "awaiting your response", "please consider",
    "best regards", "highly skilled", "years of experience in",
]
ASK_PATTERNS = [
    r"\?\s*$", r"\?[^?]{0,80}$",
    r"\b(open to|happy to|free for|book|schedule|hop on|quick call|short call|send (me|over))\b[^.]{0,80}[.!]?\s*$",
]
LINK = re.compile(r"https?://\S+|\bwww\.\S+|\b[a-z0-9-]+\.(com|io|ai|app|dev|co)\b", re.I)
NUMBER_PROOF = re.compile(r"(\$\s?\d[\d,.]*\s?[kKmM]?\+?|\b\d+(\.\d+)?\s?%|\b\d+x\b|\b\d[\d,]*\+?\s(users|clients|stores|apps|sites|orders|leads|downloads|contracts|projects)\b)", re.I)


@dataclass
class Check:
    name: str
    points: float
    max_points: float
    notes: list[str] = field(default_factory=list)


@dataclass
class Report:
    total: int
    grade: str
    checks: list[Check]
    fixes: list[str]
    words: int

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "grade": self.grade,
            "words": self.words,
            "fixes": self.fixes,
            "checks": [
                {"name": c.name, "points": round(c.points, 1), "max": c.max_points, "notes": c.notes}
                for c in self.checks
            ],
        }


def _words(text: str) -> list[str]:
    return [w.strip(".,'-").lower() for w in WORD.findall(text)]


def _keywords(text: str, limit: int = 25) -> list[str]:
    counts: dict[str, int] = {}
    for w in _words(text):
        if len(w) > 2 and w not in STOP and not w.isdigit():
            counts[w] = counts.get(w, 0) + 1
    return [w for w, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]]


def _opening(text: str) -> str:
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    return " ".join(lines[:2])[:220]


def check_hook(proposal: str, job: str) -> Check:
    opening = _opening(proposal)
    low = opening.lower()
    pts, notes = 30.0, []
    for pat in WEAK_OPENERS:
        if re.search(pat, low):
            pts -= 15
            notes.append(f"opens with a stock line: \"{opening[:60]}...\"")
            break
    if job:
        kws = _keywords(job, 15)
        hits = [k for k in kws if re.search(rf"\b{re.escape(k)}\b", low)]
        if not hits:
            pts -= 12
            notes.append("first two lines never mention the job")
        else:
            notes.append(f"opening names: {', '.join(hits[:5])}")
    if low.count(" i ") + low.startswith("i ") >= 3:
        pts -= 5
        notes.append("opening is about you, not the client")
    return Check("hook", max(0, pts), 30, notes)


def check_relevance(proposal: str, job: str) -> Check:
    if not job:
        return Check("relevance", 10, 20, ["no job post given: relevance not measured"])
    kws = _keywords(job, 20)
    body = set(_words(proposal))
    hits = [k for k in kws if k in body]
    share = len(hits) / max(1, len(kws))
    pts = min(20, share * 40)
    notes = [f"reuses {len(hits)} of {len(kws)} key words from the post"]
    missing = [k for k in kws[:8] if k not in body]
    if missing:
        notes.append(f"not mentioned: {', '.join(missing[:5])}")
    return Check("relevance", pts, 20, notes)


def check_proof(proposal: str) -> Check:
    cleaned = proposal.lower()
    for f in FILLER:  # "100% satisfaction" is a promise, not a result
        cleaned = cleaned.replace(f, " ")
    nums = NUMBER_PROOF.findall(cleaned)
    links = LINK.findall(proposal)
    pts, notes = 0.0, []
    if nums:
        pts += min(12, 6 * len(nums))
        notes.append(f"{len(nums)} numbered result(s)")
    else:
        notes.append("no numbers: add one result with a figure")
    if links:
        pts += 8
        notes.append("links to work")
    else:
        notes.append("no link to similar work")
    return Check("proof", min(20, pts), 20, notes)


def check_ask(proposal: str) -> Check:
    tail = proposal.strip()[-220:].lower()
    for pat in ASK_PATTERNS:
        if re.search(pat, tail):
            return Check("ask", 15, 15, ["ends with a question or a next step"])
    if "?" in proposal:
        return Check("ask", 8, 15, ["has a question, but not at the end"])
    return Check("ask", 0, 15, ["no question or next step at the end"])


def check_length(words: int) -> Check:
    if 80 <= words <= 220:
        return Check("length", 10, 10, [f"{words} words"])
    if 60 <= words < 80 or 220 < words <= 300:
        return Check("length", 6, 10, [f"{words} words (aim for 80 to 220)"])
    return Check("length", 2, 10, [f"{words} words: {'too short' if words < 60 else 'too long to finish'}"])


def check_clean(proposal: str) -> Check:
    low = proposal.lower()
    found = [f for f in FILLER if f in low]
    pts = max(0, 5 - 2 * len(found))
    notes = [f"filler: {', '.join(repr(f) for f in found)}"] if found else ["no stock filler"]
    return Check("clean", pts, 5, notes)


FIX_FOR = {
    "hook": "Rewrite the first line to name the client's problem in their words.",
    "relevance": "Reuse the post's own words for the task, the stack and the outcome.",
    "proof": "Add one past result with a number and a link to it.",
    "ask": "End with one specific question about their project.",
    "length": "Cut to 80 to 220 words. Keep the hook, one proof, one question.",
    "clean": "Delete the stock phrases. Say the specific thing instead.",
}


def grade_for(total: int) -> str:
    return "A" if total >= 85 else "B" if total >= 70 else "C" if total >= 55 else "D"


def check_proposal(proposal: str, job: str = "") -> Report:
    words = len(_words(proposal))
    checks = [
        check_hook(proposal, job),
        check_relevance(proposal, job),
        check_proof(proposal),
        check_ask(proposal),
        check_length(words),
        check_clean(proposal),
    ]
    total = int(round(sum(c.points for c in checks)))
    weak = sorted(checks, key=lambda c: c.points / c.max_points)
    fixes = [FIX_FOR[c.name] for c in weak if c.points / c.max_points < 0.7][:3]
    return Report(total, grade_for(total), checks, fixes, words)
