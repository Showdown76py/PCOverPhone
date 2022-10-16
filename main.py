import json
import os
import random
import socket
import string
import screenshot_api
import datetime
import sys
import threading
import time
from time import time as currentTime
from types import TracebackType

import easygui
import flask
import pyautogui
import zroya
from flask import (Flask, jsonify, redirect, render_template, request, session,
                   url_for)
from flask.helpers import make_response
from pynput.keyboard import Controller, Key
scapi = screenshot_api.API()

def generate_session_id():
    return ''.join(random.sample((string.ascii_lowercase*2)+string.digits, 12))
app = Flask(__name__, template_folder='templates')
authorizations = {
    "KEY_EXAMPLE": {
        "data": {

        },
        "expire": currentTime()
    }
}
suspended = False
emergencyStop = False
debug=False
with open('credentials.json', 'r') as f: logins = json.load(f)
for (user, psw) in logins.items():
    if psw == 'default_password_CHANGEIT':
        print('Vous avez oublié de changer le mot de passe par défaut. Ouvrez "credentials.json" pour modifier le mot de passe.')
        sys.exit(1)
    del psw, user
ratelimite = currentTime()
blockConnection = -1
machineIP = 'Pour vous connecter sur un autre appareil, allez sur http://' + socket.gethostbyname(socket.gethostname()) + '/\n'
keyboard = Controller()
status = zroya.init(
    app_name="PCOverPhone",
    company_name="Univers Developement",
    product_name="PCOverPhone",
    sub_product="Main product",
    version="BETA"
)

if not status:
    print("Initialization failed")
logins['DEBUG'] = ''.join([generate_session_id() for e in range(60)])
def askAuthorization(details=None, severity=None):
    message = 'Veuillez autoriser ou refuser cette requête faite en ligne.'
    if details: message += '\n\nDétails : ' + details
    if details and severity: message+='\nSévérité : ' + severity
    elif severity: '\n\nSévérité : ' + severity
    answer = easygui.ynbox(message, 'Demande d\'autorisation', ('Autoriser', 'Refuser'))
    time.sleep(1)
    return answer
sessions = {}
def onAction_(nid, action_id):
    global blockConnection
    if action_id == 0: # 5 minutes
        blockConnection = currentTime() + (60*5)
    elif action_id == 1: # 10 minutes
        blockConnection = currentTime() + (60*10)
    elif action_id == 2: # 20 minutes
        blockConnection = currentTime() + (60*20)
    elif action_id == 3: # 1 heure
        blockConnection = currentTime() + (60*60)
    elif action_id == 4: #None
        pass



@app.route('/nohtml')
def nohtml():
    return 'Salut ca va?'
@app.route('/createaction', methods=['POST', 'GET'])
def createac():
    global authorizations
    if request.method == 'GET':
        authorized=False
        if 'authorization' in request.args:
            if request.args['authorization'] in authorizations:
                if 'for' in authorizations[request.args['authorization']]['data'] and 'stade' in authorizations[request.args['authorization']]['data']:
                    if authorizations[request.args['authorization']]['data']['for'] == 'createcustom' and authorizations[request.args['authorization']]['data']['stade'] == 'login':
                        
                        authorizations[request.args['authorization']]['data']['stade'] = 'submit'
                        authorized=True
        return render_template('createapplication.html', authorized=authorized)
    elif request.method == 'POST':
        if len(request.form['description']) > 512:
            return 'description is Too long'
        if len(request.form['name']) > 48:
            return 'name is Too long'
        if len(request.form['button']) > 48:
            return 'button_name is Too long'
        fc = {
            request.form['name']: {
                "description": request.form['description'],
                "button": request.form['button'],
                "action": {
                    "type": request.form['btnradio'],
                    "action": request.form['action']
                }
            }
        }
        if request.form['btnradio'] == 'keyboard':
            fc[request.form['name']]['action']['run_enter'] = (True if request.form['+btnradio'] == 'true' else False)
        
        with open('pc_api/assets/customactions.json', 'r', encoding='utf-8') as f: jfile = json.load(f)
        jfile['actions'][request.form['name']] = fc[request.form['name']]
        denied = True
        if 'authorization' in request.args:
            auth = request.args['authorization']
            if auth in authorizations:
                if authorizations[auth]['data']['for'] == 'createcustom' and authorizations[auth]['data']['stade'] == 'submit':
                    denied = False
        if not denied: 
            with open('pc_api/assets/customactions.json', 'w', encoding='utf-8') as f: f.write(json.dumps(jfile, indent=4))    
            del authorizations[auth]           
        return render_template('createapplication.html', posted=True, denied=denied)
