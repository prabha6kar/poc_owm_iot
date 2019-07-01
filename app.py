#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  28 22:23:52 2019

@author: prabhakaran
"""

import dash

app = dash.Dash(__name__, sharing=True, csrf_protect=False)
server = app.server
app.config.suppress_callback_exceptions = True