o = open('views.py','w')
view = open('views.precompile.py','r').read()
template = open('canvas.html','r').read()
o.write(view.replace("TEMPLATE_PLACE_HOLDER",template))
o.close()