def onAction(nid, action_id):
    global emergencyStop, sessions
    if action_id == 0:
        emergencyStop = True
        template = zroya.Template(zroya.TemplateType.Text4)
        template.setFirstLine("Arrêt d\'urgence déclenché")
        zroya.show(template)
    elif action_id == 1:
        new_sessions = {}
        for (sessionid, settings) in sessions.items():
            new_sessions[sessionid] = {"time": settings['time'], "force_disconnect": True}
        sessions = new_sessions
        template = zroya.Template(zroya.TemplateType.Text4)
        template.setFirstLine("Les sessions expireront à la prochaine connexion.")
        template.setSecondLine('Souhaitez-vous bloquer les connexions temporairement ?')
        template.addAction('5 min')
        template.addAction('10 min')
        template.addAction('20 min')
        template.addAction('1h')
        template.addAction('Rien')
        zroya.show(template, on_action=onAction_)


def emergencyText(text):
    css = ""
    with open('static/css/bootstrap.css', 'r') as f:
        for line in f:
            css += line.strip('\n') + '\n'


    return f"""
<style>

{css}

</style>

<h1>PCOverPhone - Erreur</h1>

<div class="container" style="height: 85%; display: flex; justify-content: center; align-items: center">
{text}
</div>

<center>
    <div class="fixed-bottom" style="padding: 25px">
        <button type="refresh" onclick="window.location.href = window.location.href" class="btn btn-danger">Actualiser la page</button>
    </div>
</center>"""

@app.route('/wait')
def waiter():
    if 'time' in request.args:
        if request.args['time'].isdigit():
            time.sleep(float(request.args['time']))
            return 'Done'
    return 'Done'

@app.before_request
def before_request():
    if emergencyStop:
        return emergencyText("<center><h3>ARRÊT D'URGENCE</h1><ul/><p>L'utilisation du service est interrompue.<br/>Le redémarrage est requis pour réactiver le service de PCOverPhone.</p></center>")
    if 'id' in session and session['id'] in sessions and 'force_disconnect' in sessions[session['id']]:
        del sessions[session['id']]
        return emergencyText("<center><h3>Sortie d'urgence</h1><ul/><p>Vos sessions sont expirées pour des raisons de sécurité.<br/>Réauthentifiez-vous avec les nouveaux identifiants, si ils ont été régénéré.</p></center>")
    if suspended:
        return emergencyText("<center><h3>Service suspendu</h1><ul/><p>Vous avez décidé de suspendre le service. Votre version actuelle ne permet pas de réactiver le service, il faudra donc redémarrer le serveur.</p></center>")
    if blockConnection != -1:
        if blockConnection > currentTime():
            return emergencyText("<center><h3>Connexions bloquées</h1><ul/><p>La connexion au service est temporairement suspendue. Réessayez plus tard.</p></center>")
    if not (request.path.startswith('/login') or request.path.startswith('/static') or request.path.startswith('/wait')):
        if not 'id' in session:
            return redirect("http://" + request.url_root.split('/')[2] + '/login')

        if session['id'] not in sessions or \
           currentTime()+900 <= sessions[session['id']]['time']:
                session.pop('id', None)
                return redirect("http://" + request.url_root.split('/')[2] + '/login?logged_out')
    

def startApplication(app, name, appint=None):
    template = zroya.Template(zroya.TemplateType.Text4)
    template.setFirstLine("L'application " + name + ' a démarré')
    template.setSecondLine("Ce n'est pas vous ?")
    template.addAction("Arrêt d'urgence")
    template.addAction("Expirer les sessions")
    zroya.show(template, on_action=onAction)
    if not appint:
        os.system(app)
    else:
        os.system(f'"{app}"')
