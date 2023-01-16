import os
import math
from typing import Any
import numpy as np


# ----------------------------------------------------------------------------------
# Implementation
# ----------------------------------------------------------------------------------


class HiGHSBaseFile:
    
    tmp = "./tmp"
    filename = tmp + ""
    temporary = True
    
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.filename
    
    def __repr__(self) -> str:
        return self.filename
    
    def open_tmp_folder(self):
        """Make sure that there exists a ./tmp folder to store files
        """
        exists = os.path.exists(self.tmp)
        if not exists:
            os.mkdir(self.tmp)
    
    def delete_tmp_folder(self):
        """Delete ./tmp folder if empty
        """
        if not os.listdir(self.tmp):
            os.removedirs(self.tmp)
    
    def delete_file(self):
        if self.temporary:
            os.remove(self.filename)
            self.delete_tmp_folder()


class HiGHSOptions(dict, HiGHSBaseFile):
    
    filename = HiGHSBaseFile.tmp + "/options.txt"

    def set_options(self, **options):
        self.parse_options(**options)
        self.open_tmp_folder()
        with open(self.filename, "w") as file:
            for key, value in self.items():
                file.write(f"{key} = {value}\n")
    
    def reset_options(self, **options):
        self.__init__(**options)
        self.set_options(**options)
    
    def parse_options(self, **options):
        for key, value in options.items():
            self.__setitem__(key, value)


class HiGHSMainFile(HiGHSBaseFile):
    
    def __init__(self, file=None, suffix=None, **kwargs) -> None:
        self.parse_file(file=file, suffix=suffix, **kwargs)
    
    def parse_file(self, file=None, suffix=None, **kwargs):
        if file:
            self.temporary = False
            self.filename = file
        elif suffix:
            suffix = str(suffix).replace(".", "")
            self.filename = self._parse_from_suffix(suffix=suffix, **kwargs)
        else:
            pass


class ModelFileMPS(HiGHSMainFile):
    
    filename = HiGHSMainFile.tmp + "/model.mps"
    
    def _parse_from_suffix(self, suffix=None, **kwargs):
        return self.tmp + f"/model{suffix}.mps"


class ModelFileLP(HiGHSMainFile):
    
    filename = HiGHSMainFile.tmp + "/model.lp"
    
    def _parse_from_suffix(self, suffix=None, **kwargs):
        return self.tmp + f"/model{suffix}.lp"


class SolFile(HiGHSMainFile):
    
    filename = HiGHSBaseFile.tmp + "/solution.sol"
    
    def _parse_from_suffix(self, suffix=None, **kwargs):
        return self.tmp + f"/solution{suffix}.sol"


class LogFile(HiGHSMainFile):
    
    filename = "HiGHS.log"
    
    def parse_file(self, file=None, suffix=None, **kwargs):
        if file:
            self.filename = file
        else:
            pass


class WarmstartFile(HiGHSMainFile):
    
    filename = HiGHSBaseFile.tmp + "/warmstart.sol"
    
    def _parse_from_suffix(self, suffix=None, **kwargs):
        return self.tmp + f"/warmstart{suffix}.sol"
    
    def delete_file(self):
        path = self()
        if os.path.exists(path):
            os.remove(self.filename)
            self.delete_tmp_folder()