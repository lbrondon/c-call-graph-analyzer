"""Represent one caller-to-callee occurrence found in C source code."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CallOccurrence:
    """One syntactic function-call occurrence found by srcML."""

    project: str
    file: str
    caller: str
    callee: str

    def to_csv_row(self) -> tuple[str, str, str, str]:
        """Return values in the order required by the CSV contract."""

        return self.project, self.file, self.caller, self.callee