@app.route('/')
def mainpart():
    return render_template('main.html')
@app.route('/openlink', methods=['GET', 'POST'])
def openlink():
    if request.method == 'GET':
        return render_template('openlinks.html')
    else:
        link = request.form['link'].split(' ')[0].replace(' ', "").replace('&&', '').replace('|', '').replace(';', '')
        if not link.startswith('http'):
            link = 'http://' + link
        if not '.' in list(link):
            link += '.com'
        startApplication('start ' + link, 'web')
        return render_template('openlinks.html', showran=True, tip=True)

@app.route('/openprograms', methods=['GET', 'POST'])
def openprograms():
    with open('pc_api/assets/programs.json', 'r', encoding='utf-8') as f: jfile=json.load(f)
    still_no_programs=True
    e= []
    if len(jfile['programs']) > 0:        
        for (prog, proginfo) in jfile['programs'].items():
            e.append([prog, proginfo['executable']])
    formate = []
    i=0
    while True:
        tempformation = []

        if len(e) <= i:
            break

        tempformation.append(e[i])
        i+=1 

        if len(e) <= i:
            formate.append(tempformation)
            break

        tempformation.append(e[i])
        formate.append(tempformation)
        i+=1
        continue


        
    
            
        
    still_no_programs=False
    if request.method == 'GET':
        #JSON Pattern
        # {
        #   "programs": {
        #      "SOFTWARE_NAME":
        #          "executable": "PATH TO EXE",
        #          "icon": "ICON PATH, IF EXISTS",
        # }

        # return emergencyText(f"<center><h3>Debugging</h1><ul/><p>{formate}</p></center>")
        
        return render_template('openprograms.html', programsqm=still_no_programs, e=formate, len=len)
    else:
        if request.form.get('start-application'):
            threading.Thread(target=startApplication, args=(jfile['programs'][request.form['start-application']]['executable'],request.form['start-application'])).start()
            return render_template('openprograms.html', programsqm=still_no_programs, e=formate, showran=True, len=len)

@app.route('/opencustom/progress/', methods=['POST'])
def opencustomprogession():
    global authorizations
    if askAuthorization('accès à la création d\'action personnalisée par ' + request.remote_addr, 'critique'):
        license = generate_session_id()
        authorizations[license] = {"data": {"stade": "login", 'for': 'createcustom'}}
        return jsonify(authorized=True, authorization=license)
    return jsonify(authorized=False, authorization='None')

@app.route('/bs21/getkmh')
def getkmhs():
    evale = time.time()
    file = scapi.screenshot_kmh()
    scale = random.uniform(1.28, 1.6)
    scapi.rescaleImage(file, scale)
    read_text = scapi.read_text(file)
    result = scapi.filterText_v2(read_text, category=1)
    if len(result) == 0:
        result = scapi.filterText_v2(read_text, category=2)
    try:
        result = result[0].replace('km/h', ' km/h')
        with open('scaling_logs.log', 'a+') as f: f.write(f'\n[{str(datetime.datetime.now()).split(".")[0]}] Scale "{scale}" has successfully logged "{result}".')
        print('Rep time: ' + str((time.time() - evale) * 1000))
        return jsonify(result=result)
    except:
        with open('scaling_logs.log', 'a+') as f: f.write(f'\n[{str(datetime.datetime.now()).split(".")[0]}] Scale "{scale}" has failed.')
        print(str((time.time() - evale) * 1000))
        return jsonify(result='-- km/h')

@app.route('/suspend')
def suspendre():
    return render_template('suspend.html')

@app.route('/suspend/progress/', methods=['POST'])
def suspendprogression():
    global authorizations, suspended
    if askAuthorization('suspendre le service PCOverPhone jusqu\'à la réactivation du service par l\'IP ' + request.remote_addr, 'faible'):
        suspended = True
        return jsonify(authorized=True, authorization='None')
    return jsonify(authorized=False, authorization='None')

