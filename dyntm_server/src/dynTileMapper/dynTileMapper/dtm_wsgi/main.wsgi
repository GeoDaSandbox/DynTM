from dtm_wsgi import dtm

application = dtm.get_application(prefix='/wsgi/main.wsgi',debug=True)

