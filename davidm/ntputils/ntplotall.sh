#!/bin/bash -x

hosts=({f,x}{1,2}.fxa boot2 antcntl maincntl)

outextdev=png/png

if [ "$1" == "-d" ]
then
  outextdev="$2"
  shift 2
fi

for h in ${hosts[@]}
do
  mkdir -p ${h}
  rsync -a --bwlimit=100 "${h}:/var/log/ntpstats/*.*" ${h}/.
done

hosts[${#hosts[@]}]='aeon'

for h in ${hosts[@]}
do
  for loop_file in ${h}/loop*s.????????
  do
    plot_extdev="${loop_file/loop*s./${h}.loops.}.${outextdev}"
    if [ ${loop_file} -nt ${plot_extdev%/*} ]
    then
      ntplotloop.rb -d ${plot_extdev} ${loop_file}
    fi
  done

  for peer_file in ${h}/peer*s.????????
  do
    plot_extdev="${peer_file/peer*s./${h}.peers.}.${outextdev}"
    if [ ${peer_file} -nt ${plot_extdev%/*} ]
    then
      ntplotpeer.rb -d ${plot_extdev} ${peer_file}
    fi
  done
done
