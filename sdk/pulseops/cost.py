# Prices are per 1,000 tokens in USD
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o":                  (0.005,    0.015),
    "gpt-4o-mini":             (0.000150, 0.000600),
    "gpt-4-turbo":             (0.010,    0.030),
    "gpt-4-turbo-preview":     (0.010,    0.030),
    "gpt-4":                   (0.030,    0.060),
    "gpt-3.5-turbo":           (0.0005,   0.0015),
    "gpt-3.5-turbo-0125":      (0.0005,   0.0015),
    "text-embedding-3-small":  (0.00002,  0.0),
    "text-embedding-3-large":  (0.00013,  0.0),
    "text-embedding-ada-002":  (0.00010,  0.0),
}

DEFAULT_PRICING: tuple[float, float] = (0.001, 0.002)


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    input_price, output_price = MODEL_PRICING.get(model, DEFAULT_PRICING)
    return (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)