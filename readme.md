# Running the app
`gunicorn --config gunicorn_config.py wsgi:app`
### Database migration 
Use after importing new model into app.py.\
Create migration:\
`python manager.py migrate`\
Apply it:\
`python manage.py db upgrade`\
\
**WARNING**: Secret key must be a length of multiple of 2. 