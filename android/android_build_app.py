#!/usr/bin/env python

# Copyright (c) 2013 Intel Corporation. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
Buid web app with xwalk_app_template with argument --manifest=manifest.json.
And the build result will be copied to ../out/android.
"""

import optparse
import os
import shutil
import subprocess
import sys

def CopyApkToOut(apk_path, base_dir):
  if not os.path.exists(apk_path):
    print "Build failed"
    return 3

  destination = os.path.join(base_dir, 'out', 'android')
  if not os.path.exists(destination):
    os.makedirs(destination)
  shutil.copy2(apk_path, destination)
  return 0


def BuildApp(base_dir, app_name):
  xwalk_app_template_path = os.path.join(base_dir, 'android', 'xwalk_app_template')
  make_apk_script = os.path.join(xwalk_app_template_path, 'make_apk.py')

  # Check xwalk_app_template.
  if not os.path.exists(make_apk_script):
    print 'Please install xwalk_app_template '
    return 1

  # Check manifest.json file.
  jsonfile = os.path.join(base_dir, app_name, 'src', 'manifest.json')
  if not os.path.exists(jsonfile):
    print 'No manifest.json found at ' + jsonfile
    return 2

  manifest = "--manifest=" + jsonfile
  previous_cwd = os.getcwd()
  os.chdir(xwalk_app_template_path)
  proc = subprocess.Popen(['python', make_apk_script, manifest],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  out, _ = proc.communicate()
  print out
  os.chdir(previous_cwd)

  # Copy result to out.
  apk_path = os.path.join(xwalk_app_template_path, app_name)
  return CopyApkToOut(apk_path + '.apk', base_dir)
