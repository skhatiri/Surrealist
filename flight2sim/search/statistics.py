from typing import List
import statsmodels.stats.power as pw
from scipy import stats
import numpy as np
import logging

logger = logging.getLogger(__name__)


alpha = 0.05
power = 0.8


def similarity_test(data1: List[float], data2: List[float]):
    # null hypothesis:
    # the two distributions have the same population mean
    (w1, p1) = stats.shapiro(data1 - np.mean(data1))
    (w2, p2) = stats.shapiro(data2 - np.mean(data2))
    # logger.info (f"Shapiro:\np1:{p1},w1:{w1}\tp2:{p2},w2:{w2}")

    if p1 > alpha and p2 > alpha:
        # the distributions are Gausian, we can use ANOVA
        f, p = stats.f_oneway(data1, data2)
        logger.debug("Gausian Distribution")
    else:
        # distributions are not Gaussian, using unpaired Wilcoxon
        t, p = stats.ranksums(data1, data2)
        logger.debug("Non-Gausian Distribution")
        # logger.info (f"ANOVA\tp:{p}\tf:{f}")

    if p < alpha:
        # reject the hypothesis
        # populations are different
        eff_size = (np.mean(data1) - np.mean(data2)) / np.sqrt(
            (np.std(data1) ** 2 + np.std(data2) ** 2) / 2.0
        )
        pow = pw.FTestAnovaPower().solve_power(
            effect_size=eff_size, nobs=len(data1) + len(data2), alpha=alpha
        )
        # logger.info(f"power:{pow}")
        if pow >= power:
            # we can safely reject the null hypothesis
            # logger.info ("pow>power\nResult:\t statistically significant")
            return False
        else:
            # the population is not sufficient to decide
            nobs = pw.FTestAnovaPower().solve_power(
                effect_size=eff_size, power=power, alpha=alpha
            )
            # logger.info (f"p<alpha\nResult:\t undecidable\tneeding {nobs} samples to decide")
            # return nobs
            logger.error(
                f"too few data points to decide the distributions similarity, {nobs} needed"
            )
            return True
    else:
        # accept the hypothesis
        # the distributions are similar
        return True


def significance_test(data1: List[float], data2: List[float]):
    # null hypothesis:
    # the two distributions have the same population mean
    (w1, p1) = stats.shapiro(data1 - np.mean(data1))
    (w2, p2) = stats.shapiro(data2 - np.mean(data2))
    # logger.info (f"Shapiro:\np1:{p1},w1:{w1}\tp2:{p2},w2:{w2}")

    if p1 > alpha and p2 > alpha:
        # the distributions are Gausian, we can use ANOVA
        f, p = stats.f_oneway(data1, data2)
        distribution = "guasian"
        logger.info("Gausian Distribution")
    else:
        # distributions are not Gaussian, using unpaired Wilcoxon
        t, p = stats.ranksums(data1, data2)
        logger.info("Non-Gausian Distribution")
        # logger.info (f"ANOVA\tp:{p}\tf:{f}")
        distribution = "non-gausian"
    if p < alpha:
        # reject the hypothesis
        # populations are different
        eff_size = (np.mean(data1) - np.mean(data2)) / np.sqrt(
            (np.std(data1) ** 2 + np.std(data2) ** 2) / 2.0
        )
        pow = pw.FTestAnovaPower().solve_power(
            effect_size=eff_size, nobs=len(data1) + len(data2), alpha=alpha
        )
        # logger.info(f"power:{pow}")
        if pow >= power:
            # we can safely reject the null hypothesis
            # logger.info ("pow>power\nResult:\t statistically significant")
            return False, p1, p2, distribution, p, eff_size, pow
        else:
            # the population is not sufficient to decide
            nobs = pw.FTestAnovaPower().solve_power(
                effect_size=eff_size, power=power, alpha=alpha
            )
            # logger.info (f"p<alpha\nResult:\t undecidable\tneeding {nobs} samples to decide")
            # return nobs
            logger.error(
                f"too few data points to decide the distributions similarity, {nobs} needed"
            )
            return False, p1, p2, distribution, p, eff_size, pow
    else:
        # accept the hypothesis
        # the distributions are similar
        return True, p1, p2, distribution, p, eff_size, pow
