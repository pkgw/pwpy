# Common utilities for the wankerscripts

set -e

logfile=wank.log

# Source this later so settings above can be overridden.
. config.sh

function cmd () {
    echo + "$@" |tee -ia wank.log
    "$@" |tee -ia wank.log
}

function shhcmd () {
    echo + "$@" |tee -ia wank.log
    "$@" >> wank.log
}

echo RUN : `date` : $0 "$@" >>wank.log

