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

    def __call__(self) -> float:
        """Calculate the relevance of the paper, or abstract, as a percentage.

        Returns
        -------
        float
            The probability that the paper is relevant, as a percentage.

        Example
        -------
        >>> calculator = RelevanceCalculator(
                pos_part=2,
                neg_part=1,
                total_len=100,
                implicature_score=0.9
                )
        >>> raw_score = (2 + 1) / (2 + 0.95 + 1)
        ... = 3 / 3.95
        ... = 0.76
        >>> bycatch_coefficient
        ... = (1 + 1) / (1 + (2 - 0.95))
        ... = 2 / 1 + 1.05
        ... = 2 / 2.05
        ... = 0.97
        >>> weight = 0.9 * 0.97
        ... = 0.873
        >>> wordscore = (0.76 + 0.87) / 2
        ... return 0.815 # or 81.5%
        """
        s: float = 0.95
        probability = self.pos_part - self.neg_part / self.total_len * 100
        raw_score = (probability + 1) / (probability + s + 1)
        bycatch_coefficient = (self.neg_part + 1) / (self.neg_part + (2 - s))
        weight = self.implicature_score * bycatch_coefficient
        return np.mean([raw_score, weight], dtype=float)

    @classmethod
    def from_dict(cls, dict_input: dict):
        return RelevanceCalculator(**dict_input)

    def to_dict(self):
        return asdict(self)
