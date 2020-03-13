#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re

dir_path = os.listdir(os.path.abspath(os.path.dirname(__file__)))
handler_files = [x for x in dir_path if re.findall('[A-Za-z]\w+handler\.py$', x)]

for handler_file in handler_files:
    model_name = handler_file[:-3]
    __import__(model_name, globals=globals(), locals=locals(), fromlist=[model_name], level=1)