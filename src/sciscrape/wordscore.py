from dataclasses import (
    dataclass,
    asdict,
)
from typing import Optional, Union
from math import comb


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
        Calculates the relevance of the paper, or abstract,
            as a percentage, by using a binomial distribution formula.

        Returns:
            float: The probability that the paper is relevant, as a percentage.

        Example:
        >>> calculator =
            RelevanceCalculator(
                pos_part=2,
                neg_part=1,
                total_len=100,
                implicature_score=0.9
            )
        >>> calculator()
        0.815 # or 81.5%
        """
        # The bycatch is added to the total length,
        # in order to make the presense of bycatch words negatively impactful.
        weighted_length: int = self.total_len + self.neg_part
        neutral_part: int = weighted_length - self.pos_part
        # start binomial distribution i.e. (n! / (x! * (n-x)!) * (x/n)^x * ((n-x)/n)^(n-x))
        choice: int = comb(
            weighted_length,
            self.pos_part,
        )
        probability: float = self.get_probability(
            self.pos_part,
            weighted_length,
        )
        failure_prob: float = self.get_probability(
            neutral_part,
            weighted_length,
        )
        # The highest zero shot classification score accounts for about 20% of the final wordscore
        raw_probability: float = 1 - (choice * probability * failure_prob)
        return self.calculate_wordscore(raw_probability)

    def calculate_wordscore(self, raw_probability: float) -> float:
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
        weight = 0.8
        self.implicature_score = (
            0.5 if self.implicature_score is None else self.implicature_score
        )
        return (raw_probability * weight) + (self.implicature_score * (1 - weight))

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

        Example:
        >>> RelevanceCalculator.get_probability(2, 4)
        0.25
        """
        return (part / whole) ** part

    @classmethod
    def from_dict(cls, dict_input: dict):
        return RelevanceCalculator(**dict_input)

    def to_dict(self):
        return asdict(self)
