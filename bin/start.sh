#!/bin/bash

gunicorn app --log-file - --timeout 300
