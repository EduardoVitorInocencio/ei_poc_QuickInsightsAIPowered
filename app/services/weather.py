"""Consulta de condicoes meteorologicas atuais por cidade.

O servico usa duas APIs da Open-Meteo: geocodificacao para resolver a cidade e
forecast para obter as condicoes atuais. Nenhuma chave adicional e necessaria.
"""

import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Traduz os codigos WMO retornados pela Open-Meteo para texto em portugues.
WEATHER_DESCRIPTIONS = {
    0: "Ceu limpo",
    1: "Predominantemente limpo",
    2: "Parcialmente nublado",
    3: "Nublado",
    45: "Nevoeiro",
    48: "Nevoeiro com geada",
    51: "Garoa leve",
    53: "Garoa moderada",
    55: "Garoa intensa",
    56: "Garoa congelante leve",
    57: "Garoa congelante intensa",
    61: "Chuva leve",
    63: "Chuva moderada",
    65: "Chuva forte",
    66: "Chuva congelante leve",
    67: "Chuva congelante forte",
    71: "Neve leve",
    73: "Neve moderada",
    75: "Neve forte",
    77: "Graos de neve",
    80: "Pancadas de chuva leves",
    81: "Pancadas de chuva moderadas",
    82: "Pancadas de chuva fortes",
    85: "Pancadas de neve leves",
    86: "Pancadas de neve fortes",
    95: "Trovoada",
    96: "Trovoada com granizo leve",
    99: "Trovoada com granizo forte",
}


class JsonHttpClient(Protocol):
    """Contrato minimo que permite substituir HTTP real por fakes nos testes."""

    def get_json(
        self,
        url: str,
        params: dict[str, Any],
        timeout: float,
    ) -> dict[str, Any]:
        """Executa GET e retorna um objeto JSON.

        Args:
            url: Endpoint HTTP.
            params: Parametros que serao codificados na query string.
            timeout: Limite da requisicao em segundos.

        Returns:
            Objeto JSON desserializado.
        """


class UrllibJsonHttpClient:
    """Cliente HTTP JSON baseado somente na biblioteca padrao."""

    def get_json(
        self,
        url: str,
        params: dict[str, Any],
        timeout: float,
    ) -> dict[str, Any]:
        """Executa a requisicao e converte falhas em erros de dominio claros.

        Raises:
            RuntimeError: Em erro HTTP, conexao indisponivel ou JSON invalido.
        """
        request = Request(
            f"{url}?{urlencode(params)}",
            headers={"User-Agent": "quick-insights-weather/1.0"},
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            raise RuntimeError(
                f"Servico meteorologico retornou HTTP {error.code}."
            ) from error
        except URLError as error:
            raise RuntimeError(
                "Nao foi possivel conectar ao servico meteorologico."
            ) from error
        except json.JSONDecodeError as error:
            raise RuntimeError(
                "O servico meteorologico retornou uma resposta invalida."
            ) from error


@dataclass(frozen=True)
class Location:
    """Localidade normalizada retornada pela geocodificacao."""

    name: str
    region: str
    country: str
    country_code: str
    latitude: float
    longitude: float
    timezone: str

    @property
    def display_name(self) -> str:
        """Combina cidade, regiao e pais omitindo campos vazios."""
        parts = [self.name, self.region, self.country]
        return ", ".join(part for part in parts if part)


class WeatherService:
    """Coordena geocodificacao e consulta das condicoes atuais."""

    def __init__(
        self,
        http_client: JsonHttpClient | None = None,
        timeout: float = 10.0,
    ) -> None:
        """Configura cliente HTTP e timeout.

        Args:
            http_client: Implementacao injetavel; usa urllib por padrao.
            timeout: Limite em segundos para cada chamada externa.
        """
        self._http_client = http_client or UrllibJsonHttpClient()
        self._timeout = timeout

    def get_current_weather(
        self,
        city: str,
        country_code: str | None = None,
    ) -> dict[str, Any]:
        """Resolve uma cidade e retorna suas condicoes atuais.

        Args:
            city: Nome da cidade informado pelo usuario.
            country_code: Codigo ISO de duas letras para desambiguacao.

        Returns:
            Status, localizacao normalizada, condicoes atuais e fonte.

        Raises:
            ValueError: Se a cidade for curta demais ou nao for encontrada.
            RuntimeError: Se a API externa estiver indisponivel ou invalida.
        """
        normalized_city = city.strip()
        if len(normalized_city) < 2:
            raise ValueError("Informe uma cidade com pelo menos 2 caracteres.")

        location = self._find_location(normalized_city, country_code)
        weather = self._fetch_current_weather(location)

        return {
            "ok": True,
            "location": {
                "name": location.name,
                "region": location.region,
                "country": location.country,
                "country_code": location.country_code,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "timezone": location.timezone,
            },
            "current": weather,
            "source": "Open-Meteo",
        }

    def _find_location(
        self,
        city: str,
        country_code: str | None,
    ) -> Location:
        """Consulta a geocodificacao e escolhe o primeiro resultado."""
        params: dict[str, Any] = {
            "name": city,
            "count": 1,
            "language": "pt",
            "format": "json",
        }
        if country_code:
            params["countryCode"] = country_code.strip().upper()

        payload = self._http_client.get_json(
            GEOCODING_URL,
            params,
            self._timeout,
        )
        results = payload.get("results") or []
        if not results:
            suffix = f" ({country_code.upper()})" if country_code else ""
            raise ValueError(f"Cidade nao encontrada: {city}{suffix}")

        result = results[0]
        return Location(
            name=str(result["name"]),
            region=str(result.get("admin1", "")),
            country=str(result.get("country", "")),
            country_code=str(result.get("country_code", "")),
            latitude=float(result["latitude"]),
            longitude=float(result["longitude"]),
            timezone=str(result.get("timezone", "auto")),
        )

    def _fetch_current_weather(self, location: Location) -> dict[str, Any]:
        """Consulta e normaliza os indicadores meteorologicos atuais."""
        payload = self._http_client.get_json(
            FORECAST_URL,
            {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "current": (
                    "temperature_2m,apparent_temperature,"
                    "relative_humidity_2m,precipitation,"
                    "weather_code,wind_speed_10m"
                ),
                "timezone": location.timezone or "auto",
            },
            self._timeout,
        )
        current = payload.get("current")
        if not isinstance(current, dict):
            raise RuntimeError(
                "O servico meteorologico nao retornou condicoes atuais."
            )

        weather_code = int(current.get("weather_code", -1))
        return {
            "Local": location.display_name,
            "DataHora": current.get("time", ""),
            "Condicao": WEATHER_DESCRIPTIONS.get(
                weather_code,
                f"Codigo meteorologico {weather_code}",
            ),
            "TemperaturaC": current.get("temperature_2m"),
            "SensacaoC": current.get("apparent_temperature"),
            "UmidadePct": current.get("relative_humidity_2m"),
            "PrecipitacaoMm": current.get("precipitation"),
            "VentoKmh": current.get("wind_speed_10m"),
        }
