import os
import psycopg2
from flask import Flask, render_template, request, jsonify

# La variabile DATABASE_URL è essenziale per la connessione al DB su Render.
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    # Questa eccezione avverrà se la variabile non è stata impostata su Render.
    raise ValueError("L'ambiente richiede la variabile DATABASE_URL.")

app = Flask(__name__)

# --- Funzioni di Inizializzazione del Database ---

def init_db():
    conn = None
    try:
        # Tenta di connettersi al database usando l'URL fornito
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Crea la tabella 'robot_counters' se non esiste.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS robot_counters (
                robot_type TEXT PRIMARY KEY,
                current_count INTEGER NOT NULL DEFAULT 0
            );
        """)
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Errore durante l'inizializzazione del DB: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# Esegui l'inizializzazione del DB all'avvio del server
init_db()

# --- Routing per il Frontend e API ---

@app.route('/')
def index():
    # Renderizza la pagina HTML principale
    return render_template('index.html')


@app.route('/generate_code', methods=['POST'])
def generate_code():
    data = request.get_json()
    robot_type = data.get('robot_type')
    
    if not robot_type:
        return jsonify({"error": "Tipo di robot non specificato."}), 400

    conn = None
    new_code = None
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Blocca la riga (FOR UPDATE) per garantire l'atomicità
        cur.execute(
            "SELECT current_count FROM robot_counters WHERE robot_type = %s FOR UPDATE;", 
            (robot_type,)
        )
        
        row = cur.fetchone()
        
        if row is None:
            # Nuovo tipo di robot: inizia da 1
            current_count = 1
            cur.execute(
                "INSERT INTO robot_counters (robot_type, current_count) VALUES (%s, %s);",
                (robot_type, current_count)
            )
        else:
            # Robot esistente: incrementa il conteggio
            current_count = row[0] + 1
            cur.execute(
                "UPDATE robot_counters SET current_count = %s WHERE robot_type = %s;",
                (current_count, robot_type)
            )
        
        # Genera il codice nel formato TIPO-000N (4 cifre con zero iniziale)
        new_code = f"{robot_type}-{current_count:04d}"
        
        conn.commit()
        cur.close()
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Errore durante la generazione del codice: {e}")
        # Restituisce un errore 500 se c'è un problema di DB/connessione
        return jsonify({"error": "Errore interno del server durante la generazione del codice."}), 500
        
    finally:
        if conn:
            conn.close()

    return jsonify({"code": new_code})

if __name__ == '__main__':
    # Usato solo per i test locali. Render usa 'gunicorn app:app'
    app.run(debug=True)
