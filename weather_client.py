######################
# Roman Schesler E3FI2
######################
import requests
import json
import pandas
import matplotlib.pyplot as plt
from datetime import datetime
import sys

######################################################################
# API-Abfrage für Wetterdaten (Open-Meteo)
# Python-Client zur Abfrage, Auswertung und Visualisierung von Wetterdaten.
######################################################################

# --- SCHRITT 1: BENUTZERINTERAKTION ---
print("--- Interaktives Wetter-Abfrage-Tool (Open-Meteo API) ---")
print("Bitte Standort wählen:")
print("  [1] Mannheim (49.49 / 8.47)")
print("  [2] Berlin   (52.52 / 13.41)")
print("  [3] München  (48.14 / 11.58)")
print("  [4] Eigene Koordinaten eingeben")

wahl = input("Auswahl [1-4, Enter = Mannheim]: ")

predefined_locations = {
    "1": ("49.49", "8.47"),
    "2": ("52.52", "13.41"),
    "3": ("48.14", "11.58"),
}

if wahl in predefined_locations:
    lat, lon = predefined_locations[wahl]
elif wahl == "4":
    lat_input = input("Breitengrad (Latitude): ")
    lon_input = input("Längengrad (Longitude): ")
    try:
        lat = float(lat_input)
        lon = float(lon_input)
    except ValueError:
        print("Fehler: Bitte gültige Zahlen für Koordinaten eingeben.")
        sys.exit(1)
    # Plausibilitätsprüfung für geografisch sinnvolle Werte
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        print("Fehler: Koordinaten außerhalb des gültigen Bereichs (-90..90 / -180..180).")
        sys.exit(1)
    # für die URL wieder in Strings umwandeln
    lat = str(lat)
    lon = str(lon)
else:
    # Default: Mannheim
    lat, lon = "49.49", "8.47"

# --- SCHRITT 2: API-ANFRAGE KONSTRUIEREN ---
URL = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={lat}&longitude={lon}"
    f"&hourly=temperature_2m"
    f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,sunrise,sunset"
    f"&timezone=Europe%2FBerlin"
)

try:
    response = requests.get(URL)
    response.raise_for_status()
except Exception as e:
    print(f"Fehler bei der Verbindung: {e}")
    sys.exit(1)

parsedJson = response.json()

# Hinweis auf feste Zeitzone, damit der Nutzer die Grenzen des Tools kennt
print("\nHinweis: Alle Zeiten werden in der Zeitzone Europe/Berlin dargestellt.")

# --- SCHRITT 3: DATENAUSGABE UND ANALYSE ---
print(f"\nWetterbericht für Standort: {lat}, {lon}")
print("-" * 75)
print(f"{'Datum':<12} | {'Max Temp':<10} | {'Min Temp':<10} | {'Wind':<10} | {'Regen':<8}")
print("-" * 75)

daily = parsedJson["daily"]

frosttage = 0
gesamtregen = 0.0

max_temp_gesamt = None
max_temp_datum = None
min_temp_gesamt = None
min_temp_datum = None

for i in range(len(daily["time"])):
    date = daily["time"][i]
    t_max = daily["temperature_2m_max"][i]
    t_min = daily["temperature_2m_min"][i]
    wind = daily["wind_speed_10m_max"][i]
    rain = daily["precipitation_sum"][i]

    gesamtregen += rain
    if t_min < 0:
        frosttage += 1

    if (max_temp_gesamt is None) or (t_max > max_temp_gesamt):
        max_temp_gesamt = t_max
        max_temp_datum = date

    if (min_temp_gesamt is None) or (t_min < min_temp_gesamt):
        min_temp_gesamt = t_min
        min_temp_datum = date

    # Intelligente Icons zur Analyse (Auswertung)
    icon = ""
    if t_min < 0:
        icon += " ❄️"
    if rain > 0:
        icon += " ☔"
    if wind > 20:
        icon += " 💨"

    print(f"{date:<12} | {t_max:>4}°C     | {t_min:>4}°C     | {wind:>4} km/h | {rain:>4} mm {icon}")

