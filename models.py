from dataclasses import dataclass
from functools import total_ordering
from enum import IntEnum
from typing import Any, Dict, Tuple


class Tariff(IntEnum):
    BASIC = 1
    PREMIUM = 2
    ENTERPRISE = 3

    @classmethod
    def from_string(cls, value: str) -> 'Tariff':
        val_clean = value.strip().upper()
        if val_clean in cls.__members__:
            return cls[val_clean]
        raise ValueError(f"Unknown tariff: {value}. Allowed: {', '.join(cls.__members__.keys())}")

    def __str__(self) -> str:
        return self.name.capitalize()


class LogType(IntEnum):
    DEBG = 1
    INFO = 2
    WARN = 3
    ERROR = 4

    @classmethod
    def from_string(cls, value: str) -> 'LogType':
        val_clean = value.strip().upper()
        if val_clean in cls.__members__:
            return cls[val_clean]
        raise ValueError(f"Unknown log type: {value}. Allowed: {', '.join(cls.__members__.keys())}")

    def __str__(self) -> str:
        return self.name


@total_ordering
class CustomDate:
    _MONTHS: Tuple[str, ...] = ("jan", "feb", "mar", "apr", "may", "jun",
                               "jul", "aug", "sep", "oct", "nov", "dec")
    MONTH_MAP: Dict[str, int] = {name: i + 1 for i, name in enumerate(_MONTHS)}
    INV_MONTH_MAP: Dict[int, str] = {i + 1: name for i, name in enumerate(_MONTHS)}

    def __init__(self, date_str: str) -> None:
        try:
            day_str, month_str, year_str = date_str.strip().split()
        except ValueError:
            raise ValueError(f"Error parsing date '{date_str}': Format must be: DD jan YYYY")

        month_str = month_str.lower()
        if month_str not in self.MONTH_MAP:
            raise ValueError(f"Error parsing date '{date_str}': Unknown month: {month_str}")

        try:
            self.day: int = int(day_str)
            self.month_str: str = month_str
            self.month: int = self.MONTH_MAP[month_str]
            self.year: int = int(year_str)
            
            self._validate_date(self.day, self.month, self.year)
            
        except (TypeError, ValueError) as e:
            raise ValueError(f"Error parsing date '{date_str}': {e}")

    def _validate_date(self, day: int, month: int, year: int) -> None:
        if year < 1:
            raise ValueError("Year must be greater than 0")
        if year > 9999:
            raise ValueError("Year must be lower than 10000")
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
        
        if month in (4, 6, 9, 11):
            max_days = 30
        elif month == 2:
            is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
            max_days = 29 if is_leap else 28
        else:
            max_days = 31

        if day < 1 or day > max_days:
            raise ValueError(f"Invalid day {day} for month {month} in year {year}")

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, CustomDate) and 
                self.year == other.year and 
                self.month == other.month and 
                self.day == other.day)

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, CustomDate):
            return NotImplemented
        return (self.year, self.month, self.day) < (other.year, other.month, other.day)

    def __hash__(self) -> int:
        return hash((self.year, self.month, self.day))

    def __str__(self) -> str:
        return f"{self.day:02d} {self.INV_MONTH_MAP[self.month]} {self.year:04d}"

    def __repr__(self) -> str:
        return f"CustomDate({str(self)!r})"


@dataclass
class Site:
    domain: str
    owner: str
    tariff: Tariff

    def __init__(self, domain: str, owner: str, tariff_input: Tariff | str) -> None:
        self.domain = domain
        self.owner = owner
        if isinstance(tariff_input, Tariff):
            self.tariff = tariff_input
        else:
            self.tariff = Tariff.from_string(str(tariff_input))

    def __str__(self) -> str:
        return f"Site: {self.domain} | Owner: {self.owner} | Tariff: {self.tariff}"


@dataclass
class Log:
    domain: str
    date: CustomDate
    time: str
    type: LogType
    message: str

    def __init__(self, domain: str, date_input: CustomDate | str, time: str, type_input: LogType | str, message: str) -> None:
        self.domain = domain
        self.date = date_input if isinstance(date_input, CustomDate) else CustomDate(str(date_input))
        self.time = time
        if isinstance(type_input, LogType):
            self.type = type_input
        else:
            self.type = LogType.from_string(str(type_input))
        self.message = message

    def __str__(self) -> str:
        return f"[{self.date} {self.time}] {self.type} @ {self.domain}: {self.message}"