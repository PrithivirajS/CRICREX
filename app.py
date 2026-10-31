import os, sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.environ.get('CRICREX_DB', os.path.join(BASE_DIR, 'cricrex.db'))
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-before-deployment')

SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'captain', location TEXT DEFAULT '', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS teams (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, location TEXT NOT NULL, captain_id INTEGER NOT NULL, logo_url TEXT DEFAULT '', created_at TEXT NOT NULL, FOREIGN KEY(captain_id) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS team_players (id INTEGER PRIMARY KEY AUTOINCREMENT, team_id INTEGER NOT NULL, name TEXT NOT NULL, player_role TEXT DEFAULT 'Player', FOREIGN KEY(team_id) REFERENCES teams(id));
CREATE TABLE IF NOT EXISTS grounds (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER NOT NULL, name TEXT NOT NULL, location TEXT NOT NULL, hourly_rate REAL NOT NULL, facilities TEXT DEFAULT '', image_url TEXT DEFAULT '', created_at TEXT NOT NULL, FOREIGN KEY(owner_id) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY AUTOINCREMENT, creator_id INTEGER NOT NULL, team_id INTEGER NOT NULL, opponent_team_id INTEGER, ground_id INTEGER, title TEXT NOT NULL, match_date TEXT NOT NULL, match_format TEXT NOT NULL, fee_per_team REAL NOT NULL DEFAULT 0, location TEXT NOT NULL, need_opponent INTEGER NOT NULL DEFAULT 1, need_umpire INTEGER NOT NULL DEFAULT 1, need_scorer INTEGER NOT NULL DEFAULT 1, status TEXT NOT NULL DEFAULT 'Open', notes TEXT DEFAULT '', created_at TEXT NOT NULL, FOREIGN KEY(creator_id) REFERENCES users(id), FOREIGN KEY(team_id) REFERENCES teams(id));
CREATE TABLE IF NOT EXISTS service_profiles (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, service_type TEXT NOT NULL, location TEXT NOT NULL, experience TEXT DEFAULT '', rate REAL NOT NULL DEFAULT 0, availability TEXT DEFAULT 'Available', FOREIGN KEY(user_id) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER NOT NULL, provider_id INTEGER NOT NULL, service_type TEXT NOT NULL, amount REAL NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'Pending', payment_status TEXT NOT NULL DEFAULT 'Unpaid', created_at TEXT NOT NULL, FOREIGN KEY(match_id) REFERENCES matches(id), FOREIGN KEY(provider_id) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS opponent_requests (id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER NOT NULL, team_id INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'Pending', created_at TEXT NOT NULL, FOREIGN KEY(match_id) REFERENCES matches(id), FOREIGN KEY(team_id) REFERENCES teams(id));
'''

def db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    conn = g.pop('db', None)
    if conn is not None: conn.close()

@app.before_request
def initialize():
    conn = db(); conn.executescript(SCHEMA); conn.commit()
    # Seed a small discovery catalogue on first run.
    if conn.execute('SELECT COUNT(*) FROM grounds').fetchone()[0] == 0:
        now = datetime.now().isoformat(timespec='minutes')
        demo_hash = generate_password_hash('Demo@123')
        conn.execute("INSERT OR IGNORE INTO users(name,email,password_hash,role,location,created_at) VALUES(?,?,?,?,?,?)", ('CRICREX Ground Demo','grounds@cricrex.demo',demo_hash,'ground_owner','Bengaluru',now))
        owner = conn.execute("SELECT id FROM users WHERE email='grounds@cricrex.demo'").fetchone()['id']
        conn.executemany('INSERT INTO grounds(owner_id,name,location,hourly_rate,facilities,image_url,created_at) VALUES(?,?,?,?,?,?,?)', [
            (owner,'Green Valley Cricket Ground','Sarjapur, Bengaluru',1500,'Turf • Parking • Washrooms','',now),
            (owner,'PlayArena Cricket Ground','Kasavanahalli, Bengaluru',2000,'Turf • Floodlights • Changing room','',now),
            (owner,'Victory Sports Ground','Whitefield, Bengaluru',1200,'Practice nets • Parking','',now)])
        conn.commit()

def current_user():
    if 'user_id' not in session: return None
    return db().execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash('Please sign in to continue.', 'info'); return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_user(): return {'current_user': current_user()}

@app.route('/')
def index():
    conn=db()
    grounds=conn.execute('SELECT * FROM grounds ORDER BY id DESC LIMIT 6').fetchall()
    matches=conn.execute("SELECT m.*, t.name AS team_name FROM matches m JOIN teams t ON t.id=m.team_id WHERE m.status IN ('Open','Opponent Requested') ORDER BY m.match_date LIMIT 6").fetchall()
    return render_template('index.html', grounds=grounds, matches=matches)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); password=request.form.get('password',''); role=request.form.get('role','captain'); location=request.form.get('location','').strip()
        if not name or not email or len(password)<8:
            flash('Enter your name and email, and use a password with at least 8 characters.', 'error'); return render_template('register.html')
        if role not in ('captain','ground_owner','umpire','scorer'): role='captain'
        try:
            cur=db().execute('INSERT INTO users(name,email,password_hash,role,location,created_at) VALUES(?,?,?,?,?,?)',(name,email,generate_password_hash(password),role,location,datetime.now().isoformat(timespec='minutes'))); db().commit()
            session['user_id']=cur.lastrowid
            if role in ('umpire','scorer'):
                db().execute('INSERT INTO service_profiles(user_id,service_type,location,experience,rate) VALUES(?,?,?,?,?)',(cur.lastrowid,role,location,'New profile',0)); db().commit()
            flash('Welcome to CRICREX. Your account is ready.','success'); return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            flash('That email is already registered. Please sign in.','error')
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        user=db().execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
        if user and check_password_hash(user['password_hash'],password):
            session.clear(); session['user_id']=user['id']; return redirect(url_for('dashboard'))
        flash('Email or password was not recognised.','error')
    return render_template('login.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    u=current_user(); conn=db()
    teams=conn.execute('SELECT * FROM teams WHERE captain_id=? ORDER BY id DESC',(u['id'],)).fetchall()
    matches=conn.execute('SELECT m.*,t.name team_name,g.name ground_name FROM matches m JOIN teams t ON t.id=m.team_id LEFT JOIN grounds g ON g.id=m.ground_id WHERE m.creator_id=? OR m.opponent_team_id IN (SELECT id FROM teams WHERE captain_id=?) ORDER BY m.match_date DESC LIMIT 8',(u['id'],u['id'])).fetchall()
    grounds=conn.execute('SELECT * FROM grounds WHERE owner_id=?',(u['id'],)).fetchall() if u['role']=='ground_owner' else []
    profiles=conn.execute('SELECT * FROM service_profiles WHERE user_id=?',(u['id'],)).fetchall()
    requests=conn.execute('SELECT r.*,m.title,t.name team_name FROM opponent_requests r JOIN matches m ON m.id=r.match_id JOIN teams t ON t.id=r.team_id JOIN teams own ON own.id=m.team_id WHERE own.captain_id=? ORDER BY r.id DESC',(u['id'],)).fetchall()
    bookings=conn.execute('SELECT b.*,m.title,m.match_date FROM bookings b JOIN matches m ON m.id=b.match_id WHERE b.provider_id=? ORDER BY b.id DESC',(u['id'],)).fetchall()
    counts={'teams':len(teams),'matches':len(matches),'grounds':len(grounds),'requests':len(requests),'bookings':len(bookings)}
    return render_template('dashboard.html', user=u, teams=teams, matches=matches, grounds=grounds, profiles=profiles, requests=requests, bookings=bookings, counts=counts)

@app.route('/teams', methods=['GET','POST'])
@login_required
def teams():
    if request.method=='POST':
        name=request.form.get('name','').strip(); location=request.form.get('location','').strip(); players=[p.strip() for p in request.form.get('players','').split(',') if p.strip()]
        if name and location:
            cur=db().execute('INSERT INTO teams(name,location,captain_id,logo_url,created_at) VALUES(?,?,?,?,?)',(name,location,current_user()['id'],request.form.get('logo_url','').strip(),datetime.now().isoformat(timespec='minutes')))
            for p in players: db().execute('INSERT INTO team_players(team_id,name) VALUES(?,?)',(cur.lastrowid,p))
            db().commit(); flash('Team created successfully.','success'); return redirect(url_for('teams'))
        flash('Team name and location are required.','error')
    items=db().execute('SELECT t.*,u.name captain,(SELECT COUNT(*) FROM team_players p WHERE p.team_id=t.id) player_count FROM teams t JOIN users u ON u.id=t.captain_id ORDER BY t.id DESC').fetchall()
    return render_template('teams.html', teams=items)

@app.route('/grounds', methods=['GET','POST'])
def grounds():
    if request.method=='POST':
        u=current_user()
        if not u: return redirect(url_for('login'))
        if u['role']!='ground_owner': flash('Please sign in with a ground owner account to list a ground.','error'); return redirect(url_for('grounds'))
        name=request.form.get('name','').strip(); location=request.form.get('location','').strip(); rate=request.form.get('hourly_rate','0')
        try: rate=float(rate)
        except ValueError: rate=0
        if name and location and rate>0:
            db().execute('INSERT INTO grounds(owner_id,name,location,hourly_rate,facilities,image_url,created_at) VALUES(?,?,?,?,?,?,?)',(u['id'],name,location,rate,request.form.get('facilities','').strip(),request.form.get('image_url','').strip(),datetime.now().isoformat(timespec='minutes'))); db().commit(); flash('Ground listed.','success'); return redirect(url_for('grounds'))
        flash('Provide a ground name, location and valid hourly rate.','error')
    q=request.args.get('q','').strip(); conn=db()
    if q: items=conn.execute('SELECT g.*,u.name owner_name FROM grounds g JOIN users u ON u.id=g.owner_id WHERE g.location LIKE ? OR g.name LIKE ? ORDER BY g.id DESC',('%'+q+'%','%'+q+'%')).fetchall()
    else: items=conn.execute('SELECT g.*,u.name owner_name FROM grounds g JOIN users u ON u.id=g.owner_id ORDER BY g.id DESC').fetchall()
    return render_template('grounds.html', grounds=items, q=q)

@app.route('/matches', methods=['GET','POST'])
@login_required
def matches():
    conn=db(); u=current_user()
    if request.method=='POST':
        team_id=request.form.get('team_id'); title=request.form.get('title','').strip(); match_date=request.form.get('match_date',''); fmt=request.form.get('match_format','T20'); loc=request.form.get('location','').strip()
        try: fee=float(request.form.get('fee_per_team','0'))
        except ValueError: fee=0
        if not team_id or not title or not match_date or not loc:
            flash('Team, match title, date/time and location are required.','error')
        elif not conn.execute('SELECT id FROM teams WHERE id=? AND captain_id=?',(team_id,u['id'])).fetchone():
            flash('Select a team you manage.','error')
        else:
            need_opp=1 if request.form.get('need_opponent') else 0; ground_id=request.form.get('ground_id') or None
            status='Open' if need_opp else 'Scheduled'
            cur=conn.execute('INSERT INTO matches(creator_id,team_id,ground_id,title,match_date,match_format,fee_per_team,location,need_opponent,need_umpire,need_scorer,status,notes,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(u['id'],team_id,ground_id,title,match_date,fmt,fee,loc,need_opp,1 if request.form.get('need_umpire') else 0,1 if request.form.get('need_scorer') else 0,status,request.form.get('notes','').strip(),datetime.now().isoformat(timespec='minutes')))
            conn.commit(); flash('Match created. Continue coordinating services from the match listing.','success'); return redirect(url_for('matches'))
    items=conn.execute('SELECT m.*,t.name team_name,g.name ground_name FROM matches m JOIN teams t ON t.id=m.team_id LEFT JOIN grounds g ON g.id=m.ground_id ORDER BY m.match_date').fetchall()
    myteams=conn.execute('SELECT * FROM teams WHERE captain_id=?',(u['id'],)).fetchall(); groundlist=conn.execute('SELECT * FROM grounds ORDER BY name').fetchall()
    return render_template('matches.html', matches=items, teams=myteams, grounds=groundlist)

@app.route('/matches/<int:match_id>/request-opponent', methods=['POST'])
@login_required
def request_opponent(match_id):
    team_id=request.form.get('team_id'); u=current_user(); conn=db()
    team=conn.execute('SELECT * FROM teams WHERE id=? AND captain_id=?',(team_id,u['id'])).fetchone()
    match=conn.execute("SELECT * FROM matches WHERE id=? AND status='Open' AND creator_id<>?",(match_id,u['id'])).fetchone()
    if not team or not match: flash('Choose one of your teams and an open match created by another captain.','error')
    else:
        try: conn.execute('INSERT INTO opponent_requests(match_id,team_id,created_at) VALUES(?,?,?)',(match_id,team_id,datetime.now().isoformat(timespec='minutes'))); conn.commit(); flash('Opponent request sent to the match creator.','success')
        except sqlite3.IntegrityError: flash('Unable to send request.','error')
    return redirect(url_for('matches'))

@app.route('/opponent-requests/<int:req_id>/<action>', methods=['POST'])
@login_required
def handle_opponent(req_id,action):
    if action not in ('accept','reject'): return redirect(url_for('dashboard'))
    conn=db(); req=conn.execute('SELECT r.*,m.creator_id,m.id mid FROM opponent_requests r JOIN matches m ON m.id=r.match_id WHERE r.id=?',(req_id,)).fetchone()
    if not req or req['creator_id']!=current_user()['id']: flash('You cannot manage this request.','error')
    else:
        status='Accepted' if action=='accept' else 'Rejected'
        conn.execute('UPDATE opponent_requests SET status=? WHERE id=?',(status,req_id))
        if action=='accept': conn.execute("UPDATE matches SET opponent_team_id=(SELECT team_id FROM opponent_requests WHERE id=?),status='Opponent Confirmed' WHERE id=?",(req_id,req['mid']))
        conn.commit(); flash('Opponent request '+status.lower()+'.','success')
    return redirect(url_for('dashboard'))

@app.route('/officials', methods=['GET','POST'])
def officials():
    conn=db(); u=current_user()
    if request.method=='POST':
        if not u: return redirect(url_for('login'))
        typ=request.form.get('service_type'); location=request.form.get('location','').strip(); experience=request.form.get('experience','').strip()
        try: rate=float(request.form.get('rate','0'))
        except ValueError: rate=0
        if typ not in ('umpire','scorer') or u['role']!=typ:
            flash('Sign in with the matching umpire or scorer role to manage your profile.','error')
        else:
            existing=conn.execute('SELECT id FROM service_profiles WHERE user_id=? AND service_type=?',(u['id'],typ)).fetchone()
            if existing: conn.execute('UPDATE service_profiles SET location=?,experience=?,rate=?,availability=? WHERE id=?',(location,experience,rate,request.form.get('availability','Available'),existing['id']))
            else: conn.execute('INSERT INTO service_profiles(user_id,service_type,location,experience,rate,availability) VALUES(?,?,?,?,?,?)',(u['id'],typ,location,experience,rate,request.form.get('availability','Available')))
            conn.commit(); flash('Official profile saved.','success'); return redirect(url_for('officials'))
    typ=request.args.get('type','umpire')
    if typ not in ('umpire','scorer'): typ='umpire'
    q=request.args.get('q','').strip()
    items=conn.execute('SELECT p.*,u.name,u.email FROM service_profiles p JOIN users u ON u.id=p.user_id WHERE p.service_type=? AND p.availability=? AND (p.location LIKE ? OR u.name LIKE ?) ORDER BY p.rate',(typ,'Available','%'+q+'%','%'+q+'%')).fetchall()
    current_user_matches=conn.execute('SELECT id,title,match_date FROM matches WHERE creator_id=? ORDER BY match_date',(u['id'],)).fetchall() if u and u['role']=='captain' else []
    return render_template('officials.html', profiles=items, typ=typ, q=q, current_user_matches=current_user_matches)

@app.route('/book-official/<int:profile_id>', methods=['POST'])
@login_required
def book_official(profile_id):
    conn=db(); profile=conn.execute('SELECT * FROM service_profiles WHERE id=?',(profile_id,)).fetchone(); match_id=request.form.get('match_id')
    match=conn.execute('SELECT * FROM matches WHERE id=? AND creator_id=?',(match_id,current_user()['id'])).fetchone()
    if not profile or not match: flash('Choose one of your matches and a valid official.','error')
    else:
        conn.execute('INSERT INTO bookings(match_id,provider_id,service_type,amount,created_at) VALUES(?,?,?,?,?)',(match_id,profile['user_id'],profile['service_type'],profile['rate'],datetime.now().isoformat(timespec='minutes'))); conn.commit(); flash('Booking request sent to the official.','success')
    return redirect(url_for('officials',type=profile['service_type'] if profile else 'umpire'))

@app.route('/bookings/<int:booking_id>/<action>', methods=['POST'])
@login_required
def update_booking(booking_id,action):
    if action not in ('accept','reject','paid'): return redirect(url_for('dashboard'))
    conn=db(); b=conn.execute('SELECT * FROM bookings WHERE id=?',(booking_id,)).fetchone()
    if not b or b['provider_id']!=current_user()['id']: flash('You cannot update this booking.','error')
    else:
        if action=='paid': conn.execute("UPDATE bookings SET payment_status='Recorded' WHERE id=?",(booking_id,))
        else: conn.execute('UPDATE bookings SET status=? WHERE id=?',('Confirmed' if action=='accept' else 'Rejected',booking_id))
        conn.commit(); flash('Booking updated.','success')
    return redirect(url_for('dashboard'))

@app.route('/health')
def health(): return {'status':'ok','app':'CRICREX MVP'}

if __name__=='__main__': app.run(host='127.0.0.1',port=int(os.environ.get('PORT','5000')),debug=True)
