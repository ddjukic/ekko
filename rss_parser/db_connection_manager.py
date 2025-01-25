from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker

Base = declarative_base()

class Podcast(Base):
    __tablename__ = 'podcasts'
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True, nullable=False)
    episodes = relationship("Episode", back_populates="podcast")

class Episode(Base):
    __tablename__ = 'episodes'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    mp3_url = Column(String, nullable=False)
    publication_date = Column(DateTime, default=datetime.utcnow)
    downloaded = Column(Boolean, default=False)
    podcast_id = Column(Integer, ForeignKey('podcasts.id'))
    podcast = relationship("Podcast", back_populates="episodes")

class DatabaseConnectionManager:
    def __init__(self, db_url='sqlite:///podcast_downloads.sqlite'):
        self.engine = create_engine(db_url, echo=True, future=True)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

    def add_episode(self, podcast_title, episode):
        session = self.Session()
        podcast = session.query(Podcast).filter_by(title=podcast_title).first()
        if not podcast:
            podcast = Podcast(title=podcast_title)
            session.add(podcast)
        existing_episode = session.query(Episode).filter_by(mp3_url=episode.mp3_url).first()
        if existing_episode:
            print(f"Episode already downloaded: {episode.title}")
        else:
            new_episode = Episode(title=episode.title, mp3_url=episode.mp3_url,
                                  publication_date=episode.publication_date, downloaded=True, podcast=podcast)
            session.add(new_episode)
            session.commit()
            print(f"Episode downloaded and added to database: {episode.title}")
        session.close()

    def episode_downloaded(self, mp3_url):
        session = self.Session()
        episode = session.query(Episode).filter_by(mp3_url=mp3_url).first()
        downloaded = episode.downloaded if episode else False
        session.close()
        return downloaded