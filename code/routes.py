from functools import wraps
from http.client import ACCEPTED
import logging
from flask import Flask, render_template, redirect, flash, url_for, session, request, send_file,jsonify
from model import db, User, Sponsors, Influencers, ad_request, Campaign, Request
from datetime import datetime, timedelta
from app import app

logging.basicConfig(level=logging.DEBUG)

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return inner

@app.route('/')
def index():
        return render_template('index.html')

@app.route('/login')
def login():   
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    name = request.form.get('name') 
    password = request.form.get('password')
    role = request.form.get('role')
    if name=='' or password=='':
        return redirect(url_for('login'))  
    user = User.query.filter_by(name=name).first()
    if not user or not user.check_password(password):
        return redirect(url_for('login'))
    session['role'] = role
    session['name'] = name
    return redirect(url_for('admin'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    user_type = request.form.get('userType')
    if user_type not in ['sponsor', 'influencer']:
        return "Invalid user type", 400
    id = request.form.get('id')
    password = request.form.get('password')
    name = request.form.get('name')
    user = User(name=name, password=password, role=user_type)
    db.session.add(user)
    db.session.commit()
    
    if user_type == 'sponsor':
        company_name = request.form.get('company_name')
        industry = request.form.get('industry')
        budget = request.form.get('budget')
        sponsor = Sponsors(id=id, password=password, name=name, company_name=company_name, industry=industry, budget=budget)
        db.session.add(sponsor)
        db.session.commit()
        return redirect(url_for('login'))

    elif user_type == 'influencer':
        category = request.form.get('category')
        niche = request.form.get('niche')
        followers = request.form.get('followers')
        influencer = Influencers(id=id, password=password, name=name, category=category, niche=niche, followers=followers)
        db.session.add(influencer)
        db.session.commit()
        return redirect(url_for('login'))
    
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))



@app.route('/admin')
def admin():
    role = session.get('role')  
    user = User.query.filter_by(role=role).first()
    if user and user.role == "admin" :
        active_users = {
            'Sponsors': User.query.filter_by(role='sponsor').count(),
            'Influencers': User.query.filter_by(role='influencer').count()
        }
        total_campaigns = {
            'Public': Campaign.query.filter_by(visibility='Public').count(),
            'Private': Campaign.query.filter_by(visibility='Private').count()
        }
        request_status = {
            'Accepted': Request.query.filter_by(status='Accepted').count(),
            'Rejected': Request.query.filter_by(status='Rejected').count()
        }
        flagged_users = {
            'Sponsors': User.query.filter_by(role='sponsor', flagged=True).count(),
            'Influencers': User.query.filter_by(role='influencer', flagged=True).count()
        }
        return render_template('admin.html', active_users=active_users, total_campaigns=total_campaigns, request_status=request_status, flagged_users=flagged_users)
    
    elif user.role == "sponsor":
        sponsor = Sponsors.query.filter_by(name=user.name).first()
        if sponsor:
            return redirect(url_for('sponsor', sponsor=Sponsors.query.all()))
        else:
            return "Sponsor not found", 400
        
    elif user.role == "influencer":
        influencer = Influencers.query.filter_by(name=user.name).first()
        if influencer:
            return redirect(url_for('influencer', influencer=Influencers.query.all()))
        else:
            return "Influencer not found", 400
        
    else:
        "No User Found !!", 400

@app.route('/find', methods=['GET', 'POST'])
def find():
    users=User.query.all()
    campaigns= Campaign.query.all()
    return render_template('find.html', users=users, campaigns=campaigns)

@app.route('/find/flag/user/<int:user_id>', methods=['POST'])
def flag_user(user_id):
    user = User.query.get_or_404(user_id)
    user.flagged = not user.flagged
    db.session.commit()
    return redirect(url_for('find'))

