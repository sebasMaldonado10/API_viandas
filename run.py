from app import create_app

# Crear la aplicación (exporta `db` para el CLI de Flask-Migrate)
app = create_app()
# Importamos db
from app import db

if __name__ == "__main__":
    app.run(debug=True)

    
