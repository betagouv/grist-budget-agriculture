#!/bin/bash

gunicorn grist_budget_agriculture.app --log-file - --timeout 300
