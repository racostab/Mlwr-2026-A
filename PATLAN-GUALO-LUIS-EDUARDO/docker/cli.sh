#!/bin/bash

CONTAINER_NAME="$2"

case "$1" in
start)
    echo "Iniciando el contenedor..."
    docker start "$CONTAINER_NAME"
;;

stop)
    echo "Deteniendo el contenedor..."
    docker stop "$CONTAINER_NAME"
;;

pause)
    echo "Pausando el contenedor..."
    docker pause "$CONTAINER_NAME"
;;

unpause)
    echo "Reanudando el contenedor..."
    docker unpause "$CONTAINER_NAME"
;;

*)
    echo "Uso:"
    echo "./cli.sh start     CONTAINER_NAME"
    echo "./cli.sh stop      CONTAINER_NAME"
    echo "./cli.sh pause     CONTAINER_NAME"
    echo "./cli.sh unpause   CONTAINER_NAME"
;;
esac
