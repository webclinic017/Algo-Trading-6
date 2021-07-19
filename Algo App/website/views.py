from flask import Blueprint, render_template, flash, jsonify, redirect
from flask.globals import request
from flask.helpers import url_for
from matplotlib.pyplot import get
from flask_login import login_required, current_user
from .models import Note
from . import db
import json
import threading
from .strategies import CipherB

views = Blueprint('views', __name__)

##########################################
#Only Hardcoded part of website
strats = {}
strats['CipherB'] = CipherB, CipherB()
##########################################

threads = []
for strat in strats:
    instance = strats[strat][1]
    t = threading.Thread(target=instance.start)
    threads.append(t)

@views.route('/', methods=['GET','POST'])
@login_required
def home():
    if request.method == "POST":
        strategy_id = request.form.get('strategy')

        for i,strat in enumerate(strats.keys()):
            thread = threads[i]
            if strategy_id == strat:
                if thread.isAlive():
                    strats[strat][1].run = False
                    strats[strat] = strats[strat][0],strats[strat][0]()
                    threads[i] = threading.Thread(target=strats[strat][1].start)
                else:
                    thread.start()
                break
        
        return render_template("home.html", user=current_user, strats=[(s,strats[s],threads[i].isAlive()) for i,s in enumerate(strats)])
    return render_template("home.html", user=current_user, strats=[(s,strats[s],threads[i].isAlive()) for i,s in enumerate(strats)])