@app.route('/custom_streamdeck', methods=['GET', 'POST'])
def streamdeckmode():
    with open('pc_api/assets/customactions.json', 'r', encoding='utf-8') as f: jfile=json.load(f)
    still_no_programs=True
    e= []
    if len(jfile['actions']) > 0:
        
        for (prog, proginfo) in jfile['actions'].items():
            e.append([prog, proginfo['button'], proginfo['description'], proginfo['action']['type']])
        still_no_programs=False
    if request.method == 'GET':
        formate = []
        i=0
        while True:
            tempformation = []

            if len(e) <= i:
                break

            tempformation.append(e[i])
            i+=1 

            if len(e) <= i:
                formate.append(tempformation)
                break

            tempformation.append(e[i])
            formate.append(tempformation)
            i+=1
            continue
        return render_template('streamdeck_capp.html', programsqm=still_no_programs, e=formate, len=len)
    else:
        if request.form.get('app'):
            type = jfile['actions'][request.form['app']]['action']['type']
            action = jfile['actions'][request.form['app']]['action']['action']
            if type == 'app':
                threading.Thread(target=startApplication, args=(action,f'personnalisée "{request.form["sub"]}"', True)).start()
            elif type == 'cmd':
                threading.Thread(target=startApplication, args=(action,type)).start()
            elif type == 'website':
                link = action
                if not link.startswith('http'):
                    link = 'http://' + link
                if not '.' in list(link):
                    link += '.com'
                threading.Thread(target=startApplication, args=('start ' + link,"personnalisée (web)")).start()
            elif type == 'keyboard':
                keyboard.type(action)
                if 'run_enter' in jfile['actions'][request.form['app']]['action']:
                    if jfile['actions'][request.form['app']]['action']['run_enter']:
                        keyboard.press(Key.enter)
                        keyboard.release(Key.enter)
                threading.Thread(target=startApplication, args=("", "touches sur le clavier")).start()
            elif type == 'python':
                exec(action)
                threading.Thread(target=startApplication, args=("", "commande Python")).start()
            elif type == 'gamekey':
                keyboard.press(action)
                time.sleep(0.08)
                keyboard.release(action)
            formate = []
            i=0
            while True:
                tempformation = []

                if len(e) <= i:
                    break

                tempformation.append(e[i])
                i+=1 

                if len(e) <= i:
                    formate.append(tempformation)
                    break

                tempformation.append(e[i])
                formate.append(tempformation)
                i+=1
                continue
            return jsonify(authorized=True)
        return 'Unknown error'

@app.route('/opencustom', methods=['GET', 'POST'])
def opencustom():
    with open('pc_api/assets/customactions.json', 'r', encoding='utf-8') as f: jfile=json.load(f)
    still_no_programs=True
    e= []
    if len(jfile['actions']) > 0:
        
        for (prog, proginfo) in jfile['actions'].items():
            e.append([prog, proginfo['button'], proginfo['description'], proginfo['action']['type']])
        still_no_programs=False
    if request.method == 'GET':
        #JSON Pattern
        # {
        #   "programs": {
        #      "SOFTWARE_NAME":
        #          "executable": "PATH TO EXE",
        #          "icon": "ICON PATH, IF EXISTS",
        # }

        
        return render_template('customactions.html', programsqm=still_no_programs, e=e)
    else:
        if request.form.get('sub'):
            type = jfile['actions'][request.form['sub']]['action']['type']
            action = jfile['actions'][request.form['sub']]['action']['action']
            if type == 'app':
                threading.Thread(target=startApplication, args=(action,f'personnalisée "{request.form["sub"]}"', True)).start()
            elif type == 'cmd':
                threading.Thread(target=startApplication, args=(action,type)).start()
            elif type == 'website':
                link = action
                if not link.startswith('http'):
                    link = 'http://' + link
                if not '.' in list(link):
                    link += '.com'
                threading.Thread(target=startApplication, args=('start ' + link,"personnalisée (web)")).start()
            elif type == 'keyboard':
                keyboard.type(action)
                if 'run_enter' in jfile['actions'][request.form['sub']]['action']:
                    if jfile['actions'][request.form['sub']]['action']['run_enter']:
                        keyboard.press(Key.enter)
                        keyboard.release(Key.enter)
                threading.Thread(target=startApplication, args=("", "touches sur le clavier")).start()
            elif type == 'python':
                exec(action)
                threading.Thread(target=startApplication, args=("", "commande Python")).start()
            elif type == 'gamekey':
                keyboard.press(action)
                time.sleep(0.08)
                keyboard.release(action)

            return render_template('customactions.html', programsqm=still_no_programs, e=e, showran=True)
        return 'Unknown error'

