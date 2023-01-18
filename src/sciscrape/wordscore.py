from __future__ import annotations

from dataclasses import dataclass, asdict
from math import comb, sqrt


@dataclass(frozen=True, order=True)
class Wordscore:
    probability: float
    expectation: float
    variance: float
    standard_deviation: float
    skewness: float

    @classmethod
    def from_dict(cls, dict_input: dict):
        return cls(**dict_input)

    def to_dict(self):
        return asdict(self)


@dataclass
class WordscoreCalculator:
    """
    A class for calculating the relevance of a paper or
    abstract based on its target and bycatch words.

    This class contains attributes and methods for
    calculating the wordscore of a paper or abstract
    based on the number of times target and
    bycatch words appear in it, its length,
    and a prior zero-shot classification score.

    Attributes:
        target_count (float): The number of times a target word
            appeared in the paper or abstract.
        bycatch_count (float): The number of times a bycatch word
            appeared in the paper or abstract.
        total_length (int): The total number of words in the paper or abstract.
        implicature_score (float, Optional): The highest score
            from a prior `DocScraper` zero-shot classification.

    Methods:
        __call__ : returns wordscore value as a float
    """

    target_count: int
    bycatch_count: int
    total_length: int

    def __call__(self) -> Wordscore:
        """
        Equation Variables
        ------------------
        - `total_length`: the total number of words in the text.
        - `target_count`: the number of matches between the word and the search term.
        - `bycatch_count` represents the number of "bycatch" occurrences
            of the word, which are not matches to the search term.
        - `neutral_part`: the total number of words minus the number of matches.
        - `failure_margin`: the probability of the observations occurring
            given that the event has not occurred.
            This is calculated as the `neutral_part` divided by
            the total number of words (`total_length`) to the power of the neutral part.
        - `likelihood`: represents P(B|A), or the likelihood of
            the observations (B) occurring, given that the event (A) has occurred.
            This likelihood is calculated using a binomial distribution,
            which takes into account:
                - the number of matches (`target_count`),
                - the total number of words (`total_length`), and
                - the number of neutral words (`neutral_part`).
        -`true positives`: the probability of a match occurring, given
            that the event has occurred.
            This is calculated as the number of matches (`target_count`)
            divided by the total number of words (`total_length`).
        - `false positives`: the probability of a "bycatch" occurrence happening,
            given that the event has not occurred.
            This is calculated as the number of "bycatch" occurrences (`bycatch_count`)
            divided by the total number of words (`total_length`).
        - `positive posterior`: the probability of the event occurring,
            given the observations. This is calculated using Bayes' theorem,
            which takes into account:
                - the likelihood of the observations occurring:
                    or (`likelihood`),
                - the prior probability of the event occurring:
                    or (`true positives`); and,
                - the probability of the observations occurring given
                    that the event has not occurred:
                    or (`failure margin`).
        - `negative posterior` represents the probability of
            the event not occurring, given the observations.
            This is calculated in a similar way to the positive posterior,
            but with the likelihood and prior probability values reversed.
        - `unweighted_wordscore` represents the penulimate
            probability of the event occurring,
            which is calculated as the difference between
            the positive posterior and negative posterior.
        """
        neutral_part = self.total_length - self.target_count
        success_margin = self.get_margin(
            self.target_count,
            self.total_length,
        )
        failure_margin = self.get_margin(
            neutral_part,
            self.total_length,
        )
        target_probability = self.target_count / self.total_length
        bycatch_probability = self.bycatch_count / self.total_length
        likelihood = self.get_likelihood(success_margin, failure_margin)
        expectation = self.target_count * target_probability
        variance = expectation * (1 - target_probability)
        standard_deviation = sqrt(variance)
        skewness = (failure_margin - target_probability) / standard_deviation

        # Positive posterior is a bayes equation, in which the match likelihood
        # is multiplied by the true positives ratio
        # and then divided by the likelihood plus the failure margin
        # The formula, therefore, is
        positive_posterior = self.bayes_theorem(
            prior=target_probability,
            likelihood=likelihood,
            margin=failure_margin,
        )
        # Negative posterior is also a bayes equation,
        # in which the match likelihood is multiplied by the failure margin
        # and then divided by the likelihood plus the failure margin
        # The formula, therefore, is
        neg_posterior = self.bayes_theorem(
            prior=bycatch_probability,
            likelihood=failure_margin,
            margin=likelihood,
        )
        # Note: Failure margin treated as likelihood because it's looking for bycatch, i.e. inverse
        # Moreover, success likelihood treated as margin because it's looking for bycatch, i.e. inverse

        # The negative posterior is then subtracted
        # from the positive posterior
        # to produce the unweighted wordscore
        wordscore = positive_posterior - neg_posterior
        return Wordscore(
            wordscore,
            expectation,
            variance,
            standard_deviation,
            skewness,
        )

    def get_likelihood(
        self,
        success_margin: float,
        failure_margin: float,
    ) -> float:
        """
        Applies the binomial probability mass function, given:
        - the total length `(y)`;
        - the total number of target matches `(n)`; and,
        - the `failure margin` defined as: `((n-y)/y)**(n-y)`

        Returns:
            model (float) : The likelihood of a paper of length `y` being
            relevant to our query, given the presense of `n` matches,
            i.e. `P(y|n)`.

        Further Explanation:
            - Total combinations is total length choose matching words, `nCx`;
            or `(n! / (x! * (n-x)!)`
        --------
        >>> P(y|n) = (n! / (y! * (n-y)!) * (y/n)**y * ((n-y)/n)**(n-y))
        """
        total_combinations = comb(
            self.total_length,
            self.target_count,
        )
        model = total_combinations * success_margin * failure_margin
        return model

    def bayes_theorem(
        self,
        *,
        prior: float,
        likelihood: float,
        margin: float,
    ) -> float:
        """
        bayes_theorem calculates the posterior using Bayes Theorem.

        Args:
            prior (float): The total number of true positive words found.
            likelihood (float): The likelihood of this outcome,
                given the calculated binomial probability
            margin (float): The probability of failure,
                given the calculated binomial probability

        Returns:
            posterior (float): the likelihood of the paper being a match given the words present.
        --------
        >>> P(n|y) = (n! / (y! * (n-y)!) * (y/n)**y * ((n-y)/n)**(n-y)) * (y/n))
            / ((n! / (y! * (n-y)!) * (y/n)**y * ((n-y)/n)**(n-y)) + ((n-y)/n)**(n-y)))
        >>> P(n|y) = (P(y|n) * P(y)) / (P(y|n) + P(n-y))
        """
        hypothesis = prior * likelihood
        total_evidence = hypothesis + margin
        posterior = hypothesis / total_evidence
        return posterior

    def get_margin(
        self,
        part: int | float,
        whole: int | float,
    ) -> float:
        """
        Calculates the margin of an event occurring based on the part divided by the whole,
        to the power of the part. e.g. Failure Margin is the neutral part `m`
        over the total length `n` to the power of `m`, i.e. `(m/n)** m`

        Args:
            part (int or float): The part that represents the event of interest.
            whole (int or float): The total amount or size.

        Returns:
            float: The probability of the event occurring.

        Example
        ------
        >>> WordscoreCalculator.get_margin(part=2, whole=4)
        (2 / 4) ** 2
        = 4 / 16
        = 1 / 4
        = 0.25
        """
        return (part / whole) ** part

    @classmethod
    def from_dict(cls, dict_input: dict):
        return cls(**dict_input)

    def to_dict(self):
        return asdict(self)
