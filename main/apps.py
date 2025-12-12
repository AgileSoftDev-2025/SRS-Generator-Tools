from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

#from flask import Flask, render_template
#import plantuml
#import sqlite3

#app = Flask(__name__)

#def get_uml_from_db():
    #conn = sqlite3.connect("uml.db")  # file database
    #cursor = conn.cursor()
    #cursor.execute("SELECT uml_text FROM uml_diagram ORDER BY id DESC LIMIT 1")
    #uml_text = cursor.fetchone()[0]
    #conn.close()
    #return uml_text

#def generate_uml_image(uml_text):
    #server = plantuml.PlantUML(url="http://www.plantuml.com/plantuml/png/")
    #return server.get_url(uml_text)

#@app.route("/preview")
#def preview():
    #uml_text = get_uml_from_db()              # Ambil UML dari database
    #image_url = generate_uml_image(uml_text)  # Convert ke URL gambar
    #return render_template("preview.html", uml_image_url=image_url)

#if __name__ == "__main__":
    #app.run(debug=True)