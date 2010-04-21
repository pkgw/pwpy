#!/bin/bash

# flag end channels
uvflag vis=$1 flagval=f line=ch,100,1,1,1
uvflag vis=$1 flagval=f line=ch,100,924,1,1

# flag short-spacings
uvflag vis=$1 select="uvrange(0,0.08)" flagval=f

# flag bad antennas
uvflag vis=$1 select="ant(10,32,33)" flagval=f
