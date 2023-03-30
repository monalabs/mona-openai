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


def _count_unknowns(prompt, answer, extract_func):
    return len(extract_func(prompt) - extract_func(answer))


def _extract_phone_numbers(prompt):
    """
    Extract phone numbers from a prompt string and return as a set.
    """
    phone_numbers = set()
    # We use "US" just as a default region in case there are no country codes
    # since we don't care about the formatting of the found number, but just
    # whether it is a phone number or not, this has no consequences.
    for match in PhoneNumberMatcher(prompt, "US"):
        number_string = "+{}{}".format(
            match.number.country_code, match.number.national_number
        )
        phone_numbers.add(number_string)
    return phone_numbers


def _count_unknown_phone_numbers(prompt, answer):
    """
    Count the number of phone numbers that appear in the prompt but
    not in the input prompt.
    """
    return _count_unknowns(prompt, answer, _extract_phone_numbers)


def _extract_all_emails(prompt):
    """
    returns all email addresses found in the given prompt.
    """
    return set(re.findall(EMAIL_RE_PATTERN, prompt))


def _count_unknown_emails(prompt, answer):
    """
    Returns the number of email addresses found in prompt and not in
    the answer param.
    """
    return _count_unknowns(prompt, answer, _extract_all_emails)


def get_full_privacy_analysis(prompt, answers):
    """
    Returns a dictionary with a full privacy analysis of the given
    prompt, when comparing to the "answer" param.
    """
    # TODO(itai): Extract the phone numbers from the prompt just once
    #   to improve efficiency.
    return {
        "prompt_phone_number_count": len(_extract_phone_numbers(prompt)),
        "answer_unknown_phone_number_count": tuple(
            _count_unknown_phone_numbers(prompt, answer) for answer in answers
        ),
        "prompt_email_count": len(_extract_all_emails(prompt)),
        "answer_unkown_email_count": tuple(
            _count_unknown_emails(prompt, answer) for answer in answers
        ),
    }