@app.route('/screenshots', methods=['GET', 'POST'])
def screenshots():
    denied = False
    if 'screenshots' not in request.cookies:
        denied = True
    authr = []
    with open('authorized_screenshots.donotedit', 'r') as f:
        for line in f: authr.append(line.replace('\n', ''))
    newauthr = []
    for el in authr: 
        if len(el) > 6: newauthr.append(el)
    del authr 
    if not denied:
        if request.cookies['screenshots'] in newauthr:
            denied = False
    pid = None
    if 'pid' in request.args:
        pid = request.args['pid']
    if request.method == 'GET':
        return render_template('screenshot.html', authorized=(not denied), screenshot_available=(True if pid else False), screenshot_code=pid)
    elif request.method == 'POST': 
        if askAuthorization("Autoriser le navigateur à prendre des captures d'écran du PC\n\nATTENTION: LA SESSION DE CAPTURES N'EXPIRE PAS, LE NAVIGATEUR POURRA EN GÉNÉRER A TOUT MOMENT SI LE SERVICE DE PCOVERPHONE EST ACTIF."):
            auth = generate_session_id()
            with open('authorized_screenshots.donotedit', 'a') as f: f.write(auth + '\n')
            rep = make_response(jsonify(authorized=True, authorization='None'))
            rep.set_cookie('screenshots', auth)
            return rep
        return jsonify(authorized=False, authorization='None')

@app.route('/screenshots/take')
def take_screenshot():
    denied = False
    if 'screenshots' not in request.cookies:
        denied = True
    authr = []
    with open('authorized_screenshots.donotedit', 'r') as f:
        for line in f: authr.append(line.replace('\n', ''))
    newauthr = []
    for el in authr: 
        if len(el) > 6: newauthr.append(el)
    del authr 

    if denied: return jsonify(authorized=False)

    if request.cookies['screenshots'] in newauthr:
        denied = False

    if denied: return jsonify(authorized=False)
    try:
        screenshot = pyautogui.screenshot()
        ide = generate_session_id()
        screenshot.save("static/screenshots/" + ide + '.png')
        del screenshot
    except OSError:
        return jsonify(unexpected_error=True, uac=True)
    except:
        return jsonify(unexpected_error=True, uac=False)

    return jsonify(authorized=True, pid=ide)


    
@app.route('/login', methods=['GET', 'POST'])
def hey():
    global sessions
    if 'id' in session:
        return redirect('/')
    if request.method == 'GET':
        if 'logged_out' not in request.args:
            return render_template('login.html', invalid=False, machineip=machineIP, debug=debug, debugpassword=logins['DEBUG'])
        else:
            return render_template('login.html', invalid=False, machineip=machineIP, loggedout=True, debug=debug, debugpassword=logins['DEBUG'])
    else:
        if request.form['uname'] in logins:
            if logins[request.form['uname']] == request.form['psw']:
                session['id'] = generate_session_id()
                sessions[session['id']] = {'time': currentTime()}
                return render_template('login.html', authentificated=True, machineip=machineIP, debug=debug, debugpassword=logins['DEBUG'])
        return render_template('login.html', invalid=True, debug=debug, machineip=machineIP, debugpassword=logins['DEBUG'])

if __name__ == '__main__':
    app.secret_key = 'YrXeAdZS8WJdzWjze52r2K2wH3RqWxgxMQCcEtFCeeGrMQADxsEpMgwk9cmGzt5W9hYDmg7b7qsKQRdcUucxAyummESxWyjGFUbR2TTXTVjzq8C9srgSNA4K5x7DV3ac'
    #sett = input('Voulez-vous ouvrir le panel automatiquement après le lancement ? (O/n)    ')
    # if sett.lower() == 'n':
    #     sett = False
    # sett = True
    app.run(host='192.168.1.17', port=80, debug=debug, threaded=True)
    # except:
    #     print('Le port 80 est déjà utilisé. Trouvez un moyen de le libérer.')
