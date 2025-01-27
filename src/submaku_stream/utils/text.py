import re


def remove_redundant_repeats(text):
    """
    Remove redundant repeats

    Such as Hello world REPEAT A REPEAT A REPEAT A REPEAT B REPEAT B AA REPEAT B REPEAT B

    -> Such as Helo world REPEAT A REPEAT B A REPEAT B

    :param text: original text
    :return: processed text
    """
    pattern = r"(.*?)(\1+)"
    result = re.sub(pattern, r"\1", text)
    return result
