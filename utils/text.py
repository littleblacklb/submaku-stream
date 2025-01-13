import re


def remove_repeated_phrases(text):
    """
    Removes consecutive repeated phrases of unknown length from the given text.

    Args:
        text (str): The input text containing potential repetitions.

    Returns:
        str: The text with consecutive repetitions removed.
    """
    # Regex to match repeated phrases, allowing for spaces or punctuation
    pattern = r"(\b.+?\b)(?:\s+\1)+"
    # Remove the repetition parts
    cleaned_text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return cleaned_text
