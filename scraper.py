import os
import requests
import pandas as pd
from datetime import datetime

API_KEY = os.getenv('GOOGLE_API_KEY')
HISTORY_FILE = 'seen_places.txt'
TARGET_COUNT = 100

QUERIES = [
    "perusahaan baja di Jakarta", "konstruksi baja di Jakarta",
    "perusahaan baja di Bogor", "kontraktor konstruksi di Bogor",
    "perusahaan baja di Depok", "baja ringan dan berat di Depok",
    "perusahaan baja di Tangerang", "pabrik baja di Tangerang",
    "perusahaan baja di Bekasi", "konstruksi baja di Bekasi",
    "distributor besi dan baja Jabodetabek", "bengkel konstruksi baja Jabodetabek"
]

def load_seen_places():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return set(line.strip() for line in f.readlines())
    return set()

def save_seen_place(place_id):
    with open(HISTORY_FILE, 'a') as f:
        f.write(f"{place_id}\n")

def build_photo_url(photo_name):
    if not photo_name:
        return "Tidak ada foto"
    return f"https://places.googleapis.com/v1/{photo_name}/media?maxHeightPx=400&maxWidthPx=400&key={API_KEY}"

def main():
    if not API_KEY:
        print("Error: GOOGLE_API_KEY belum disetel.")
        return

    seen_places = load_seen_places()
    extracted_data = []
    
    search_url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'places.id,places.displayName,places.nationalPhoneNumber,places.formattedAddress,places.rating,places.websiteUri,places.googleMapsUri,places.photos'
    }
    
    print(f"Memulai pengambilan data dengan API Baru... Telah mengambil {len(seen_places)} data sebelumnya.")

    for query in QUERIES:
        if len(extracted_data) >= TARGET_COUNT:
            break
            
        print(f"\nMencari dengan query: {query}")
        
        payload = {
            "textQuery": query,
            "pageSize": 20
        }
        
        try:
            response = requests.post(search_url, json=payload, headers=headers)
            
            if response.status_code != 200:
                print(f"  -> Error dari Google: {response.status_code}")
                print(f"  -> Detail: {response.text}")
                continue
                
            data = response.json()
            places = data.get('places', [])
            
            if not places:
                print("  -> Tidak ada hasil untuk query ini.")
                continue
            
            for place in places:
                if len(extracted_data) >= TARGET_COUNT:
                    break
                    
                place_id = place.get('id')
                if not place_id or place_id in seen_places:
                    continue
                    
                # Ekstrak data
                name = place.get('displayName', {}).get('text', 'Tidak ada nama')
                phone = place.get('nationalPhoneNumber', 'Tidak ada telepon')
                address = place.get('formattedAddress', 'Tidak ada alamat')
                rating = place.get('rating', 'Tidak ada rating')
                website = place.get('websiteUri', 'Tidak ada website')
                maps_link = place.get('googleMapsUri', 'Tidak ada link maps')
                
                # Cek foto
                photos = place.get('photos', [])
                photo_url = "Tidak ada foto"
                if photos:
                    photo_name = photos[0].get('name')
                    photo_url = build_photo_url(photo_name)
                
                extracted_data.append({
                    "Nama Perusahaan": name,
                    "Telepon / WA": phone,
                    "Email": "Cek di website",
                    "Alamat": address,
                    "Rating": rating,
                    "Website": website,
                    "Link Maps": maps_link,
                    "Foto": photo_url
                })
                
                seen_places.add(place_id)
                save_seen_place(place_id)
                
            print(f"  -> Berhasil mendapat tambahan {len(places)} data dari query ini. Total terkumpul: {len(extracted_data)}")
            
        except Exception as e:
            print(f"  -> Terjadi kesalahan saat memproses query {query}: {e}")

    if extracted_data:
        df = pd.DataFrame(extracted_data)
        today_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"Data_Baja_Konstruksi_{today_str}.xlsx"
        
        df.to_excel(filename, index=False)
        print(f"\nSELESAI! Berhasil menyimpan {len(extracted_data)} data baru ke {filename}.")
    else:
        print("\nTidak ada data baru yang ditemukan hari ini.")

if __name__ == "__main__":
    main()