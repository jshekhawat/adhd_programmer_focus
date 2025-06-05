from dataclasses import dataclass
import fractions

@dataclass
class AppConfig:
    FPS = 0.5
    VIDEO_PTIME = 1 / FPS
    VIDEO_CLOCK_RATE = 90000
    VIDEO_TIME_BASE =  fractions.Fraction(1, VIDEO_CLOCK_RATE)
    SECONDS_PER_REC = 10
