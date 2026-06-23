def dedupe_preserve_order(links: list[str]) -> list[str]:
    seen = set()
    result = []
    for link in links:
        if link not in seen:
            seen.add(link)
            result.append(link)
    return result


def oldest_first(links: list[str]) -> list[str]:
    return list(reversed(links))
