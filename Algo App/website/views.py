from flask import Blueprint, render_template, flash, jsonify, redirect
from flask.globals import request
from flask.helpers import url_for
from flask_login import login_required, current_user
from .models import Note
from . import db
import json
import threading
from .strategies import Stoch_Scalp, SMA5_Cross, Triple_STrend

views = Blueprint('views', __name__)


@views.route('/', methods=['GET','POST'])
@login_required
def home():
    status = [] #TODO: Get status of each strategy
    if request.method == "POST":
        strategy_id = request.form.get('strategy')
        if strategy_id == "strat1":
            algo = Stoch_Scalp()
            t = threading.Thread(target=algo.start)
            t.start()
        elif strategy_id == "strat2":
            algo = SMA5_Cross()
            t = threading.Thread(target=algo.start)
            t.start()
        elif strategy_id == "strat3":
            algo = Triple_STrend()
            t = threading.Thread(target=algo.start)
            t.start()
      
    return render_template("home.html", user=current_user, status=status)