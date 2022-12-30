from dataclasses import dataclass, asdict
import numpy as np


@dataclass(slots=True, order=True)
class RelevanceCalculator:
    """
    A class for calculating the relevance of a paper or abstract based on its target and bycatch words.

    This class contains attributes and methods for calculating the wordscore of a paper or abstract
    based on the number of times target and bycatch words appear in it, its length,
    and a prior zero-shot classification score.

    Attributes
    ----------
    pos_part : float
        The number of times a target word appeared in the paper or abstract.
    neg_part : float
        The number of times a bycatch word appeared in the paper or abstract.
    total_len : int
        The total number of words in the paper or abstract.
    implicature_score : float
        The highest score from a prior `DocScraper` zero-shot classification.

    Methods
    -------
    __call__ : returns wordscore value as a float

    """

    pos_part: float
    neg_part: float
    total_len: int
    implicature_score: float
    s: float = 0.95

    def __call__(self) -> float:
        """
        Calculates the relevance of the paper, or abstract, as a percentage.

        Returns:
            float: The probability that the paper is relevant, as a percentage.

        Example:
        >>> calculator = RelevanceCalculator(
                pos_part=2,
                neg_part=1,
                total_len=100,
                implicature_score=0.9
                )
        >>> wordscore = (0.76 + 0.87) / 2
        0.815 # or 81.5%
        """
        probability = self.get_probability()
        raw_score = self.get_raw_score(probability)
        bycatch_coefficient = self.get_bycatch_coefficient()
        weight = self.get_weight(bycatch_coefficient)
        return np.mean([raw_score, weight], dtype=float)

    def get_probability(self):
        """
        Gets the percent chance that the paper is relevant.

        Returns:
            float: the percent chance that the paper is relevant.

        Example:
        >>> probability = (5 - 3) / 20 * 100
        2 / 20 * 100
        0.1 * 100
        10
        """
        return (self.pos_part - self.neg_part) + 1 / self.total_len * 100

    def get_raw_score(self, probability: float) -> float:
        """
        Gets the preliminary score before it gets weighted.

        Args:
            probability (float): the percent chance that the paper is relevant.

        Returns:
            float: The preliminary score before being weighted.

        Example:
        >>> raw_score = (2 + 1) / (2 + 0.95 + 1)
        0.76
        """
        return (probability + 1) / (probability + self.s + 1)

    def get_bycatch_coefficient(self) -> float:
        """
        Gets a probability value, which is determined from the number of bycatch words identified.

        Returns:
            float: The preliminary score before being weighted.

        Example:
        >>> bycatch_coefficient = (1 + 1) / (1 + (2 - 0.95))
        2 / 1 + 1.05
        2 / 2.05
        0.97
        """
        return (self.neg_part + 1) / (self.neg_part + (2 - self.s))

    def get_weight(self, bycatch_coefficient: float) -> float:
        """
        Returns the weight as a result of the implicature score and bycatch coefficient.

        Args:
            bycatch_coefficient (float): A probability that is determined from the number of bycatch words identified.

        Returns:
            float: The weight as a result of the implicature score and bycatch coefficient.

        Example:
        >>> weight = 0.9 * 0.97
        0.873
        """
        return self.implicature_score * bycatch_coefficient

    @classmethod
    def from_dict(cls, dict_input: dict):
        return RelevanceCalculator(**dict_input)

    def to_dict(self):
        return asdict(self)
