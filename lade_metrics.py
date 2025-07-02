from typing import Sequence


def kendall_rank_correlation(pred: Sequence[int], truth: Sequence[int]) -> float:
    """Return Kendall rank correlation between predicted and true sequences."""
    assert len(pred) == len(truth)
    n = len(pred)
    concordant = discordant = 0
    pos_truth = {v: i for i, v in enumerate(truth)}
    for i in range(n):
        for j in range(i + 1, n):
            a = pred[i]
            b = pred[j]
            if pos_truth[a] < pos_truth[b]:
                concordant += 1
            else:
                discordant += 1
    if concordant + discordant == 0:
        return 0.0
    return (concordant - discordant) / (concordant + discordant)


def edit_distance(pred: Sequence[int], truth: Sequence[int]) -> int:
    """Compute Levenshtein edit distance between two sequences."""
    m, n = len(pred), len(truth)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if pred[i - 1] == truth[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )
    return dp[m][n]


def location_square_deviation(pred: Sequence[int], truth: Sequence[int]) -> float:
    pos_truth = {v: i for i, v in enumerate(truth)}
    sq = 0.0
    for i, node in enumerate(pred):
        if node in pos_truth:
            sq += (pos_truth[node] - i) ** 2
    return sq / len(pred) if pred else 0.0


def hit_rate_at_k(pred: Sequence[int], truth: Sequence[int], k: int) -> float:
    k = min(k, len(pred), len(truth))
    return len(set(pred[:k]) & set(truth[:k])) / float(k)
