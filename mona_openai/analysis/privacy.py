from typing import Iterable

"""
Functionality for extracting privacy information from GAI responses
when comparing to given input prompts.

TODO(itai): Add many more functions to extract information such as:
    Bank accounts, full names, SSN, passport numbers, etc...
"""
import re

from phonenumbers import PhoneNumberMatcher

# TODO(itai): Add module-level tests for this module, specifically for email
#   extraction, since this is our own logic and not using an external library.

EMAIL_RE_PATTERN = (
    r"([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\"([]!#-[^-~"
    r" \t]|(\\[\t -~]))+\")@([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A"
    r"-Z^-~]+)*|\[[\t -Z^-~]*])"
)


def _extract_phone_numbers(text):
    """
    Extract phone numbers from a prompt string and return as a set.
    """
    phone_numbers = set()
    # We use "US" just as a default region in case there are no country codes
    # since we don't care about the formatting of the found number, but just
    # whether it is a phone number or not, this has no consequences.
    for match in PhoneNumberMatcher(text, "US"):
        number_string = "+{}{}".format(
            match.number.country_code, match.number.national_number
        )
        phone_numbers.add(number_string)
    return phone_numbers


def _extract_all_emails(text):
    """
    returns all email addresses found in the given prompt.
    """
    return set(re.findall(EMAIL_RE_PATTERN, text))


class PrivacyAnalyzer:
    """
    An analyzer class that takes a text and provides functionality to extract
    privacy-related metrics from that text.
    """

    def __init__(self, text) -> None:
        self._text = text
        self._phone_numbers = _extract_phone_numbers(text)
        self._emails = _extract_all_emails(text)

    def get_phone_numbers_count(self):
        """
        Returns the number of phone numbers in the initially given text.
        """
        return len(self._phone_numbers)

    def get_emails_count(self):
        """
        Returns the number of email addresses in the initially given text.
        """
        return len(self._emails)

    @classmethod
    def _get_phone_numbers_from_instance(cls, instance):
        return instance._phone_numbers

    @classmethod
    def _get_emails_from_instance(cls, instance):
        return instance._emails

    def _get_previously_unseen_x_count(
        self, others: Iterable["PrivacyAnalyzer"], extraction_function
    ):
        return len(
            extraction_function(self)
            - set().union(
                *tuple(extraction_function(other) for other in others)
            )
        )

    def get_previously_unseen_phone_numbers_count(
        self, others: Iterable["PrivacyAnalyzer"]
    ):
        """
        Returns the number of phone numbers in the initially given text, that
        don't also appear in any of the given other analyzers.
        """
        return self._get_previously_unseen_x_count(
            others, self._get_phone_numbers_from_instance
        )

    def get_previously_unseen_emails_count(
        self, others: Iterable["PrivacyAnalyzer"]
    ):
        """
        Returns the number of email addresses in the initially given text,
        that don't also appear in any of the given other analyzers.
        """
        return self._get_previously_unseen_x_count(
            others, self._get_emails_from_instance
        )


def get_privacy_analyzers(texts):
    """
    Returns a tuple of PrivacyAnalyzer objects, one for each text in the given
    iterable.
    """
    return tuple(PrivacyAnalyzer(text) for text in texts)
