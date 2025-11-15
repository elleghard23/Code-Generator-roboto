import os
import psycopg2
from flask import Flask, render_template, request, jsonify

# Assicurati che l'ambiente abbia la variabile DATABASE_URL.
# Se non presente, l'app non può avviarsi in produzione.
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("L'ambiente richiede la variabile DATABASE_URL.")

app = Flask(__name__)

# Configurazione del database e creazione della tabella
def init_db():
    conn = None
    try:
        # Tenta di connettersi al database
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # SQL per creare la tabella 'robot_counters' se non esiste
        # Utilizziamo 'robot_type' come chiave primaria per garantire unicità
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
        # In caso di errore, assicurarsi che la transazione venga annullata
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# Inizializza il DB all'avvio dell'applicazione
init_db()


@app.route('/')
def index():
    # Renderizza il frontend per la selezione del robot
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
        # Stabilisce la connessione
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Inizia una transazione per garantire l'atomicità:
        # 1. Tenta di ottenere il contatore esistente per il tipo di robot.
        # 2. Utilizza 'FOR UPDATE' per bloccare la riga fino alla COMMIT,
        #    impedendo ad altri utenti di leggere lo stesso valore prima dell'incremento.
        cur.execute(
            "SELECT current_count FROM robot_counters WHERE robot_type = %s FOR UPDATE;", 
            (robot_type,)
        )
        
        row = cur.fetchone()
        
        if row is None:
            # Se la riga non esiste, la crea con il conteggio 1
            current_count = 1
            cur.execute(
                "INSERT INTO robot_counters (robot_type, current_count) VALUES (%s, %s);",
                (robot_type, current_count)
            )
        else:
            # Se la riga esiste, incrementa il conteggio
            current_count = row[0] + 1
            cur.execute(
                "UPDATE robot_counters SET current_count = %s WHERE robot_type = %s;",
                (current_count, robot_type)
            )
        
        # Genera il nuovo codice (Formato: TIPO-000N)
        new_code = f"{robot_type}-{current_count:04d}"
        
        # Conferma la transazione, rilasciando il blocco della riga
        conn.commit()
        
        cur.close()
        
    except Exception as e:
        # Annulla la transazione in caso di errore
        if conn:
            conn.rollback()
        print(f"Errore durante la generazione del codice: {e}")
        return jsonify({"error": "Errore interno del server durante la generazione del codice."}), 500
        
    finally:
        # Chiude la connessione
        if conn:
            conn.close()

    return jsonify({"code": new_code})

if __name__ == '__main__':
    # Nota: Per l'ambiente di produzione, Gunicorn eseguirà l'app.
    # Questo è solo per i test locali.
    app.run(debug=True)
        if row is None:
            # Nuovo robot/prefisso: inizia da 1
            new_count = 1
            conn.execute(
                "INSERT INTO counters (prefix, current_count) VALUES (?, ?)", 
                (prefix, new_count)
            )
        else:
            # Robot esistente: incrementa
            new_count = row['current_count'] + 1
            conn.execute(
                "UPDATE counters SET current_count = ? WHERE prefix = ?", 
                (new_count, prefix)
            )
        
        # Formatta il codice (es. "ROB-A-00125")
        # Usiamo 5 cifre con leading zeros
        formatted_count = f"{new_count:05d}" 
        new_code = f"{prefix}-{formatted_count}"
        
        conn.commit() # Rilascia il blocco
        
        return jsonify({"code": new_code}), 200

    except Exception as e:
        conn.rollback() # Annulla l'operazione in caso di errore
        return jsonify({"error": f"Errore DB: {str(e)}"}), 500
    finally:
        conn.close()

# --- Routing per il Frontend ---

@app.route('/')
def index():
    # Renderizza la pagina HTML principale (creata al Passo 2)
    robot_list = [
        {"id": "ROB-A", "name": "Robot Assemblaggio A", "img": "robot_a.jpg"},
        {"id": "ROB-B", "name": "Robot Saldatura B", "img": "robot_b.jpg"},
        # Aggiungi altri robot qui
    ]
    return render_template('index.html', robots=robot_list)


if __name__ == '__main__':
    app.run(debug=True)
