from mona_openai.analysis.textual import TextualAnalyzer


def test_get_length():
    text = "bla balskdf nblaskd"
    assert TextualAnalyzer(text).get_length() == len(text)


def test_get_word_count():
    text = "bla balskdf nblaskd"
    assert TextualAnalyzer(text).get_word_count() == 3


def test_get_preposition_count():
    text = "bla balskdf of nblaskd from there"
    assert TextualAnalyzer(text).get_preposition_count() == 2


def test_get_preposition_ratio():
    text = "bla balskdf of nblaskd from there"
    assert TextualAnalyzer(text).get_preposition_ratio() == 2 / 6


def test_get_preposition_ratio_no_words():
    text = "  "
    assert TextualAnalyzer(text).get_preposition_ratio() == 0


def test_new_words():
    assert (
        TextualAnalyzer("this is a word").get_words_not_in_others_count(
            (
                TextualAnalyzer("has this word"),
                TextualAnalyzer("no bla bla is"),
            )
        )
        == 1
    )
