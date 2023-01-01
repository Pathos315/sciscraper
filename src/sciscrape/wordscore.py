from dataclasses import (
    dataclass,
    asdict,
)
from typing import Optional, Union
from math import comb
import numpy as np
from scipy.stats import binom


@dataclass(slots=True, order=True)
class RelevanceCalculator:
    """
    A class for calculating the relevance of a paper or
    abstract based on its target and bycatch words.

    This class contains attributes and methods for
    calculating the wordscore of a paper or abstract
    based on the number of times target and
    bycatch words appear in it, its length,
    and a prior zero-shot classification score.

    Attributes:
        pos_part (float): The number of times a target word
            appeared in the paper or abstract.
        neg_part (float): The number of times a bycatch word
            appeared in the paper or abstract.
        total_len (int): The total number of words in the paper or abstract.
        implicature_score (float, Optional): The highest score
            from a prior `DocScraper` zero-shot classification.

    Methods:
        __call__ : returns wordscore value as a float
    """

    pos_part: int
    neg_part: int
    total_len: int
    implicature_score: Optional[float]

    def __call__(self) -> float:
        """
        Equation Variables
        ------------------
        - `total_len`: the total number of words in the text.
        - `pos_part`: the number of matches between the word and the search term.
        - `neg_part` represents the number of "bycatch" occurrences of the word, which are not matches to the search term.
        - `neutral_part`: the total number of words minus the number of matches.
        - `failure_margin`: the probability of the observations occurring given that the event has not occurred.
            This is calculated as the `neutral_part` divided by the total number of words (`total_len`) to the power of the neutral part.
        - `match_likelihood`: represents P(B|A), or the likelihood of the observations (B) occurring, given that the event (A) has occurred.
            This likelihood is calculated using a binomial distribution, which takes into account:
                - the number of matches (`pos_part`),
                - the total number of words (`total_len`), and
                - the number of neutral words (`neutral_part`).
        -`true positives`: the probability of a match occurring, given that the event has occurred.
            This is calculated as the number of matches (`pos_part`) divided by the total number of words (`total_len`).
        - `false positives`: the probability of a "bycatch" occurrence happening, given that the event has not occurred.
            This is calculated as the number of "bycatch" occurrences (`neg_part`) divided by the total number of words (`total_len`).
        - `positive posterior`: the probability of the event occurring, given the observations.
            This is calculated using Bayes' theorem, which takes into account:
                - the likelihood of the observations occurring (`match_likelihood`),
                - the prior probability of the event occurring (`true positives`), and
                - the probability of the observations occurring given that the event has not occurred, (`failure margin`).
        - `negative posterior` represents the probability of the event not occurring, given the observations.
            This is calculated in a similar way to the positive posterior, but with the likelihood and prior probability values reversed.
        - `unweighted_wordscore` represents the penulimate probability of the event occurring,
            which is calculated as the difference between the positive posterior and negative posterior.
        """
        # Neutral Part is all the words that are not the matching words
        neutral_part: int = self.total_len - self.pos_part

        # Failure Margin is the neutral part (k) over the total length n to the power of k,
        # i.e. (k/n)** k
        failure_margin: float = self.get_probability(
            neutral_part,
            self.total_len,
        )

        # Success_likelihood is the binomial distribution formula
        # Total combinations is total length choose matching words, nCx
        # i.e. (n! / (x! * (n-x)!)
        # i.e. total_length! / (positive_part! * (total_length - positive_part)!)
        # success margin = (x/n)^x
        # i.e. positive part / total length to the power of the positive part
        # these all produce the match likelihood
        match_likelihood: float = self.get_binomial_probability(failure_margin)

        # True positives is the positive part over the total length
        true_positive: float = self.pos_part / self.total_len

        # False positives is the bycatch part over the total length
        false_positive: float = self.neg_part / self.total_len

        # positive posterior is a bayes equation, in which the match likelihood is multiplied by the true positives ratio
        # and then divided by the likelihood plus the failure margin
        # The formula, therefore, is
        pos_posterior = self.bayes_theorem(
            true_positive,
            match_likelihood,
            failure_margin,
        )
        # negative posterior is also a bayes equation,
        # in which the match likelihood is multiplied by the failure margin
        # and then divided by the likelihood plus the failure margin
        # The formula, therefore, is
        neg_posterior = self.bayes_theorem(
            false_positive,
            failure_margin,  # failure margin treated as likelihood because it's inversed
            match_likelihood,  # success likelihood treated as margin because it's inversed
        )
        # The negative posterior is then subtracted
        # from the positive posterior
        # to produce the unweighted wordscore
        unweighted_wordscore = pos_posterior - neg_posterior
        # The highest zero shot classification score
        # accounts for about 20% of the final wordscore
        return self.calculate_wordscore(unweighted_wordscore)

    def get_binomial_probability(self, failure_margin) -> float:
        # start binomial distribution i.e. (n! / (x! * (n-x)!) * (x/n)^x * ((n-x)/n)^(n-x))
        total_combinations: int = comb(
            self.total_len,
            self.pos_part,
        )
        success_probability: float = self.get_probability(
            self.pos_part,
            self.total_len,
        )
        return total_combinations * success_probability * failure_margin

    @staticmethod
    def bayes_theorem(prior: float, likelihood: float, margin: float) -> float:
        """
        bayes_theorem calculates the posterior using Bayes Theorem.

        Args:
            prior (float): The total number of true positive words found.
            likelihood (float): The likelihood of this outcome, given the calculated binomial probability
            margin (float): The probability of failure, given the calculated binomial probability

        Returns:
            float: posterior, or the likelihood of the paper being a match given the words present.
        """
        hypothesis = prior * likelihood
        total_evidence = hypothesis + margin
        posterior = hypothesis / total_evidence
        return posterior

    def calculate_wordscore(self, likelihood: float) -> float:
        """
        Calculates the final word score based on the
            raw probability and the implicature score.

        Args:
            raw_probability (float): The raw probability that the paper is relevant.

        Returns:
            float: The final word score, as a percentage.

        Example:
        >>> calculator =
            RelevanceCalculator(
                pos_part=2,
                neg_part=1,
                total_len=100,
                implicature_score=0.9
            )
        >>> calculator.calculate_wordscore(0.6)
        0.74 # or 74%
        """
        weight = 0.85
        self.implicature_score = (
            0.5 if self.implicature_score is None else self.implicature_score
        )
        return (likelihood * weight) + (self.implicature_score * (1 - weight))

    @staticmethod
    def get_probability(
        part: Union[int, float],
        whole: Union[int, float],
    ) -> float:
        """
        Calculates the probability of an event occurring based on the part and the whole.

        Args:
            part (int or float): The part that represents the event of interest.
            whole (int or float): The total amount or size.

        Returns:
            float: The probability of the event occurring.

        Example
        ------
        >>> RelevanceCalculator.get_probability(part=2, whole=4)
        (2 / 4) ** 2
        = 4 / 16
        = 1 / 4
        = 0.25
        """
        return (part / whole) ** part

    @classmethod
    def from_dict(cls, dict_input: dict):
        return RelevanceCalculator(**dict_input)

    def to_dict(self):
        return asdict(self)
