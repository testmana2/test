"""Coverage data for Coverage."""

import os
import cPickle as pickle

from backward import sorted    # pylint: disable-msg=W0622


class CoverageData:
    """Manages collected coverage data, including file storage.
    
    The data file format is a pickled dict, with these keys:
    
        * collector: a string identifying the collecting software

        * lines: a dict mapping filenames to sorted lists of line numbers
          executed:
            { 'file1': [17,23,45],  'file2': [1,2,3], ... }
    
    """
    
    # Name of the data file (unless environment variable is set).
    filename_default = ".coverage"

    # Environment variable naming the data file.
    filename_env = "COVERAGE_FILE"

    def __init__(self, basename=None, suffix=None, collector=None):
        """Create a CoverageData.
        
        `basename` is the name of the file to use for storing data.
        
        `suffix` is a suffix to append to the base file name. This can be used
        for multiple or parallel execution, so that many coverage data files
        can exist simultaneously.

        `collector` is a string describing the coverage measurement software.

        """
        self.basename = basename
        self.collector = collector
        self.suffix = suffix
        
        self.use_file = True
        self.filename = None

        # A map from canonical Python source file name to a dictionary in
        # which there's an entry for each line number that has been
        # executed:
        #
        #   {
        #       'filename1.py': { 12: True, 47: True, ... },
        #       ...
        #       }
        #
        self.lines = {}
        
    def usefile(self, use_file=True):
        """Set whether or not to use a disk file for data."""
        self.use_file = use_file

    def _make_filename(self):
        """Construct the filename that will be used for data file storage."""
        assert self.use_file
        if not self.filename:
            self.filename = (self.basename or
                    os.environ.get(self.filename_env, self.filename_default))

            if self.suffix:
                self.filename += self.suffix

    def read(self):
        """Read coverage data from the coverage data file (if it exists)."""
        data = {}
        if self.use_file:
            self._make_filename()
            data = self._read_file(self.filename)
        self.lines = data

    def write(self):
        """Write the collected coverage data to a file."""
        if self.use_file:
            self._make_filename()
            self.write_file(self.filename)

    def erase(self):
        """Erase the data, both in this object, and from its file storage."""
        if self.use_file:
            self._make_filename()
            if self.filename and os.path.exists(self.filename):
                os.remove(self.filename)
        self.lines = {}
        
    def line_data(self):
        """Return the map from filenames to lists of line numbers executed."""
        return dict(
            [(f, sorted(linemap.keys())) for f, linemap in self.lines.items()]
            )

    def write_file(self, filename):
        """Write the coverage data to `filename`."""

        # Create the file data.        
        data = {}

        data['lines'] = self.line_data()

        if self.collector:
            data['collector'] = self.collector

        # Write the pickle to the file.
        fdata = open(filename, 'wb')
        try:
            pickle.dump(data, fdata, 2)
        finally:
            fdata.close()

    def read_file(self, filename):
        """Read the coverage data from `filename`."""
        self.lines = self._read_file(filename)

    def _read_file(self, filename):
        """Return the stored coverage data from the given file."""
        try:
            fdata = open(filename, 'rb')
            try:
                data = pickle.load(fdata)
            finally:
                fdata.close()
            if isinstance(data, dict):
                # Unpack the 'lines' item.
                lines = dict([
                    (f, dict([(l, True) for l in linenos]))
                        for f,linenos in data['lines'].items()
                    ])
                return lines
            else:
                return {}
        except Exception:
            return {}

    def combine_parallel_data(self):
        """ Treat self.filename as a file prefix, and combine the data from all
            of the files starting with that prefix.
        """
        self._make_filename()
        data_dir, local = os.path.split(self.filename)
        for f in os.listdir(data_dir or '.'):
            if f.startswith(local):
                full_path = os.path.join(data_dir, f)
                new_data = self._read_file(full_path)
                for filename, file_data in new_data.items():
                    self.lines.setdefault(filename, {}).update(file_data)

    def add_line_data(self, data_points):
        """Add executed line data.
        
        `data_points` is (filename, lineno) pairs.
        
        """
        for filename, lineno in data_points:
            self.lines.setdefault(filename, {})[lineno] = True

    def executed_files(self):
        """A list of all files that had been measured as executed."""
        return self.lines.keys()

    def executed_lines(self, filename):
        """A map containing all the line numbers executed in `filename`.
        
        If `filename` hasn't been collected at all (because it wasn't executed)
        then return an empty map.

        """
        return self.lines.get(filename) or {}

    def summary(self):
        """Return a dict summarizing the coverage data.
        
        Keys are the basename of the filenames, and values are the number of
        executed lines.  This is useful in the unit tests.
        
        """
        summ = {}
        for filename, lines in self.lines.items():
            summ[os.path.basename(filename)] = len(lines)
        return summ
