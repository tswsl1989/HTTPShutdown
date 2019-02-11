from flask import Flask, render_template, flash, redirect, url_for, g, request

import os
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", default=None)

@app.route('/')
def web_root():
    return render_template("index.html")

action_texts = { "poweroff": "shut down and turn off", "reboot": "shut down and attempt to restart"}

@app.route('/action')
@app.route('/action/<action>', methods=['GET', 'POST'])
def web_action(action=None):
    if action is None:
        flash("No action specified", "error")
        return redirect(url_for("web_root"))

    if not action in ["poweroff", "reboot"]:
        flash(f"Action '{action}' is not valid", "error")
        return redirect(url_for("web_root"))

    from dbus import SystemBus, Interface
    try:
        bus = SystemBus()
    except Exception:
        flash("Unable to access DBus", "error")
        return redirect(url_for("web_root"))
    lg = bus.get_object('org.freedesktop.login1','/org/freedesktop/login1')
    pm = Interface(lg, 'org.freedesktop.login1.Manager')

    if request.method == "POST":
        try:
            assert request.form['vcode'] == request.form['verify']
            assert request.form['action'] == action
        except AssertionError:
            flash(f"Action verification failed - no further action taken", "error")
            return redirect(url_for("web_root"))

        try:
            if action == "poweroff":
                assert pm.CanPowerOff() == "yes"

            if action == "reboot":
                assert pm.CanReboot() == "yes"
        except AssertionError:
            flash("Permission denied", "error")
            return redirect(url_for("web_root"))

        try:
            if action == "poweroff":
                flash("pm.PowerOff(False)")

            if action == "reboot":
                pm.Reboot(False)
            flash("Power management request sent", "success")
        except Exception as e:
            flash(str(e), "error")
            return redirect(url_for("web_root"))

        return redirect(url_for("web_root"))
    else:

        g.acttext = action_texts[action]
        g.action = action
        import random
        g.vcode = random.randrange(100000,999999)
        return render_template("confirm.html")

