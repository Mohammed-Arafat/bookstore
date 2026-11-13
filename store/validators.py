
from django.core.exceptions import ValidationError


def validate_isbn(value):
    """
    Validate ISBN-10 and ISBN-13 format and checksum.
    """

    if not value.isdigit():
        raise ValidationError(
            "ISBN must contain only digits."
        )

    # ISBN-10 validation
    if len(value) == 10:

        total = sum(
            int(digit) * (10 - index)
            for index, digit in enumerate(value)
        )

        if total % 11 != 0:
            raise ValidationError(
                "Invalid ISBN-10 checksum."
            )

    # ISBN-13 validation
    elif len(value) == 13:

        total = sum(
            int(digit) * (1 if index % 2 == 0 else 3)
            for index, digit in enumerate(value)
        )

        if total % 10 != 0:
            raise ValidationError(
                "Invalid ISBN-13 checksum."
            )

    else:
        raise ValidationError(
            "ISBN must contain exactly 10 or 13 digits."
        )
