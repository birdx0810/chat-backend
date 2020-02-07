#!/bin/bash

kill -SIGTERM $(cat ./logs/service.pid)

