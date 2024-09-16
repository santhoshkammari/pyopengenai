import re


class TextFilter:
    @staticmethod
    def _remove_mulitline_space(text):
        text = text.replace("\n\n", "\n")
        return text

    @staticmethod
    def _replace_single_line_words_to_single_sentence(text):
        for match in re.findall(r'\w+\n\w+\n', text):
            text = text.replace(match, match.replace('\n', " "))
        return text

    @staticmethod
    def filter_text(text):
        text = TextFilter._remove_mulitline_space(text)
        text = TextFilter._replace_single_line_words_to_single_sentence(text)
        text = TextFilter._remove_mulitline_space(text)
        return text