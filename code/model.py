from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired
from app import app

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable = False, unique = True)
    passhash = db.Column(db.String(512), nullable = False, unique = True)
    role = db.Column(db.String(80), nullable = False)
    flagged = db.Column(db.Boolean, default = False)
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.passhash, password)

class Sponsors(db.Model):
    __tablename__ = 'Sponsors'
    id = db.Column(db.Integer, primary_key=True)
    passhash = db.Column(db.String(512), nullable = False, unique = True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    name = db.Column(db.String(80), primary_key=True)
    company_name = db.Column(db.String(512), unique = True, nullable = False)
    industry = db.Column(db.String(512), nullable = False)
    budget = db.Column(db.Integer, nullable = False)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.passhash, password)

class Influencers(db.Model):
    __tablename__ = 'Influencers'
    id = db.Column(db.Integer, primary_key=True)
    passhash = db.Column(db.String(512), nullable = False, unique = True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    name = db.Column(db.String(80), primary_key=True)
    category = db.Column(db.String(80), nullable = False)
    niche = db.Column(db.String(512), nullable = False)
    followers = db.Column(db.Integer, nullable = False)
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.passhash, password)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=True)
    description = db.Column(db.String(512), nullable = False)
    start_date = db.Column(db.Integer, nullable = False)
    end_date = db.Column(db.Integer, nullable = False)
    budget = db.Column(db.Integer, nullable = False)
    visibility = db.Column(db.String(80), nullable = False)
    goals = db.Column(db.Integer, nullable = False)
    niche = db.Column(db.String(100), nullable = False)
    flagged = db.Column(db.Boolean, default = False)
    
    sponsor_id = db.Column(db.Integer, db.ForeignKey('Sponsors.id'), nullable=True)
    influencer_id = db.Column(db.Integer, db.ForeignKey('Influencers.id'), nullable=True)
    Sponsor = db.relationship('Sponsors', backref=db.backref('campaigns', lazy=True))
    influencer = db.relationship('Influencers', backref=db.backref('campaigns', lazy=True))

class ad_request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey(Campaign.id))
    influencer_id = db.Column(db.Integer, db.ForeignKey(Influencers.id))
    requirements = db.Column(db.String(80), nullable = False)
    payment_amount = db.Column(db.Integer, nullable = False)
    status = db.Column(db.String(80), nullable = False)
    
    campaign = db.relationship('Campaign', backref=db.backref('ad_request', lazy=True))
    influencer = db.relationship('Influencers', backref=db.backref('ad_request', lazy=True))
 
class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey(Campaign.id),nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey(Influencers.id),nullable=False)
    message = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pending')

    campaign = db.relationship('Campaign', backref=db.backref('Request', lazy=True))
    influencer = db.relationship('Influencers', backref=db.backref('Request', lazy=True))

with app.app_context():
    db.create_all()
    
    #admin login
    admin = User.query.filter_by(name='admin').first()
    if not admin:
        admin = User(name='admin', password='admin', role='admin')
        db.session.add(admin)
        db.session.commit() 
