import json

def read_json_file(file_path):
    """Liest die JSON-Datei ein und gibt die 'text_lines' zurück."""
    with open(file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
    return data.get("text_lines", [])

# Funktion zum Parsen der Daten aus dem übergebenen String
def parse_data_string(text_lines):
    """Parst den Eingabestring und trennt Parameter/Werte von Begründungen."""
    lines = text_lines
    parameter_data = {}
    wetterdaten = {}

    for line in lines:
        line = line.strip().strip('"')
        if ' = ' in line:
            key, value = line.split(' = ', 1)
            # Wenn "weil" enthalten ist, Begründung extrahieren
            if "weil" in value:
                value, begründung = value.split("weil", 1)
                begründung = begründung.strip()
            else:
                begründung = ""
            
            # Füge Wetterdaten in die Wetterdatentabelle ein
            if any(monat in key for monat in ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]):
                monat = key.split()[1]  # Monat extrahieren
                if monat not in wetterdaten:
                    wetterdaten[monat] = {}
                if "Schneefall" in key:
                    wetterdaten[monat]["Schneefall [mm]"] = float(value)
                elif "Niederschlag" in key:
                    wetterdaten[monat]["Niederschlag [mm]"] = float(value)
            else:
                parameter_data[key.strip()] = {"value": value.strip(), "begründung": begründung}

    return parameter_data, wetterdaten