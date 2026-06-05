import random


def should_log(is_error: bool, sample_rate: float) -> bool:
    if is_error:
        return True
    return random.random() < sample_rate