from lightning_sdk import Studio

studio = Studio(name='fixed-moccasin-3jhs', teamspace='ekko', user='dejandukic')

studio.upload_file(file_path='./ekko_prototype/Masters of Scale.txt', remote_path='/ekko/transcripts/Masters of Scale.txt', progress_bar=True)