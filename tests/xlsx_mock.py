"""Creates a class for mocking an XLSX file

This module creates a class for encapsulating an in-memory XLSX file by
inheriting from openpyxl.Workbook, including a method for loading data into a
worksheet from an iterable of iterables and a property for using a Workbook
object as if it were a file

See https://openpyxl.readthedocs.io/ for more information about Openpyxl.

"""

from io import BytesIO
from typing import Iterable

from openpyxl import Workbook
from openpyxl.worksheet import Worksheet


class XlsxMock(Workbook):
    """Class for mocking an XLSX file"""

    def __init__(self, *args, **kwargs):
        """Initializes XlsxMock object, passing arguments to Workbook.__init__

        Args:
            args: options passed through to openpyxl.Workbook.__init__
            kwargs: options passed through to openpyxl.Workbook.__init__

        """
        super().__init__(*args, **kwargs)

    @staticmethod
    def load_data(worksheet: Worksheet, data: Iterable) -> None:
        """Loads data into worksheet from iterable of iterables

        Args:
            worksheet: a Worksheet object within a Workbook object
            data: an iterable of iterables

        """

        for i, row in enumerate(data):
            for j, item in enumerate(row):
                worksheet.cell(row=i + 1, column=j + 1).value = item

    @property
    def as_file(self) -> BytesIO:
        """Returns a file-like object version of the XlsxMock object"""

        return_value = BytesIO()
        self.save(return_value)
        return_value.seek(0)

        return return_value
