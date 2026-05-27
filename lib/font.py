class Font:
    def __init__(self, mono, regular, bold, italic, bold_italic):
        self.mono = mono
        self.r = regular
        self.b = bold
        self.ri = italic
        self.bi = bold_italic

    def get_s(self, typ: str):
        match typ:
            case 'R':
                return self.r
            case 'RI':
                return self.ri
            case 'B':
                return self.b
            case 'BI':
                return self.bi

    def get_f(self, bold: bool = False, italic: bool = False):
        if not bold and not italic:
            return self.r
        if not bold and italic:
            return self.ri
        if bold and not italic:
            return self.b
        if bold and italic:
            return self.bi


UBUNTU_MONO = Font(
    True,
    "font/Ubuntu/UbuntuMono-R.ttf",
    "font/Ubuntu/UbuntuMono-B.ttf",
    "font/Ubuntu/UbuntuMono-RI.ttf",
    "font/Ubuntu/UbuntuMono-BI.ttf",
)

IBM_PLEX_SANS = Font(
    False,
    "font/IBMPlexSans/IBMPlexSans-Regular.ttf",
    "font/IBMPlexSans/IBMPlexSans-Bold.ttf",
    "font/IBMPlexSans/IBMPlexSans-Italic.ttf",
    "font/IBMPlexSans/IBMPlexSans-BoldItalic.ttf",
)

__all__ = [
    "UBUNTU_MONO",
    "IBM_PLEX_SANS",
]
