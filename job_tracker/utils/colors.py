"""Color utilities for terminal output using colorama."""

try:
    from colorama import Fore, Style, init
    # Initialize colorama for Windows support
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    # Fallback if colorama is not available
    def init(**kwargs):
        pass

    class _Fore:
        GREEN = ""
        YELLOW = ""
        CYAN = ""
        BLUE = ""
        MAGENTA = ""
        RED = ""
        WHITE = ""
        LIGHTGREEN_EX = ""
        LIGHTBLUE_EX = ""
        LIGHTYELLOW_EX = ""

    class _Style:
        BRIGHT = ""
        RESET_ALL = ""

    Fore = _Fore()
    Style = _Style()


# Color mapping for application statuses
STATUS_COLORS = {
    "Applied": Fore.CYAN,                      # Blue - starting point
    "Interview Scheduled": Fore.LIGHTYELLOW_EX, # Yellow - attention needed
    "Interviewed": Fore.YELLOW,                # Yellow - waiting for results
    "Offer": Fore.LIGHTGREEN_EX,               # Light green - very positive
    "Accepted": Fore.GREEN,                    # Green - success!
    "Rejected": Fore.RED,                      # Red - terminal negative
    "Withdrawn": Fore.WHITE,                   # White/gray - neutral terminal
}


def colorize_status(status_name: str, bold: bool = True) -> str:
    """
    Apply color to a status name based on its type.

    Args:
        status_name: The status name to colorize
        bold: Whether to make the text bold (default: True)

    Returns:
        The status name wrapped in color codes

    Color Mapping:
        - Applied: Cyan (starting point)
        - Interview Scheduled: Light Yellow (attention needed)
        - Interviewed: Yellow (waiting for results)
        - Offer: Light Green (very positive)
        - Accepted: Green (success!)
        - Rejected: Red (terminal negative)
        - Withdrawn: White (neutral terminal)

    Example:
        >>> colorize_status("Applied")
        '\x1b[96mApplied\x1b[0m'  # Cyan colored
        >>> colorize_status("Rejected")
        '\x1b[91mRejected\x1b[0m'  # Red colored
    """
    color = STATUS_COLORS.get(status_name, Fore.WHITE)
    style = Style.BRIGHT if bold else ""
    return f"{style}{color}{status_name}{Style.RESET_ALL}"



