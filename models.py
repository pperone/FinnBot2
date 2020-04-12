from finn_bot import db
from sqlalchemy_utils import ScalarListType

class Team(db.Model):
  __tablename__ = 'teams'

  channel = db.Column(db.String(), primary_key=True)
  users = db.Column(db.ARRAY(db.String))
  current = db.Column(db.Integer())

  def __init__(self, channel, users, current):
    self.channel = channel
    self.users = users
    self.current = current

  def serialize(self):
    return {
      'channel': self.channel,
      'users' : self.users,
      'current': self.current
    }
