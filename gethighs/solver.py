import os
import time
import math
import subprocess
import numpy as np
import pyomo.environ as pyo
from gethighs.highsfiles import HiGHSBaseFile, HiGHSOptions,\
    ModelFileMPS, SolFile, WarmstartFile, LogFile


# ----------------------------------------------------------------------------------
# Implementation
# ----------------------------------------------------------------------------------

SOL_ERROR_MSG = """HiGHS failed when writing the solution file - It is incomplete. Try setting a longer `sleep_time`. Insert a 'try-except' block and re-solve the problem"""


class HiGHS:

    cmd_keys = ("time_limit", "write_model_file", "solution_file")
    base_file = HiGHSBaseFile()

    def __init__(
        self,
        executable="highs",
        time_limit=None,
        write_model_file=None,
        solution_file=None,
        log_file=None,
        **options,
    ):
        """HiGHS solver compatible with pyomo

        Parameters
        ----------
        executable : str | None, optional
            Path to highs executable file. If None, it is assumed to be in PATH

        time_limit : float | int | str | None, optional
            Time limit passed to HiGHS, by default None

        write_model_file : str | None, optional
            Output file (path included) to write model as .lp or .mps, by default None

        solution_file : str | None, optional
            Output file (path included) to write HiGHS solution as .sol, by default None

        log_file : str | None, optional
            Log file (path included) to write HiGHS log as .log, by default uses HiGHS.log
        """
        # Basic keyword arguments passed in cmd line
        self.executable = executable
        self.time_limit = time_limit
        self.write_model_file = write_model_file
        self.solution_file = solution_file
        self.log_file = log_file

        # Other arguments stored in dict
        self.options = HiGHSOptions(**options)

        # Fill future properties
        self.model = None
        self.all_symbols = None
        self.suffix = None
        self.modelfile = ModelFileMPS()
        self.solfile = SolFile()
        self.logfile = LogFile()
        self.warmstart_file = WarmstartFile()
        self.status = "Unsolved"
        self.primal_solutions = "Unsolved"
        self.objective = "Unsolved"

    def __repr__(self) -> str:
        return f"""status: {self.status}\nprimal_solutions: {self.primal_solutions}\nobjective: {self.objective}"""

    def set_options(self, **options):
        """Set HiGHS options to be stored in a dictonary and parsed to the solver when calling ``solve``
        """
        self.options.set_options(**options)

    def reset_options(self, **options):
        """Erase all current HiGHS options and restart. They shall be then stored in a dictonary
        and parsed to the solver when calling ``solve``
        """
        self.__init__(executable=self.executable, **options)

    def parse_options(self, **options):
        """This is a similar method to ``set_options`` in which the options are not yet stored in temporary file
        """
        cmd_options, other_options = self._split_options(**options)
        self._parse_cmd_options(**cmd_options)
        self.options.parse_options(**other_options)

    def _split_options(self, **options):
        cmd_options = {}
        other_options = {}
        for key, val in options.items():
            if key in self.cmd_keys:
                cmd_options[key] = val
            else:
                other_options[key] = val
        return cmd_options, other_options

    def _parse_cmd_options(self, **options):
        for key, value in options.items():
            if value is not None:
                self.__setattr__(key, value)

    def solve(
        self,
        model,
        time_limit=None,
        warmstart=False,
        write_model_file=None,
        solution_file=None,
        log_file=None,
        removefiles=True,
        removelog=False,
        symbolic_model=False,
        rounding_digits=8,
        truncate_precision=8,
        sleep_time=0.1,
        **options
    ):
        """Solve the current Pyomo optimization model using HiGHS executable

        Parameters
        ----------
        model : Model
            Pyomo initialized model instance

        time_limit : int | float | str, optional
            Time limit in seconds. Overrides time_limit parameter from options. By default None

        warmstart : bool, optional
            Either or not to use the current solutions as warmstart. Be careful about model changes.
            Infeasible solutions won't work in HiGHS. By default False

        write_model_file : str, optional
            File to wtore model as .lp or .mps (path included), by default None

        solution_file : str, optional
            File to store solution as .sol (path included), by default None

        log_file : str, optional
            File to store HiGHS log file (path included). By default None, which stores in "HiGHS.log"
            relative to the current path

        removefiles : bool, optional
            Either or not to remove temporary files after optimization (model, options, and solution),
            by default True

        removelog : bool, optional
            Either or not to remove the log file (for now the feature is broken and it should be removed manually),
            by default False

        symbolic_model : bool, optional
            Either or not to write model using symbols, by default False

        rounding_digits : int, optional
            Digits considered when reading solution, by default 8

        truncate_precision : int, optional
            Significant digits considered when reading solution (after rounding), by default 8

        sleep_time : float | int, optional
            Time (in seconds) considered to check for a solution and interrupt the process, by default 0.1

        Returns
        -------
        str
            Description of solver results.
            Model is modified inplace to store new solutions as .value of decision variables.
        """

        self.base_file.open_tmp_folder()

        self._parse_cmd_options(
            time_limit=time_limit,
            write_model_file=write_model_file,
            solution_file=solution_file,
            log_file=log_file,
        )

        suffix = str(int(time.time_ns()))
        self.suffix = suffix

        self.modelfile.parse_file(file=self.write_model_file, suffix=suffix)
        modelfile = self.modelfile()
        self._write_symbol_map(model, modelfile, symbols=symbolic_model)

        self.solfile.parse_file(file=self.solution_file, suffix=suffix)
        solfile = self.solfile()

        self.warmstart_file.parse_file(suffix=suffix)
        rsf = ""
        if warmstart:
            warmstart_file = self.warmstart_file()
            self._write_warmstartfile(warmstart_file)
            rsf = f"--read_solution_file {warmstart_file} "

        self.logfile.parse_file(file=self.log_file, suffix=None)
        logfile = self.logfile()
        options["log_file"] = logfile

        self.set_options(**options)
        options_file = self.options()

        time.sleep(sleep_time)
        cmd_time = self._cmd_timelim
        cmd_line = \
            f"{self.executable} {cmd_time} --solution_file {solfile} {rsf}--options_file {options_file} {modelfile}"
        self.cmd_line = cmd_line
        process = subprocess.Popen(cmd_line, shell=True)
        time.sleep(sleep_time)
        while not os.path.exists(solfile):
            time.sleep(sleep_time)
        while not self._check_complete_sol():
            time.sleep(sleep_time)
        time.sleep(sleep_time)
        process.terminate()

        self._read_values_from_sol(
            rounding_digits=rounding_digits,
            truncate_precision=truncate_precision,
        )

        if removefiles:
            self._delete_files()

        if removelog:
            self.logfile.delete_file()

        return self.__repr__()

    def _delete_files(self):
        self.options.delete_file()
        self.modelfile.delete_file()
        self.solfile.delete_file()
        self.warmstart_file.delete_file()

    @property
    def n_var(self):
        return sum([1 for obj in self.all_symbols.values() if pyo.is_variable_type(obj)])

    @property
    def _cmd_timelim(self):
        if self.time_limit:
            return f" --time_limit {self.time_limit}"
        else:
            return ""

    def _write_symbol_map(self, model, filename="model.mps", symbols=False):
        filename, map_id = model.write(filename, io_options={'symbolic_solver_labels': symbols})
        all_symbols = {}
        for symbol, obj in model.solutions.symbol_map[map_id].bySymbol.items():
            all_symbols[symbol] = obj
        self.all_symbols = all_symbols
        self.model = model

    def _check_complete_sol(self):
        with open(self.solfile(), "r") as file:
            file_txt = file.read()
            check = "# Basis\nHiGHS" in file_txt
            check = check and file_txt.endswith("\n")
        return check

    def _read_values_from_sol(self, rounding_digits=8, truncate_precision=8, **kwargs):
        status = None
        primal_solutions = None
        objective = None
        solfile = self.solfile()

        with open(solfile, "r") as file:
            lines = file.readlines()
            for j, line in enumerate(lines):
                while status is None and j <= 10:
                    if "Model status" in line:
                        status = lines[j + 1].rstrip("\n")
                else:
                    if "# Primal solution values" in line:
                        primal_solutions = lines[j + 1].rstrip("\n")
                        objective_line = lines[j + 2].rstrip("\n")
                        splt = objective_line.split(sep=" ", maxsplit=1)
                        try:
                            objective = float(splt[-1])
                        except (ValueError, TypeError):
                            pass
                        continue
                    else:
                        splt = line.split(sep=" ", maxsplit=1)
                        if splt[0] in self.all_symbols.keys():
                            if pyo.is_variable_type(self.all_symbols[splt[0]]):
                                if len(splt) > 0:
                                    value = round(float(splt[1]), rounding_digits)
                                    self.all_symbols[splt[0]].value = truncate(value, precision=truncate_precision)
                                else:
                                    raise SystemError(SOL_ERROR_MSG)

        self.status = status
        self.primal_solutions = primal_solutions
        self.objective = objective

    def _write_warmstartfile(self, filename):
        with open(filename, "w") as file:
            file.write("Model status\n")
            file.write(f"Unknown\n\n")
            file.write("# Primal solution values\n")
            file.write(f"Unknown\n")
            file.write(f"Objective Unknown\n")
            N = self.n_var
            file.write(f"# Columns {N}\n")
            for key, obj in self.all_symbols.items():
                if pyo.is_variable_type(obj):
                    if obj.value is None:
                        file.write(f"{key} 0.0\n")
                    else:
                        file.write(f"{key} {obj.value}\n")


def truncate(x: float, precision=16):
    base = math.floor(np.log10(abs(x) + 10**(-precision)))
    digits = max(precision - base, 1)
    return round(x, digits)
