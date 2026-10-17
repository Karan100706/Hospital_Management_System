import sqlite3
from datetime import date, datetime
from pathlib import Path
import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
DB = APP_DIR / 'hms.db'

st.set_page_config(page_title='HMS | Hospital Management System', page_icon='🏥', layout='wide', initial_sidebar_state='expanded')

# ----------------------------- Database -----------------------------

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db(); cur = con.cursor()
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT);
    CREATE TABLE IF NOT EXISTS patients(id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT UNIQUE, name TEXT, age INTEGER, gender TEXT, contact TEXT, blood_group TEXT, disease TEXT, address TEXT, history TEXT, doctor TEXT, created_at TEXT);
    CREATE TABLE IF NOT EXISTS doctors(id INTEGER PRIMARY KEY AUTOINCREMENT, doctor_id TEXT UNIQUE, name TEXT, department TEXT, contact TEXT, experience INTEGER, availability TEXT, fee REAL);
    CREATE TABLE IF NOT EXISTS appointments(id INTEGER PRIMARY KEY AUTOINCREMENT, appointment_id TEXT UNIQUE, patient TEXT, doctor TEXT, appt_date TEXT, appt_time TEXT, status TEXT, reason TEXT);
    CREATE TABLE IF NOT EXISTS prescriptions(id INTEGER PRIMARY KEY AUTOINCREMENT, rx_id TEXT UNIQUE, patient TEXT, doctor TEXT, rx_date TEXT, diagnosis TEXT, medicines TEXT, instructions TEXT);
    CREATE TABLE IF NOT EXISTS bills(id INTEGER PRIMARY KEY AUTOINCREMENT, bill_id TEXT UNIQUE, patient TEXT, consultation REAL, medicine REAL, lab REAL, room REAL, total REAL, status TEXT, bill_date TEXT);
    CREATE TABLE IF NOT EXISTS beds(id INTEGER PRIMARY KEY AUTOINCREMENT, bed_id TEXT UNIQUE, room TEXT, bed_type TEXT, status TEXT, patient TEXT);
    CREATE TABLE IF NOT EXISTS admissions(id INTEGER PRIMARY KEY AUTOINCREMENT, admission_id TEXT UNIQUE, patient TEXT, room TEXT, bed TEXT, admission_date TEXT, discharge_date TEXT, status TEXT);
    CREATE TABLE IF NOT EXISTS labs(id INTEGER PRIMARY KEY AUTOINCREMENT, test_id TEXT UNIQUE, patient TEXT, test_name TEXT, result TEXT, amount REAL, test_date TEXT, status TEXT);
    CREATE TABLE IF NOT EXISTS activity(id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, created_at TEXT);
    ''')
    if cur.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
        cur.execute('INSERT INTO users(username,password,role) VALUES(?,?,?)', ('admin','admin123','Administrator'))
    if cur.execute('SELECT COUNT(*) FROM patients').fetchone()[0] == 0:
        cur.executemany('INSERT INTO patients(patient_id,name,age,gender,contact,blood_group,disease,address,history,doctor,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)', [
            ('P001','Rahul Sharma',32,'Male','9876543210','B+','Fever','Ahmedabad','No major history','Dr. Neha Mehta',str(date.today())),
            ('P002','Priya Patel',27,'Female','9876501234','O+','Migraine','Ahmedabad','Occasional migraine','Dr. Amit Shah',str(date.today()))])
    if cur.execute('SELECT COUNT(*) FROM doctors').fetchone()[0] == 0:
        cur.executemany('INSERT INTO doctors(doctor_id,name,department,contact,experience,availability,fee) VALUES(?,?,?,?,?,?,?)', [
            ('D001','Dr. Amit Shah','Cardiology','9876111111',12,'Mon-Fri, 10 AM-2 PM',800),
            ('D002','Dr. Neha Mehta','General Medicine','9876222222',8,'Mon-Sat, 9 AM-1 PM',500)])
    if cur.execute('SELECT COUNT(*) FROM appointments').fetchone()[0] == 0:
        cur.execute('INSERT INTO appointments(appointment_id,patient,doctor,appt_date,appt_time,status,reason) VALUES(?,?,?,?,?,?,?)', ('A001','Rahul Sharma','Dr. Neha Mehta',str(date.today()),'10:00 AM','Confirmed','Fever'))
    if cur.execute('SELECT COUNT(*) FROM bills').fetchone()[0] == 0:
        cur.execute('INSERT INTO bills(bill_id,patient,consultation,medicine,lab,room,total,status,bill_date) VALUES(?,?,?,?,?,?,?,?,?)', ('B001','Rahul Sharma',500,700,300,0,1500,'Paid',str(date.today())))
    if cur.execute('SELECT COUNT(*) FROM prescriptions').fetchone()[0] == 0:
        cur.execute('INSERT INTO prescriptions(rx_id,patient,doctor,rx_date,diagnosis,medicines,instructions) VALUES(?,?,?,?,?,?,?)', ('RX001','Rahul Sharma','Dr. Neha Mehta',str(date.today()),'Fever','Paracetamol 500mg - 1 tablet twice daily','Take after meals and rest.'))
    if cur.execute('SELECT COUNT(*) FROM beds').fetchone()[0] == 0:
        cur.executemany('INSERT INTO beds(bed_id,room,bed_type,status,patient) VALUES(?,?,?,?,?)', [
            ('B101','101','General','Available',''),('B102','101','General','Occupied','Rahul Sharma'),('B201','201','Private','Available',''),('B202','202','ICU','Available',''),('B301','301','Semi-Private','Available','')])
    if cur.execute('SELECT COUNT(*) FROM admissions').fetchone()[0] == 0:
        cur.execute('INSERT INTO admissions(admission_id,patient,room,bed,admission_date,discharge_date,status) VALUES(?,?,?,?,?,?,?)', ('ADM001','Rahul Sharma','101','B102',str(date.today()),'','Admitted'))
    if cur.execute('SELECT COUNT(*) FROM labs').fetchone()[0] == 0:
        cur.execute('INSERT INTO labs(test_id,patient,test_name,result,amount,test_date,status) VALUES(?,?,?,?,?,?,?)', ('LAB001','Rahul Sharma','CBC','Normal',300,str(date.today()),'Completed'))
    con.commit(); con.close()

init_db()

# ----------------------------- Helpers -----------------------------

def q(sql, params=()):
    con=db(); rows=con.execute(sql,params).fetchall(); con.close(); return [dict(r) for r in rows]

def one(sql, params=()):
    rows=q(sql,params); return rows[0] if rows else None

def run(sql, params=()):
    con=db(); cur=con.execute(sql,params); con.commit(); last=cur.lastrowid; con.close(); return last

def df(sql, params=()):
    return pd.DataFrame(q(sql,params))

def log(msg): run('INSERT INTO activity(message,created_at) VALUES(?,?)',(msg,datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

def money(x): return f'₹{float(x or 0):,.0f}'

def next_id(prefix, table, column):
    rows=q(f'SELECT {column} AS v FROM {table}')
    nums=[]
    for r in rows:
        s=str(r['v'])
        if s.startswith(prefix):
            try: nums.append(int(s[len(prefix):]))
            except ValueError: pass
    return f'{prefix}{max(nums,default=0)+1:03d}'

def safe_pdf(title, lines):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        import io
        buf=io.BytesIO(); c=canvas.Canvas(buf,pagesize=A4); w,h=A4; y=h-55
        c.setFont('Helvetica-Bold',18); c.drawString(45,y,title); y-=30
        c.setFont('Helvetica',10)
        for line in lines:
            if y < 45: c.showPage(); y=h-45; c.setFont('Helvetica',10)
            for chunk in str(line).split('\n'):
                c.drawString(45,y,chunk[:115]); y-=16
        c.save(); return buf.getvalue()
    except Exception:
        return None

# ----------------------------- Login -----------------------------
if 'logged_in' not in st.session_state: st.session_state.logged_in=False
if not st.session_state.logged_in:
    st.markdown('<div style="text-align:center;padding-top:7vh">🏥</div>', unsafe_allow_html=True)
    st.title('Hospital Management System')
    st.caption('Secure academic demo • Streamlit + Python + SQLite')
    with st.form('login'):
        u=st.text_input('Username', 'admin'); p=st.text_input('Password', type='password'); submit=st.form_submit_button('🔐 Login', use_container_width=True)
        if submit:
            user=one('SELECT * FROM users WHERE username=? AND password=?',(u,p))
            if user:
                st.session_state.logged_in=True; st.session_state.user=user; st.rerun()
            else: st.error('Invalid username or password.')
    st.info('Demo login: **admin** / **admin123**')
    st.stop()

# ----------------------------- Sidebar -----------------------------
st.sidebar.title('🏥 HMS')
st.sidebar.caption('Hospital Management System')
st.sidebar.success(f"Logged in: {st.session_state.user['username']} • {st.session_state.user['role']}")
pages=['Dashboard','Patients','Doctors','Appointments','Prescriptions','Billing','Beds & Rooms','Admissions','Laboratory','Reports & Analytics','Activity Log']
page=st.sidebar.radio('Navigation',pages)
st.sidebar.divider()
if st.sidebar.button('🔄 Refresh Data',use_container_width=True): st.rerun()
if st.sidebar.button('🚪 Logout',use_container_width=True): st.session_state.logged_in=False; st.rerun()
st.sidebar.info('Academic Project\nStreamlit + Python + SQLite')
st.sidebar.caption('HMS Demo Version 3.0')

# ----------------------------- Dashboard -----------------------------
if page=='Dashboard':
    st.title('🏥 Hospital Management System'); st.subheader('Management Dashboard')
    patients=df('SELECT * FROM patients'); doctors=df('SELECT * FROM doctors'); ap=df('SELECT * FROM appointments'); bills=df('SELECT * FROM bills'); beds=df('SELECT * FROM beds'); adm=df('SELECT * FROM admissions'); labs=df('SELECT * FROM labs')
    today=str(date.today()); today_ap=len(ap[ap.appt_date==today]) if not ap.empty else 0
    paid=bills.loc[bills.status=='Paid','total'].sum() if not bills.empty else 0; pending=bills.loc[bills.status=='Pending','total'].sum() if not bills.empty else 0
    metrics=[('👥 Total Patients',len(patients)),('🧑‍⚕️ Doctors',len(doctors)),("📅 Today's Appointments",today_ap),('💰 Collected Revenue',money(paid)),('🧾 Outstanding',money(pending)),('🛏️ Available Beds',len(beds[beds.status=='Available'])),('🏨 Active Admissions',len(adm[adm.status=='Admitted'])),('🧪 Lab Tests',len(labs))]
    for row in [metrics[:4],metrics[4:]]:
        cols=st.columns(4)
        for c,(label,val) in zip(cols,row): c.metric(label,val)
    st.divider(); l,r=st.columns(2)
    with l:
        st.subheader('📊 Appointment Status')
        if not ap.empty: st.bar_chart(ap.status.value_counts())
    with r:
        st.subheader('💳 Billing Overview')
        st.bar_chart(pd.DataFrame({'Amount':[bills.total.sum() if not bills.empty else 0,paid,pending]},index=['Total','Paid','Pending']))
    l,r=st.columns(2)
    with l: st.subheader('👥 Recent Patients'); st.dataframe(patients[['patient_id','name','age','gender','disease','doctor']].tail(5),use_container_width=True,hide_index=True)
    with r: st.subheader('📅 Recent Appointments'); st.dataframe(ap[['appointment_id','patient','doctor','appt_date','status']].tail(5),use_container_width=True,hide_index=True)

# ----------------------------- Patients -----------------------------
elif page=='Patients':
    st.title('👥 Patient Management')
    with st.expander('➕ Add New Patient',expanded=False):
        doctors=q('SELECT name FROM doctors')
        with st.form('patient_add'):
            c1,c2,c3=st.columns(3); pid=c1.text_input('Patient ID',next_id('P','patients','patient_id')); name=c2.text_input('Full Name'); age=c3.number_input('Age',0,120,25); gender=c1.selectbox('Gender',['Male','Female','Other']); contact=c2.text_input('Contact'); blood=c3.selectbox('Blood Group',['A+','A-','B+','B-','AB+','AB-','O+','O-']); disease=c1.text_input('Disease / Diagnosis'); address=c2.text_input('Address'); doctor=c3.selectbox('Assigned Doctor',['Not Assigned']+[d['name'] for d in doctors]); history=st.text_area('Medical History',height=80)
            if st.form_submit_button('Save Patient',use_container_width=True):
                try:
                    run('INSERT INTO patients(patient_id,name,age,gender,contact,blood_group,disease,address,history,doctor,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(pid,name,age,gender,contact,blood,disease,address,history,doctor,str(date.today()))); log(f'Patient {name} added.'); st.success('Patient added successfully.'); st.rerun()
                except sqlite3.IntegrityError: st.error('Patient ID already exists.')
    patients=df('SELECT * FROM patients ORDER BY id DESC'); search=st.text_input('🔎 Search patients by name, ID, disease or contact')
    if search: patients=patients[patients.astype(str).apply(lambda x:x.str.contains(search,case=False,na=False)).any(axis=1)]
    st.dataframe(patients[['patient_id','name','age','gender','contact','blood_group','disease','doctor','address']],use_container_width=True,hide_index=True)
    st.divider(); st.subheader('🛠️ Patient Record Actions')
    allp=q('SELECT patient_id,name FROM patients');
    if allp:
        selected=st.selectbox('Select Patient',[x['patient_id']+' — '+x['name'] for x in allp]); pid=selected.split(' — ')[0]; p=one('SELECT * FROM patients WHERE patient_id=?',(pid,))
        c1,c2,c3,c4=st.columns(4); c1.metric('Patient ID',p['patient_id']); c2.metric('Age',p['age']); c3.metric('Blood Group',p['blood_group']); c4.metric('Doctor',p['doctor'])
        st.write(f"**Diagnosis:** {p['disease']}  |  **Contact:** {p['contact']}  |  **Address:** {p['address']}")
        st.write(f"**Medical History:** {p['history']}")
        if st.button('🗑️ Delete Patient',type='secondary'):
            run('DELETE FROM patients WHERE patient_id=?',(pid,)); log(f'Patient {p["name"]} deleted.'); st.success('Patient deleted.'); st.rerun()
        hist=df('SELECT appointment_id,doctor,appt_date,appt_time,status,reason FROM appointments WHERE patient=? ORDER BY id DESC',(p['name'],)); st.write('### Appointment History'); st.dataframe(hist,use_container_width=True,hide_index=True)

# ----------------------------- Doctors -----------------------------
elif page=='Doctors':
    st.title('🧑‍⚕️ Doctor Management')
    departments=['General Medicine','Cardiology','Neurology','Orthopedics','Pediatrics','Dermatology','ENT','Gynecology','Emergency','Radiology']
    with st.expander('➕ Add New Doctor'):
        with st.form('doctor_add'):
            c1,c2,c3=st.columns(3); did=c1.text_input('Doctor ID',next_id('D','doctors','doctor_id')); name=c2.text_input('Doctor Name'); dept=c3.selectbox('Department',departments); contact=c1.text_input('Contact'); exp=c2.number_input('Experience (years)',0,60,5); avail=c3.text_input('Availability','Mon-Fri, 10 AM-2 PM'); fee=c1.number_input('Consultation Fee (₹)',0.0,100000.0,500.0,step=100.0)
            if st.form_submit_button('Save Doctor',use_container_width=True):
                try: run('INSERT INTO doctors(doctor_id,name,department,contact,experience,availability,fee) VALUES(?,?,?,?,?,?,?)',(did,name,dept,contact,exp,avail,fee)); log(f'Doctor {name} added.'); st.success('Doctor added.'); st.rerun()
                except sqlite3.IntegrityError: st.error('Doctor ID already exists.')
    doctors=df('SELECT * FROM doctors ORDER BY id DESC'); st.dataframe(doctors,use_container_width=True,hide_index=True)
    st.subheader('📌 Doctor Workload'); ap=df('SELECT doctor FROM appointments');
    if not ap.empty: st.bar_chart(ap.doctor.value_counts())

# ----------------------------- Appointments -----------------------------
elif page=='Appointments':
    st.title('📅 Appointment Management')
    patients=q('SELECT name FROM patients'); doctors=q('SELECT name FROM doctors')
    with st.expander('➕ Book Appointment'):
        with st.form('appt_add'):
            c1,c2,c3=st.columns(3); aid=c1.text_input('Appointment ID',next_id('A','appointments','appointment_id')); patient=c2.selectbox('Patient',[x['name'] for x in patients]); doctor=c3.selectbox('Doctor',[x['name'] for x in doctors]); apdate=c1.date_input('Date',date.today()); aptime=c2.text_input('Time','10:00 AM'); status=c3.selectbox('Status',['Pending','Confirmed','Completed','Cancelled']); reason=st.text_input('Reason / Symptoms')
            if st.form_submit_button('Book Appointment',use_container_width=True):
                try: run('INSERT INTO appointments(appointment_id,patient,doctor,appt_date,appt_time,status,reason) VALUES(?,?,?,?,?,?,?)',(aid,patient,doctor,str(apdate),aptime,status,reason)); log(f'Appointment {aid} booked for {patient}.'); st.success('Appointment booked.'); st.rerun()
                except sqlite3.IntegrityError: st.error('Appointment ID already exists.')
    ap=df('SELECT * FROM appointments ORDER BY appt_date DESC,id DESC'); st.dataframe(ap[['appointment_id','patient','doctor','appt_date','appt_time','status','reason']],use_container_width=True,hide_index=True)
    st.subheader('⚡ Update Appointment Status'); ids=ap.appointment_id.tolist() if not ap.empty else []
    if ids:
        sel=st.selectbox('Appointment',ids); new_status=st.selectbox('New Status',['Pending','Confirmed','Completed','Cancelled'])
        if st.button('Update Status'):
            run('UPDATE appointments SET status=? WHERE appointment_id=?',(new_status,sel)); log(f'Appointment {sel} marked {new_status}.'); st.success('Status updated.'); st.rerun()

# ----------------------------- Prescriptions -----------------------------
elif page=='Prescriptions':
    st.title('💊 Prescription Management')
    patients=q('SELECT name FROM patients'); doctors=q('SELECT name FROM doctors')
    with st.expander('➕ Create Prescription'):
        with st.form('rx_add'):
            c1,c2=st.columns(2); rxid=c1.text_input('Prescription ID',next_id('RX','prescriptions','rx_id')); patient=c2.selectbox('Patient',[x['name'] for x in patients]); doctor=c1.selectbox('Doctor',[x['name'] for x in doctors]); rxdate=c2.date_input('Date',date.today()); diagnosis=st.text_input('Diagnosis'); medicines=st.text_area('Medicines',placeholder='Paracetamol 500mg — 1 tablet twice daily\nVitamin D — once daily'); instructions=st.text_area('Instructions')
            if st.form_submit_button('Save Prescription',use_container_width=True):
                try: run('INSERT INTO prescriptions(rx_id,patient,doctor,rx_date,diagnosis,medicines,instructions) VALUES(?,?,?,?,?,?,?)',(rxid,patient,doctor,str(rxdate),diagnosis,medicines,instructions)); log(f'Prescription {rxid} created.'); st.success('Prescription saved.'); st.rerun()
                except sqlite3.IntegrityError: st.error('Prescription ID already exists.')
    rx=df('SELECT * FROM prescriptions ORDER BY id DESC'); st.dataframe(rx,use_container_width=True,hide_index=True)
    if not rx.empty:
        selected=st.selectbox('Select prescription',rx.rx_id.tolist()); r=rx[rx.rx_id==selected].iloc[0]
        lines=['HOSPITAL MANAGEMENT SYSTEM','PRESCRIPTION','',f'Prescription ID: {r.rx_id}',f'Patient: {r.patient}',f'Doctor: {r.doctor}',f'Date: {r.rx_date}',f'Diagnosis: {r.diagnosis}','', 'Medicines:',r.medicines,'','Instructions:',r.instructions]
        st.text('\n'.join(lines)); pdf=safe_pdf('HMS Prescription',lines)
        if pdf: st.download_button('⬇️ Download Prescription PDF',pdf,file_name=f'{r.rx_id}.pdf',mime='application/pdf')

# ----------------------------- Billing -----------------------------
elif page=='Billing':
    st.title('💳 Billing & Invoice Management')
    patients=q('SELECT name FROM patients')
    with st.expander('➕ Create Bill'):
        with st.form('bill_add'):
            c1,c2,c3=st.columns(3); bid=c1.text_input('Bill ID',next_id('B','bills','bill_id')); patient=c2.selectbox('Patient',[x['name'] for x in patients]); bdate=c3.date_input('Bill Date',date.today()); consultation=c1.number_input('Consultation ₹',0.0,100000.0,500.0,step=100.0); medicine=c2.number_input('Medicine ₹',0.0,100000.0,0.0,step=100.0); lab=c3.number_input('Lab ₹',0.0,100000.0,0.0,step=100.0); room=c1.number_input('Room ₹',0.0,100000.0,0.0,step=100.0); status=c2.selectbox('Payment Status',['Paid','Pending']); total=consultation+medicine+lab+room; st.info(f'Invoice Total: **{money(total)}**')
            if st.form_submit_button('Create Bill',use_container_width=True):
                try: run('INSERT INTO bills(bill_id,patient,consultation,medicine,lab,room,total,status,bill_date) VALUES(?,?,?,?,?,?,?,?,?)',(bid,patient,consultation,medicine,lab,room,total,status,str(bdate))); log(f'Bill {bid} created for {patient}.'); st.success('Bill created.'); st.rerun()
                except sqlite3.IntegrityError: st.error('Bill ID already exists.')
    bills=df('SELECT * FROM bills ORDER BY id DESC'); paid=bills.loc[bills.status=='Paid','total'].sum() if not bills.empty else 0; pending=bills.loc[bills.status=='Pending','total'].sum() if not bills.empty else 0
    c1,c2,c3=st.columns(3); c1.metric('Total Billing',money(bills.total.sum() if not bills.empty else 0)); c2.metric('Paid',money(paid)); c3.metric('Pending',money(pending)); st.dataframe(bills,use_container_width=True,hide_index=True)
    if not bills.empty:
        sel=st.selectbox('Select Invoice',bills.bill_id.tolist()); b=bills[bills.bill_id==sel].iloc[0]
        lines=['HOSPITAL MANAGEMENT SYSTEM','INVOICE / BILL','',f'Bill ID: {b.bill_id}',f'Date: {b.bill_date}',f'Patient: {b.patient}','',f'Consultation: {money(b.consultation)}',f'Medicine: {money(b.medicine)}',f'Laboratory: {money(b.lab)}',f'Room: {money(b.room)}','',f'TOTAL: {money(b.total)}',f'Payment Status: {b.status}']
        st.text('\n'.join(lines)); pdf=safe_pdf('HMS Invoice',lines)
        if pdf: st.download_button('⬇️ Download Invoice PDF',pdf,file_name=f'{b.bill_id}_invoice.pdf',mime='application/pdf')
        if st.button('🗑️ Delete Selected Bill'):
            run('DELETE FROM bills WHERE bill_id=?',(sel,)); log(f'Bill {sel} deleted.'); st.rerun()

# ----------------------------- Beds -----------------------------
elif page=='Beds & Rooms':
    st.title('🛏️ Bed & Room Management'); beds=df('SELECT * FROM beds ORDER BY room,bed_id'); available=len(beds[beds.status=='Available']); occupied=len(beds[beds.status=='Occupied'])
    c1,c2,c3=st.columns(3); c1.metric('Total Beds',len(beds)); c2.metric('Available',available); c3.metric('Occupied',occupied)
    st.dataframe(beds,use_container_width=True,hide_index=True)
    with st.expander('➕ Add Bed'):
        with st.form('bed_add'):
            c1,c2=st.columns(2); bed=c1.text_input('Bed ID',next_id('BED','beds','bed_id')); room=c2.text_input('Room Number'); typ=c1.selectbox('Bed Type',['General','Semi-Private','Private','ICU','Emergency']); status=c2.selectbox('Status',['Available','Occupied']); patient=c1.text_input('Patient if occupied')
            if st.form_submit_button('Save Bed',use_container_width=True):
                try: run('INSERT INTO beds(bed_id,room,bed_type,status,patient) VALUES(?,?,?,?,?)',(bed,room,typ,status,patient if status=='Occupied' else '')); st.success('Bed added.'); st.rerun()
                except sqlite3.IntegrityError: st.error('Bed ID already exists.')

# ----------------------------- Admissions -----------------------------
elif page=='Admissions':
    st.title('🏨 Admissions & Discharge')
    patients=q('SELECT name FROM patients'); beds=q("SELECT * FROM beds WHERE status='Available'")
    with st.expander('➕ Admit Patient'):
        if beds:
            with st.form('adm_add'):
                c1,c2,c3=st.columns(3); aid=c1.text_input('Admission ID',next_id('ADM','admissions','admission_id')); patient=c2.selectbox('Patient',[x['name'] for x in patients]); bed=c3.selectbox('Available Bed',[x['bed_id'] for x in beds]); admdate=c1.date_input('Admission Date',date.today()); room=next(x['room'] for x in beds if x['bed_id']==bed)
                if st.form_submit_button('Admit Patient',use_container_width=True):
                    try:
                        run('INSERT INTO admissions(admission_id,patient,room,bed,admission_date,discharge_date,status) VALUES(?,?,?,?,?,?,?)',(aid,patient,room,bed,str(admdate),'','Admitted')); run('UPDATE beds SET status="Occupied",patient=? WHERE bed_id=?',(patient,bed)); log(f'{patient} admitted to bed {bed}.'); st.success('Patient admitted.'); st.rerun()
                    except sqlite3.IntegrityError: st.error('Admission ID already exists.')
        else: st.warning('No available beds.')
    adm=df('SELECT * FROM admissions ORDER BY id DESC'); st.dataframe(adm,use_container_width=True,hide_index=True)
    active=adm[adm.status=='Admitted'] if not adm.empty else pd.DataFrame()
    if not active.empty:
        sel=st.selectbox('Active Admission',active.admission_id.tolist())
        if st.button('🚪 Discharge Patient',use_container_width=True):
            a=active[active.admission_id==sel].iloc[0]; run('UPDATE admissions SET discharge_date=?,status="Discharged" WHERE admission_id=?',(str(date.today()),sel)); run('UPDATE beds SET status="Available",patient="" WHERE bed_id=?',(a.bed,)); log(f'{a.patient} discharged from {a.bed}.'); st.success('Patient discharged and bed released.'); st.rerun()

# ----------------------------- Laboratory -----------------------------
elif page=='Laboratory':
    st.title('🧪 Laboratory Management')
    patients=q('SELECT name FROM patients')
    with st.expander('➕ Add Lab Test'):
        with st.form('lab_add'):
            c1,c2,c3=st.columns(3); tid=c1.text_input('Test ID',next_id('LAB','labs','test_id')); patient=c2.selectbox('Patient',[x['name'] for x in patients]); test=c3.text_input('Test Name','CBC'); result=c1.text_input('Result','Pending'); amount=c2.number_input('Test Amount ₹',0.0,100000.0,300.0,step=50.0); tdate=c3.date_input('Test Date',date.today()); status=c1.selectbox('Status',['Pending','Completed','Abnormal'])
            if st.form_submit_button('Save Lab Test',use_container_width=True):
                try: run('INSERT INTO labs(test_id,patient,test_name,result,amount,test_date,status) VALUES(?,?,?,?,?,?,?)',(tid,patient,test,result,amount,str(tdate),status)); log(f'Lab test {tid} created for {patient}.'); st.success('Lab test saved.'); st.rerun()
                except sqlite3.IntegrityError: st.error('Test ID already exists.')
    labs=df('SELECT * FROM labs ORDER BY id DESC'); st.dataframe(labs,use_container_width=True,hide_index=True)

# ----------------------------- Reports -----------------------------
elif page=='Reports & Analytics':
    st.title('📈 Reports & Analytics')
    patients=df('SELECT * FROM patients'); doctors=df('SELECT * FROM doctors'); ap=df('SELECT * FROM appointments'); bills=df('SELECT * FROM bills'); beds=df('SELECT * FROM beds'); adm=df('SELECT * FROM admissions'); labs=df('SELECT * FROM labs'); rx=df('SELECT * FROM prescriptions')
    tabs=st.tabs(['👥 Patients','📅 Appointments','💰 Revenue','🛏️ Hospital Summary'])
    with tabs[0]:
        st.write('**Patients by Disease**');
        if not patients.empty: st.bar_chart(patients.disease.replace('', 'Not specified').value_counts())
        st.write('**Blood Group Distribution**');
        if not patients.empty: st.bar_chart(patients.blood_group.value_counts())
    with tabs[1]:
        if not ap.empty: st.bar_chart(ap.status.value_counts()); st.bar_chart(ap.doctor.value_counts())
    with tabs[2]:
        total=bills.total.sum() if not bills.empty else 0; paid=bills.loc[bills.status=='Paid','total'].sum() if not bills.empty else 0; pending=bills.loc[bills.status=='Pending','total'].sum() if not bills.empty else 0
        c1,c2,c3=st.columns(3); c1.metric('Total',money(total)); c2.metric('Collected',money(paid)); c3.metric('Outstanding',money(pending))
        if not bills.empty: st.line_chart(bills.groupby('bill_date').total.sum().sort_index())
    with tabs[3]:
        summary=pd.DataFrame({'Metric':['Patients','Doctors','Appointments','Prescriptions','Bills','Lab Tests','Beds','Available Beds','Occupied Beds','Active Admissions','Total Revenue','Collected','Outstanding'],'Value':[len(patients),len(doctors),len(ap),len(rx),len(bills),len(labs),len(beds),len(beds[beds.status=='Available']),len(beds[beds.status=='Occupied']),len(adm[adm.status=='Admitted']),money(bills.total.sum() if not bills.empty else 0),money(bills.loc[bills.status=='Paid','total'].sum() if not bills.empty else 0),money(bills.loc[bills.status=='Pending','total'].sum() if not bills.empty else 0)]}); st.dataframe(summary,use_container_width=True,hide_index=True)
        st.download_button('⬇️ Download Summary CSV',summary.to_csv(index=False),file_name='HMS_summary.csv',mime='text/csv')

# ----------------------------- Activity -----------------------------
elif page=='Activity Log':
    st.title('🕒 Activity Log'); st.caption('Recent actions performed in the HMS demo.')
    act=df('SELECT created_at AS Time,message AS Activity FROM activity ORDER BY id DESC LIMIT 100'); st.dataframe(act,use_container_width=True,hide_index=True)

st.sidebar.markdown('---')
st.sidebar.caption('🏥 HMS • Academic Project • v3.0')
