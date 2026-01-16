"""
Real-Debrid Automation Tool
Convierte torrents/magnets en descargas directas a máxima velocidad
"""

import requests
import time
import os
import sys
from pathlib import Path

class RealDebrid:
    BASE_URL = "https://api.real-debrid.com/rest/1.0"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def check_auth(self) -> dict:
        """Verifica que la API key sea válida"""
        r = requests.get(f"{self.BASE_URL}/user", headers=self.headers)
        r.raise_for_status()
        return r.json()
    
    def add_torrent_file(self, torrent_path: str) -> str:
        """Sube un archivo .torrent y retorna el ID"""
        with open(torrent_path, 'rb') as f:
            r = requests.put(
                f"{self.BASE_URL}/torrents/addTorrent",
                headers=self.headers,
                files={'file': f}
            )
        r.raise_for_status()
        return r.json()['id']
    
    def add_magnet(self, magnet_link: str) -> str:
        """Añade un magnet link y retorna el ID"""
        r = requests.post(
            f"{self.BASE_URL}/torrents/addMagnet",
            headers=self.headers,
            data={'magnet': magnet_link}
        )
        r.raise_for_status()
        return r.json()['id']
    
    def select_files(self, torrent_id: str, files: str = "all"):
        """Selecciona los archivos a descargar (por defecto todos)"""
        r = requests.post(
            f"{self.BASE_URL}/torrents/selectFiles/{torrent_id}",
            headers=self.headers,
            data={'files': files}
        )
        r.raise_for_status()
    
    def get_torrent_info(self, torrent_id: str) -> dict:
        """Obtiene información del torrent"""
        r = requests.get(
            f"{self.BASE_URL}/torrents/info/{torrent_id}",
            headers=self.headers
        )
        r.raise_for_status()
        return r.json()
    
    def unrestrict_link(self, link: str) -> dict:
        """Convierte un link en descarga directa premium"""
        r = requests.post(
            f"{self.BASE_URL}/unrestrict/link",
            headers=self.headers,
            data={'link': link}
        )
        r.raise_for_status()
        return r.json()
    
    def wait_for_download(self, torrent_id: str, timeout: int = 300) -> dict:
        """Espera a que Real-Debrid descargue el torrent"""
        start = time.time()
        while time.time() - start < timeout:
            info = self.get_torrent_info(torrent_id)
            status = info.get('status')
            progress = info.get('progress', 0)
            
            print(f"\r[...] Estado: {status} | Progreso: {progress}%", end="", flush=True)
            
            if status == 'downloaded':
                print("\n[OK] Descarga completada en Real-Debrid!")
                return info
            elif status == 'error' or status == 'dead':
                raise Exception(f"Error en torrent: {status}")
            
            time.sleep(2)
        
        raise TimeoutError("Timeout esperando descarga")
    
    def process_torrent(self, source: str) -> list:
        """
        Procesa un torrent (archivo o magnet) y retorna enlaces directos
        """
        # Detectar si es archivo o magnet
        if source.startswith('magnet:'):
            print(f"[MAGNET] Anadiendo magnet link...")
            torrent_id = self.add_magnet(source)
        elif os.path.exists(source):
            print(f"[FILE] Subiendo archivo: {Path(source).name}")
            torrent_id = self.add_torrent_file(source)
        else:
            raise ValueError("Debe ser un magnet link o ruta a archivo .torrent")
        
        print(f"[INFO] Torrent ID: {torrent_id}")
        
        # Seleccionar todos los archivos
        print("[...] Seleccionando archivos...")
        self.select_files(torrent_id)
        
        # Esperar descarga en Real-Debrid
        info = self.wait_for_download(torrent_id)
        
        # Obtener enlaces directos
        direct_links = []
        for link in info.get('links', []):
            print(f"[UNLOCK] Desbloqueando: {link[:50]}...")
            unrestricted = self.unrestrict_link(link)
            direct_links.append({
                'filename': unrestricted.get('filename'),
                'filesize': unrestricted.get('filesize'),
                'download': unrestricted.get('download'),
                'streamable': unrestricted.get('streamable', False)
            })
        
        return direct_links


def format_size(size_bytes: int) -> str:
    """Formatea bytes a unidad legible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def main():
    print("""
============================================================
           REAL-DEBRID AUTOMATION TOOL
      Convierte torrents en descargas directas
============================================================
    """)
    
    # Cargar API key desde variable de entorno o archivo
    api_key = os.environ.get('REAL_DEBRID_API_KEY')
    
    config_file = Path(__file__).parent / '.api_key'
    if not api_key and config_file.exists():
        api_key = config_file.read_text().strip()
    
    if not api_key:
        print("[!] No se encontro API key de Real-Debrid")
        print("[i] Obten tu API key en: https://real-debrid.com/apitoken")
        api_key = input("\n[KEY] Introduce tu API key: ").strip()
        
        # Guardar para futuras ejecuciones
        save = input("[?] Guardar API key para el futuro? (s/n): ").lower()
        if save == 's':
            config_file.write_text(api_key)
            print(f"[OK] API key guardada en: {config_file}")
    
    # Inicializar cliente
    rd = RealDebrid(api_key)
    
    # Verificar autenticación
    try:
        user = rd.check_auth()
        print(f"\n[USER] Usuario: {user.get('username')}")
        print(f"[TIME] Premium hasta: {user.get('expiration')}")
        print(f"[PTS] Puntos: {user.get('points')}")
    except Exception as e:
        print(f"[ERROR] Error de autenticacion: {e}")
        sys.exit(1)
    
    # Obtener torrent/magnet
    if len(sys.argv) > 1:
        source = sys.argv[1]
    else:
        print("\n" + "="*50)
        source = input("[>] Introduce ruta a .torrent o magnet link:\n> ").strip()
    
    if not source:
        print("[ERROR] No se proporciono ningun torrent/magnet")
        sys.exit(1)
    
    # Procesar
    try:
        print("\n" + "="*50)
        links = rd.process_torrent(source)
        
        print("\n" + "="*50)
        print("[SUCCESS] ENLACES DIRECTOS LISTOS!")
        print("="*50 + "\n")
        
        for i, link in enumerate(links, 1):
            print(f"[FILE] Archivo {i}: {link['filename']}")
            print(f"   [SIZE] Tamano: {format_size(link['filesize'])}")
            print(f"   [STREAM] Streamable: {'Si' if link['streamable'] else 'No'}")
            print(f"   [LINK] Enlace:")
            print(f"   {link['download']}")
            print()
        
        # Copiar al portapapeles si hay un solo enlace
        if len(links) == 1:
            try:
                import pyperclip
                pyperclip.copy(links[0]['download'])
                print("[COPY] Enlace copiado al portapapeles!")
            except:
                pass
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
