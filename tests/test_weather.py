"""Testes do servico meteorologico sem acesso a rede."""

import unittest

from app.services.weather import (
    FORECAST_URL,
    GEOCODING_URL,
    WeatherService,
)


class FakeHttpClient:
    """Simula geocodificacao e clima sem depender da internet."""

    def __init__(self, geocoding_results=None) -> None:
        """Permite substituir os resultados de geocodificacao por teste."""
        self.geocoding_results = geocoding_results
        self.calls = []

    def get_json(self, url, params, timeout):
        """Retorna payload conforme o endpoint solicitado e registra a chamada."""
        self.calls.append((url, params, timeout))
        if url == GEOCODING_URL:
            return {
                "results": self.geocoding_results
                if self.geocoding_results is not None
                else [
                    {
                        "name": "Sao Paulo",
                        "admin1": "Sao Paulo",
                        "country": "Brasil",
                        "country_code": "BR",
                        "latitude": -23.55,
                        "longitude": -46.63,
                        "timezone": "America/Sao_Paulo",
                    }
                ]
            }
        if url == FORECAST_URL:
            return {
                "current": {
                    "time": "2026-06-07T10:00",
                    "temperature_2m": 21.5,
                    "apparent_temperature": 21.0,
                    "relative_humidity_2m": 65,
                    "precipitation": 0.0,
                    "weather_code": 2,
                    "wind_speed_10m": 8.5,
                }
            }
        raise AssertionError(f"URL inesperada: {url}")


class WeatherServiceTests(unittest.TestCase):
    """Valida normalizacao meteorologica e tratamento de cidades ausentes."""

    def test_returns_current_weather(self) -> None:
        """Uma cidade valida deve produzir todos os indicadores atuais."""
        http_client = FakeHttpClient()
        service = WeatherService(http_client=http_client)

        result = service.get_current_weather("Sao Paulo", "br")

        self.assertTrue(result["ok"])
        self.assertEqual(result["location"]["country_code"], "BR")
        self.assertEqual(result["current"]["Condicao"], "Parcialmente nublado")
        self.assertEqual(result["current"]["TemperaturaC"], 21.5)
        self.assertEqual(len(http_client.calls), 2)
        self.assertEqual(
            http_client.calls[0][1]["countryCode"],
            "BR",
        )

    def test_rejects_unknown_city(self) -> None:
        """Geocodificacao vazia deve resultar em erro claro para o usuario."""
        service = WeatherService(
            http_client=FakeHttpClient(geocoding_results=[]),
        )

        with self.assertRaisesRegex(ValueError, "Cidade nao encontrada"):
            service.get_current_weather("Cidade inexistente")

if __name__ == "__main__":
    unittest.main()
