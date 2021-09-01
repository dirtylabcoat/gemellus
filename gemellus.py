#!/usr/bin/python3

import os
import sys
import getopt
import hashlib
import sqlite3

class Configuration:
  def __init__(self, input_dir: str):
    self.input_dir = input_dir

def config_from_args(argv):
  # Default to current directory
  input_dir = './'
  try:
    opts, _ = getopt.getopt(argv,"hd:",["help", "dir="])
  except getopt.GetoptError as opts_error:
    print ("Something error happens:", opts_error)
    sys.exit(2)
  for opt, arg in opts:
    if opt in ("-h", "--help"):
      print ("Usage: gemellus.py -d <directory_to_search>")
      sys.exit()
    elif opt in ("-d", "--dir"):
      input_dir = arg
  config = Configuration(input_dir)
  return config

def sha1(fname):
  hash_sha1 = hashlib.sha1()
  with open(fname, "rb") as f:
    for chunk in iter(lambda: f.read(4096), b""):
      hash_sha1.update(chunk)
  return hash_sha1.hexdigest()

if __name__ == "__main__":
  config = config_from_args(sys.argv[1:])
  # Create SQLite DB and table
  conn = sqlite3.connect('/tmp/gemellus.db')
  conn.execute('DROP TABLE IF EXISTS files')
  conn.execute('CREATE TABLE files (filepath VARCHAR(256), size INT, hash VARCHAR(32))')
  for subdir, dirs, files in os.walk(config.input_dir, topdown = True):
    for file in files:
      filepath = os.path.abspath(os.path.join(subdir, file))
      file_hash = sha1(filepath)
      file_size = os.path.getsize(filepath)      
      # Add/update DB with filepath and hash
      cur = conn.cursor()
      cur.execute('INSERT INTO files VALUES (?, ?, ?)', (filepath, file_size, file_hash))
      conn.commit()
  # Find duplicates in DB
  cur = conn.cursor()
  cur.execute('SELECT filepath, size, hash FROM files WHERE hash IN (SELECT hash FROM files GROUP BY hash HAVING COUNT(*) > 1) ORDER BY hash, filepath')
   # cur.execute('SELECT * FROM files')
  rows = cur.fetchall()
  duplicates = {}
  for row in rows:
    if row[2] in duplicates:
      duplicates[row[2]].append(row[0])
    else:
      duplicates[row[2]] = [row[0]]
  conn.close()
  for k in duplicates:
    print (k, '=>')
    for v in duplicates[k]:
      print (v)
