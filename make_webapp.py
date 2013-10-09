#!/usr/bin/env python

# Copyright (c) 2013 Intel Corporation. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
Make webapps for both android and tizen

Sample usage from shell script:
Build all apps for both Tizen and Android
    python make_webapp.py
Build specified app
    python make_webapp.py --app=MemoryGame
Only build for Android
    python make_webapp.py --target=android
Update Web Apps before build
    python make_webapp.py -u

The build result will be under out directory.

In the build time:
If the app is a submodule from external repo, it will create a new branch named
'auto_patch', and patch needed patches.
When build finished, submodule branch will checkout to 'master' branch,
'auto_patch' will be remained for future analyze, and will be recreated
in the next build.
"""
import optparse
import os
import shutil
import subprocess
import sys

import android.android_build_app


def FindApps(app_list):
  for i in os.listdir('.'):
    if os.path.isdir(i):
      check_file = os.path.join('.', i, 'manifest.json')
      if os.path.exists(check_file):
        app_list.append(i)


def BuildForAndroidApp(current_real_path, app, build_result):
  return_value = android.android_build_app.BuildApp(current_real_path, app)
  if not return_value:
    build_result = build_result + app + ' :OK\n'
  else:
    build_result = build_result + app + ' :Failed, error code = ' + str(return_value) +'\n'
  return build_result

def CheckoutToMasterBranch(current_real_path, app):
  # Check whether it's a git submodule.
  git_file = os.path.join(current_real_path, app, 'src', '.git')
  if not os.path.exists(git_file):
    return

  # cd to submodule dir.
  previous_cwd = os.getcwd()
  os.chdir(os.path.join(current_real_path, app, 'src'))

  proc = subprocess.Popen(['git', 'checkout', 'master'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
  out, _ = proc.communicate()
  print out
  # Revert cd.
  os.chdir(previous_cwd)


def ApplyPatches(current_real_path, app):
  # Check whether it's a git submodule.
  git_file = os.path.join(current_real_path, app, 'src', '.git')
  if not os.path.exists(git_file):
    #TODO Need to be designed.
    # It's not a git submodule, no patch needed.
    return

  # Checkout to 'master' branch.
  CheckoutToMasterBranch(current_real_path, app)

  # cd to submodule dir.
  previous_cwd = os.getcwd()
  os.chdir(os.path.join(current_real_path, app, 'src'))

  # Delete previous auto_patch branch.
  proc = subprocess.Popen(['git', 'branch', '-D', 'auto_patch'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
  out, _ = proc.communicate()
  print out

  # Create auto_patch branch.
  proc = subprocess.Popen(['git', 'checkout', '-b', 'auto_patch', 'origin/master'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
  out, _ = proc.communicate()
  print out

  # Copy manifest.json.
  jsonfile = os.path.join(current_real_path, app, 'manifest.json')
  shutil.copy2(jsonfile, '.')

  #TODO
  # Apply patches with code.

  # Commit patch.
  proc = subprocess.Popen(['git', 'add', '*'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
  out, _ = proc.communicate()
  print out

  proc = subprocess.Popen(['git', 'commit', '-m', 'Auto patch'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
  out, _ = proc.communicate()
  print out

  # Revert cd.
  os.chdir(previous_cwd)


def BuildApps(func, current_real_path, app_list, build_result):
  for app in app_list:
    print 'Build ' + app + ':'
    ApplyPatches(current_real_path, app)
    build_result = func(current_real_path, app, build_result)
    # Checkout to master branch to make 'git status' happy.
    CheckoutToMasterBranch(current_real_path, app)
    # The 'auto_patch' branch will be remained for future analyze.
    # And will be delete in the next build time.
  return build_result


def RunDownloadScript(options, current_real_path):
  if not options.version:
    print ('Please use --version or -v argument to specify xwalk application template version\n'
          'Or you can run android/get_xwalk_app_template.py to download')
    return False
  print 'Downloading xwalk_app_template'
  version = '--version=' + options.version
  download_script = os.path.join(current_real_path, 'android', 'get_xwalk_app_template.py')
  proc = subprocess.Popen(['python', download_script, version],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
  out, _ = proc.communicate()
  print out
  return True


def CheckAndroidBuildTool(options, current_real_path):
  xwalk_app_template_path = os.path.join(current_real_path, 'android', 'xwalk_app_template')
  if not os.path.exists(xwalk_app_template_path):
    if RunDownloadScript(options, current_real_path):
      return True
    return False
  return True


def UpdateWebApps():
  print 'Update submodules..'
  proc = subprocess.Popen(['git', 'submodule', 'foreach', 'git', 'checkout', 'master'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
  out, _ = proc.communicate()
  print out
  proc = subprocess.Popen(['git', 'submodule', 'foreach', 'git', 'pull'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
  out, _ = proc.communicate()
  print out


def InitWebApps():
  print 'Init submodules..'
  proc = subprocess.Popen(['git', 'submodule', 'update', '--init'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
  out, _ = proc.communicate()
  print out


def Build_WebApps(options, current_real_path, build_result):
  app_list = []
  if options.app:
    app_list.append(options.app)
  else:
    # No app specified, loop to find all available apps.
    FindApps(app_list)

  if len(app_list) == 0:
    build_result += 'No available apps.\n'
    return build_result

  # Init git submodules at the first time.
  # (git will automatically check whether need init the next time).
  InitWebApps()

  # Update git submodules if needed.
  if options.update:
    UpdateWebApps()

  # Build apps.
  if options.target == 'android':
    if CheckAndroidBuildTool(options, current_real_path):
      build_result = BuildApps(BuildForAndroidApp, current_real_path, app_list, build_result)
    else:
      build_result += 'No Build tools\n'
  elif options.target == 'tizen':
    print 'Tizen build not implemented'
  else:
    if CheckAndroidBuildTool(options, current_real_path):
      build_result = BuildApps(BuildForAndroidApp, current_real_path, app_list, build_result)
    else:
      build_result += 'No Build tools\n'
  return build_result


def main():
  build_result = '\nBuild Result:\n'
  parser = optparse.OptionParser()
  parser.add_option('--app',
      help='The app name, If no app specified, all apps will be built '
           'Such as: --app=MemoryGame')
  parser.add_option('--target',
      help='Target, If no target specified, all targets will be built '
           'Such as: --target=android')
  parser.add_option('-u', '--update', action='store_true',
      dest='update', default=False,
      help='Whether update web apps to latest version')
  parser.add_option('-v', '--version', action='store', dest='version',
      help='The xwalk application template version. Such as: '
           '--version=1.29.7.0')
  options, _ = parser.parse_args()
  current_real_path = os.path.abspath(os.path.dirname(sys.argv[0]))
  try:
    build_result = Build_WebApps(options, current_real_path, build_result)
  except:
    print 'Unexpected error:', sys.exc_info()[0]
  finally:
    print build_result
  return 0


if __name__ == '__main__':
  sys.exit(main())
