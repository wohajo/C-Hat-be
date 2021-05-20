## Running the server
`$ docker-compose up`
## Running the app
gunicorn --bind=127.0.0.1:8081 --worker-class eventlet -w 1 app:app
`$ python app.py`
### Database migration 
Use after importing new model into app.py.\
Create migration:\
`$ python manager.py db migrate`\
Apply it:\
`$ python manage.py db upgrade`\
\
**WARNING**: Secret key must be a length of multiple of 2. 