# This file is part of the Reference Data Repository (refdata).
#
# Copyright (C) 2021 New York University.
#
# refdata is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

from typing import Dict, List, Optional

import gzip
import pandas as pd

from refdata.base import DatasetDescriptor
from refdata.loader import CSVLoader, JsonLoader

import refdata.error as err


class DatasetHandle(DatasetDescriptor):
    """Handle for a dataset in the local data store. Provides the functionality
    to read data in different formats from the downloaded data file.
    """
    def __init__(self, doc: Dict, datafile: str):
        """Initialize the descriptor information and the path to the downloaded
        data file. This will also create an instance of the dataset loader that
        is dependent on the dataset format.

        Parameters
        ----------
        doc: dict
            Dictionary serialization for the dataset descriptor.
        datafile: string
            Path to the downloaded file.
        """
        super(DatasetHandle, self).__init__(doc=doc)
        self.datafile = datafile
        # Create the format-dependent instance of the dataset loader.
        parameters = self.format
        if parameters.is_csv:
            self.loader = CSVLoader(
                parameters=parameters,
                schema=[c.identifier for c in self.columns]
            )
        elif parameters.is_json:
            self.loader = JsonLoader(parameters)
        else:
            raise err.InvalidFormatError("unknown format '{}'".format(parameters.format_type))

    def load(self, columns: List[str]) -> List[List]:
        """Load data for the specified columns from the downloaded dataset
        file. The list of columns is expected to contain only identifier for
        columns in the schema that is defined in the dataset descriptor.

        Parameters
        ----------
        columns: list of string
            Column identifier defining the content and the schema of the
            returned data.

        Returns
        -------
        list of list
        """
        # Open the file depending on whether it is compressed or not. By now,
        # we only support gzip compression.
        if self.compression == 'gzip':
            f = gzip.open(self.datafile, 'rt')
        else:
            f = open(self.datafile, 'rt')
        # Use the format-specific loader to get the data frame. Ensure to close
        # the opened file when done.
        try:
            return self.loader.read(f, columns=columns)
        finally:
            f.close()

    def load_df(self, columns: Optional[str] = None) -> pd.DataFrame:
        """Load dataset as a pandas data frame.

        This is a shortcut to load all (or a given selection of) columns in
        the dataset as a pandas data frame. If the list of columns is not
        given the full dataset is returned.

        Parameters
        ----------
        columns: list of string, default=None
            Column identifier defining the content and the schema of the
            returned data frame.

        Returns
        -------
        pd.DataFrame
        """
        # If columns are not specified use the full list of columns that are
        # defined in the dataset descriptor.
        columns = columns if columns is not None else [c.identifier for c in self.columns]
        return pd.DataFrame(data=self.load(columns), columns=columns)
