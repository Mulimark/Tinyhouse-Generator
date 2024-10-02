import json

def read_json_file(file_path):
    #Liest die JSON-Datei ein und gibt die 'text_lines' zurück

    with open(file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
    return data.get("text_lines", [])


def parse_data_string(text_lines):
    #Funktion zum Parsen der Daten aus dem übergebenen String
    lines = text_lines
    parameter_data = {}
    wetterdaten = {}

    for line in lines:
        line = line.strip().strip('"')
        if ' = ' in line:
            key, value = line.split(' = ', 1)
            # Wenn "weil" enthalten ist -> Begründung extrahieren
            if "weil" in value:
                value, begründung = value.split("weil", 1)
                begründung = begründung.strip()
            else:
                begründung = ""
            
            # Füge Wetterdaten in die korrekte Wetterdatentabelle ein
            if any(monat in key for monat in ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]):
                monat = key.split()[1]  # Monat herauslesen
                if monat not in wetterdaten:
                    wetterdaten[monat] = {}
                if "Schneefall" in key:
                    wetterdaten[monat]["Schneefall [mm]"] = float(value)
                elif "Niederschlag" in key:
                    wetterdaten[monat]["Niederschlag [mm]"] = float(value)
            else:
                parameter_data[key.strip()] = {"value": value.strip(), "begründung": begründung}

    return parameter_data, wetterdaten

def get_inner_tree_by_param_name(output, param_name):

    #Hilfsfunktion, um basierend auf ParamName das entsprechende InnerTree zu erhalten.
    # Prüfen, ob output eine Liste oder ein Dictionary ist
    
    if isinstance(output, list):
        print(f"Warning: Output is a list, expected a dictionary. Output: {output}")
        # Gehe davon aus, dass jedes Element der Liste ein Dictionary ist und versuche, "ParamName" zu finden
        for item in output:
            if isinstance(item, dict) and item.get("ParamName") == param_name:
                return item.get("InnerTree")
    elif isinstance(output, dict) and "values" in output:
        for item in output["values"]:
            if "ParamName" in item and item["ParamName"] == param_name:
                return item["InnerTree"]
    else:
        print(f"Unexpected output structure: {output}")

    print(f"Kein InnerTree gefunden für {param_name}")
    return None  # Falls das ParamName nicht gefunden wird