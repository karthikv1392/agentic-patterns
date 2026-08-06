"""Text Analyzer Tool — Registry & Adapter pattern.

Registry metadata
-----------------
  capabilities : ["analyze", "text-stats", "word-count", "keywords", "frequency",
                  "reading-time", "vocabulary", "metrics", "complexity"]
  best_for     : measuring text properties, extracting top keywords, assessing
                 reading complexity, vocabulary richness analysis.

Implementation — fully deterministic, zero LLM calls
------------------------------------------------------
Pure Python text analysis using only the standard library:

  • Word / sentence / paragraph counts
  • Vocabulary richness (unique words ÷ total words)
  • Average sentence length
  • Estimated reading time (200 wpm average)
  • Top-N content keywords by frequency (stopwords filtered)
  • Flesch-Kincaid readability estimate (syllable approximation)

Because no LLM is involved, the same input always produces the same output.
The contrast with the agents (which ARE LLM-based) is the whole point of
having a separate Tool abstraction in the registry.
"""

import re
from collections import Counter

from shared.base_tool import BaseTool

CAPABILITIES = [
    "analyze", "text-stats", "word-count", "keywords", "frequency",
    "reading-time", "vocabulary", "metrics", "complexity",
]

BEST_FOR = [
    "counting words, sentences, and paragraphs",
    "extracting top keywords by frequency",
    "measuring vocabulary richness",
    "estimating reading time and text complexity",
]

_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "it", "its", "this", "that", "these", "those",
    "i", "you", "he", "she", "we", "they", "not", "no", "so", "as", "if",
    "from", "about", "into", "also", "can", "just", "than", "then", "when",
    "which", "who", "what", "how", "all", "each", "more", "one", "two",
    "any", "our", "your", "their", "my", "his", "her", "up", "out", "s",
})


def _count_syllables(word: str) -> int:
    """Approximate syllable count using vowel-group heuristic."""
    word = word.lower().rstrip("e")
    vowels = re.findall(r"[aeiouy]+", word)
    return max(len(vowels), 1)


def _flesch_kincaid_grade(total_words: int, total_sentences: int, total_syllables: int) -> float:
    if total_sentences == 0 or total_words == 0:
        return 0.0
    return (
        0.39 * (total_words / total_sentences)
        + 11.8 * (total_syllables / total_words)
        - 15.59
    )


class TextAnalyzerTool(BaseTool):

    @property
    def name(self) -> str:
        return "Text Analyzer"

    @property
    def description(self) -> str:
        return (
            "Deterministically analyses any text: word/sentence/paragraph counts, "
            "vocabulary richness, top keywords by frequency, reading time, "
            "and Flesch-Kincaid readability grade. No LLM — pure Python."
        )

    @property
    def capabilities(self) -> list[str]:
        return CAPABILITIES

    def run(self, task: str) -> str:
        """Analyse the text contained in *task* and return statistics."""
        text = task  # the full input (may include context + sub-task prefix)

        # --- tokenise ---
        words     = re.findall(r"\b[a-zA-Z']+\b", text)
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        word_count      = len(words)
        sentence_count  = max(len(sentences), 1)
        paragraph_count = max(len(paragraphs), 1)
        unique_words    = len({w.lower() for w in words})
        vocab_richness  = (unique_words / word_count * 100) if word_count else 0
        avg_sent_len    = word_count / sentence_count
        reading_time    = word_count / 200  # minutes at 200 wpm

        # Flesch-Kincaid
        total_syllables = sum(_count_syllables(w) for w in words)
        fk_grade        = _flesch_kincaid_grade(word_count, sentence_count, total_syllables)

        # Top keywords (excluding stopwords, min 3 chars)
        content_words = [w.lower() for w in words if w.lower() not in _STOPWORDS and len(w) >= 3]
        top_keywords  = Counter(content_words).most_common(10)

        # --- format output ---
        lines = [
            "**Text Analyzer Tool** *(deterministic — pure Python, no LLM)*\n",
            "**Basic Statistics**\n",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total words | **{word_count:,}** |",
            f"| Unique words | **{unique_words:,}** ({vocab_richness:.1f}% vocabulary richness) |",
            f"| Sentences | **{sentence_count}** |",
            f"| Paragraphs | **{paragraph_count}** |",
            f"| Avg sentence length | **{avg_sent_len:.1f}** words |",
            f"| Estimated reading time | **{reading_time:.1f} min** |",
            f"| Flesch-Kincaid grade | **{fk_grade:.1f}** "
            f"({'easy' if fk_grade < 8 else 'moderate' if fk_grade < 12 else 'complex'}) |",
            "",
        ]

        if top_keywords:
            lines.append("**Top Keywords by Frequency**\n")
            for word, count in top_keywords:
                bar = "█" * count
                lines.append(f"• `{word}` — {count}x  {bar}")

        return "\n".join(lines)
