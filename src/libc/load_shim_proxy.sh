#!/bin/bash

shimlib_path=`pwd`/libnetworkinterpose.so

export LD_PRELOAD=$LD_PRELOAD:$shimlib_path

