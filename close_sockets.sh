#!/usr/bin/env bash
# Disclaimer: This script was purpose built for CentOS/RHEL-7
# It most likely will not work on your system without
# modification.
# This is an example of how to kill sockets with gdb
# This example kills celery worker sockets.

# Where we're doing to dump our gdb commands.
gdb_file=gdb.commands
# The parent tends to be the first pid that shows up in the list.
celery_parent=$(ps -ef | grep celery.worker | awk 'NR==1 {print $2}')
celery_ampq_fds=$(lsof -np $celery_parent | grep TCP | awk '{print $4}')
# Argument that runs gdb and closes the TCP socket file descriptors
sweep_the_leg=$1

function cleanup() {
  echo "celery_parent is $celery_parent"
  echo "celery_ampq_fds are ${celery_ampq_fds}"
  echo "Deleting old gdb_commands"
  rm -f $gdb_file
}

function close_sockets() {
  for i in $celery_ampq_fds;
  do
    echo "call close($i)" >> $gdb_file
  done
  echo "quit" >> $gdb_file
  gdb -p $celery_parent -x $gdb_file &> /dev/null
}

main() {
  cleanup
  if [ "$sweep_the_leg" == "-k" ];
  then
    while true
    do
      echo "You're going down Daniel San!"
      close_sockets
      sleep 30
    done
  fi
}

main "$@"
