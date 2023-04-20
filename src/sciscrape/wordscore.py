from __future__ import annotations

from dataclasses import dataclass
from math import comb, sqrt


@dataclass(frozen=True)
class Wordscore:
    probability: float
    expectation: float
    variance: float
    standard_deviation: float
    skewness: float


@dataclass
class WordscoreCalculator:
    """
    A class for calculating the relevance of a paper or
    abstract based on its target and bycatch words.

    This class contains attributes and methods for
    calculating the wordscore of a paper or abstract
    based on the number of times target and
    bycatch words appear in it, and its overall length.

    Attributes:
        `target_count` (float): The number of times a target word,
            i.e. a word that indicates the paper is what we're looking for,
            appeared in the paper or abstract.
            In the context of the binomial trials
            this class will run, the `target_count` can be thought of as `k`
        `bycatch_count` (float): The number of times a bycatch word,
            i.e. a word that indicates the paper is
            NOT what we're looking for,
            appeared in the paper or abstract.
            In the context of the binomial trials this class will run,
            the `bycatch_count` can ALSO be thought of as `k`,
            or even `k'`/`k-prime`.
            I'm afraid this will likely lead to confusion.
        `total_length` (int): The total number of words found in
            the paper or abstract. In the context of the binomial
            trial this class will run,
            `total_length` can always be thought of as `n`.

    Methods:
        __call__ : returns a wordscore value as a float.
    """

    target_count: int
    bycatch_count: int
    total_length: int

    def __call__(self) -> Wordscore:
        """
        Intermediary Variables
        ------------------
        - `neutral_part`: or `total_length` minus the `target_count`.
            These are the words in the text that are either bycatch words,
            or they're irrelevant to what we're looking for.
        - `failure_margin`: the `neutral_part` divided by `total_length`
            to the power of the `neutral_part`.\n
            In other words:

            ```
            >>> failure_margin = (neutral part / total_length) ** neutral_part

            ```
            The `failure_margin` is derived from the probability mass function.

        - `success_margin`: defined as the `target_count` and
            the `total_length` to the power of the `target_count`.
            In other words:

            ```
            >>> success_margin = (target_count / total_length) ** target_count

            ```

        - `likelihood`: defined as the likelihood, P(B|A) of our paper being
            a match given the presence of `target_count` words.
            This is calculated using a binomial distribution formula

            ```
            >>> P(target_count | total_length) =
                (total_length! / (target_count! * (total_length - target_count)!)
                * success_margin
                * failure_margin
            ```
        - `target_probability`: defined as `target_count / total_length`
        - `bycatch_probability`: defined as `bycatch_count / total_length`
        - `positive posterior`: the probability of the `target_count` being present,
            given the paper provided. This is calculated using Bayes' theorem, i.e.:

            ```
            >>>  positive_posterior = (likelihood * true positives) / failure_margin
            ```

        - `negative posterior` represents the probability of the event
            not occurring, given the observations.
            This is calculated in a similar way to the positive posterior,
            but the `likelihood` and `failure_margin` swap places,
            and `target_probability` is swapped out for `bycatch_probability`.
            i.e.

            ```
            >>> negative_posterior = (failure_margin * bycatch_probability) / likelihood
            ```

        - `wordscore` is the final output as a float. It is simply:

            ```
            >>> wordscore = positive_posterior - negative posterior
            ```

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

        positive_posterior = self.bayes_theorem(
            prior=target_probability,
            likelihood=likelihood,
            margin=failure_margin,
        )
        negative_posterior = self.bayes_theorem(
            prior=bycatch_probability,
            likelihood=failure_margin,
            margin=likelihood,
        )
        # Note: Failure margin treated as likelihood because it's
        # looking for bycatch, i.e. inverse
        # Moreover, success likelihood treated as
        # margin because it's looking for bycatch, i.e. inverse

        # The negative posterior is then subtracted
        # from the positive posterior
        # to produce the final wordscore
        wordscore = positive_posterior - negative_posterior
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
        Args:
        - `success_margin` (float): defined as
            `(target_matches/total_length)**target_matches`; and
        - `failure margin` (float): defined as
            `((total_length-target_matches)/total_length)**(total_length-target_matches)`

        Returns:
            likelihood (float) : The likelihood of a paper of `total_length` being
            relevant to our query, given the presense of `target_matches` matches.

        Further Explanation:
            - `total_combinations` is `total length` choose `target_matches`; i.e. `nCx`
            or `(target_matches! / (total_length! * (total_length-target_matches)!)`
        --------

        >>> total_combinations = (target_matches! / (total_length! * (total_length-target_matches)!)
        >>> P(total_length|target_matches) = total_combinations * success_margin * failure_margin

        """
        total_combinations = comb(
            self.total_length,
            self.target_count,
        )
        likelihood = total_combinations * success_margin * failure_margin
        return likelihood

    def bayes_theorem(
        self,
        *,
        prior: float,
        likelihood: float,
        margin: float,
    ) -> float:
        """
        `bayes_theorem` calculates the posterior using Bayes Theorem.

        Args:
            `prior` (float): The *probability* of a match,
                which here is the `target_words` or `bycatch_words` / `total_length`.
            `likelihood` (float): The likelihood of this outcome,
                given the previously calculated binomial probability
            `margin` (float): The probability of failure

        Returns:
            posterior (float): the likelihood of the paper being
                a match given the words present.
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
        to the power of the part. e.g. `failure_margin` is the `neutral part`
        over the `total length`  to the power of `neutral part`.

        Args:
            part (int or float): The part that represents
                the event being looked into.
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
