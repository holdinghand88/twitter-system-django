from pickle import TRUE
from celery import shared_task
from django.shortcuts import render, redirect, get_object_or_404
import time
import asyncio
from .models import *
from .utils import autolike
import datetime
from django.core.files import File
from pathlib import Path
import shutil
import pytz

@shared_task
def test(instance_id):
    print("Starting Execution..")
    autolike = get_object_or_404(AutoLikeSetting,id=instance_id)
    today = datetime.datetime.today().astimezone(pytz.timezone('Asia/Tokyo'))
    print(today)
    next_execution_date = today + datetime.timedelta(hours=1)
    print(next_execution_date)
    return autolike.status