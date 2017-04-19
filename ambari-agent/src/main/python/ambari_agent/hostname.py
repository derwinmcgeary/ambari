#!/usr/bin/env python

'''
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import socket
import subprocess
import urllib2
import logging
import traceback

logger = logging.getLogger(__name__)

cached_hostname = None
cached_public_hostname = None
cached_server_hostnames = []

def arrayFromCsvString(str):
  CSV_DELIMITER = ','

  result_array = []
  items = str.lower().split(CSV_DELIMITER)

  for item in items:
    result_array.append(item.strip())
  return result_array

def isValidHostname(candidate): # Ref: https://blogs.msdn.microsoft.com/oldnewthing/20120412-00/?p=7873/
  allowedChars = set(string.ascii_letters + string.digits + '-' + '.')

  if len(candidate) > 255 or len(candidate) < 1:
    return False

  if not set(candidate) <= allowedChars:
    return False

  if candidate[0] == '.' or candidate[-2:] == "..":
    return False

  if candidate[-1] == '.':
    candidate = candidate[:-1]

    for part in candidate.split("."):
      if len(part) > 63 or len(part) == 0:
        return False

    if part[0] == '-' or part[-1] == '-':
      return False

  return True
  
def hostname(config):
  global cached_hostname
  if cached_hostname is not None:
    return cached_hostname

  try:
    scriptname = config.get('agent', 'hostname_script')
    try:
      osStat = subprocess.Popen([scriptname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      out, err = osStat.communicate()
      if (0 == osStat.returncode and 0 != len(out.strip())):
        cached_hostname = out.strip()
      else:
        cached_hostname = socket.getfqdn()
    except:
      cached_hostname = socket.getfqdn()
  except:
    cached_hostname = socket.getfqdn()
  cached_hostname = cached_hostname.lower()
  return cached_hostname


def public_hostname(config):
  global cached_public_hostname
  if cached_public_hostname is not None:
    return cached_public_hostname

  out = ''
  err = ''
  try:
    if config.has_option('agent', 'public_hostname_script'):
      scriptname = config.get('agent', 'public_hostname_script')
      output = subprocess.Popen(scriptname, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
      out, err = output.communicate()
      if (0 == output.returncode and 0 != len(out.strip())):
        cached_public_hostname = out.strip().lower()
        logger.info("Read public hostname '" + cached_public_hostname + "' using agent:public_hostname_script")
        return cached_public_hostname
      else:
        logger.warn("Execution of '{0}' returned {1}. {2}\n{3}".format(scriptname, output.returncode, err.strip(), out.strip()))
  except:
    #ignore for now.
    trace_info = traceback.format_exc()
    logger.info("Error using the scriptname:" +  trace_info
                + " :out " + out + " :err " + err)
    logger.info("Defaulting to fqdn.")

  try:
    handle = urllib2.urlopen('http://169.254.169.254/latest/meta-data/public-hostname', '', 2)
    str = handle.read()
    handle.close()
    if isValidHostname(str.lower):
      cached_public_hostname = str.lower()
    else:
      throw ValueError("Result from http://169.254.169.254/latest/meta-data/public-hostname was not a valid hostname")
      logger.warn("Result from http://169.254.169.254/latest/meta-data/public-hostname was not a valid hostname")
    logger.info("Read public hostname '" + cached_public_hostname + "' from http://169.254.169.254/latest/meta-data/public-hostname")
  except:
    cached_public_hostname = socket.getfqdn().lower()
    logger.info("Read public hostname '" + cached_public_hostname + "' using socket.getfqdn()")
  return cached_public_hostname

def server_hostnames(config):
  """
  Reads the ambari server name from the config or using the supplied script
  """
  global cached_server_hostnames
  if cached_server_hostnames != []:
    return cached_server_hostnames

  if config.has_option('server', 'hostname_script'):
    scriptname = config.get('server', 'hostname_script')
    try:
      osStat = subprocess.Popen([scriptname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      out, err = osStat.communicate()
      if (0 == osStat.returncode and 0 != len(out.strip())):
        cached_server_hostnames = arrayFromCsvString(out)
        logger.info("Read server hostname '" + cached_server_hostnames + "' using server:hostname_script")
    except Exception, err:
      logger.info("Unable to execute hostname_script for server hostname. " + str(err))

  if not cached_server_hostnames:
    cached_server_hostnames  = arrayFromCsvString(config.get('server', 'hostname'))
  return cached_server_hostnames


def main(argv=None):
  print hostname()
  print public_hostname()
  print server_hostname()

if __name__ == '__main__':
  main()
