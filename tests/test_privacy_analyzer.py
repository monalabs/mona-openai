from mona_openai.analysis.privacy import PrivacyAnalyzer


def test_phone_numbers_count():
    assert (
        PrivacyAnalyzer(
            "Here's a phone number: +972584932014 and another one: "
            "(212)456-7890"
        ).get_phone_numbers_count()
        == 2
    )


def test_emails_count():
    assert (
        PrivacyAnalyzer(
            "Here's an email: itai@monalabs.io and another one: "
            "flsdakjflkjsa@gmail.com"
        ).get_emails_count()
        == 2
    )


def test_other_phone_numbers():
    assert (
        PrivacyAnalyzer(
            "Here's a phone number: +972584932014 and another one: "
            "(212)456-7890"
        ).get_previously_unseen_phone_numbers_count(
            (
                PrivacyAnalyzer(
                    "Here's a different phone number: +972584332014 an "
                    "existing one: (212)456-7890"
                ),
                PrivacyAnalyzer(" a different phone number: +972584332015"),
            )
        )
        == 1
    )


def test_other_emails():
    assert (
        PrivacyAnalyzer(
            "Here's an email: itai@monalabs.io and another one: "
            "flsdakjflkjsa@gmail.com"
        ).get_previously_unseen_emails_count(
            (
                PrivacyAnalyzer(
                    "Here's a different email: flasdkjfg@gmail.com an "
                    "existing one: flsdakjflkjsa@gmail.com"
                ),
                PrivacyAnalyzer(
                    " a different email: f4234lsdakjflkjsa@gmail.com"
                ),
            )
        )
        == 1
    )