print("-" * 75)
print(f"Sonnenzeiten heute: Aufgang {daily['sunrise'][0].split('T')[1]} / Untergang {daily['sunset'][0].split('T')[1]}")

# --- SCHRITT 3b: KURZER WETTER-BERICHT (Zusatzanalyse) ---
print("\nZusammenfassung der nächsten Tage:")
if max_temp_gesamt is not None and min_temp_gesamt is not None:
    print(f"- Wärmster Tag:   {max_temp_datum} mit ca. {max_temp_gesamt:.1f}°C")
    print(f"- Kältester Tag:  {min_temp_datum} mit ca. {min_temp_gesamt:.1f}°C")
print(f"- Gesamtregen im Zeitraum: {gesamtregen:.1f} mm")
print(f"- Frosttage (Min < 0°C):   {frosttage} Tag(e)")

# einfache, gut nachvollziehbare Schwellenwerte für eine grobe Einschätzung:
# unter 1 mm gilt als "eher trocken", 1-10 mm als "mäßig nass", darüber als "sehr regnerisch"
if gesamtregen < 1.0:
    regen_text = "eher trocken"
elif gesamtregen < 10.0:
    regen_text = "mäßig nass"
else:
    regen_text = "sehr regnerisch"

print(f"- Einschätzung: Insgesamt wirkt es {regen_text}.")

# --- SCHRITT 4: SPEICHERN DER DATEN (JSON Export) ---
# Export einer kuratierten JSON-Struktur mit den wichtigsten Analysewerten
export_data = {
    "request": {
        "latitude": lat,
        "longitude": lon,
        "timezone": parsedJson.get("timezone", "Europe/Berlin"),
    },
    "daily": {
        "time": daily["time"],
        "temperature_2m_max": daily["temperature_2m_max"],
        "temperature_2m_min": daily["temperature_2m_min"],
        "precipitation_sum": daily["precipitation_sum"],
        "wind_speed_10m_max": daily["wind_speed_10m_max"],
        "sunrise": daily["sunrise"],
        "sunset": daily["sunset"],
    },
    "hourly": {
        "time": parsedJson["hourly"]["time"],
        "temperature_2m": parsedJson["hourly"]["temperature_2m"],
    },
    "analysis": {
        "warmest_day": {
            "date": max_temp_datum,
            "temperature_max": max_temp_gesamt,
        },
        "coldest_day": {
            "date": min_temp_datum,
            "temperature_min": min_temp_gesamt,
        },
        "total_precipitation": gesamtregen,
        "frost_days": frosttage,
        "rain_classification": regen_text,
    },
}

with open("wetter_data.json", "w", encoding="utf-8") as f:
    json.dump(export_data, f, indent=4, ensure_ascii=False)
print("\n[System]: Daten erfolgreich in 'wetter_data.json' exportiert.")

# --- SCHRITT 5: VISUALISIERUNG (Diagramm) ---
data_hourly = {
    "Zeit": parsedJson["hourly"]["time"],
    "Temperatur": parsedJson["hourly"]["temperature_2m"]
}
df = pandas.DataFrame(data_hourly)

plt.figure(figsize=(10, 5))
# Temperaturkurve in ORANGE
plt.plot(df["Temperatur"], label="Temperaturverlauf (stündlich)", color="orange", linewidth=2)
# Null-Grad-Linie in BLAU
plt.axhline(0, color="blue", linewidth=1.0, linestyle="--", label="0°C-Linie")

plt.xlabel("Stunden ab Vorhersagebeginn")
plt.ylabel("Temperatur in °C")

titel = f"Wettertrend für Koordinaten {lat} / {lon}"
if max_temp_gesamt is not None and min_temp_gesamt is not None:
    titel += f" (max {max_temp_gesamt:.1f}°C / min {min_temp_gesamt:.1f}°C)"
plt.title(titel)

plt.grid(True, alpha=0.3)
plt.legend()

# nicht starr auf 48 Stunden begrenzen
if len(df) > 1:
    plt.xlim(0, min(48, len(df) - 1))

plt.tight_layout()
plt.show()