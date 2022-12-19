from dataclasses import dataclass, asdict
from sciscraper.scrape.log import logger


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
    pos_chances: int
    neg_chances: int
    total_len: int

    def __call__(self) -> float:
        """Calculate the relevance of the paper, or abstract, as a percentage.

        Variables
        -------
        WEIGHT : float
            Constant. Prevents abstracts from being over-represented.
        pos_odds : float
            The odds that a target word appeared.
        neg_odds : float
            The odds that a bycatch word appeared.
        len_factor : float
            An additional variable designed to keep abstracts
            from being over-represented.

        Returns
        -------
        float
            The probability that the paper is relevant, as a percentage.

        Note
        ----
        `len_factor` is the probability of any match occuring,
        accounting for total number of words analyzed. The more
        words in the sample, then the higher the likelihood that
        the paper is a match.
        If the ratio between the total odds
        (i.e. `pos_odds` + `neg_odds`)
        and the total words (i.e. `total_len`) is very small,
        (e.g. 1:10000), then:
        >>> 1 - (0.0001 * 0.75) = 1 - 0.0075 ≈ 1
        If the preliminary odds-to-probability score is say, 75%,
        then it's going to still be roughly 75% afterwards.
        But if that ratio were larger, (e.g. 0.3), then:
        >>> 1 - (0.3 * 0.75) = 1 - .225 = .775
        That score, when applied to our 75% preliminary score,
        is going to be nearly three-fourths of
        what it was, or roughly 66%.

        Example
        --------
        ``
        wordcalc = RelevanceCalculator(
                        pos_part = 4,
                        neg_part = 2,
                        pos_chances = 10,
                        neg_chances = 10,
                        total_len = 60
                        )

        wordcalc()

        pos_odds    = 4 / 10   #   target word odds
                    = 0.4

        neg_odds    = 2 / 10   #   bycatch word odds
                    = 0.2

        len_factor  = 1 - (((10 + 10)/60) * 0.75)
                    = 1 - ((20/60) * 0.75)
                    = 1 - (.3 * 0.75)
                    = 1 - .225
                    = 0.775

        # odds to probability formula below
        output      = 0.4 / (0.4 + 0.2)
                    = 0.4 / 0.6
                    = 0.66 * 0.775
                    = 0.52 or 52%
        """

        pos_odds: float = self.calc_odds(self.pos_part, self.pos_chances)
        neg_odds: float = self.calc_odds(self.neg_part, self.neg_chances)
        len_factor = self.get_len_factor()
        logger.debug(
            "pos_odds=%f,\
            neg_odds=%f,\
            len_factor=%f",
            pos_odds,
            neg_odds,
            len_factor,
        )
        try:
            raw_score: float = pos_odds / (
                pos_odds + neg_odds
            )  # Calculate the raw score
            adjusted_score = (
                raw_score * len_factor
            )  # Adjust the score based on the length of the word
            wordscore = max(0.00, adjusted_score)  # Ensure the score is not less than 0
        except ZeroDivisionError as zero_error:
            logger.debug(
                "func_repr=%s,\
                error=%s,\
                action_undertaken=%s",
                repr(self.__call__),
                zero_error,
                "Returning wordscore value of 0.00",
            )
            wordscore = 0.00
        return wordscore

    def get_len_factor(self) -> float:
        weight = 0.75
        all_chances: int = self.pos_chances + self.neg_chances
        probability: float = (1 / all_chances) * self.total_len  # somehow this works?
        adjusted_probability: float = probability * weight
        return 1 - adjusted_probability

    @staticmethod
    def calc_odds(part: float, chances: float) -> float:
        odds = part / chances
        return max(0.00, odds)

    @classmethod
    def from_dict(cls, dict_input: dict):
        return RelevanceCalculator(**dict_input)

    def to_dict(self):
        return asdict(self)
