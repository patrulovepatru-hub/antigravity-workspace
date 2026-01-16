#!/usr/bin/env python3
"""
SISTEMA AUTÓNOMO DE GENERACIÓN DE NEGOCIOS ONLINE
Version: 2.0 - Multi-país + Trending Detection
Hardware optimizado: AMD 9800X3D + 64GB RAM
"""

import os
import sys
import json
import time
import requests
import subprocess
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()


class TrendingDetector:
    """Detector de productos trending"""
    
    def get_top_opportunities(self):
        """Productos con alto potencial de conversión"""
        # Simulación - en v2.1 integraremos APIs reales
        trending = [
            {"name": "ai writing assistant", "score": 95, "cpc": 4.5},
            {"name": "standing desk converter", "score": 92, "cpc": 3.8},
            {"name": "mechanical keyboard wireless", "score": 89, "cpc": 3.2},
            {"name": "noise cancelling earbuds", "score": 87, "cpc": 4.1},
            {"name": "portable monitor", "score": 85, "cpc": 3.6}
        ]
        return trending


class AutonomousEngine:
    """Motor principal del sistema autónomo - v2.0"""
    
    def __init__(self):
        self.version = "2.0.0"
        self.base_path = Path.home() / "autonomous-business"
        self.sites_path = self.base_path / "sites"
        self.logs_path = self.base_path / "logs"
        self.data_path = self.base_path / "data"
        
        # Crear directorios
        for path in [self.sites_path, self.logs_path, self.data_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Cargar credenciales
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.cloudflare_token = os.getenv("CLOUDFLARE_API_TOKEN")
        
        # Amazon Associate Tags (multi-país)
        self.amazon_tags = {
            "com": os.getenv("AMAZON_ASSOCIATE_TAG_COM", ""),
            "uk": os.getenv("AMAZON_ASSOCIATE_TAG_UK", ""),
            "es": os.getenv("AMAZON_ASSOCIATE_TAG_ES", ""),
            "it": os.getenv("AMAZON_ASSOCIATE_TAG_IT", ""),
            "fr": os.getenv("AMAZON_ASSOCIATE_TAG_FR", ""),
            "de": os.getenv("AMAZON_ASSOCIATE_TAG_DE", "")
        }
        
        # Validar credenciales
        self._validate_credentials()
        
        # Configuración
        self.content_language = os.getenv("CONTENT_LANGUAGE", "en")
        self.target_sites_per_day = int(os.getenv("TARGET_SITES_PER_DAY", 3))
        
        # Trending detector
        self.trending = TrendingDetector()
        
        # Nichos base + trending
        self.base_niches = [
            {
                "name": "ai_productivity_tools",
                "keywords": ["ai tools", "productivity software", "automation"],
                "cpc": 3.8,
                "products": ["ai writing tools", "task management apps", "note taking software"]
            },
            {
                "name": "remote_work_gadgets",
                "keywords": ["remote work", "home office", "ergonomic"],
                "cpc": 3.2,
                "products": ["webcams", "microphones", "ergonomic chairs"]
            },
            {
                "name": "smart_home_devices",
                "keywords": ["smart home", "iot devices", "home automation"],
                "cpc": 2.9,
                "products": ["smart lights", "security cameras", "smart plugs"]
            },
            {
                "name": "fitness_tech",
                "keywords": ["fitness tracker", "smart watch", "health tech"],
                "cpc": 3.5,
                "products": ["fitness trackers", "smart scales", "heart rate monitors"]
            },
            {
                "name": "gaming_peripherals",
                "keywords": ["gaming mouse", "mechanical keyboard", "gaming headset"],
                "cpc": 2.7,
                "products": ["gaming mice", "keyboards", "headsets"]
            }
        ]
        
        self.log_file = self.logs_path / "system.log"
        self.metrics_file = self.data_path / "metrics.json"
        
        self.log(f"✅ Sistema iniciado - Version {self.version}")
    
    def _validate_credentials(self):
        """Validar credenciales necesarias"""
        required = {
            "ANTHROPIC_API_KEY": self.anthropic_key,
            "GITHUB_TOKEN": self.github_token,
            "CLOUDFLARE_API_TOKEN": self.cloudflare_token
        }
        
        missing = [k for k, v in required.items() if not v]
        
        if missing:
            print("❌ ERROR: Faltan credenciales críticas:")
            for cred in missing:
                print(f"   - {cred}")
            print("\n💡 Edita el archivo .env con tus credenciales")
            sys.exit(1)
        
        # Verificar Amazon tags
        if not any(self.amazon_tags.values()):
            print("⚠️ WARNING: No Amazon Associate tags configured")
    
    def log(self, message: str, level: str = "INFO"):
        """Logging con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        print(log_entry)
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    
    def call_claude(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        """Llamar a Claude API"""
        self.log("🤖 Llamando a Claude API...")
        
        headers = {
            "x-api-key": self.anthropic_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": max_tokens,
            "messages": [{
                "role": "user",
                "content": prompt
            }]
        }
        
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                content = response.json()["content"][0]["text"]
                self.log("✅ Respuesta recibida de Claude")
                return content
            else:
                self.log(f"❌ Error API Claude: {response.status_code} - {response.text}", level="ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Excepción: {e}", level="ERROR")
            return None
    
    def select_smart_niche(self):
        """Seleccionar nicho inteligentemente (base o trending)"""
        
        # 70% base niches, 30% trending
        if random.random() < 0.7:
            niche = random.choice(self.base_niches)
            self.log(f"📊 Nicho seleccionado (base): {niche['name']}")
        else:
            # Trending product
            opportunities = self.trending.get_top_opportunities()
            if opportunities:
                top = opportunities[0]
                niche = {
                    "name": f"trending_{top['name'].replace(' ', '_')}",
                    "keywords": [top['name']],
                    "cpc": top['cpc'],
                    "products": [top['name']],
                    "trending": True
                }
                self.log(f"🔥 Nicho seleccionado (trending): {niche['name']} (score: {top['score']})")
            else:
                niche = random.choice(self.base_niches)
        
        return niche
    
    def generate_business_plan(self, niche: Dict) -> Optional[Dict]:
        """Generar plan de negocio"""
        self.log(f"📋 Generando plan: {niche['name']}")
        
        trending_note = " This is a TRENDING product with high demand right now!" if niche.get('trending') else ""
        
        prompt = f"""You are an expert in online business creation. Generate a detailed business plan for a niche affiliate website.

Niche: {niche['name']}
Target Keywords: {', '.join(niche['keywords'])}
Average CPC: ${niche['cpc']}
Product Categories: {', '.join(niche['products'])}
{trending_note}

Create a business plan in JSON format with this exact structure:
{{
  "site_name": "short-domain-friendly-name",
  "tagline": "compelling tagline under 60 chars",
  "target_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "content_pillars": ["pillar1", "pillar2", "pillar3"],
  "top_products": ["product1", "product2", "product3", "product4", "product5"],
  "traffic_strategy": "specific SEO and content strategy",
  "monetization_focus": "affiliate links placement strategy",
  "estimated_monthly_revenue_month3": 500
}}

Requirements:
- Site name must be catchy, SEO-friendly
- Keywords must have commercial intent
- Products must be available on Amazon
- Be specific and actionable

Respond ONLY with valid JSON, no explanations."""

        response = self.call_claude(prompt, max_tokens=1500)
        
        if not response:
            return None
        
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
            plan = json.loads(json_str)
            
            self.log(f"✅ Plan generado: {plan['site_name']}")
            return plan
            
        except json.JSONDecodeError as e:
            self.log(f"❌ Error parseando JSON: {e}", level="ERROR")
            return None
    
    def generate_html_content(self, plan: Dict) -> str:
        """Generar HTML con geo-targeting multi-país"""
        self.log(f"✍️ Generando HTML para {plan['site_name']}")
        
        # Preparar productos con keywords únicas
        products_info = []
        for i, product in enumerate(plan['top_products'][:5], 1):
            keyword = product.lower().replace(' ', '+').replace('&', 'and')
            if i > 1:
                keyword = f"{keyword}+{plan['target_keywords'][min(i-1, len(plan['target_keywords'])-1)].replace(' ', '+')}"
            
            products_info.append({
                'name': product,
                'keyword': keyword,
                'id': f'product{i}'
            })
        
        products_list = '\n'.join([f"- Product {i}: {p['name']} → Amazon search: {p['keyword']}" for i, p in enumerate(products_info, 1)])
        
        # Estilos aleatorios para diversificación
        styles = [
            "modern minimalist with lots of white space and blue accents",
            "dark mode with neon highlights and gradients",
            "corporate professional with grays and navy blue",
            "vibrant and colorful with rounded corners",
            "elegant luxury with gold accents and serif fonts"
        ]
        chosen_style = random.choice(styles)
        
        prompt = f"""Create a complete, professional HTML page for this affiliate website:

Site Name: {plan['site_name']}
Tagline: {plan['tagline']}
Keywords: {', '.join(plan['target_keywords'])}

Products to feature (use EXACT search keywords in links):
{products_list}

Amazon Affiliate Configuration - GEO-TARGETING:
Create a JavaScript function that detects the visitor's country and redirects to the appropriate Amazon store:
- US visitors → amazon.com (tag: {self.amazon_tags['com']})
- UK visitors → amazon.co.uk (tag: {self.amazon_tags['uk']})
- Spanish visitors → amazon.es (tag: {self.amazon_tags['es']})
- Italian visitors → amazon.it (tag: {self.amazon_tags['it']})
- French visitors → amazon.fr (tag: {self.amazon_tags['fr']})
- German visitors → amazon.de (tag: {self.amazon_tags['de']})

Requirements:
1. Complete HTML5 structure with modern, responsive CSS
2. Include a hero section with the tagline
3. Product showcase section with the 5 products listed above
4. JavaScript geo-targeting function in <head>:
   <script>
   function getAmazonLink(keyword) {{
     const locale = navigator.language.toLowerCase();
     const country = locale.split('-')[1] || 'us';
     const stores = {{
       'us': {{domain: 'amazon.com', tag: '{self.amazon_tags["com"]}'}},
       'gb': {{domain: 'amazon.co.uk', tag: '{self.amazon_tags["uk"]}'}},
       'es': {{domain: 'amazon.es', tag: '{self.amazon_tags["es"]}'}},
       'it': {{domain: 'amazon.it', tag: '{self.amazon_tags["it"]}'}},
       'fr': {{domain: 'amazon.fr', tag: '{self.amazon_tags["fr"]}'}},
       'de': {{domain: 'amazon.de', tag: '{self.amazon_tags["de"]}'}}
     }};
     const store = stores[country] || stores['us'];
     return `https://${{store.domain}}/s?k=${{keyword}}&tag=${{store.tag}}`;
   }}
   </script>
5. Use onclick: onclick="window.open(getAmazonLink('KEYWORD'), '_blank')"
6. SEO meta tags (title, description, keywords)
7. Navigation menu
8. Footer with Amazon affiliate disclaimer (mention all 6 countries)
9. Inline CSS only
10. Mobile-responsive with {chosen_style} aesthetic
11. Professional color scheme
12. Call-to-action buttons ("Check Price", "View on Amazon")
13. Product descriptions (2-3 sentences each)

Write ONLY the HTML code, no explanations. Production-ready."""

        html = self.call_claude(prompt, max_tokens=4000)
        
        if html and "<!DOCTYPE html>" in html:
            html = html.replace("```html", "").replace("```", "").strip()
            self.log("✅ HTML generado con geo-targeting")
            return html
        else:
            self.log("❌ Error: HTML inválido", level="ERROR")
            return None
    
    def create_site(self, plan: Dict) -> Optional[Path]:
        """Crear sitio completo"""
        site_name = plan['site_name'].lower().replace(" ", "-")
        site_path = self.sites_path / site_name
        
        if site_path.exists():
            self.log(f"⚠️ Sitio {site_name} ya existe", level="WARNING")
            return None
        
        site_path.mkdir(parents=True, exist_ok=True)
        self.log(f"📁 Creando sitio: {site_path}")
        
        # Generar HTML
        html_content = self.generate_html_content(plan)
        if not html_content:
            return None
        
        # Guardar index.html
        (site_path / "index.html").write_text(html_content, encoding="utf-8")
        
        # robots.txt
        robots = f"""User-agent: *
Allow: /
Sitemap: https://{site_name}.pages.dev/sitemap.xml

User-agent: Googlebot
Allow: /"""
        (site_path / "robots.txt").write_text(robots, encoding="utf-8")
        
        # README
        readme = f"""# {plan['site_name']}

## Info
- **Tagline**: {plan['tagline']}
- **Keywords**: {', '.join(plan['target_keywords'])}
- **Productos**: {', '.join(plan['top_products'])}
- **Creado**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Version**: {self.version}

## Estrategia
- **Monetización**: {plan['monetization_focus']}
- **Tráfico**: {plan['traffic_strategy']}
- **Revenue estimado (mes 3)**: ${plan['estimated_monthly_revenue_month3']}

## Deployment
```bash
wrangler pages deploy . --project-name={site_name}
```

## URL
https://{site_name}.pages.dev

## Amazon Tags (6 países)
- US: {self.amazon_tags['com']}
- UK: {self.amazon_tags['uk']}
- ES: {self.amazon_tags['es']}
- IT: {self.amazon_tags['it']}
- FR: {self.amazon_tags['fr']}
- DE: {self.amazon_tags['de']}
"""
        (site_path / "README.md").write_text(readme, encoding="utf-8")
        
        self.log(f"✅ Sitio {site_name} creado")
        return site_path
    
    def deploy_to_cloudflare(self, site_path: Path, site_name: str) -> Optional[str]:
        """Deploy a Cloudflare Pages"""
        self.log(f"☁️ Desplegando {site_name}...")
        
        try:
            # Verificar wrangler
            subprocess.run(["wrangler", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("❌ Wrangler no instalado", level="ERROR")
            self.log(f"💡 Deploy manual: cd {site_path} && wrangler pages deploy .")
            return None
        
        try:
            os.environ["CLOUDFLARE_API_TOKEN"] = self.cloudflare_token
            
            cmd = [
                "wrangler", "pages", "deploy", str(site_path),
                "--project-name", site_name,
                "--branch", "main"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=site_path)
            
            if result.returncode == 0:
                url = f"https://{site_name}.pages.dev"
                self.log(f"✅ Deployado: {url}")
                return url
            else:
                self.log(f"⚠️ Error deployment: {result.stderr}", level="WARNING")
                self.log(f"💡 Manual: cd {site_path} && wrangler pages deploy .")
                return None
                
        except Exception as e:
            self.log(f"❌ Excepción deployment: {e}", level="ERROR")
            return None
    
    def save_metrics(self, site_name: str, plan: Dict, url: Optional[str]):
        """Guardar métricas"""
        metrics = {
            "site_name": site_name,
            "url": url or "pending",
            "created_at": datetime.now().isoformat(),
            "niche": plan.get('niche', 'unknown'),
            "keywords": plan['target_keywords'],
            "estimated_revenue": plan['estimated_monthly_revenue_month3'],
            "status": "deployed" if url else "local",
            "version": self.version,
            "trending": plan.get('trending', False)
        }
        
        if self.metrics_file.exists():
            with open(self.metrics_file, "r") as f:
                all_metrics = json.load(f)
        else:
            all_metrics = []
        
        all_metrics.append(metrics)
        
        with open(self.metrics_file, "w") as f:
            json.dump(all_metrics, f, indent=2, ensure_ascii=False)
        
        self.log(f"📊 Métricas guardadas: {len(all_metrics)} sitios totales")
    
    def build_business(self, niche: Dict) -> bool:
        """Pipeline completo"""
        self.log("\n" + "="*60)
        self.log(f"🚀 NUEVO NEGOCIO: {niche['name']}")
        self.log("="*60 + "\n")
        
        try:
            # 1. Plan
            plan = self.generate_business_plan(niche)
            if not plan:
                return False
            
            plan['niche'] = niche['name']
            plan['trending'] = niche.get('trending', False)
            
            # 2. Crear
            site_path = self.create_site(plan)
            if not site_path:
                return False
            
            site_name = plan['site_name'].lower().replace(" ", "-")
            
            # 3. Deploy
            url = self.deploy_to_cloudflare(site_path, site_name)
            
            # 4. Métricas
            self.save_metrics(site_name, plan, url)
            
            self.log("\n" + "="*60)
            self.log(f"✅ COMPLETADO: {site_name.upper()}")
            if url:
                self.log(f"🌐 URL: {url}")
            else:
                self.log(f"📁 Local: {site_path}")
            self.log("="*60 + "\n")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error: {e}", level="ERROR")
            return False
    
    def run_autonomous(self, interval_hours: float = 8):
        """Modo autónomo"""
        self.log("\n" + "🚀"*30)
        self.log(f"SISTEMA AUTÓNOMO v{self.version} INICIADO")
        self.log("🚀"*30 + "\n")
        self.log(f"⚙️ Configuración:")
        self.log(f"   - Idioma: {self.content_language}")
        self.log(f"   - Sitios/día objetivo: {self.target_sites_per_day}")
        self.log(f"   - Intervalo: {interval_hours}h")
        self.log(f"   - Amazon países: {len([t for t in self.amazon_tags.values() if t])}")
        self.log("")
        
        sites_created = 0
        
        while True:
            try:
                # Selección inteligente de nicho
                niche = self.select_smart_niche()
                
                # Pipeline
                success = self.build_business(niche)
                
                if success:
                    sites_created += 1
                    self.log(f"\n💰 PROGRESO: {sites_created} sitios creados")
                    self.log(f"⏳ Próximo en: {interval_hours}h\n")
                    time.sleep(interval_hours * 3600)
                else:
                    self.log("⚠️ Error. Reintento en 30min", level="WARNING")
                    time.sleep(1800)
                    
            except KeyboardInterrupt:
                self.log(f"\n🛑 Detenido. Total: {sites_created} sitios")
                break
            except Exception as e:
                self.log(f"❌ Error crítico: {e}", level="ERROR")
                time.sleep(3600)


def main():
    """Punto de entrada"""
    print("\n" + "="*60)
    print("  AUTONOMOUS BUSINESS SYSTEM v2.0")
    print("  Multi-país + Trending Detection")
    print("="*60 + "\n")
    
    engine = AutonomousEngine()
    
    print("✅ Motor inicializado\n")
    print("Modo de operación:")
    print("  1) Crear UN sitio de prueba")
    print("  2) Modo AUTÓNOMO")
    print("  3) Crear 5 sitios AHORA (batch)")
    print("  4) Salir")
    
    choice = input("\nOpción (1/2/3/4): ").strip()
    
    if choice == "1":
        niche = engine.select_smart_niche()
        print(f"\n🧪 Creando sitio: {niche['name']}\n")
        engine.build_business(niche)
        
    elif choice == "2":
        interval = input("\nHoras entre sitios (default: 8): ").strip()
        interval = float(interval) if interval else 8.0
        print(f"\n🤖 Modo autónomo (intervalo: {interval}h)")
        print("💡 Ctrl+C para detener\n")
        time.sleep(2)
        engine.run_autonomous(interval_hours=interval)
        
    elif choice == "3":
        print("\n🚀 Creando 5 sitios en batch...\n")
        for i in range(5):
            niche = engine.select_smart_niche()
            print(f"\n[{i+1}/5] Creando {niche['name']}...")
            engine.build_business(niche)
            if i < 4:
                print("\n⏳ Esperando 2 minutos...")
                time.sleep(120)
        print("\n✅ Batch completado!")
        
    else:
        print("\n👋 Saliendo...")


if __name__ == "__main__":
    main()
