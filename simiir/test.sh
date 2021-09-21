#!/usr/bin/bash

i=0
shopt -s nullglob
configs=()
for f in ../simulations/*.xml
do
    cmd="python run_simiir.py $f"
    configs+=$cmd

done

for i in "$configs[@]":
do
    echo $i
    echo "hello"
    printf "\n"
done