@app.route('/find/flag/campaign/<int:campaign_id>', methods=['POST'])
def flag_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    campaign.flagged = not campaign.flagged
    db.session.commit()
    return redirect(url_for('find'))
 
@app.route('/stat')
def stat():
    user = User.query.all()
    sponsor_count = sum(1 for user in user if user.role=='sponsor')
    influencer_count = sum(1 for user in user if user.role=='influencer')
    return render_template('stat.html',user=User.query.all(), sponsor_count=sponsor_count,influencer_count=influencer_count )


 
    
@app.route('/sponsor')
def sponsor():
    sponsor = Sponsors.query.all() 
    influencer = Influencers.query.all()
    campaign = Campaign.query.all()
    pending_requests = Request.query.filter(Request.status != 'Accepted').all()
    return render_template('sponsor.html', requests=pending_requests, campaign=campaign, sponsor=sponsor,influencer=influencer)

@app.route('/accept_request/<int:request_id>')
def accept_request(request_id):
    request = Request.query.get_or_404(request_id)
    request.status = 'Accepted'
    db.session.commit()
    flash('Request accepted.')
    return redirect(url_for('sponsor'))

@app.route('/reject_request/<int:request_id>')
def reject_request(request_id):
    request = Request.query.get_or_404(request_id)
    request.status = 'Rejected'
    db.session.commit()
    flash('Request denied.')
    return redirect(url_for('sponsor'))
    

@app.route('/campaign')
def campaign():
    ad_requests = ad_request.query.all()
    campaigns = Campaign.query.all()
    return render_template('campaign.html', campaigns=campaigns, ad_requests=ad_requests)

@app.route('/create_campaign', methods=['GET', 'POST'])
def create_campaign():
    if request.method == 'POST':
        id = request.form['id']
        name = request.form['name']
        description = request.form['description']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        budget = request.form['budget']
        visibility = request.form['visibility']
        goals = request.form['goals']
        niche = request.form['niche']
        
        new_campaign = Campaign(
            id=id,
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            visibility=visibility,
            goals=goals,
            niche=niche
        )
        db.session.add(new_campaign)
        db.session.commit()
        return redirect(url_for('campaign'))
    return render_template('create_campaign.html')

@app.route('/campaign/edit/<int:campaign_id>', methods=['GET', 'POST'])
def edit_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if request.method == 'POST':
        campaign.name = request.form['name']
        campaign.description = request.form['description']
        campaign.start_date = request.form['start_date']
        campaign.end_date = request.form['end_date']
        campaign.budget = request.form['budget']
        campaign.visibility = request.form['visibility']
        campaign.goals = request.form['goals']
        db.session.commit()
        return redirect(url_for('campaign'))
    return render_template('edit_campaign.html', campaign=campaign)

@app.route('/campaign/delete/<int:campaign_id>', methods=['POST'])
def delete_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    db.session.delete(campaign)
    db.session.commit()
    return redirect(url_for('campaign'))

@app.route('/adrequest/create', methods=['GET', 'POST'])
def create_adrequest():
    if request.method == 'POST':
        campaign_id = request.form['campaign_id']
        influencer_id = request.form['influencer_id']
        requirements = request.form['requirements']
        payment_amount = request.form['payment_amount']
        status = request.form['status']

        new_adrequest=ad_request(
            campaign_id=campaign_id,
            influencer_id=influencer_id,
            requirements=requirements,
            payment_amount=payment_amount,
            status=status
        )
        db.session.add(new_adrequest)
        db.session.commit()
        return redirect(url_for('campaign'))
    campaigns = Campaign.query.all()
    influencers = Influencers.query.all()
    return render_template('create_adrequest.html', campaigns=campaigns, influencers=influencers)

