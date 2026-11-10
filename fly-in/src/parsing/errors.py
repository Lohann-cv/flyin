"""A custom error for when a map cannot be parsed"""

class ParseError(Exception):
    """Raised when a map file cannot be parsed due to an error.

    Attributes:
        message: The message descrbing the error.
        line_no: The line where the error occured, or None if it's a file error.
    """

    def __init__(self, message:str, line_no: int | None = None) -> None:
        """Build the error and its printable message.

        Args:
            message: The message descrbing the error.
            line_no: The line where the error occured, or None if it's a file error.
        """
        self.message: str = message
        self.line_no: int | None = line_no
        prefix = f"Line {line_no}: " if line_no is not None else ""
        super().__init__(f"{prefix}{message}")
