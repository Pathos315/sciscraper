from dataclasses import dataclass, asdict
from math import comb
import numpy as np
from sciscrape.log import logger


@dataclass(slots=True, order=True)
class RelevanceCalculator:
    """
    RelevanceCalculator contains all the variables necessary to calculate the `wordscore` of a paper or abstract.

    Attributes
    ----------
    pos_part : float
        The number of times a target word appeared in the paper or abstract.
    neg_part : float
        The number of times a bycatch word appeared in the paper or abstract.
    pos_changes : int
        The total number of target words from the set.
    neg_chances : int
        The total number of bycatch words from the set.
    total_len : int
        The total number of words in the paper or abstract.

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
        """
        s: float = 0.95
        raw_score = (self.pos_part + 1) / (self.pos_part + s + 1)
        bycatch_coefficient = (self.neg_part + 1) / (self.neg_part + (2 - s))
        weight = self.implicature_score * bycatch_coefficient
        return np.mean([raw_score, weight], dtype=float)

    @classmethod
    def from_dict(cls, dict_input: dict):
        return RelevanceCalculator(**dict_input)

    def to_dict(self):
        return asdict(self)