@app.route('/adrequest/edit/<int:ad_request_id>', methods=['GET', 'POST'])
def edit_adrequest(ad_request_id):
    ad_requests = ad_request.query.get_or_404(ad_request_id)
    if request.method == 'POST':
        ad_requests.campaign_id = request.form['campaign_id']
        ad_requests.influencer_id = request.form['influencer_id']
        ad_requests.requirements = request.form['requirements']
        ad_requests.payment_amount = request.form['payment_amount']
        ad_requests.status = request.form['status']
        db.session.commit()
        return redirect(url_for('campaign'))
    campaigns = Campaign.query.all()
    influencers = Influencers.query.all()
    return render_template('edit_adrequest.html', ad_request=ad_request, campaigns=campaigns, influencers=influencers)

@app.route('/adrequest/delete/<int:ad_request_id>', methods=['POST'])
def delete_adrequest(ad_request_id):
    ad_requests = ad_request.query.get_or_404(ad_request_id)
    db.session.delete(ad_requests)
    db.session.commit()
    return redirect(url_for('campaign'))


@app.route('/adrequest')
def adrequest():
    return render_template('adrequest.html')



@app.route('/influencer')   
def influencer():
    requests = Request.query.filter_by(status=session.get('status'))
    influencer = Influencers.query.filter_by(name=session.get('name'))
    campaign = Campaign.query.all()
    status = 'accepted'
    return render_template('influencer.html', influencer=influencer, campaign=campaign, requests=requests)

@app.route('/profile')
def profile():
    influencer = Influencers.query.filter_by(name=session.get('name')) 
    return render_template('profile.html', influencer=influencer)

@app.route('/profile', methods=['POST'])
def profile_post():
    id = request.form.get('id')
    name = request.form.get('name')
    password = request.form.get('password')
    category = request.form.get('category')
    niche = request.form.get('niche')
    followers = request.form.get('followers')
     
    influencer = Influencers.query.filter_by(name=name).first() 
    if influencer:
        influencer.password = password
        influencer.category = category
        influencer.niche = niche
        influencer.followers = followers
        db.session.commit()    
    return redirect(url_for('profile', influencer=influencer))

@app.route('/camp_influ')
def camp_influ():
    campaign = Campaign.query.all()
    ad_requests = ad_request.query.all()
    return render_template('camp_influ.html', campaign=campaign, ad_requests=ad_requests)

@app.route('/accept_request1/<int:ad_request_id>')
def accept_request1(ad_request_id):
    request = Request.query.get_or_404(ad_request_id)
    request.status = 'Accepted'
    db.session.commit()
    flash('Request accepted.')
    return redirect(url_for('camp_influ'))

@app.route('/reject_request1/<int:ad_request_id>')
def reject_request1(ad_request_id):
    request = Request.query.get_or_404(ad_request_id)
    request.status = 'Rejected'
    db.session.commit()
    flash('Request denied.')
    return redirect(url_for('camp_influ'))

@app.route('/campaign/<int:campaign_id>')
def view_camp(campaign_id):
    campaign = Campaign.query.filter_by(id=campaign_id).first()
    if campaign:
        return render_template('view_camp.html', campaign=campaign)
    else:
        return "Campaign not found", 404

@app.route('/request_camp', methods=['GET', 'POST'])
def request_camp():
    if request.method == 'POST':
        campaign_id = request.form.get('campaign_id')
        influencer_id = request.form.get('influencer_id')
        message = request.form.get('message')
        status = request.form.get('status', 'Pending')  
        
        if not campaign_id or not influencer_id or not message:
            flash('Campaign ID, Influencer ID, and Message are required.')
            return redirect(url_for('request_camp'))
        
        new_request = Request(
            campaign_id=campaign_id,
            influencer_id=influencer_id,
            message=message,
            status=status
        )
        db.session.add(new_request)
        db.session.commit()
        flash('Request created successfully.')
        return redirect(url_for('influencer'))
    
    campaigns = Campaign.query.all()
    requests=Request.query.all()
    influencers = Influencers.query.all()
    return render_template('request_camp.html', influencers=influencers, campaigns=campaigns, requests=requests)


